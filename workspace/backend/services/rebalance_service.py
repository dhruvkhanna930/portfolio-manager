"""Rebalancing simulator (CLAUDE.md §14.8).

A pure "what if": given hypothetical target weights, recompute what §14.1's risk
metrics and §14.3's diversification would have looked like *had the portfolio
been held at those weights over the same historical window*.

Nothing here is persisted and no transaction is ever created -- this answers
"what would this allocation have felt like", not "place these trades".
"""

from decimal import Decimal

from models import Holding
from services import analytics_service, health_service, risk_service

WEIGHT_SUM_TOLERANCE = 0.01  # accept 0.99-1.01 to allow for rounding in the UI


class InvalidWeightsError(Exception):
    pass


def _hypothetical_return_series(weight_by_asset, period):
    """Daily returns of a fixed-weight portfolio over the historical window.

    Constant weights imply continuous rebalancing back to target, which is the
    standard way to evaluate a target allocation and is exactly the "what if I
    had held these proportions" question being asked.

    Assets without enough price history in the window (e.g. a dead or merged
    fund whose NAV feed stopped years ago) are dropped and the remaining weights
    renormalized. An earlier version instead intersected all assets' trading
    dates, which meant one stale holding emptied the intersection and silently
    produced zero observations and all-null metrics. Dropping-and-renormalizing
    degrades gracefully, and the excluded ids are returned so the caller can say
    which assets the simulation actually covers.

    Returns (returns_by_date, index_by_date, excluded_asset_ids).
    """
    start = risk_service._period_start(period)
    returns_by_asset = {
        asset_id: risk_service.to_daily_returns(
            risk_service.get_asset_price_series(asset_id, start_date=start)
        )
        for asset_id in weight_by_asset
    }

    contributing, excluded = [], []
    for asset_id, weight in weight_by_asset.items():
        if weight <= 0:
            continue
        if len(returns_by_asset[asset_id]) >= risk_service.MIN_OBSERVATIONS:
            contributing.append(asset_id)
        else:
            excluded.append(asset_id)

    if not contributing:
        return {}, {}, excluded

    total_weight = sum(weight_by_asset[a] for a in contributing)
    if total_weight <= 0:
        return {}, {}, excluded
    normalized = {a: weight_by_asset[a] / total_weight for a in contributing}

    # Union of trading dates across contributing assets; on any given date only
    # those that actually traded are counted, with their weights renormalized so
    # a market holiday for one name doesn't read as that name returning 0%.
    all_dates = sorted({d for a in contributing for d in returns_by_asset[a]})

    returns_by_date = {}
    for d in all_dates:
        present = [a for a in contributing if d in returns_by_asset[a]]
        weight_present = sum(normalized[a] for a in present)
        if weight_present <= 0:
            continue
        returns_by_date[d] = sum(
            (normalized[a] / weight_present) * returns_by_asset[a][d] for a in present
        )

    index_by_date, level = {}, 100.0
    for d in sorted(returns_by_date):
        level *= 1.0 + returns_by_date[d]
        index_by_date[d] = level
    return returns_by_date, index_by_date, excluded


def preview(target_weights, period="1Y", benchmark_code=risk_service.DEFAULT_BENCHMARK):
    """target_weights: {asset_id: weight} where weights are fractions summing to ~1.

    Returns current vs. hypothetical metrics side by side plus the implied trades
    -- described only as value shifts, never as orders.
    """
    if not target_weights:
        raise InvalidWeightsError("no target weights provided")

    weights = {int(k): float(v) for k, v in target_weights.items()}
    if any(w < 0 for w in weights.values()):
        raise InvalidWeightsError("weights cannot be negative")

    total = sum(weights.values())
    if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
        raise InvalidWeightsError(
            f"weights must sum to 1.0 (got {total:.4f}); send fractions, not percentages"
        )
    weights = {k: v / total for k, v in weights.items()}  # normalize away rounding

    holdings = {h.asset_id: h for h in Holding.query.all()}
    unknown = [a for a in weights if a not in holdings]
    if unknown:
        raise InvalidWeightsError(
            f"asset_id(s) {unknown} are not currently held -- the simulator reweights "
            "existing holdings, it doesn't add new ones"
        )

    rows = analytics_service.compute_holding_metrics(list(holdings.values()))
    total_current = sum((r["current_value"] for r in rows), Decimal("0"))
    current_value_by_asset = {r["holding"].asset_id: r["current_value"] for r in rows}

    # --- current state ---
    current_weights = (
        [float(v / total_current) for v in current_value_by_asset.values()] if total_current > 0 else []
    )
    current_risk = risk_service.get_portfolio_risk(period=period, benchmark_code=benchmark_code)

    # --- hypothetical state ---
    _hyp_returns, hyp_index, excluded = _hypothetical_return_series(weights, period)
    start = risk_service._period_start(period)
    bench_returns = risk_service.to_daily_returns(
        risk_service.get_benchmark_price_series(benchmark_code, start_date=start)
    )
    hyp_risk = risk_service.compute_metrics(hyp_index, bench_returns)

    hyp_weight_list = [w for w in weights.values() if w > 0]

    # --- implied shifts ---
    changes = []
    for asset_id, holding in holdings.items():
        current_value = current_value_by_asset.get(asset_id, Decimal("0"))
        target_value = total_current * Decimal(str(weights.get(asset_id, 0.0)))
        changes.append(
            {
                "asset_id": asset_id,
                "symbol": holding.asset.symbol,
                "name": holding.asset.name,
                "current_value": current_value,
                "current_weight_pct": (
                    current_value / total_current * 100 if total_current > 0 else Decimal("0")
                ),
                "target_value": target_value,
                "target_weight_pct": Decimal(str(weights.get(asset_id, 0.0) * 100)),
                "value_change": target_value - current_value,
            }
        )
    changes.sort(key=lambda c: c["value_change"], reverse=True)

    def _pack(risk, weight_list):
        return {
            "volatility": risk.get("volatility"),
            "annualized_return": risk.get("annualized_return"),
            "sharpe": risk.get("sharpe"),
            "sortino": risk.get("sortino"),
            "max_drawdown": risk.get("max_drawdown"),
            "var_95": risk.get("var_95"),
            "beta": risk.get("beta"),
            "observations": risk.get("observations"),
            "diversification_score": (
                health_service.diversification_score(weight_list) if weight_list else None
            ),
            "hhi": health_service.herfindahl_index(weight_list) if weight_list else None,
        }

    return {
        "period": period,
        "benchmark_code": benchmark_code,
        "total_current": total_current,
        "current": _pack(current_risk, current_weights),
        "hypothetical": _pack(hyp_risk, hyp_weight_list),
        "excluded_from_simulation": [
            {
                "asset_id": asset_id,
                "symbol": holdings[asset_id].asset.symbol,
                "reason": "not enough price history in this period to simulate",
            }
            for asset_id in excluded
        ],
        "changes": changes,
        "note": (
            "Hypothetical only -- nothing is saved and no transaction is created. Assumes "
            "these weights were held constantly over the historical window, which implies "
            "continuous rebalancing and ignores taxes and trading costs."
        ),
        "disclaimer": health_service.DISCLAIMER,
    }


def equal_weight_suggestion():
    """Convenience: the equal-weight vector across current holdings, offered as a
    starting point for the simulator rather than as a recommendation.
    """
    holdings = Holding.query.all()
    if not holdings:
        return {}
    w = 1.0 / len(holdings)
    return {h.asset_id: w for h in holdings}
