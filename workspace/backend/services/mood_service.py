"""Market Mood Score (CLAUDE.md §14.9).

Our own simple composite of breadth, momentum and volatility across the curated
market_index_constituents basket. Explicitly NOT a Fear & Greed Index clone --
different inputs, different methodology, no claim of equivalence to any
proprietary index (§0.3 item 20).

Every input is real cached data: today's price_snapshot day-change for breadth,
price_history moving averages for momentum, price_history returns for volatility.
"""

import statistics
from datetime import date, timedelta

from models import MarketIndexConstituent
from services import risk_service
from services.market_service import DEFAULT_INDEX

# Component weights -- named, not magic numbers, same principle as §14.3.
WEIGHT_BREADTH = 0.40
WEIGHT_MOMENTUM = 0.35
WEIGHT_VOLATILITY = 0.25

assert abs(WEIGHT_BREADTH + WEIGHT_MOMENTUM + WEIGHT_VOLATILITY - 1.0) < 1e-9

MOMENTUM_SHORT_DAYS = 5
MOMENTUM_LONG_DAYS = 20

# A short-vs-long moving-average spread of +/- this much maps to the full 0-100
# momentum range. 5% is a large divergence for a broad basket.
MOMENTUM_FULL_SCALE_PCT = 5.0

# Annualized basket volatility at or above this scores 0 on the calm axis.
VOLATILITY_CEILING_PCT = 35.0

BANDS = (
    (80, "Very Bullish"),
    (60, "Bullish"),
    (40, "Neutral"),
    (20, "Bearish"),
    (0, "Very Bearish"),
)

DISCLAIMER = (
    "The Market Mood Score is our own simple composite of market breadth, momentum and "
    "volatility across a curated large-cap basket. It is descriptive of recent market "
    "behaviour, not a forecast, and is not related to any proprietary sentiment index."
)


def _band(score):
    for threshold, label in BANDS:
        if score >= threshold:
            return label
    return "Very Bearish"


def _breadth_component(constituents):
    """Share of the basket up on the day. 50 = evenly split, 100 = everything up."""
    changes = [
        float(c.asset.price_snapshot.day_change_pct)
        for c in constituents
        if c.asset.price_snapshot is not None and c.asset.price_snapshot.day_change_pct is not None
    ]
    if not changes:
        return None, {"advancers": 0, "decliners": 0, "measured": 0}
    advancers = sum(1 for v in changes if v > 0)
    decliners = sum(1 for v in changes if v < 0)
    return (
        100.0 * advancers / len(changes),
        {"advancers": advancers, "decliners": decliners, "measured": len(changes)},
    )


def _basket_index_series(asset_ids, lookback_days=120):
    """Equal-weighted basket level from cached price_history.

    Equal-weighted rather than cap-weighted: we don't store market caps, and
    inventing them would violate the §14 rule. Equal weighting is a legitimate,
    clearly-stated methodology, not an approximation of a cap-weighted index.
    """
    start = date.today() - timedelta(days=lookback_days * 2)
    per_asset = {}
    for asset_id in asset_ids:
        series = risk_service.get_asset_price_series(asset_id, start_date=start)
        if len(series) >= MOMENTUM_LONG_DAYS + 1:
            per_asset[asset_id] = series
    if not per_asset:
        return {}

    # Only dates where every included constituent traded, so the basket level
    # never jumps because one name is missing a quote.
    shared = set.intersection(*(set(s) for s in per_asset.values()))
    if len(shared) < MOMENTUM_LONG_DAYS + 1:
        return {}

    ordered = sorted(shared)
    base = {aid: per_asset[aid][ordered[0]] for aid in per_asset}
    level_by_date = {}
    for d in ordered:
        normalized = [per_asset[aid][d] / base[aid] for aid in per_asset if base[aid] > 0]
        if normalized:
            level_by_date[d] = 100.0 * sum(normalized) / len(normalized)
    return level_by_date


def _momentum_component(level_by_date):
    """Short vs. long moving average of the basket, mapped onto 0-100."""
    dates = sorted(level_by_date)
    if len(dates) < MOMENTUM_LONG_DAYS:
        return None, {}
    levels = [level_by_date[d] for d in dates]
    short_ma = statistics.fmean(levels[-MOMENTUM_SHORT_DAYS:])
    long_ma = statistics.fmean(levels[-MOMENTUM_LONG_DAYS:])
    if long_ma <= 0:
        return None, {}
    spread_pct = (short_ma - long_ma) / long_ma * 100.0
    scaled = max(-1.0, min(1.0, spread_pct / MOMENTUM_FULL_SCALE_PCT))
    return (scaled + 1.0) / 2.0 * 100.0, {
        f"ma{MOMENTUM_SHORT_DAYS}": round(short_ma, 2),
        f"ma{MOMENTUM_LONG_DAYS}": round(long_ma, 2),
        "spread_pct": round(spread_pct, 2),
    }


def _volatility_component(level_by_date):
    """Calm scores high: 100 minus normalized annualized basket volatility."""
    returns_by_date = risk_service.to_daily_returns(level_by_date)
    returns = [returns_by_date[d] for d in sorted(returns_by_date)]
    if len(returns) < MOMENTUM_LONG_DAYS:
        return None, {}
    vol = risk_service.annualized_volatility(returns)
    if vol is None:
        return None, {}
    vol_pct = vol * 100.0
    normalized = min(100.0, vol_pct / VOLATILITY_CEILING_PCT * 100.0)
    return 100.0 - normalized, {"annualized_volatility_pct": round(vol_pct, 2)}


def get_market_mood(index_name=DEFAULT_INDEX):
    constituents = MarketIndexConstituent.query.filter_by(index_name=index_name).all()
    if not constituents:
        return {
            "index_name": index_name,
            "score": None,
            "band": None,
            "insufficient_data": True,
            "reason": "No index constituents seeded yet.",
            "components": {},
            "disclaimer": DISCLAIMER,
        }

    breadth, breadth_detail = _breadth_component(constituents)
    level_by_date = _basket_index_series([c.asset_id for c in constituents])
    momentum, momentum_detail = _momentum_component(level_by_date)
    calm, vol_detail = _volatility_component(level_by_date)

    components = {
        "breadth": {
            "score": breadth,
            "weight": WEIGHT_BREADTH,
            "detail": breadth_detail,
            "explanation": "Share of basket constituents trading up today.",
        },
        "momentum": {
            "score": momentum,
            "weight": WEIGHT_MOMENTUM,
            "detail": momentum_detail,
            "explanation": (
                f"{MOMENTUM_SHORT_DAYS}-day vs {MOMENTUM_LONG_DAYS}-day moving average of an "
                "equal-weighted basket level."
            ),
        },
        "calm": {
            "score": calm,
            "weight": WEIGHT_VOLATILITY,
            "detail": vol_detail,
            "explanation": "100 minus recent annualized basket volatility, normalized.",
        },
    }

    # Renormalize over whatever could actually be measured, so a missing
    # component shifts nothing rather than dragging the composite toward zero.
    usable = [(c["weight"], c["score"]) for c in components.values() if c["score"] is not None]
    total_weight = sum(w for w, _ in usable)
    score = round(sum(w * s for w, s in usable) / total_weight) if total_weight > 0 else None

    return {
        "index_name": index_name,
        "score": score,
        "band": _band(score) if score is not None else None,
        "insufficient_data": score is None,
        "constituents_count": len(constituents),
        "excluded_components": [k for k, c in components.items() if c["score"] is None],
        "components": components,
        "methodology": (
            f"Weighted composite: breadth {WEIGHT_BREADTH:.0%}, momentum {WEIGHT_MOMENTUM:.0%}, "
            f"calm {WEIGHT_VOLATILITY:.0%}, computed from our own cached prices for the "
            f"{index_name} basket."
        ),
        "disclaimer": DISCLAIMER,
    }
