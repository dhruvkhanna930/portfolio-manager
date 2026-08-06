"""Diversification + Portfolio Health Score (CLAUDE.md §14.3).

Carries §13's guardrails: this is **rule-based and educational**, never
personalized financial advice. Every component is a transparent formula over
data we already hold, the weights are named constants below rather than magic
numbers, and the response ships the component breakdown so a user can see
exactly why a score is what it is instead of trusting a black box.
"""

import math
from decimal import Decimal

from models import Holding
from services import analytics_service, risk_service

# --- Health Score component weights (§14.3). Must sum to 1.0. ---
WEIGHT_DIVERSIFICATION = 0.30
WEIGHT_CASH_RESERVE = 0.25
WEIGHT_VOLATILITY = 0.25
WEIGHT_SECTOR_BALANCE = 0.20

_WEIGHTS = (
    WEIGHT_DIVERSIFICATION + WEIGHT_CASH_RESERVE + WEIGHT_VOLATILITY + WEIGHT_SECTOR_BALANCE
)
assert abs(_WEIGHTS - 1.0) < 1e-9, "Health Score weights must sum to 1.0"

# §14.3 says cash reserve is "capped/scaled" and volatility "normalized" without
# fixing the scale, so both are pinned here explicitly rather than left implicit.

# Cash at or above this share of portfolio value scores a full 100. 10% is a
# conventional "dry powder" level; beyond it, more idle cash isn't more health.
CASH_RESERVE_TARGET_RATIO = 0.10

# Annualized volatility mapped onto 0-100: 0% vol -> 0, at/above this -> 100.
# 40% is roughly a high-volatility single-stock equity portfolio, so it's the
# point where the volatility component contributes nothing.
VOLATILITY_CEILING_PCT = 40.0

# Bands used only for wording the educational summary, not for the number.
BAND_STRONG = 75
BAND_MODERATE = 50

# A single sector above this share of the portfolio is worth pointing out. Keyed
# off the actual allocation percentage rather than the derived score, so the
# threshold means the plainly-readable thing it says.
SECTOR_CONCENTRATION_ALERT_PCT = 40.0

DISCLAIMER = (
    "Educational information only, not investment advice. These scores are simple "
    "rule-based measures of your current allocation and past price volatility -- "
    "they do not predict future returns and do not account for your goals, taxes, "
    "or personal circumstances."
)


def _weights_from_rows(rows):
    total = sum((r["current_value"] for r in rows), Decimal("0"))
    if total <= 0:
        return [], total
    return [float(r["current_value"] / total) for r in rows], total


def shannon_entropy(weights):
    """-Sum(w ln w). Zero-weight holdings are skipped (0 ln 0 is defined as 0)."""
    return -sum(w * math.log(w) for w in weights if w > 0)


def herfindahl_index(weights):
    """Sum(w^2). 1.0 = everything in one holding; 1/n = perfectly even."""
    return sum(w * w for w in weights)


def diversification_score(weights):
    """Shannon entropy normalized to 0-100, where 100 is a perfectly even split.

    ln(n) is the maximum possible entropy for n holdings, so dividing by it
    measures evenness independently of how many holdings there are. With a single
    holding ln(1) = 0 and the ratio is undefined -- that case is a genuinely
    undiversified portfolio, so it scores 0 rather than dividing by zero.
    """
    n = len([w for w in weights if w > 0])
    if n <= 1:
        return 0.0
    return (shannon_entropy(weights) / math.log(n)) * 100.0


def cash_reserve_score(wallet_balance, total_current):
    """Idle cash as a share of invested value, scaled against the target ratio.

    A fully-invested portfolio with no cash buffer scores 0; one holding the
    target share or more scores 100. If nothing is invested yet, cash is all
    there is -- that's not a "healthy reserve", so it scores 0 rather than 100.
    """
    total = float(total_current)
    cash = float(wallet_balance)
    if total <= 0:
        return 0.0
    ratio = cash / total
    return max(0.0, min(1.0, ratio / CASH_RESERVE_TARGET_RATIO)) * 100.0


def volatility_score(annualized_volatility_pct):
    """100 - normalized volatility: lower volatility scores higher.

    Returns None when volatility can't be measured (too little price history) so
    the caller can renormalize instead of silently treating unknown as perfect.
    """
    if annualized_volatility_pct is None:
        return None
    normalized = min(100.0, (annualized_volatility_pct / VOLATILITY_CEILING_PCT) * 100.0)
    return 100.0 - normalized


def sector_balance_score(sector_items, total_current):
    """Inverse of the largest single-sector share (§14.3).

    100% in one sector -> 0; an even spread across sectors -> high. With only one
    sector present the score is 0, which is the intended reading: no sector
    diversification at all.
    """
    total = float(total_current)
    if total <= 0 or not sector_items:
        return 0.0
    largest = max(float(item["value"]) for item in sector_items) / total
    return (1.0 - largest) * 100.0


def _build_insights(components, hhi, n_holdings, largest_sector):
    """Strengths / watch-outs / suggestions, phrased as observations and
    educational prompts (§13) -- never "buy X" or "sell Y".
    """
    strengths, watchouts, suggestions = [], [], []

    div = components["diversification"]["score"]
    if div >= 70:
        strengths.append(f"Holdings are fairly evenly weighted (diversification {div:.0f}/100).")
    elif div > 0:
        watchouts.append(
            f"Value is concentrated in a few holdings (diversification {div:.0f}/100)."
        )
        suggestions.append(
            "Concentration isn't automatically bad, but it does mean your result depends "
            "heavily on a small number of positions."
        )
    if n_holdings <= 1:
        watchouts.append("A single holding carries the entire portfolio's risk.")

    cash = components["cash_reserve"]["score"]
    if cash >= 80:
        strengths.append("You're holding a healthy cash buffer relative to invested value.")
    elif cash <= 20:
        watchouts.append("Very little idle cash relative to invested value.")
        suggestions.append(
            "Some investors keep a cash reserve so they aren't forced to sell at a bad time."
        )

    vol = components["volatility"]["score"]
    if vol is not None:
        measured = components["volatility"]["annualized_volatility_pct"]
        if vol >= 60:
            strengths.append(f"Historical volatility is moderate ({measured:.1f}% annualized).")
        elif vol <= 30:
            watchouts.append(f"Historical volatility is high ({measured:.1f}% annualized).")
            suggestions.append(
                "Higher volatility means larger swings in both directions -- worth checking "
                "it matches the time horizon you're investing over."
            )

    largest_sector_pct = float(largest_sector["pct"]) if largest_sector else 0.0
    if largest_sector and largest_sector_pct >= SECTOR_CONCENTRATION_ALERT_PCT:
        watchouts.append(
            f"{largest_sector['label']} makes up {largest_sector_pct:.0f}% of the portfolio."
        )
        suggestions.append(
            "When one sector dominates, sector-specific news tends to move the whole portfolio "
            "at once -- even a portfolio that looks evenly split by holding can be concentrated "
            "by sector."
        )
    elif components["sector_balance"]["score"] >= 65:
        strengths.append("Exposure is spread reasonably across sectors.")

    if hhi >= 0.25:
        watchouts.append(
            f"Concentration index (HHI) is {hhi:.2f} -- above 0.25 is generally considered concentrated."
        )

    return {"strengths": strengths, "watchouts": watchouts, "suggestions": suggestions}


def get_health_score(period="1Y"):
    """Portfolio Health Score + its full component breakdown (§14.3).

    Replaces the old /api/portfolio/insights panel.
    """
    from services import wallet_service

    holdings = Holding.query.all()
    rows = analytics_service.compute_holding_metrics(holdings)
    weights, total_current = _weights_from_rows(rows)

    if not weights:
        return {
            "health_score": None,
            "insufficient_data": True,
            "reason": "No holdings yet -- add some investments to see a health score.",
            "disclaimer": DISCLAIMER,
            "components": {},
            "insights": {"strengths": [], "watchouts": [], "suggestions": []},
        }

    hhi = herfindahl_index(weights)
    div_score = diversification_score(weights)

    wallet_balance = wallet_service.get_balance()
    cash_score = cash_reserve_score(wallet_balance, total_current)

    portfolio_risk = risk_service.get_portfolio_risk(period=period)
    raw_vol = portfolio_risk.get("volatility")
    vol_pct = raw_vol * 100.0 if raw_vol is not None else None
    vol_score = volatility_score(vol_pct)

    allocation = analytics_service.get_allocation(by="sector")
    sector_items = allocation["items"]
    sec_score = sector_balance_score(sector_items, total_current)
    largest_sector = sector_items[0] if sector_items else None

    components = {
        "diversification": {
            "score": div_score,
            "weight": WEIGHT_DIVERSIFICATION,
            "shannon_entropy": shannon_entropy(weights),
            "hhi": hhi,
            "n_holdings": len(weights),
            "explanation": "Shannon entropy of holding weights, normalized so an even split scores 100.",
        },
        "cash_reserve": {
            "score": cash_score,
            "weight": WEIGHT_CASH_RESERVE,
            "wallet_balance": wallet_balance,
            "target_ratio": CASH_RESERVE_TARGET_RATIO,
            "explanation": (
                f"Idle cash vs. invested value, scaled so {CASH_RESERVE_TARGET_RATIO:.0%} or more scores 100."
            ),
        },
        "volatility": {
            "score": vol_score,
            "weight": WEIGHT_VOLATILITY,
            "annualized_volatility_pct": vol_pct,
            "ceiling_pct": VOLATILITY_CEILING_PCT,
            "explanation": (
                f"100 minus annualized volatility normalized against a {VOLATILITY_CEILING_PCT:.0f}% ceiling."
            ),
        },
        "sector_balance": {
            "score": sec_score,
            "weight": WEIGHT_SECTOR_BALANCE,
            "largest_sector": largest_sector["label"] if largest_sector else None,
            "largest_sector_pct": float(largest_sector["pct"]) if largest_sector else None,
            "explanation": "Inverse of the largest single sector's share of the portfolio.",
        },
    }

    # Volatility can be unmeasurable on a very new portfolio. Rather than scoring
    # it 0 (which would unfairly tank the total) or 100 (which would flatter it),
    # drop it and renormalize the remaining weights so they still sum to 1.
    usable = [(c["weight"], c["score"]) for c in components.values() if c["score"] is not None]
    total_weight = sum(w for w, _ in usable)
    health = round(sum(w * s for w, s in usable) / total_weight) if total_weight > 0 else None

    return {
        "health_score": health,
        "insufficient_data": False,
        "period": period,
        "band": (
            "Strong" if health >= BAND_STRONG else "Moderate" if health >= BAND_MODERATE else "Needs attention"
        )
        if health is not None
        else None,
        "excluded_components": [k for k, c in components.items() if c["score"] is None],
        "components": components,
        "insights": _build_insights(components, hhi, len(weights), largest_sector),
        "disclaimer": DISCLAIMER,
    }
