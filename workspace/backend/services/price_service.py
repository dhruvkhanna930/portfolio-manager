import logging
from datetime import date, datetime, timezone
from decimal import Decimal

import requests
import yfinance as yf
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
