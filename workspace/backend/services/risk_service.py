"""Risk metrics (CLAUDE.md §14.1) and correlation (§14.2).

Everything here is derived from daily returns computed off our own cached
price_history / the §6.8 portfolio value series. Nothing is fetched from a
"risk metrics" API -- there isn't a free one, and inventing numbers would break
the §14 rule.

Two things that are easy to get wrong and are handled explicitly:

  * **Calendar alignment.** Two assets only share a return observation on dates
    where *both* traded. Beta/correlation/tracking-error are computed on the
    intersection of date sets, never on two independently-indexed arrays that
    happen to be the same length. Misaligning these is the classic way to get a
    beta of 40 or a correlation outside [-1, 1].
  * **Stale series.** A dead/merged fund whose history stops years ago would
    otherwise silently contribute a flat or ancient return series. Anything with
    too few overlapping observations returns None rather than a confident-looking
    fabricated number.
"""

import math
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from models import AssetMetric, Holding, PriceHistory, db

TRADING_DAYS_PER_YEAR = 252

# Risk-free rate is an assumption, not fetched data (§14 rule) -- no free live
# G-Sec API. Surfaced in the response so the UI can label it.
DEFAULT_RISK_FREE_RATE_PCT = Decimal("6.5")

# Below this many overlapping observations, a metric is statistically meaningless
# -- return None instead of a number that looks authoritative.
MIN_OBSERVATIONS = 30

VALID_PERIODS = ("1Y", "3Y", "5Y", "ALL")

_PERIOD_DELTA = {
    "1Y": relativedelta(years=1),
    "3Y": relativedelta(years=3),
    "5Y": relativedelta(years=5),
}

DEFAULT_BENCHMARK = "NIFTY50"


# --------------------------------------------------------------------------
# series helpers
# --------------------------------------------------------------------------


def _period_start(period):
    if period == "ALL" or period not in _PERIOD_DELTA:
        return None
    return date.today() - _PERIOD_DELTA[period]


def get_asset_price_series(asset_id, start_date=None):
    """{date: float close} from our cached price_history."""
    query = PriceHistory.query.filter_by(asset_id=asset_id)
    if start_date:
        query = query.filter(PriceHistory.price_date >= start_date)
    rows = query.order_by(PriceHistory.price_date).all()
    return {r.price_date: float(r.close_price) for r in rows}


def get_benchmark_price_series(benchmark_code, start_date=None):
    from services.benchmark_service import get_benchmark_series

    return {d: float(v) for d, v in get_benchmark_series(benchmark_code, start_date=start_date)}


def to_daily_returns(price_by_date):
    """{date: price} -> {date: simple return vs. the previous *available* close}.

    Keyed by date (not a bare list) so callers can align two series on shared
    dates. A zero/negative prior price is skipped rather than producing an
    infinite return.
    """
    dates = sorted(price_by_date)
    returns = {}
    for prev_d, d in zip(dates, dates[1:]):
        prev = price_by_date[prev_d]
        cur = price_by_date[d]
        if prev and prev > 0:
            returns[d] = (cur - prev) / prev
    return returns


def align(returns_a, returns_b):
    """Two return dicts -> two lists over their shared dates, in date order.
    This is what keeps beta/correlation honest.
    """
    shared = sorted(set(returns_a) & set(returns_b))
    return [returns_a[d] for d in shared], [returns_b[d] for d in shared]


# --------------------------------------------------------------------------
# primitive statistics (plain Python -- these are small series, and being
# explicit here makes the formulas auditable against §14.1)
# --------------------------------------------------------------------------


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _stdev(xs):
    """Sample standard deviation (n-1). Sample, not population: these are a
    sample of returns drawn from an ongoing process, not a complete population.
    """
    n = len(xs)
    if n < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def _covariance(xs, ys):
    n = len(xs)
    if n < 2 or n != len(ys):
        return 0.0
    mx, my = _mean(xs), _mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (n - 1)


def _percentile(xs, pct):
    """Linear-interpolated percentile; pct in [0, 100]."""
    if not xs:
        return None
    ordered = sorted(xs)
    if len(ordered) == 1:
        return ordered[0]
    k = (len(ordered) - 1) * (pct / 100.0)
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return ordered[int(k)]
    return ordered[lo] * (hi - k) + ordered[hi] * (k - lo)


def pearson_correlation(xs, ys):
    """Pearson r, clamped to [-1, 1] to absorb float error at the extremes."""
    sx, sy = _stdev(xs), _stdev(ys)
    if sx == 0 or sy == 0:
        return None
    r = _covariance(xs, ys) / (sx * sy)
    return max(-1.0, min(1.0, r))


# --------------------------------------------------------------------------
# §14.1 metrics
# --------------------------------------------------------------------------


def annualized_volatility(returns):
    if len(returns) < 2:
        return None
    return _stdev(returns) * math.sqrt(TRADING_DAYS_PER_YEAR)


def annualized_return(returns):
    """Arithmetic mean daily return, annualized -- matches the Sharpe numerator
    in §14.1 (mean(daily_return) x 252).
    """
    if not returns:
        return None
    return _mean(returns) * TRADING_DAYS_PER_YEAR


def sharpe_ratio(returns, risk_free_rate_pct):
    vol = annualized_volatility(returns)
    if not vol:
        return None
    return (annualized_return(returns) - float(risk_free_rate_pct) / 100.0) / vol


def sortino_ratio(returns, risk_free_rate_pct):
    """Same as Sharpe but the denominator only penalizes downside deviation --
    upside volatility isn't risk to an investor.
    """
    downside = [r for r in returns if r < 0]
    if len(downside) < 2:
        return None
    downside_dev = _stdev(downside) * math.sqrt(TRADING_DAYS_PER_YEAR)
    if downside_dev == 0:
        return None
    return (annualized_return(returns) - float(risk_free_rate_pct) / 100.0) / downside_dev


def max_drawdown(price_by_date):
    """Worst peak-to-trough decline over the window, as a positive fraction.

    Computed on the *price/value* path rather than by compounding returns, so it
    reflects the actual observed trough.
    """
    dates = sorted(price_by_date)
    if len(dates) < 2:
        return None
    peak = float("-inf")
    worst = 0.0
    for d in dates:
        value = price_by_date[d]
        peak = max(peak, value)
        if peak > 0:
            worst = max(worst, (peak - value) / peak)
    return worst


def value_at_risk_95(returns):
    """Historical (not parametric) VaR: the 5th percentile of observed daily
    returns. Returned as a positive magnitude of loss.
    """
    if len(returns) < MIN_OBSERVATIONS:
        return None
    p5 = _percentile(returns, 5)
    return abs(p5) if p5 is not None and p5 < 0 else 0.0


def calmar_ratio(returns, price_by_date):
    ann_return = annualized_return(returns)
    mdd = max_drawdown(price_by_date)
    if ann_return is None or not mdd:
        return None
    return ann_return / abs(mdd)


def beta(asset_returns, benchmark_returns):
    """cov(asset, benchmark) / var(benchmark), on shared dates only."""
    a, b = align(asset_returns, benchmark_returns)
    if len(a) < MIN_OBSERVATIONS:
        return None
    var_b = _stdev(b) ** 2
    if var_b == 0:
        return None
    return _covariance(a, b) / var_b


def tracking_error(asset_returns, benchmark_returns):
    a, b = align(asset_returns, benchmark_returns)
    if len(a) < MIN_OBSERVATIONS:
        return None
    diffs = [x - y for x, y in zip(a, b)]
    return _stdev(diffs) * math.sqrt(TRADING_DAYS_PER_YEAR)


def compute_metrics(price_by_date, benchmark_returns=None, risk_free_rate_pct=None):
    """All §14.1 metrics for one price/value series. Returns None per-metric
    where there isn't enough data rather than guessing.
    """
    rfr = DEFAULT_RISK_FREE_RATE_PCT if risk_free_rate_pct is None else risk_free_rate_pct
    returns_by_date = to_daily_returns(price_by_date)
    returns = [returns_by_date[d] for d in sorted(returns_by_date)]

    if len(returns) < MIN_OBSERVATIONS:
        return {
            "observations": len(returns),
            "sufficient_data": False,
            "volatility": None,
            "annualized_return": None,
            "sharpe": None,
            "sortino": None,
            "max_drawdown": None,
            "var_95": None,
            "calmar": None,
            "beta": None,
            "tracking_error": None,
        }

    return {
        "observations": len(returns),
        "sufficient_data": True,
        "volatility": annualized_volatility(returns),
        "annualized_return": annualized_return(returns),
        "sharpe": sharpe_ratio(returns, rfr),
        "sortino": sortino_ratio(returns, rfr),
        "max_drawdown": max_drawdown(price_by_date),
        "var_95": value_at_risk_95(returns),
        "calmar": calmar_ratio(returns, price_by_date),
        "beta": beta(returns_by_date, benchmark_returns) if benchmark_returns else None,
        "tracking_error": (
            tracking_error(returns_by_date, benchmark_returns) if benchmark_returns else None
        ),
    }


# --------------------------------------------------------------------------
# public entry points
# --------------------------------------------------------------------------


def get_asset_risk(asset_id, period="1Y", benchmark_code=DEFAULT_BENCHMARK, risk_free_rate_pct=None):
    if period not in VALID_PERIODS:
        raise ValueError(f"invalid risk period: {period}")

    start = _period_start(period)
    prices = get_asset_price_series(asset_id, start_date=start)
    bench_returns = to_daily_returns(get_benchmark_price_series(benchmark_code, start_date=start))

    metrics = compute_metrics(prices, bench_returns, risk_free_rate_pct)
    metrics.update(
        {
            "scope": "asset",
            "asset_id": asset_id,
            "period": period,
            "benchmark_code": benchmark_code,
            "risk_free_rate_pct": (
                DEFAULT_RISK_FREE_RATE_PCT if risk_free_rate_pct is None else Decimal(str(risk_free_rate_pct))
            ),
        }
    )
    return metrics


def get_portfolio_value_series(period="1Y"):
    """The §6.8 portfolio value path as {date: float}, reused rather than
    recomputed so the value chart and these numbers agree.

    NOTE: this is a *money-weighted* path -- it moves when the user buys or
    sells, not only when the market moves. It is correct for "what is my
    portfolio worth", and wrong as an input to return/risk statistics. Use
    get_portfolio_return_series() for anything statistical.
    """
    from services import analytics_service

    perf_period = period if period in analytics_service.VALID_PERFORMANCE_PERIODS else "1Y"
    perf = analytics_service.get_portfolio_performance(period=perf_period)
    return {p["date"]: float(p["value"]) for p in perf["points"] if p["value"] is not None}


def get_portfolio_return_series(period="1Y"):
    """Time-weighted daily portfolio returns -- the correct input to §14.1.

    Deriving returns from the raw portfolio *value* series is wrong: buying
    100k of stock lifts portfolio value 100k, and naive differencing books that
    contribution as a colossal one-day "gain". With most of this portfolio bought
    on a single day, that produced ~300% annualized volatility and a Calmar of 27
    -- numbers that look authoritative and are pure artifact.

    Instead each day's portfolio return is the weighted average of its holdings'
    *price* returns, weighted by yesterday's market values:

        r_p[t] = Sum_i ( w_i[t-1] x r_i[t] ),  w_i[t-1] = value_i[t-1] / total[t-1]

    Because weights come from t-1, shares bought on day t contribute nothing on
    day t -- cash flows drop out and only market movement is measured. This is
    the standard time-weighted return, the same basis on which funds report
    performance.

    Returns (returns_by_date, index_by_date) where the index is growth of 100
    compounded from those returns -- drawdown/Calmar need a path, and this one
    reflects only market movement.
    """
    from models import Transaction

    transactions = Transaction.query.order_by(
        Transaction.txn_date, Transaction.transaction_id
    ).all()
    if not transactions:
        return {}, {}

    asset_ids = sorted({t.asset_id for t in transactions})
    start = _period_start(period)

    # Replay per-asset quantity over time, collapsing same-day trades to their
    # end-of-day cumulative quantity.
    qty_timeline = {aid: [] for aid in asset_ids}  # [(date, qty)]
    running = {aid: 0.0 for aid in asset_ids}
    for txn in transactions:
        if txn.txn_type == "BUY":
            running[txn.asset_id] += float(txn.quantity)
        elif txn.txn_type == "SELL":
            running[txn.asset_id] -= float(txn.quantity)
        # DIVIDEND leaves quantity unchanged.
        timeline = qty_timeline[txn.asset_id]
        if timeline and timeline[-1][0] == txn.txn_date:
            timeline[-1] = (txn.txn_date, running[txn.asset_id])
        else:
            timeline.append((txn.txn_date, running[txn.asset_id]))

    def qty_on(asset_id, d):
        held = 0.0
        for txn_date, qty in qty_timeline[asset_id]:
            if txn_date <= d:
                held = qty
            else:
                break
        return held

    # Prices are pulled unbounded-below so a date early in the window can still
    # forward-fill from the last close before it.
    prices = {aid: get_asset_price_series(aid) for aid in asset_ids}
    price_dates = {aid: sorted(prices[aid]) for aid in asset_ids}

    def price_on(asset_id, d):
        series, dates = prices[asset_id], price_dates[asset_id]
        chosen = None
        for pd_ in dates:
            if pd_ <= d:
                chosen = pd_
            else:
                break
        return series[chosen] if chosen is not None else None

    # Evaluate on dates where at least one held asset actually traded.
    all_dates = sorted({d for aid in asset_ids for d in price_dates[aid] if start is None or d >= start})
    if len(all_dates) < 2:
        return {}, {}

    returns_by_date = {}
    for prev_d, d in zip(all_dates, all_dates[1:]):
        weighted_return, total_prev = 0.0, 0.0
        contributions = []
        for aid in asset_ids:
            qty_prev = qty_on(aid, prev_d)
            if qty_prev <= 0:
                continue
            p_prev, p_now = price_on(aid, prev_d), price_on(aid, d)
            if not p_prev or p_now is None or p_prev <= 0:
                continue
            value_prev = qty_prev * p_prev
            total_prev += value_prev
            contributions.append((value_prev, (p_now - p_prev) / p_prev))
        if total_prev <= 0:
            continue
        for value_prev, asset_return in contributions:
            weighted_return += (value_prev / total_prev) * asset_return
        returns_by_date[d] = weighted_return

    index_by_date, level = {}, 100.0
    for d in sorted(returns_by_date):
        level *= 1.0 + returns_by_date[d]
        index_by_date[d] = level

    return returns_by_date, index_by_date


def get_portfolio_risk(period="1Y", benchmark_code=DEFAULT_BENCHMARK, risk_free_rate_pct=None):
    """Portfolio-level aggregates -- computed on request, never stored (§14.1)."""
    if period not in VALID_PERIODS:
        raise ValueError(f"invalid risk period: {period}")

    _returns, index_series = get_portfolio_return_series(period)
    start = _period_start(period)
    bench_returns = to_daily_returns(get_benchmark_price_series(benchmark_code, start_date=start))

    # compute_metrics re-derives returns from the series it's given; the
    # time-weighted index is built so that differencing it reproduces exactly
    # the time-weighted returns above.
    metrics = compute_metrics(index_series, bench_returns, risk_free_rate_pct)
    metrics.update(
        {
            "scope": "portfolio",
            "asset_id": None,
            "period": period,
            "benchmark_code": benchmark_code,
            "risk_free_rate_pct": (
                DEFAULT_RISK_FREE_RATE_PCT if risk_free_rate_pct is None else Decimal(str(risk_free_rate_pct))
            ),
        }
    )
    return metrics


# Which computed metrics get persisted to asset_metrics (§14.1). Portfolio-level
# aggregates are deliberately absent -- those stay on-request.
PERSISTED_METRIC_KEYS = (
    "volatility",
    "annualized_return",
    "sharpe",
    "sortino",
    "max_drawdown",
    "var_95",
    "calmar",
    "beta",
    "tracking_error",
)


def store_asset_metrics(asset_id, period="1Y", benchmark_code=DEFAULT_BENCHMARK):
    """Upsert one asset's metrics into the existing asset_metrics table."""
    metrics = get_asset_risk(asset_id, period=period, benchmark_code=benchmark_code)
    now = date.today()
    written = 0

    for key in PERSISTED_METRIC_KEYS:
        value = metrics.get(key)
        if value is None:
            continue
        row = db.session.get(AssetMetric, (asset_id, key, period))
        if row is None:
            row = AssetMetric(asset_id=asset_id, metric_key=key, period=period)
            db.session.add(row)
        row.metric_value = Decimal(str(round(value, 6)))
        row.as_of = now
        written += 1

    db.session.commit()
    return {"asset_id": asset_id, "period": period, "metrics_written": written}


def refresh_all_holding_metrics(period="1Y"):
    """Recompute + persist metrics for every currently-held asset."""
    asset_ids = sorted({h.asset_id for h in Holding.query.all()})
    return [store_asset_metrics(aid, period=period) for aid in asset_ids]


# --------------------------------------------------------------------------
# §14.2 correlation matrix
# --------------------------------------------------------------------------


def get_risk_return_scatter(period="1Y"):
    """Per-holding risk vs. return, plus position size (§15.2's BubbleScatter).

    Exists as one endpoint rather than letting the browser loop over
    /analytics/risk per holding: that would be one request and one full metric
    computation per asset, for three numbers each. Nothing new is calculated
    here -- it's the same annualized volatility and return already defined
    above, gathered in a single pass.
    """
    if period not in VALID_PERIODS:
        raise ValueError(f"invalid risk period: {period}")

    start = _period_start(period)
    points, excluded = [], []
    total_value = Decimal("0")

    holdings = Holding.query.all()
    values = {}
    for holding in holdings:
        snapshot = holding.asset.price_snapshot
        if snapshot is None or snapshot.price is None:
            continue
        value = Decimal(holding.quantity) * Decimal(snapshot.price)
        values[holding.asset_id] = value
        total_value += value

    for holding in holdings:
        asset = holding.asset
        prices = get_asset_price_series(holding.asset_id, start_date=start)
        rets = to_daily_returns(prices)
        if len(rets) < MIN_OBSERVATIONS:
            excluded.append(
                {
                    "asset_id": holding.asset_id,
                    "symbol": asset.symbol,
                    "reason": f"only {len(rets)} daily observations in this period",
                }
            )
            continue
        ordered = [rets[d] for d in sorted(rets)]
        value = values.get(holding.asset_id)
        points.append(
            {
                "asset_id": holding.asset_id,
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "volatility": annualized_volatility(ordered),
                "annualized_return": annualized_return(ordered),
                "current_value": value,
                "weight_pct": (value / total_value * 100) if value and total_value > 0 else None,
                "observations": len(ordered),
            }
        )

    points.sort(key=lambda p: p["current_value"] or Decimal("0"), reverse=True)
    return {
        "period": period,
        "points": points,
        "excluded": excluded,
        "note": (
            "Annualized volatility and return from daily closes over the selected period. "
            "Bubble size is the position's current value, not a risk measure."
        ),
    }


def get_correlation_matrix(period="1Y"):
    """Pairwise Pearson correlation of daily returns across current holdings.
    Computed on the fly, never stored (§14.2).
    """
    if period not in VALID_PERIODS:
        raise ValueError(f"invalid correlation period: {period}")

    start = _period_start(period)
    holdings = Holding.query.all()

    assets, returns_by_asset = [], []
    for holding in holdings:
        prices = get_asset_price_series(holding.asset_id, start_date=start)
        rets = to_daily_returns(prices)
        assets.append(
            {
                "asset_id": holding.asset_id,
                "symbol": holding.asset.symbol,
                "name": holding.asset.name,
                "observations": len(rets),
            }
        )
        returns_by_asset.append(rets)

    matrix = []
    for i, _ in enumerate(assets):
        row = []
        for j, _ in enumerate(assets):
            if i == j:
                row.append(1.0)
                continue
            a, b = align(returns_by_asset[i], returns_by_asset[j])
            # Too little overlap -> None, not 0. A zero would read as "these are
            # uncorrelated", which is a much stronger claim than "we don't know".
            row.append(pearson_correlation(a, b) if len(a) >= MIN_OBSERVATIONS else None)
        matrix.append(row)

    return {
        "period": period,
        "assets": assets,
        "matrix": matrix,
        "note": (
            "Pearson correlation of daily returns over dates where both assets traded. "
            "null means too few overlapping observations to measure."
        ),
    }
