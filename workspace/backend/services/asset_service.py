import logging
from decimal import Decimal

import requests
import yfinance as yf

from models import AssetMetadata, Holding, MutualFundDetails, StockDetails, Watchlist, db
from services import price_service

logger = logging.getLogger(__name__)

MFAPI_META_URL = "https://api.mfapi.in/mf/{scheme_code}"
SIMILAR_ASSETS_LIMIT = 6


class UnsupportedAssetTypeError(Exception):
    pass


class AssetNotFoundError(Exception):
    pass


def list_assets():
    return AssetMetadata.query.order_by(AssetMetadata.name).all()


def search_own_assets(q, limit=10):
    """Search *our own* asset_metadata (symbol, name, isin) -- distinct from
    /assets/search/live (§7), which hits yfinance/mfapi.in's live universe. This
    is what the Navbar's global search box uses: instant, no external call, only
    matches assets already resolved into the DB.
    """
    from sqlalchemy import or_

    pattern = f"%{q}%"
    return (
        AssetMetadata.query.filter(
            or_(
                AssetMetadata.symbol.ilike(pattern),
                AssetMetadata.name.ilike(pattern),
                AssetMetadata.isin.ilike(pattern),
            )
        )
        .order_by(AssetMetadata.name)
        .limit(limit)
        .all()
    )


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


def get_asset_detail(asset_id):
    """Fundamentals + about, per CLAUDE.md §4/§7. Which fields are populated
    depends on asset_type -- callers should only render the subset relevant to
    the asset they got back, the rest come through as None.
    """
    asset = db.session.get(AssetMetadata, asset_id)
    if asset is None:
        raise AssetNotFoundError(asset_id)

    snapshot = asset.price_snapshot
    data = {
        "asset_id": asset.asset_id,
        "symbol": asset.symbol,
        "name": asset.name,
        "asset_type": asset.asset_type,
        "currency": asset.currency,
        "logo_url": asset.logo_url,
        "last_synced_at": asset.last_synced_at,
        "current_price": snapshot.price if snapshot else None,
        "prev_close": snapshot.prev_close if snapshot else None,
        "day_change": snapshot.day_change if snapshot else None,
        "day_change_pct": snapshot.day_change_pct if snapshot else None,
        "is_stale": snapshot.is_stale if snapshot else None,
        "as_of": snapshot.as_of if snapshot else None,
        "is_held": Holding.query.filter_by(asset_id=asset.asset_id).first() is not None,
        "is_watchlisted": Watchlist.query.filter_by(asset_id=asset.asset_id).first() is not None,
    }

    if asset.asset_type == "STOCK":
        details = asset.stock_details
        data.update(
            {
                "exchange": details.exchange if details else None,
                "sector": details.sector if details else None,
                "industry": details.industry if details else None,
                "country": details.country if details else None,
            }
        )
        # Deep fundamentals (market cap, PE, 52w range, "about" text) are LIVE-only
        # per §3 layer 3 -- never persisted to a cache table, fetched fresh on each
        # detail view. Best-effort: a slow/failed yfinance call must not 500 the page.
        try:
            info = yf.Ticker(asset.symbol).info
            data["market_cap"] = info.get("marketCap")
            data["pe_ratio"] = info.get("trailingPE")
            data["week52_high"] = info.get("fiftyTwoWeekHigh")
            data["week52_low"] = info.get("fiftyTwoWeekLow")
            data["description"] = info.get("longBusinessSummary")
            # §15.4: the rest of what .info genuinely returns. Every key here is
            # a real yfinance field -- anything it omits for a given ticker stays
            # None and the UI hides that row, rather than being back-filled with
            # a guess.
            data["forward_pe"] = info.get("forwardPE")
            data["price_to_book"] = info.get("priceToBook")
            data["book_value"] = info.get("bookValue")
            data["dividend_yield"] = info.get("dividendYield")
            data["beta"] = info.get("beta")
            data["eps"] = info.get("trailingEps")
            data["profit_margin"] = info.get("profitMargins")
            data["return_on_equity"] = info.get("returnOnEquity")
            data["debt_to_equity"] = info.get("debtToEquity")
            data["revenue"] = info.get("totalRevenue")
            data["employees"] = info.get("fullTimeEmployees")
            data["website"] = info.get("website")
            data["day_high"] = info.get("dayHigh")
            data["day_low"] = info.get("dayLow")
            data["volume"] = info.get("volume")
            data["avg_volume"] = info.get("averageVolume")
        except Exception:
            logger.warning("Could not fetch live fundamentals for %s", asset.symbol, exc_info=True)

    elif asset.asset_type == "MUTUAL_FUND":
        details = asset.mutual_fund_details
        data.update(
            {
                "fund_house": details.fund_house.name if details and details.fund_house else None,
                "category": details.category if details else None,
                "sub_category": details.sub_category if details else None,
                "plan_type": details.plan_type if details else None,
                "option_type": details.option_type if details else None,
                "expense_ratio": details.expense_ratio if details else None,
                "aum": details.aum if details else None,
                "risk_level": details.risk_level if details else None,
                "benchmark": details.benchmark if details else None,
            }
        )

    elif asset.asset_type == "BOND":
        details = asset.bond_details
        data.update(
            {
                "issuer": details.issuer if details else None,
                "coupon_rate": details.coupon_rate if details else None,
                "face_value": details.face_value if details else None,
                "maturity_date": details.maturity_date if details else None,
                "credit_rating": details.credit_rating if details else None,
                "payment_frequency": details.payment_frequency if details else None,
            }
        )
        # §6.9: current_yield = (coupon_rate × face_value) / current_price × 100.
        # coupon_rate is stored as a percentage number (e.g. 7.100 = 7.1%), so the
        # /100 and the trailing ×100 cancel -- this is the dimensionally-correct
        # form for our storage convention, not a literal copy of the doc's formula.
        if details and details.coupon_rate and details.face_value and snapshot and snapshot.price:
            data["current_yield"] = (
                Decimal(details.coupon_rate) * Decimal(details.face_value) / Decimal(snapshot.price)
            )

    return data


def get_similar_assets(asset_id, limit=SIMILAR_ASSETS_LIMIT):
    """Same asset_type + same sector/category -- a plain SQL filter, not a
    scoring model, per §7. Falls back to same-type-only if the source asset has
    no sector/category on file.
    """
    asset = db.session.get(AssetMetadata, asset_id)
    if asset is None:
        raise AssetNotFoundError(asset_id)

    query = AssetMetadata.query.filter(
        AssetMetadata.asset_type == asset.asset_type, AssetMetadata.asset_id != asset.asset_id
    )

    if asset.asset_type == "STOCK":
        sector = asset.stock_details.sector if asset.stock_details else None
        if sector:
            query = query.join(AssetMetadata.stock_details).filter(StockDetails.sector == sector)
    elif asset.asset_type == "MUTUAL_FUND":
        category = asset.mutual_fund_details.category if asset.mutual_fund_details else None
        if category:
            query = query.join(AssetMetadata.mutual_fund_details).filter(
                MutualFundDetails.category == category
            )
    # BOND: no rich category field to filter on -- same-type-only is the whole rule.

    return query.order_by(AssetMetadata.name).limit(limit).all()


def get_peer_ranking(asset_id, period="1Y"):
    """Where this asset sits among *the assets in your own database* (§15.4).

    This is deliberately NOT a market-wide or exchange-wide ranking, and the
    response says so in `scope_note`: the comparison set is only the assets you
    have resolved into this app, which is a self-selected handful, not a sector
    universe. Ranking it against that set is a fair statement about your own
    watchlist; calling it "rank in sector" would not be.

    Ranked on total return over the period, computed from cached price history.
    """
    from services import risk_service

    asset = db.session.get(AssetMetadata, asset_id)
    if asset is None:
        raise AssetNotFoundError(asset_id)

    peers = get_similar_assets(asset_id, limit=50)
    universe = [asset] + list(peers)
    start = risk_service._period_start(period)

    scored = []
    for candidate in universe:
        prices = risk_service.get_asset_price_series(candidate.asset_id, start_date=start)
        if len(prices) < 2:
            continue
        ordered = sorted(prices)
        first, last = prices[ordered[0]], prices[ordered[-1]]
        if first <= 0:
            continue
        scored.append(
            {
                "asset_id": candidate.asset_id,
                "symbol": candidate.symbol,
                "name": candidate.name,
                "return_pct": (last - first) / first * 100,
                "observations": len(prices),
            }
        )

    if not any(s["asset_id"] == asset_id for s in scored):
        return {
            "asset_id": asset_id,
            "period": period,
            "rank": None,
            "total": len(scored),
            "peers": [],
            "comparison_basis": _peer_basis(asset),
            "scope_note": _PEER_SCOPE_NOTE,
            "reason": "Not enough cached price history for this asset in the selected period.",
        }

    scored.sort(key=lambda s: s["return_pct"], reverse=True)
    for index, row in enumerate(scored, start=1):
        row["rank"] = index
        row["is_current"] = row["asset_id"] == asset_id

    rank = next(row["rank"] for row in scored if row["is_current"])
    return {
        "asset_id": asset_id,
        "period": period,
        "rank": rank,
        "total": len(scored),
        "peers": scored,
        "comparison_basis": _peer_basis(asset),
        "scope_note": _PEER_SCOPE_NOTE,
    }


_PEER_SCOPE_NOTE = (
    "Ranked only against assets already added to this app -- not an exchange-wide or "
    "official sector ranking."
)


def _peer_basis(asset):
    if asset.asset_type == "STOCK" and asset.stock_details and asset.stock_details.sector:
        return f"Stocks you track in {asset.stock_details.sector}"
    if (
        asset.asset_type == "MUTUAL_FUND"
        and asset.mutual_fund_details
        and asset.mutual_fund_details.category
    ):
        return f"Funds you track in {asset.mutual_fund_details.category}"
    return f"{asset.asset_type.replace('_', ' ').title()}s you track"
