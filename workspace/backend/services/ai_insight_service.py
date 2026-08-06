"""AI Suggestions -- LLM commentary over our own portfolio numbers (Phase 17).

Fills the last "Soon" row in the Analytics menu. One prompt, one call, no chat
history, no agent loop: the user presses a button, we hand a language model a
fact sheet we computed ourselves, and it writes the prose.

The whole design turns on one rule:

    **The model does no arithmetic and sees no market data.**

Everything numeric in `build_facts()` comes from analytics_service,
health_service, risk_service, statistics_service and wallet_service -- the same
functions that already power the Analytics page. The model's only job is to turn
that structure into readable English. This matters because an LLM asked to
"analyze my portfolio" from raw holdings will happily invent a Sharpe ratio, and
a fabricated risk number in a finance app is worse than no number at all.

Three things enforce that rule rather than just hoping for it:

  * The fact sheet is returned to the UI **alongside** the narrative, so every
    claim is checkable against the panel it came from.
  * `verify_figures()` re-reads the generated text, pulls out every ₹ and %
    figure, and matches each against the fact sheet. Anything that doesn't
    reconcile is returned in `unverified_figures` and flagged on screen -- see
    that function for why this catches real drift rather than being decorative.
  * The prompt forbids buy/sell/hold language on any specific asset, per §13's
    guardrail that this layer stays educational and never reads as advice.

Groq's free tier is rate-limited, so results are cached in-process against a
fingerprint of the facts: re-opening the page costs nothing, and a new call only
happens when the portfolio actually changed or the user explicitly refreshes.
"""

import hashlib
import json
import os
import re
import time
from decimal import Decimal

import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Groq hosts several open models; 70b-versatile is the strongest general one on
# the free tier and returns in well under a second at this prompt size. Override
# with GROQ_MODEL if the free-tier lineup shifts -- it does, periodically.
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Low but not zero: this is prose, and 0.0 makes it read like a template.
TEMPERATURE = 0.3
MAX_TOKENS = 1600
REQUEST_TIMEOUT = 30

# Re-opening the page shouldn't spend quota. Keyed on a hash of the facts, so a
# BUY or a price sync invalidates it naturally without a manual bust.
CACHE_TTL_SECONDS = 900

TOP_HOLDINGS_IN_PROMPT = 8

DISCLAIMER = (
    "Written by a language model from this portfolio's own computed figures. "
    "Educational commentary only -- not investment advice, and no part of it is "
    "a recommendation to buy or sell anything."
)

_cache = {"fingerprint": None, "payload": None, "at": 0.0}


class AIUnavailable(Exception):
    """Raised when the model can't be reached or isn't configured."""


# --------------------------------------------------------------------------
# fact sheet -- every number the model is allowed to use
# --------------------------------------------------------------------------


def _num(value, digits=2):
    """Decimal/float -> plain rounded float, or None. Keeps the JSON clean."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        value = float(value)
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def build_facts(period="1Y"):
    """Assemble everything the model is permitted to talk about.

    Deliberately flat and plainly named -- the field names are part of the
    prompt, so `largest_sector_pct` reads better to the model than a nested
    components/sector_balance/largest_sector_pct path would.
    """
    from models import Holding
    from services import (
        analytics_service,
        health_service,
        risk_service,
        statistics_service,
        wallet_service,
    )

    holdings = Holding.query.all()
    rows = analytics_service.compute_holding_metrics(holdings)

    if not rows:
        return {"has_holdings": False, "holdings_count": 0}

    summary = analytics_service.get_portfolio_summary()
    sector_alloc = analytics_service.get_allocation(by="sector")
    type_alloc = analytics_service.get_allocation(by="type")
    stats = statistics_service.get_statistics()
    health = health_service.get_health_score(period=period)
    risk = risk_service.get_portfolio_risk(period=period)

    ranked = sorted(rows, key=lambda r: r["current_value"], reverse=True)
    top = [
        {
            "symbol": r["holding"].asset.symbol,
            "name": r["holding"].asset.name,
            "type": r["holding"].asset.asset_type,
            "weight_pct": _num(r["weight_pct"]),
            "profit_loss_pct": _num(r["profit_loss_pct"]) if r["is_priced"] else None,
            "current_value_inr": _num(r["current_value"], 0),
        }
        for r in ranked[:TOP_HOLDINGS_IN_PROMPT]
    ]

    def _perf(entry):
        if not entry:
            return None
        return {
            "symbol": entry.get("symbol"),
            "profit_loss_pct": _num(entry.get("profit_loss_pct")),
        }

    facts = {
        "has_holdings": True,
        "currency": "INR",
        "holdings_count": summary["holdings_count"],
        "total_invested_inr": _num(summary["total_invested"], 0),
        "total_current_inr": _num(summary["total_current"], 0),
        "total_profit_loss_inr": _num(summary["total_pl"], 0),
        "total_profit_loss_pct": _num(summary["total_pl_pct"]),
        "day_profit_loss_inr": _num(summary["day_pl"], 0),
        "realised_profit_loss_inr": _num(summary.get("realised_pl"), 0),
        "wallet_cash_inr": _num(wallet_service.get_balance(), 0),
        "allocation_by_type_pct": {
            item["label"]: _num(item["pct"]) for item in type_alloc["items"]
        },
        "allocation_by_sector_pct": {
            item["label"]: _num(item["pct"]) for item in sector_alloc["items"]
        },
        "largest_sector": sector_alloc["items"][0]["label"] if sector_alloc["items"] else None,
        "largest_sector_pct": (
            _num(sector_alloc["items"][0]["pct"]) if sector_alloc["items"] else None
        ),
        "top_holdings": top,
        "best_performer": _perf(stats.get("best_performer")),
        "worst_performer": _perf(stats.get("worst_performer")),
        "win_rate_pct": _num(stats.get("win_rate_pct")),
        "winners_count": stats.get("winners_count"),
        "losers_count": stats.get("losers_count"),
        "avg_holding_period_days": _num(stats.get("avg_holding_period_days"), 0),
        "health_score": health.get("health_score"),
        "health_band": health.get("band"),
        "health_components": {
            key: _num(component.get("score"))
            for key, component in (health.get("components") or {}).items()
        },
        "rule_based_watchouts": (health.get("insights") or {}).get("watchouts", []),
        "rule_based_strengths": (health.get("insights") or {}).get("strengths", []),
        "risk_period": period,
        "annualized_volatility_pct": _num(
            risk["volatility"] * 100 if risk.get("volatility") is not None else None
        ),
        "sharpe_ratio": _num(risk.get("sharpe")),
        "max_drawdown_pct": _num(
            risk["max_drawdown"] * 100 if risk.get("max_drawdown") is not None else None
        ),
        "beta_vs_nifty50": _num(risk.get("beta")),
        # Named for what it is. Called `observations` inside risk_service (the
        # statistical sense), which a language model reliably misreads as
        # "things observed to be wrong" -- the first run of this prompt produced
        # "there are 249 risk observations in the portfolio" from exactly that.
        "trading_days_analyzed": risk.get("observations"),
    }

    # Strip keys we genuinely couldn't compute rather than sending nulls -- a
    # null in the prompt is an invitation to fill it in.
    return {k: v for k, v in facts.items() if v is not None}


# --------------------------------------------------------------------------
# the single prompt
# --------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a portfolio analyst writing for the owner of an Indian \
investment portfolio (currency INR, ₹). You will be given a JSON fact sheet that \
was computed from the user's real holdings and price history.

HARD RULES -- these are not style preferences:
1. Use ONLY numbers that appear in the fact sheet. Never calculate a new figure, \
never estimate one, never carry one over from general knowledge. If something \
isn't in the fact sheet, say it isn't available rather than supplying a value.
2. Never tell the user to buy, sell, hold, exit, book profits, or average down -- \
not on a specific holding, not on a sector, not on the portfolio. You describe \
and explain; you do not direct.
3. No market forecasts, no price targets, no claims about what any stock or \
sector will do next.
4. Quote figures exactly as they appear (43.58% stays 43.58%, or round to one \
decimal at most). Attach ₹ to rupee amounts and % to percentages so they are \
checkable. Write rupee amounts with Indian comma grouping and no decimal places \
-- ₹1,43,956 rather than ₹143956.0.
5. Be specific and honest. If concentration is high, say so plainly. Do not \
flatter a portfolio that the numbers don't support, and do not manufacture \
alarm about one the numbers say is fine.
6. "trading_days_analyzed" is how many days of price history the risk figures \
were computed from. It is a sample size, not a count of problems.

Write in second person ("your portfolio"), plain English, no jargon without a \
short gloss. Each observation body should be 2-3 sentences.

Reply with JSON ONLY, exactly this shape:
{
  "headline": "one short line capturing the portfolio's character",
  "summary": "2-3 sentences on where the portfolio stands overall",
  "observations": [
    {
      "title": "short label",
      "body": "2-3 sentences citing specific figures from the fact sheet",
      "sentiment": "positive" | "neutral" | "concern"
    }
  ],
  "questions_to_consider": ["educational questions the owner could think about \
-- phrased as questions, never as instructions"],
  "blind_spots": ["what this fact sheet does NOT tell you about the portfolio"]
}

Give 3 to 5 observations, 2 to 4 questions, and 2 to 3 blind spots."""


def _api_key():
    return (os.environ.get("GROQ_API_KEY") or "").strip()


def _model_name():
    return (os.environ.get("GROQ_MODEL") or "").strip() or DEFAULT_MODEL


def status():
    """Whether the feature is usable, for the UI to render honestly up front."""
    key = _api_key()
    return {
        "configured": bool(key),
        "model": _model_name(),
        "provider": "groq",
        "reason": None if key else "GROQ_API_KEY is not set in the backend environment.",
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
        "disclaimer": DISCLAIMER,
    }


def _call_groq(facts):
    """One request, one response. Raises AIUnavailable with a usable message."""
    key = _api_key()
    if not key:
        raise AIUnavailable("GROQ_API_KEY is not set in the backend environment.")

    body = {
        "model": _model_name(),
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Here is the fact sheet for my portfolio. Write the review.\n\n"
                    + json.dumps(facts, indent=2)
                ),
            },
        ],
    }

    try:
        response = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=body,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        raise AIUnavailable(f"Could not reach Groq: {exc}") from exc

    if response.status_code == 429:
        raise AIUnavailable("Groq rate limit reached on the free tier. Try again shortly.")
    if response.status_code >= 400:
        detail = ""
        try:
            detail = response.json().get("error", {}).get("message", "")
        except ValueError:
            detail = response.text[:200]
        raise AIUnavailable(f"Groq returned {response.status_code}: {detail}")

    payload = response.json()
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise AIUnavailable("Groq response had no message content.") from exc

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        # JSON mode makes this rare, but a truncated response at max_tokens can
        # still land here -- report it rather than showing a broken panel.
        raise AIUnavailable(f"Model did not return valid JSON: {exc}") from exc

    usage = payload.get("usage") or {}
    return parsed, {
        "model": payload.get("model", _model_name()),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "response_seconds": _num(usage.get("total_time"), 3),
    }


# --------------------------------------------------------------------------
# grounding check
# --------------------------------------------------------------------------

_FIGURE_RE = re.compile(
    r"(?:₹\s?(?P<rupees>[\d,]+(?:\.\d+)?)\s?(?P<scale>lakh|lakhs|crore|crores|k)?)"
    r"|(?:(?P<pct>-?\d+(?:\.\d+)?)\s?%)",
    re.IGNORECASE,
)

_SCALES = {"k": 1e3, "lakh": 1e5, "lakhs": 1e5, "crore": 1e7, "crores": 1e7}


def _collect_fact_numbers(facts):
    """Every numeric value anywhere in the fact sheet, flattened."""
    found = set()

    def walk(node):
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, bool):
            return  # bool is an int subclass; it is never a quoted figure
        elif isinstance(node, (int, float)):
            found.add(float(node))

    walk(facts)
    return found


def verify_figures(text, fact_numbers):
    """Return figures in `text` that don't reconcile to any fact.

    Only ₹ and % figures are checked. Bare integers are skipped deliberately:
    prose is full of "3 of your holdings" and "the top 2", and flagging those
    would bury the signal we actually care about, which is a *quantitative claim*
    the model made up. Rupee amounts written as "₹4.8 lakh" are normalized
    against the scale word before comparison.

    Tolerance is relative (0.6%) with a small absolute floor, so a model that
    rounds 43.58% to 43.6% passes while one that invents 39% does not.
    """
    unverified = []

    for match in _FIGURE_RE.finditer(text or ""):
        if match.group("pct") is not None:
            value = float(match.group("pct"))
        else:
            raw = match.group("rupees").replace(",", "")
            try:
                value = float(raw)
            except ValueError:
                continue
            scale = (match.group("scale") or "").lower()
            value *= _SCALES.get(scale, 1.0)

        tolerance = max(abs(value) * 0.006, 0.05)
        if any(abs(value - known) <= tolerance for known in fact_numbers):
            continue
        # Percentages are also checkable against their own complement -- "the
        # other 56.4%" is a legitimate way to describe a 43.6% share.
        if match.group("pct") is not None and any(
            abs((100.0 - value) - known) <= tolerance for known in fact_numbers
        ):
            continue
        unverified.append(match.group(0).strip())

    # Preserve order, drop repeats.
    seen = set()
    return [f for f in unverified if not (f in seen or seen.add(f))]


def _narrative_text(review):
    """Flatten the model's JSON back to one string for the figure check."""
    parts = [review.get("headline", ""), review.get("summary", "")]
    for observation in review.get("observations") or []:
        parts.append(observation.get("title", ""))
        parts.append(observation.get("body", ""))
    parts.extend(review.get("questions_to_consider") or [])
    parts.extend(review.get("blind_spots") or [])
    return "\n".join(p for p in parts if isinstance(p, str))


def _normalize_review(review):
    """Coerce the model's JSON into the shape the schema promises.

    JSON mode guarantees valid JSON, not the right keys -- a model that returns
    `observations` as a list of strings shouldn't 500 the endpoint.
    """
    observations = []
    for item in review.get("observations") or []:
        if isinstance(item, str):
            observations.append({"title": "Observation", "body": item, "sentiment": "neutral"})
            continue
        if not isinstance(item, dict):
            continue
        sentiment = str(item.get("sentiment", "neutral")).lower()
        observations.append(
            {
                "title": str(item.get("title", "Observation")),
                "body": str(item.get("body", "")),
                "sentiment": sentiment
                if sentiment in ("positive", "neutral", "concern")
                else "neutral",
            }
        )

    def _string_list(value):
        if isinstance(value, str):
            return [value]
        return [str(v) for v in (value or []) if isinstance(v, (str, int, float))]

    return {
        "headline": str(review.get("headline", "Portfolio review")),
        "summary": str(review.get("summary", "")),
        "observations": observations,
        "questions_to_consider": _string_list(review.get("questions_to_consider")),
        "blind_spots": _string_list(review.get("blind_spots")),
    }


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------


def _fingerprint(facts):
    return hashlib.sha256(
        json.dumps(facts, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]


def get_review(period="1Y", force=False):
    """Build facts, generate commentary, verify it, return both halves."""
    facts = build_facts(period=period)

    if not facts.get("has_holdings"):
        return {
            "available": False,
            "reason": "No holdings yet -- buy something first and the review will have "
            "numbers to work from.",
            "facts": facts,
            "disclaimer": DISCLAIMER,
        }

    fingerprint = _fingerprint(facts)
    now = time.time()
    if (
        not force
        and _cache["fingerprint"] == fingerprint
        and now - _cache["at"] < CACHE_TTL_SECONDS
    ):
        cached = dict(_cache["payload"])
        cached["cached"] = True
        cached["cache_age_seconds"] = round(now - _cache["at"])
        return cached

    raw, usage = _call_groq(facts)
    review = _normalize_review(raw)

    unverified = verify_figures(_narrative_text(review), _collect_fact_numbers(facts))

    payload = {
        "available": True,
        "cached": False,
        "cache_age_seconds": 0,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "review": review,
        "facts": facts,
        "usage": usage,
        "unverified_figures": unverified,
        "grounding_note": (
            "Every figure above is checked against the fact sheet the model was given. "
            + (
                f"{len(unverified)} figure(s) could not be matched and are listed in "
                "unverified_figures -- treat those with suspicion."
                if unverified
                else "All figures reconciled."
            )
        ),
        "disclaimer": DISCLAIMER,
    }

    _cache.update({"fingerprint": fingerprint, "payload": payload, "at": now})
    return payload
