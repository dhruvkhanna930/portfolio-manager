"""Benchmark index history + comparison lines (CLAUDE.md §14.4).

Two very different kinds of number live here, and the distinction is the whole
point of this module:

  * NIFTY50 / SENSEX / GOLD are **real fetched market data** (yfinance), cached
    in benchmark_price_history exactly like asset prices.
  * FD and inflation are **user-editable assumptions**, not data. There is no
    free API for "the" FD rate (it varies per bank/tenure) or a live inflation
    print, so we never pretend to fetch them -- they're compounding lines drawn
    from a rate the user controls, and every response carries is_assumption=True
    so the UI can label them as such (§14 rule, §0.3).
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

import yfinance as yf
from dateutil.relativedelta import relativedelta

from models import BenchmarkPriceHistory, db

logger = logging.getLogger(__name__)

# benchmark_code -> (yfinance ticker, display label)
BENCHMARKS = {
    "NIFTY50": ("^NSEI", "NIFTY 50"),
    "SENSEX": ("^BSESN", "SENSEX"),
    # Gold has no index ticker on yfinance for INR retail; GOLDBEES is a liquid
    # Indian gold ETF, so it tracks domestic gold prices including INR moves.
    "GOLD": ("GOLDBEES.NS", "Gold (GOLDBEES ETF)"),
}

# Defaults only -- the user can override both per request (§14.4).
DEFAULT_FD_RATE_PCT = Decimal("7")
DEFAULT_INFLATION_RATE_PCT = Decimal("6")

VALID_PERIODS = ("1M", "6M", "1Y", "3Y", "5Y", "ALL")

_PERIOD_DELTA = {
    "1M": relativedelta(months=1),
    "6M": relativedelta(months=6),
    "1Y": relativedelta(years=1),
    "3Y": relativedelta(years=3),
    "5Y": relativedelta(years=5),
}


def sync_benchmark(benchmark_code):
    """Fetch and cache one benchmark's daily closes. Incremental: only pulls the
    span not already cached. Never raises -- a benchmark failing to sync must not
    break the price-sync job that calls it.
    """
    if benchmark_code not in BENCHMARKS:
        raise ValueError(f"unknown benchmark: {benchmark_code}")

    ticker_symbol, _label = BENCHMARKS[benchmark_code]
    latest = (
        BenchmarkPriceHistory.query.filter_by(benchmark_code=benchmark_code)
        .order_by(BenchmarkPriceHistory.price_date.desc())
        .first()
    )

    try:
        if latest is None:
            frame = yf.Ticker(ticker_symbol).history(period="max", interval="1d")
        else:
            # Re-fetch a small overlap so the most recent close gets corrected if
            # it was captured mid-session.
            start = latest.price_date - timedelta(days=5)
            frame = yf.Ticker(ticker_symbol).history(start=start, interval="1d")
    except Exception:
        logger.warning("Benchmark sync failed for %s (%s)", benchmark_code, ticker_symbol, exc_info=True)
        return {"benchmark_code": benchmark_code, "status": "failed", "rows_added": 0}

    if frame is None or frame.empty:
        logger.warning("Benchmark sync returned no rows for %s", benchmark_code)
        return {"benchmark_code": benchmark_code, "status": "empty", "rows_added": 0}

    existing = {
        row.price_date
        for row in BenchmarkPriceHistory.query.filter_by(benchmark_code=benchmark_code).all()
    }
    added = 0
    for idx, row in frame.iterrows():
        price_date = idx.date()
        close = row["Close"]
        # yfinance emits NaN closes for suspended/holiday rows -- NaN is not None
        # and float(NaN) inserts happily, so it has to be filtered explicitly or
        # it lands as a null close and blows the NOT NULL constraint.
        if close is None or price_date in existing or close != close:
            continue
        db.session.add(
            BenchmarkPriceHistory(
                benchmark_code=benchmark_code,
                price_date=price_date,
                close_price=Decimal(str(round(float(close), 4))),
            )
        )
        existing.add(price_date)
        added += 1

    db.session.commit()
    return {"benchmark_code": benchmark_code, "status": "updated", "rows_added": added}


def sync_all_benchmarks():
    results = [sync_benchmark(code) for code in BENCHMARKS]
    return {
        "summary": {
            "total": len(results),
            "updated": sum(1 for r in results if r["status"] == "updated"),
            "failed": sum(1 for r in results if r["status"] != "updated"),
        },
        "results": results,
    }


def get_benchmark_series(benchmark_code, start_date=None, end_date=None):
    """Raw cached closes as [(date, Decimal)], ascending. Read-only -- never fetches."""
    query = BenchmarkPriceHistory.query.filter_by(benchmark_code=benchmark_code)
    if start_date:
        query = query.filter(BenchmarkPriceHistory.price_date >= start_date)
    if end_date:
        query = query.filter(BenchmarkPriceHistory.price_date <= end_date)
    rows = query.order_by(BenchmarkPriceHistory.price_date).all()
    return [(r.price_date, Decimal(r.close_price)) for r in rows]


def _rebase_to_100(series):
    """Normalize a price series so every benchmark starts at 100 -- the only way
    NIFTY (~24000), SENSEX (~80000), GOLD (~60) and a portfolio in rupees can
    share one axis and be compared on *percentage* growth rather than magnitude.
    """
    if not series:
        return []
    base = series[0][1]
    if base == 0:
        return []
    return [{"date": d, "value": (v / base) * 100} for d, v in series]


def _compounding_line(dates, annual_rate_pct):
    """A constant-growth line at annual_rate_pct, rebased to 100. Used for the FD
    and inflation comparison lines -- these are assumptions, not fetched data.
    """
    if not dates:
        return []
    start = dates[0]
    rate = float(annual_rate_pct) / 100.0
    points = []
    for d in dates:
        years = (d - start).days / 365.0
        points.append({"date": d, "value": Decimal(str(round(100.0 * ((1.0 + rate) ** years), 4)))})
    return points


def _resolve_start_date(period, earliest):
    if period == "ALL" or period not in _PERIOD_DELTA:
        return earliest
    return max(date.today() - _PERIOD_DELTA[period], earliest)


def compare(codes=None, period="1Y", fd_rate_pct=None, inflation_rate_pct=None):
    """Portfolio vs. benchmarks vs. assumption lines, all rebased to 100 (§14.4).

    Returns real market series and assumption series in the same shape but tagged
    with is_assumption so the UI can never present a made-up FD rate as if it
    were fetched data.
    """
    from services import analytics_service

    if period not in VALID_PERIODS:
        raise ValueError(f"invalid benchmark period: {period}")

    codes = [c for c in (codes or ["NIFTY50"]) if c in BENCHMARKS]
    fd_rate = Decimal(str(fd_rate_pct)) if fd_rate_pct is not None else DEFAULT_FD_RATE_PCT
    inflation_rate = (
        Decimal(str(inflation_rate_pct)) if inflation_rate_pct is not None else DEFAULT_INFLATION_RATE_PCT
    )

    # The portfolio's own value series is the anchor -- benchmarks are clipped to
    # its window so all lines cover the same span and start at a common 100.
    perf = analytics_service.get_portfolio_performance(period=period if period != "ALL" else "ALL")
    portfolio_points = [(p["date"], p["value"]) for p in perf["points"] if p["value"] is not None]

    if portfolio_points:
        start_date = portfolio_points[0][0]
        end_date = portfolio_points[-1][0]
    else:
        start_date = _resolve_start_date(period, date.today() - relativedelta(years=1))
        end_date = date.today()

    series = []
    if portfolio_points:
        series.append(
            {
                "code": "PORTFOLIO",
                "label": "My Portfolio",
                "is_assumption": False,
                "points": _rebase_to_100(portfolio_points),
            }
        )

    for code in codes:
        raw = get_benchmark_series(code, start_date=start_date, end_date=end_date)
        if not raw:
            continue
        series.append(
            {
                "code": code,
                "label": BENCHMARKS[code][1],
                "is_assumption": False,
                "points": _rebase_to_100(raw),
            }
        )

    # Assumption lines share the portfolio's date axis when there is one, so the
    # comparison is like-for-like rather than drawn over a different span.
    axis_dates = [d for d, _ in portfolio_points]
    if not axis_dates:
        axis_dates = [d for d, _ in get_benchmark_series(codes[0], start_date, end_date)] if codes else []

    if axis_dates:
        series.append(
            {
                "code": "FD",
                "label": f"Fixed Deposit @ {fd_rate}% (assumed)",
                "is_assumption": True,
                "points": _compounding_line(axis_dates, fd_rate),
            }
        )
        series.append(
            {
                "code": "INFLATION",
                "label": f"Inflation @ {inflation_rate}% (assumed)",
                "is_assumption": True,
                "points": _compounding_line(axis_dates, inflation_rate),
            }
        )

    return {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "fd_rate_pct": fd_rate,
        "inflation_rate_pct": inflation_rate,
        "note": (
            "All lines are rebased to 100 at the start of the period so they can be "
            "compared on growth, not absolute level. FD and inflation are user-editable "
            "assumptions, not fetched market data."
        ),
        "series": series,
    }
