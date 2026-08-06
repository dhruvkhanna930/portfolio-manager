"""Recommendation model (Phase 16).

A port of the recommendation-model workstream onto this app's Flask/SQLAlchemy
stack and Indian asset universe, under §13's guardrails: rule-based first,
educational framing, additive-only (no existing schema or endpoint changes).

Three recommendation modes:

  * ``similar``       -- candidates whose fundamentals resemble what you already
                         hold, for topping up a style you already run.
  * ``complementary`` -- candidates that diversify away from your current sector
                         and beta concentration.
  * ``risk_profile``  -- a cold-start list needing no holdings at all, matched to
                         a stated risk appetite.

Every candidate is scored on four components, **all normalized to 0-100 before
blending**. That normalization is the substantive fix over the original
implementation, which blended a cosine-similarity sum (range ~0-7) against two
0-100 scores using weights of 0.40/0.35/0.25. On those scales the 0.40
"fundamental weight" contributed roughly 2% of the result -- the stated weights
and the effective weights were completely different numbers. Here every
component genuinely carries the weight it claims.

Data sources, in keeping with §14's rule that nothing is fabricated:

  * fundamentals   -- yfinance ``.info``, cached into the existing asset_metrics
                      table (§5.1) so a page load doesn't re-fetch 50 tickers.
  * momentum       -- our own cached price_history (§5.1).
  * sentiment      -- our own news_cache sentiment column (§5.1), which the news
                      provider already supplies. The original reached for a
                      250MB DistilBERT dependency to recompute what we cache.
  * ml forecast    -- services/ml_forecast_service (LSTM/GRU, optional).

The candidate universe is the Nifty50 basket we already sync (§4.1) plus any
stock already in the user's own catalogue -- not a hard-coded list of US
megacaps, which is what the original shipped and which would recommend NASDAQ
tickers to a portfolio denominated in rupees.
"""

import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from models import AssetMetadata, AssetMetric, Holding, NewsCache, PriceHistory, db
from services import ml_forecast_service
from services.analytics_service import _sector_label

# --------------------------------------------------------------------------
# Configuration -- deliberately visible, per §14.3's "not a black box" rule
# --------------------------------------------------------------------------

# Component weights. Anchored on the original's stated intent (fundamentals
# 0.40, trained models 0.25) with its combined 0.35 "AI score" split back into
# the two things it was actually made of -- sentiment 0.4 x 0.35 and forecast
# 0.6 x 0.35 -- rounded to 0.15 and 0.20.
WEIGHTS = {
    "fit": 0.40,
    "momentum": 0.20,
    "sentiment": 0.15,
    "ml": 0.25,
}

NEUTRAL = 50.0

VALID_MODES = ("similar", "complementary", "risk_profile")
VALID_RISK_PROFILES = ("conservative", "balanced", "assertive", "aggressive")

DEFAULT_LIMIT = 8
MAX_LIMIT = 25

# Fundamentals change slowly; a day-old P/E is fine and saves ~50 network calls
# per request. Stored in asset_metrics under this sentinel period.
FUNDAMENTALS_PERIOD = "FUND"
FUNDAMENTALS_MAX_AGE_HOURS = 24

# Features used for the similarity vector. Chosen to describe *style* -- how
# expensive, how volatile, how income-oriented, how profitable -- rather than
# size, so a small-cap and a large-cap running the same playbook can match.
SIMILARITY_FEATURES = ("pe_ratio", "beta", "dividend_yield", "profit_margin", "return_on_equity")

# Plausibility bounds. yfinance occasionally returns a P/E of 40,000 for a
# company emerging from a loss year; left unbounded, one such row dominates the
# standardization and flattens every other stock's score to near-identical.
FEATURE_BOUNDS = {
    "pe_ratio": (0.0, 150.0),
    "beta": (-1.0, 3.5),
    "dividend_yield": (0.0, 15.0),
    "profit_margin": (-100.0, 100.0),
    "return_on_equity": (-100.0, 100.0),
}

NEWS_LOOKBACK_DAYS = 30
MIN_NEWS_FOR_SENTIMENT = 2

DISCLAIMER = (
    "Educational information only -- not investment advice, and not a "
    "prediction. These are rule-based similarity and exposure measures over "
    "your own holdings plus a small model signal, shown so you can see how the "
    "ranking was built. No order is placed and nothing here is a suggestion to "
    "buy or sell."
)


# --------------------------------------------------------------------------
# Fundamentals -- fetched once, cached in asset_metrics
# --------------------------------------------------------------------------


def _as_float(value):
    try:
        if value is None:
            return None
        result = float(value)
        return None if math.isnan(result) or math.isinf(result) else result
    except (TypeError, ValueError):
        return None


def _read_cached_fundamentals(asset_id):
    """Return cached fundamentals if present and fresh, else None."""
    rows = AssetMetric.query.filter(
        AssetMetric.asset_id == asset_id,
        AssetMetric.period == FUNDAMENTALS_PERIOD,
    ).all()
    if not rows:
        return None

    newest = max((r.as_of for r in rows if r.as_of), default=None)
    if newest is None:
        return None
    if datetime.utcnow() - newest > timedelta(hours=FUNDAMENTALS_MAX_AGE_HOURS):
        return None

    return {r.metric_key: (float(r.metric_value) if r.metric_value is not None else None) for r in rows}


def _write_cached_fundamentals(asset_id, values):
    now = datetime.utcnow()
    for key, value in values.items():
        if value is None:
            continue
        row = db.session.get(AssetMetric, (asset_id, key, FUNDAMENTALS_PERIOD))
        if row is None:
            row = AssetMetric(asset_id=asset_id, metric_key=key, period=FUNDAMENTALS_PERIOD)
            db.session.add(row)
        row.metric_value = round(value, 6)
        row.as_of = now
    db.session.commit()


def _fetch_fundamentals(symbol):
    """Live yfinance fundamentals. Returns {} on any failure -- never raises."""
    try:
        import yfinance as yf

        info = yf.Ticker(symbol).info or {}
    except Exception:  # noqa: BLE001 - yfinance is unofficial; absence is normal
        return {}

    dividend_yield = _as_float(info.get("dividendYield"))
    profit_margin = _as_float(info.get("profitMargins"))
    roe = _as_float(info.get("returnOnEquity"))

    return {
        "pe_ratio": _as_float(info.get("trailingPE")),
        "beta": _as_float(info.get("beta")),
        # yfinance is inconsistent here: dividendYield already arrives as a
        # percentage while profitMargins and returnOnEquity arrive as fractions.
        # Converting both the same way is what made a 0.45% yield render as 45%
        # on the asset detail page before it was fixed.
        "dividend_yield": dividend_yield,
        "profit_margin": profit_margin * 100.0 if profit_margin is not None else None,
        "return_on_equity": roe * 100.0 if roe is not None else None,
        "market_cap": _as_float(info.get("marketCap")),
    }


def get_fundamentals(asset, use_cache=True):
    """Fundamentals for one asset, cache-first."""
    if use_cache:
        cached = _read_cached_fundamentals(asset.asset_id)
        if cached is not None:
            return cached

    values = _fetch_fundamentals(asset.symbol)
    if values:
        _write_cached_fundamentals(asset.asset_id, values)
    return values


# --------------------------------------------------------------------------
# Candidate universe
# --------------------------------------------------------------------------


def _candidate_universe():
    """Stocks we can responsibly rank: the synced index basket plus own catalogue.

    Restricted to STOCK because every signal below (beta, P/E, OHLCV windows for
    the network) is equity-shaped. Mutual funds and bonds are deliberately out
    of scope rather than scored with fields that don't apply to them.
    """
    # The Nifty50 seed (§4.1) is itself written into asset_metadata, so every
    # STOCK row is either an index constituent or something the user resolved --
    # both are legitimate candidates and no extra join is needed to include them.
    return AssetMetadata.query.filter(AssetMetadata.asset_type == "STOCK").all()


def _held_asset_ids():
    return {h.asset_id for h in Holding.query.all()}


# Sector labels arrive from two vocabularies that don't agree. The Nifty50 seed
# (§4.1) uses Indian market convention -- "IT", "FMCG", "Metals" -- while assets
# resolved through yfinance carry GICS-style labels -- "Technology", "Consumer
# Goods", "Basic Materials". Left unmapped, a portfolio 47% in "Technology"
# looks like it holds no "IT", so the diversifier mode cheerfully recommends
# HCLTECH to someone already concentrated in TCS, INFY and WIPRO. Verified on
# real data before this map existed.
_SECTOR_ALIASES = {
    "it": "Technology",
    "information technology": "Technology",
    "technology": "Technology",
    "software": "Technology",
    "basic materials": "Metals",
    "metals": "Metals",
    "metals & mining": "Metals",
    "consumer goods": "FMCG",
    "consumer defensive": "FMCG",
    "consumer staples": "FMCG",
    "fmcg": "FMCG",
    "consumer cyclical": "Consumer Durables",
    "consumer discretionary": "Consumer Durables",
    "consumer durables": "Consumer Durables",
    "oil & gas": "Energy",
    "energy": "Energy",
    "pharmaceuticals": "Healthcare",
    "pharma": "Healthcare",
    "healthcare": "Healthcare",
    "financials": "Financial Services",
    "financial services": "Financial Services",
    "banking": "Financial Services",
    "telecommunications": "Telecom",
    "communication services": "Telecom",
    "telecom": "Telecom",
    "utilities": "Power",
    "power": "Power",
}


def _canonical_sector(label):
    """Collapse the two sector vocabularies onto one so gaps are real gaps."""
    if not label:
        return "Other"
    return _SECTOR_ALIASES.get(label.strip().lower(), label.strip())


def _sector_weights():
    """Current portfolio weight per sector, as fractions summing to ~1.

    Value-weighted rather than count-weighted: holding one huge IT position and
    four tiny ones is an IT concentration problem, and a count-based view would
    report it as well diversified.
    """
    from services.analytics_service import compute_holding_metrics

    rows = compute_holding_metrics(Holding.query.all())
    total = sum((r["current_value"] for r in rows), Decimal("0"))
    if total <= 0:
        return {}

    weights = {}
    for row in rows:
        sector = _canonical_sector(_sector_label(row["holding"].asset))
        weights[sector] = weights.get(sector, Decimal("0")) + row["current_value"]

    return {sector: float(value / total) for sector, value in weights.items()}


# --------------------------------------------------------------------------
# Scoring components -- each returns 0-100
# --------------------------------------------------------------------------


def _clamp_feature(key, value):
    if value is None:
        return None
    low, high = FEATURE_BOUNDS[key]
    return max(low, min(high, value))


def _feature_vector(fundamentals):
    """Style vector, or None if too sparse to compare honestly."""
    vector = []
    present = 0
    for key in SIMILARITY_FEATURES:
        value = _clamp_feature(key, fundamentals.get(key))
        if value is None:
            vector.append(None)
        else:
            vector.append(value)
            present += 1
    # Fewer than three shared dimensions and "similarity" is mostly imputation.
    return vector if present >= 3 else None


def _standardize(vectors):
    """Z-score each dimension across candidates, imputing gaps at the mean.

    Standardizing matters because the raw features have wildly different units
    -- a P/E of 25 and a beta of 1.1 are not comparable magnitudes, and cosine
    similarity on raw values would be dominated entirely by P/E.
    """
    n_dims = len(SIMILARITY_FEATURES)
    means, stdevs = [], []

    for d in range(n_dims):
        values = [v[d] for v in vectors if v[d] is not None]
        if values:
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            stdev = math.sqrt(variance)
        else:
            mean, stdev = 0.0, 0.0
        means.append(mean)
        stdevs.append(stdev if stdev > 1e-9 else 1.0)

    return [
        [((v[d] if v[d] is not None else means[d]) - means[d]) / stdevs[d] for d in range(n_dims)]
        for v in vectors
    ]


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return dot / (na * nb)


def _centroid(vectors):
    if not vectors:
        return None
    n_dims = len(vectors[0])
    return [sum(v[d] for v in vectors) / len(vectors) for d in range(n_dims)]


def _momentum_score(asset_id):
    """Trend strength from our own cached closes, 0-100."""
    rows = (
        PriceHistory.query.filter(PriceHistory.asset_id == asset_id)
        .order_by(PriceHistory.price_date.desc())
        .limit(90)
        .all()
    )
    if len(rows) < 30:
        return None

    closes = [float(r.close_price) for r in reversed(rows)]
    if closes[0] <= 0:
        return None

    total_return = (closes[-1] / closes[0] - 1.0) * 100.0
    # Same saturating map the ML score uses, so the two are on one scale.
    return round(NEUTRAL * (1.0 + math.tanh(total_return / 12.0)), 2)


def _sentiment_score(asset_id):
    """Score our own cached news sentiment for this asset, 0-100."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=NEWS_LOOKBACK_DAYS)
    rows = NewsCache.query.filter(
        NewsCache.asset_id == asset_id,
        NewsCache.published_at >= cutoff,
    ).all()

    labelled = [r.sentiment for r in rows if r.sentiment]
    if len(labelled) < MIN_NEWS_FOR_SENTIMENT:
        return None

    points = {"POSITIVE": 100.0, "NEUTRAL": 50.0, "NEGATIVE": 0.0}
    scored = [points.get(s.upper(), 50.0) for s in labelled]
    return round(sum(scored) / len(scored), 2)


def _risk_profile_fit(fundamentals, profile):
    """How well a stock matches a stated risk appetite, 0-100.

    Kept as an explicit rule table rather than a learned model: the thresholds
    are the kind of thing a user should be able to read and disagree with.
    """
    score = NEUTRAL
    pe = fundamentals.get("pe_ratio") or 0.0
    beta_value = fundamentals.get("beta") or 0.0
    dividend = fundamentals.get("dividend_yield") or 0.0
    margin = fundamentals.get("profit_margin") or 0.0
    roe = fundamentals.get("return_on_equity") or 0.0

    if profile == "conservative":
        if 0 < pe < 15:
            score += 15
        elif 15 <= pe < 25:
            score += 5
        if 0 < beta_value < 0.8:
            score += 15
        elif 0.8 <= beta_value < 1.2:
            score += 5
        if dividend > 2.0:
            score += 10
    elif profile == "balanced":
        if 0 < pe < 30:
            score += 10
        if 0 < beta_value < 1.3:
            score += 10
        if margin > 10.0:
            score += 10
    elif profile == "assertive":
        if 15 < pe < 50:
            score += 15
        if 1.0 < beta_value < 1.8:
            score += 10
        if margin > 15.0:
            score += 10
    else:  # aggressive
        if pe > 20:
            score += 15
        if beta_value > 1.2:
            score += 15
        if roe > 15.0:
            score += 10

    return min(100.0, score)


def _complementary_fit(fundamentals, sector, sector_weights, portfolio_beta):
    """How much a stock diversifies the current portfolio, 0-100.

    Sector exposure is scored *continuously* against how much of the portfolio
    already sits in that sector, rather than as an in/out flag. A binary "new
    sector = +25" rule gives every unheld sector an identical score, so a dozen
    candidates tie at the ceiling and the final ordering falls out of whatever
    order the database returned rows in. Weighting by the actual gap means the
    most under-represented sector genuinely ranks first.
    """
    exposure = sector_weights.get(sector, 0.0) if sector else 0.0
    # exposure is a fraction of portfolio value; gap of 1.0 = you hold none.
    gap = max(0.0, 1.0 - exposure)
    score = NEUTRAL + 30.0 * gap

    beta_value = fundamentals.get("beta")
    if beta_value is not None and portfolio_beta is not None and portfolio_beta > 0:
        # Reward lowering portfolio beta, proportional to how much it lowers it.
        relief = max(-1.0, min(1.0, (portfolio_beta - beta_value) / portfolio_beta))
        score += 12.0 * relief

    dividend = fundamentals.get("dividend_yield")
    if dividend is not None:
        score += min(8.0, dividend * 2.0)

    return max(0.0, min(100.0, score))


# --------------------------------------------------------------------------
# Blending
# --------------------------------------------------------------------------


def _blend(components):
    """Weighted blend over whichever components are available.

    Missing components are dropped and the remaining weights renormalized,
    rather than being imputed at the neutral 50. Imputing would quietly pull
    every score toward the middle and make a stock with no news look
    meaningfully different from one with genuinely neutral news.
    """
    usable = [(v, WEIGHTS[k]) for k, v in components.items() if v is not None]
    if not usable:
        return NEUTRAL, 0.0

    total_weight = sum(w for _, w in usable)
    blended = sum(v * w for v, w in usable) / total_weight
    return round(blended, 2), round(total_weight, 2)


def _confidence(coverage, has_ml_model):
    """How much of the blend was backed by real data, as a label."""
    if coverage >= 0.85 and has_ml_model:
        return "high"
    if coverage >= 0.6:
        return "medium"
    return "low"


def _explain(components, mode):
    """Plain-language reasons, ordered by contribution."""
    labels = {
        "fit": {
            "similar": "fundamentals resemble your holdings",
            "complementary": "diversifies your current mix",
            "risk_profile": "matches your stated risk appetite",
        }[mode],
        "momentum": "recent price trend",
        "sentiment": "tone of recent news",
        "ml": "short-horizon model signal",
    }

    reasons = []
    for key, value in components.items():
        if value is None:
            continue
        if value >= 65:
            direction = "supports"
        elif value <= 35:
            direction = "weighs against"
        else:
            continue
        reasons.append({"factor": labels[key], "direction": direction, "score": value})

    reasons.sort(key=lambda r: abs(r["score"] - NEUTRAL), reverse=True)
    return reasons[:3]


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------


def recommend(mode="similar", risk_profile="balanced", limit=DEFAULT_LIMIT, use_ml=True):
    """Rank candidate stocks under one of the three modes.

    Read-only: nothing is persisted except the fundamentals cache, which is a
    cache of fetched market data, not user data.
    """
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {VALID_MODES}")
    profile = (risk_profile or "balanced").lower()
    if profile not in VALID_RISK_PROFILES:
        raise ValueError(f"risk_profile must be one of {VALID_RISK_PROFILES}")

    limit = max(1, min(MAX_LIMIT, int(limit)))

    held_ids = _held_asset_ids()
    universe = _candidate_universe()

    # Candidates exclude what you already own -- the whole point is to surface
    # something new. The original ranked the user's *own* holdings by their
    # similarity to each other and returned those, so its "recommendations" were
    # always a re-listing of the existing portfolio.
    candidates = [a for a in universe if a.asset_id not in held_ids]

    if not candidates:
        return {
            "mode": mode,
            "risk_profile": profile if mode == "risk_profile" else None,
            "recommendations": [],
            "note": "No candidate stocks outside your current holdings yet.",
            "weights": WEIGHTS,
            "model": ml_forecast_service.model_status() if use_ml else None,
            "disclaimer": DISCLAIMER,
        }

    held_assets = [db.session.get(AssetMetadata, aid) for aid in held_ids]
    held_assets = [a for a in held_assets if a is not None and a.asset_type == "STOCK"]
    sector_weights = _sector_weights()

    needs_portfolio = mode in ("similar", "complementary")
    if needs_portfolio and not held_assets:
        return {
            "mode": mode,
            "risk_profile": None,
            "recommendations": [],
            "note": (
                "This mode compares candidates against stocks you hold, and there "
                "are none yet. Try the risk-profile mode, which needs no holdings."
            ),
            "weights": WEIGHTS,
            "model": ml_forecast_service.model_status() if use_ml else None,
            "disclaimer": DISCLAIMER,
        }

    # ---- fundamentals for everything we need to compare -------------------
    candidate_funds = {a.asset_id: get_fundamentals(a) for a in candidates}
    held_funds = {a.asset_id: get_fundamentals(a) for a in held_assets}

    portfolio_beta = None
    betas = [f.get("beta") for f in held_funds.values() if f.get("beta") is not None]
    if betas:
        portfolio_beta = sum(betas) / len(betas)

    # ---- fit component ----------------------------------------------------
    fit_by_id = {}

    if mode == "similar":
        # Standardize candidates and holdings together so both sit in one space;
        # standardizing them separately would make the centroid meaningless.
        ordered = candidates + held_assets
        raw_vectors = []
        for asset in ordered:
            funds = candidate_funds.get(asset.asset_id) or held_funds.get(asset.asset_id) or {}
            raw_vectors.append(_feature_vector(funds) or [None] * len(SIMILARITY_FEATURES))

        standardized = _standardize(raw_vectors)
        candidate_vectors = standardized[: len(candidates)]
        held_vectors = standardized[len(candidates) :]

        centroid = _centroid(held_vectors)
        for asset, vector in zip(candidates, candidate_vectors):
            similarity = _cosine(vector, centroid) if centroid else 0.0
            # cosine lives in [-1, 1]; map onto 0-100 so it shares a scale with
            # every other component.
            fit_by_id[asset.asset_id] = round((similarity + 1.0) * 50.0, 2)

    elif mode == "complementary":
        for asset in candidates:
            fit_by_id[asset.asset_id] = round(
                _complementary_fit(
                    candidate_funds.get(asset.asset_id, {}),
                    _canonical_sector(_sector_label(asset)),
                    sector_weights,
                    portfolio_beta,
                ),
                2,
            )
    else:
        for asset in candidates:
            fit_by_id[asset.asset_id] = round(
                _risk_profile_fit(candidate_funds.get(asset.asset_id, {}), profile), 2
            )

    # ---- shortlist before the expensive signals ---------------------------
    # The ML forecast downloads six months of OHLCV per symbol. Running it over
    # the full universe would mean ~50 network round-trips per page load, so
    # only the top slice by cheap signals gets the model treatment.
    shortlist = sorted(candidates, key=lambda a: fit_by_id.get(a.asset_id, 0.0), reverse=True)
    shortlist = shortlist[: min(len(candidates), max(limit * 2, limit + 4))]

    ml_status = ml_forecast_service.model_status() if use_ml else None
    has_ml_model = bool(ml_status and ml_status.get("trained_models_available"))

    results = []
    for asset in shortlist:
        funds = candidate_funds.get(asset.asset_id, {})

        ml_score = None
        ml_detail = None
        if use_ml:
            ml_detail = ml_forecast_service.forecast(asset.symbol, asset.asset_id)
            if ml_detail.get("source") != "unavailable":
                ml_score = ml_detail.get("score")

        components = {
            "fit": fit_by_id.get(asset.asset_id),
            "momentum": _momentum_score(asset.asset_id),
            "sentiment": _sentiment_score(asset.asset_id),
            "ml": ml_score,
        }

        final_score, coverage = _blend(components)

        results.append(
            {
                "asset_id": asset.asset_id,
                "symbol": asset.symbol,
                "name": asset.name,
                "sector": _canonical_sector(_sector_label(asset)),
                "final_score": final_score,
                "components": components,
                "weights_applied": {k: WEIGHTS[k] for k, v in components.items() if v is not None},
                "coverage": coverage,
                "confidence": _confidence(coverage, has_ml_model),
                "reasons": _explain(components, mode),
                "fundamentals": {
                    "pe_ratio": funds.get("pe_ratio"),
                    "beta": funds.get("beta"),
                    "dividend_yield": funds.get("dividend_yield"),
                    "profit_margin": funds.get("profit_margin"),
                    "return_on_equity": funds.get("return_on_equity"),
                    "market_cap": funds.get("market_cap"),
                },
                "ml_detail": ml_detail,
            }
        )

    results.sort(key=lambda r: r["final_score"], reverse=True)

    return {
        "mode": mode,
        "risk_profile": profile if mode == "risk_profile" else None,
        "recommendations": results[:limit],
        "candidates_considered": len(candidates),
        "holdings_compared": len(held_assets),
        "weights": WEIGHTS,
        "model": ml_status,
        "disclaimer": DISCLAIMER,
    }
