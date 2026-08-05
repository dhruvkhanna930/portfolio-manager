import logging

import requests
import yfinance as yf

from models import AssetMetadata, MutualFundDetails, StockDetails, db
from services import price_service

logger = logging.getLogger(__name__)

MFAPI_META_URL = "https://api.mfapi.in/mf/{scheme_code}"


class UnsupportedAssetTypeError(Exception):
    pass


def list_assets():
    return AssetMetadata.query.order_by(AssetMetadata.name).all()


def sector_label(asset):
    """Sector-ish bucket label for an asset -- single source of truth shared by
    the allocation-by-sector aggregation and the asset serializer, so a table
    row's displayed sector always matches the donut bucket it was counted in.
    """
    if asset.asset_type == "STOCK":
        if asset.stock_details and asset.stock_details.sector:
            return asset.stock_details.sector
        return "Other"
    if asset.asset_type == "MUTUAL_FUND":
        if asset.mutual_fund_details and asset.mutual_fund_details.category:
            return asset.mutual_fund_details.category
        return "Mutual Funds"
    if asset.asset_type == "BOND":
        return "Bonds"
    return "Other"


def _create_stock(symbol, name):
    asset = AssetMetadata(
        symbol=symbol, asset_type="STOCK", name=name, currency="INR", price_source="LIVE"
    )
    db.session.add(asset)
    db.session.flush()

    sector = industry = exchange = None
    try:
        info = yf.Ticker(symbol).info
        sector = info.get("sector")
        industry = info.get("industry")
        exchange = info.get("exchange")
        if info.get("shortName"):
            asset.name = info["shortName"]
        if info.get("currency"):
            asset.currency = info["currency"]
    except Exception:
        # Fundamentals are a nice-to-have; a missing sector must not block the buy.
        logger.warning("Could not fetch yfinance info for %s", symbol, exc_info=True)

    db.session.add(
        StockDetails(
            asset_id=asset.asset_id,
            exchange="NSE" if symbol.endswith(".NS") else ("BSE" if symbol.endswith(".BO") else exchange),
            sector=sector,
            industry=industry,
            country="India" if symbol.endswith((".NS", ".BO")) else None,
        )
    )
    return asset


def _create_mutual_fund(scheme_code, name):
    asset = AssetMetadata(
        symbol=scheme_code, asset_type="MUTUAL_FUND", name=name, currency="INR", price_source="LIVE"
    )
    db.session.add(asset)
    db.session.flush()

    category = None
    try:
        meta = requests.get(MFAPI_META_URL.format(scheme_code=scheme_code), timeout=10).json().get("meta", {})
        category = meta.get("scheme_category")
        if meta.get("scheme_name"):
            asset.name = meta["scheme_name"]
        if meta.get("isin_growth"):
            asset.isin = meta["isin_growth"]
    except Exception:
        logger.warning("Could not fetch mfapi.in meta for scheme %s", scheme_code, exc_info=True)

    scheme_name = (asset.name or "").upper()
    db.session.add(
        MutualFundDetails(
            asset_id=asset.asset_id,
            category=category,
            plan_type="DIRECT" if "DIRECT" in scheme_name else ("REGULAR" if "REGULAR" in scheme_name else None),
            option_type="IDCW" if "IDCW" in scheme_name else ("GROWTH" if "GROWTH" in scheme_name else None),
        )
    )
    return asset


def resolve_asset(symbol, asset_type, name=None):
    """Given a live-search pick, return the existing asset or create it along with
    its type-specific details row, then do the one-time historical backfill into
    price_history (§4.1, §4.2). Returns (asset, created, history_rows_added).
    """
    if asset_type not in ("STOCK", "MUTUAL_FUND"):
        # Bonds are curated-only -- there's no live search or history source for
        # Indian retail bonds, so they can't be resolved this way (§4.1).
        raise UnsupportedAssetTypeError(asset_type)

    existing = AssetMetadata.query.filter_by(symbol=symbol, asset_type=asset_type).first()
    if existing is not None:
        return existing, False, 0

    if asset_type == "STOCK":
        asset = _create_stock(symbol, name or symbol)
    else:
        asset = _create_mutual_fund(symbol, name or symbol)

    db.session.commit()

    history_rows = price_service.backfill_history(asset)
    # Seed the live snapshot too, so the new asset has a current price immediately
    # rather than waiting for the next scheduled sync.
    price_service.sync_asset(asset)

    return asset, True, history_rows
