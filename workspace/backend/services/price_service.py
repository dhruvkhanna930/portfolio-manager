import logging
import math
import time
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import requests
import yfinance as yf
from dateutil.relativedelta import relativedelta
from tenacity import retry, stop_after_attempt, wait_exponential

from models import AssetMetadata, PriceHistory, PriceSnapshot, db

logger = logging.getLogger(__name__)

MFAPI_LATEST_URL = "https://api.mfapi.in/mf/{scheme_code}/latest"
MFAPI_HISTORY_URL = "https://api.mfapi.in/mf/{scheme_code}"
RETRY_ATTEMPTS = 3

_retry = retry(
    stop=stop_after_attempt(RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)

# §4.2: full period set for the per-asset chart. 1D is the only live call --
# everything else is served from the price_history cache.
HISTORY_PERIODS = ("1D", "1W", "1M", "6M", "1Y", "3Y", "5Y", "ALL")

_HISTORY_PERIOD_DELTA = {
    "1W": relativedelta(weeks=1),
    "1M": relativedelta(months=1),
    "6M": relativedelta(months=6),
    "1Y": relativedelta(years=1),
    "3Y": relativedelta(years=3),
    "5Y": relativedelta(years=5),
}

_HISTORY_MAX_POINTS = {
    "1W": 400,
    "1M": 400,
    "6M": 400,
    "1Y": 400,
    "3Y": 250,
    "5Y": 250,
    "ALL": 200,
}

INTRADAY_CACHE_TTL_SECONDS = 300
_intraday_cache = {}  # asset_id -> (fetched_at_monotonic, points)


class AssetNotFoundError(Exception):
    pass


class PriceNotFoundError(Exception):
    pass


class PriceFetchError(Exception):
    pass


def _to_decimal(value, ndigits=4):
    if value is None:
        return None
    return Decimal(str(round(float(value), ndigits)))


@_retry
def get_stock_price(symbol):
    """Fetch latest price for a stock via yfinance. Raises PriceFetchError after retries."""
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info
    price = info.get("lastPrice") if hasattr(info, "get") else info.last_price
    prev_close = info.get("previousClose") if hasattr(info, "get") else info.previous_close
    if price is None:
        raise PriceFetchError(f"No price data returned for {symbol}")
    return {"price": float(price), "prev_close": float(prev_close) if prev_close is not None else None}


@_retry
def get_mf_nav(scheme_code):
    """Fetch latest NAV for a mutual fund scheme via mfapi.in. Raises PriceFetchError after retries."""
    resp = requests.get(MFAPI_LATEST_URL.format(scheme_code=scheme_code), timeout=8)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "SUCCESS" or not payload.get("data"):
        raise PriceFetchError(f"No NAV data returned for scheme {scheme_code}")
    latest = payload["data"][0]
    return {
        "price": float(latest["nav"]),
        "prev_close": None,
        "nav_date": datetime.strptime(latest["date"], "%d-%m-%Y").date(),
    }


def _upsert_snapshot_and_history(asset, price, prev_close, price_date, source):
    day_change = None
    day_change_pct = None
    if prev_close:
        day_change = price - prev_close
        day_change_pct = (day_change / prev_close) * 100

    now = datetime.now(timezone.utc)
    snapshot = db.session.get(PriceSnapshot, asset.asset_id)
    if snapshot is None:
        snapshot = PriceSnapshot(asset_id=asset.asset_id)
        db.session.add(snapshot)

    snapshot.price = _to_decimal(price)
    snapshot.prev_close = _to_decimal(prev_close)
    snapshot.day_change = _to_decimal(day_change)
    snapshot.day_change_pct = _to_decimal(day_change_pct)
    snapshot.is_stale = False
    snapshot.as_of = now

    if db.session.get(PriceHistory, (asset.asset_id, price_date)) is None:
        db.session.add(
            PriceHistory(
                asset_id=asset.asset_id,
                price_date=price_date,
                close_price=_to_decimal(price),
                source=source,
            )
        )

    asset.last_synced_at = now
    return snapshot


def _fallback_to_stale(asset):
    snapshot = db.session.get(PriceSnapshot, asset.asset_id)
    if snapshot is None:
        return {
            "asset_id": asset.asset_id,
            "symbol": asset.symbol,
            "status": "failed",
            "message": "price fetch failed and no cached price is available",
        }
    snapshot.is_stale = True
    db.session.commit()
    return {
        "asset_id": asset.asset_id,
        "symbol": asset.symbol,
        "status": "stale",
        "price": str(snapshot.price),
        "as_of": snapshot.as_of.isoformat(),
        "is_stale": True,
    }


def sync_asset(asset):
    """Sync a single LIVE-priced asset. Never raises — falls back to stale cache on failure."""
    if asset.price_source != "LIVE":
        return {"asset_id": asset.asset_id, "symbol": asset.symbol, "status": "skipped"}

    try:
        if asset.asset_type == "STOCK":
            result = get_stock_price(asset.symbol)
            source = "yfinance"
        elif asset.asset_type == "MUTUAL_FUND":
            result = get_mf_nav(asset.symbol)
            source = "mfapi"
        else:
            return {"asset_id": asset.asset_id, "symbol": asset.symbol, "status": "skipped"}
    except Exception:
        logger.warning(
            "Price fetch failed for asset_id=%s symbol=%s after %d attempts, falling back to cache",
            asset.asset_id,
            asset.symbol,
            RETRY_ATTEMPTS,
            exc_info=True,
        )
        return _fallback_to_stale(asset)

    price_date = result.get("nav_date") or date.today()
    snapshot = _upsert_snapshot_and_history(
        asset, result["price"], result.get("prev_close"), price_date, source
    )
    db.session.commit()
    return {
        "asset_id": asset.asset_id,
        "symbol": asset.symbol,
        "status": "updated",
        "price": str(snapshot.price),
        "as_of": snapshot.as_of.isoformat(),
        "is_stale": False,
    }


def sync_all_live_assets():
    assets = AssetMetadata.query.filter_by(price_source="LIVE").all()
    results = [sync_asset(a) for a in assets]
    summary = {
        "total": len(results),
        "updated": sum(1 for r in results if r["status"] == "updated"),
        "stale": sum(1 for r in results if r["status"] == "stale"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
    }
    return {"summary": summary, "results": results}


@_retry
def _fetch_stock_history(symbol):
    frame = yf.Ticker(symbol).history(period="max", interval="1d")
    if frame is None or frame.empty:
        raise PriceFetchError(f"No history returned for {symbol}")
    return [(idx.date(), float(row["Close"])) for idx, row in frame.iterrows()]


@_retry
def _fetch_mf_history(scheme_code):
    resp = requests.get(MFAPI_HISTORY_URL.format(scheme_code=scheme_code), timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "SUCCESS" or not payload.get("data"):
        raise PriceFetchError(f"No NAV history returned for scheme {scheme_code}")
    return [
        (datetime.strptime(row["date"], "%d-%m-%Y").date(), float(row["nav"]))
        for row in payload["data"]
    ]


def backfill_history(asset):
    """One-time deep historical pull on asset resolve (§4.2), so every period
    button later reads from price_history instead of live-calling per view.
    Returns the number of rows inserted. Never raises -- a failed backfill
    shouldn't block the BUY that follows.
    """
    try:
        if asset.asset_type == "STOCK":
            points = _fetch_stock_history(asset.symbol)
            source = "yfinance"
        elif asset.asset_type == "MUTUAL_FUND":
            points = _fetch_mf_history(asset.symbol)
            source = "mfapi"
        else:
            # Bonds have no fetchable history -- price_history rows only appear
            # when the user manually updates the price (§4.2).
            return 0
    except Exception:
        logger.warning(
            "Historical backfill failed for asset_id=%s symbol=%s", asset.asset_id, asset.symbol,
            exc_info=True,
        )
        return 0

    existing = {
        row.price_date
        for row in PriceHistory.query.filter_by(asset_id=asset.asset_id).all()
    }
    inserted = 0
    for price_date, close_price in points:
        if price_date in existing:
            continue
        db.session.add(
            PriceHistory(
                asset_id=asset.asset_id,
                price_date=price_date,
                close_price=_to_decimal(close_price),
                source=source,
            )
        )
        existing.add(price_date)
        inserted += 1

    db.session.commit()
    return inserted


def get_price(asset_id):
    asset = db.session.get(AssetMetadata, asset_id)
    if asset is None:
        raise AssetNotFoundError(asset_id)
    snapshot = db.session.get(PriceSnapshot, asset_id)
    if snapshot is None:
        raise PriceNotFoundError(asset_id)
    return snapshot


def set_manual_price(asset_id, price):
    asset = db.session.get(AssetMetadata, asset_id)
    if asset is None:
        raise AssetNotFoundError(asset_id)

    now = datetime.now(timezone.utc)
    price_date = now.date()

    snapshot = db.session.get(PriceSnapshot, asset.asset_id)
    if snapshot is None:
        snapshot = PriceSnapshot(asset_id=asset.asset_id)
        db.session.add(snapshot)

    prev_close = snapshot.price if snapshot.price is not None else None
    day_change = (price - prev_close) if prev_close else None
    day_change_pct = (day_change / prev_close * 100) if prev_close else None

    snapshot.prev_close = _to_decimal(prev_close) if prev_close is not None else snapshot.prev_close
    snapshot.price = _to_decimal(price)
    snapshot.day_change = _to_decimal(day_change) if day_change is not None else None
    snapshot.day_change_pct = _to_decimal(day_change_pct) if day_change_pct is not None else None
    snapshot.is_stale = False
    snapshot.as_of = now

    if db.session.get(PriceHistory, (asset.asset_id, price_date)) is None:
        db.session.add(
            PriceHistory(asset_id=asset.asset_id, price_date=price_date, close_price=_to_decimal(price), source="manual")
        )

    asset.last_synced_at = now
    db.session.commit()
    return snapshot


def _downsample_points(points, max_points):
    if len(points) <= max_points:
        return points
    stride = math.ceil(len(points) / max_points)
    sampled = points[::stride]
    if sampled[-1] is not points[-1]:
        sampled.append(points[-1])
    return sampled


@_retry
def _fetch_intraday(symbol):
    frame = yf.Ticker(symbol).history(period="1d", interval="5m")
    if frame is None or frame.empty:
        raise PriceFetchError(f"No intraday data for {symbol}")
    return [
        {
            "t": idx.to_pydatetime().isoformat(),
            "open": _to_decimal(row["Open"]),
            "high": _to_decimal(row["High"]),
            "low": _to_decimal(row["Low"]),
            "close": _to_decimal(row["Close"]),
        }
        for idx, row in frame.iterrows()
    ]


def _latest_vs_prev_close(asset):
    """§4.2: mutual funds don't trade intraday, and bonds have no live feed at
    all -- for both, "1D" is just latest NAV/price vs. previous close, two
    points, not a faked curve. Sourced from the cached snapshot, no live call.
    """
    snapshot = db.session.get(PriceSnapshot, asset.asset_id)
    if snapshot is None or snapshot.price is None:
        return []

    points = []
    if snapshot.prev_close is not None and snapshot.as_of is not None:
        # The exact date prev_close was recorded isn't tracked -- "as_of minus a
        # day" is a labeled approximation for charting, not a real timestamp.
        points.append(
            {
                "t": (snapshot.as_of - timedelta(days=1)).isoformat(),
                "open": None,
                "high": None,
                "low": None,
                "close": _to_decimal(snapshot.prev_close),
                "label": "Prev Close",
            }
        )
    points.append(
        {
            "t": snapshot.as_of.isoformat() if snapshot.as_of else datetime.now(timezone.utc).isoformat(),
            "open": None,
            "high": None,
            "low": None,
            "close": _to_decimal(snapshot.price),
            "label": "Latest",
        }
    )
    return points


def get_price_history(asset_id, period="1M"):
    """Chart data for the Asset Detail page, per §4.2 / §7. 1D is a live call
    for stocks (cached in-process for a few minutes); everything else reads
    price_history and never touches yfinance/mfapi.in.
    """
    if period not in HISTORY_PERIODS:
        raise ValueError(f"invalid history period: {period}")

    asset = db.session.get(AssetMetadata, asset_id)
    if asset is None:
        raise AssetNotFoundError(asset_id)

    if period == "1D":
        if asset.asset_type == "STOCK":
            cached = _intraday_cache.get(asset_id)
            now_ts = time.monotonic()
            if cached and now_ts - cached[0] < INTRADAY_CACHE_TTL_SECONDS:
                points = cached[1]
            else:
                try:
                    points = _fetch_intraday(asset.symbol)
                    _intraday_cache[asset_id] = (now_ts, points)
                except Exception:
                    logger.warning(
                        "Intraday fetch failed for %s, falling back to latest vs prev close",
                        asset.symbol,
                        exc_info=True,
                    )
                    points = _latest_vs_prev_close(asset)
        else:
            points = _latest_vs_prev_close(asset)
        return {"asset_id": asset_id, "period": period, "points": points}

    end_date = date.today()
    query = PriceHistory.query.filter(PriceHistory.asset_id == asset_id)
    if period != "ALL":
        start_date = end_date - _HISTORY_PERIOD_DELTA[period]
        query = query.filter(PriceHistory.price_date >= start_date)
    rows = query.order_by(PriceHistory.price_date).all()

    points = [
        {
            "t": row.price_date.isoformat(),
            "open": None,
            "high": None,
            "low": None,
            "close": _to_decimal(row.close_price),
        }
        for row in rows
    ]
    points = _downsample_points(points, _HISTORY_MAX_POINTS[period])
    return {"asset_id": asset_id, "period": period, "points": points}
