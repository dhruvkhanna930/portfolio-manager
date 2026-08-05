from models import AssetMetadata, Holding, MarketIndexConstituent, StockDetails, db

DEFAULT_INDEX = "NIFTY50"

# A fixed curated basket (§4.1, §12 Phase 12) synced on the regular price-sync
# schedule regardless of what the user actually holds -- purely to power
# market-wide movers. Not meant to be a perfectly current index roster, just a
# stable, well-known large-cap basket for demo/dev purposes.
NIFTY50_CONSTITUENTS = [
    ("RELIANCE.NS", "Reliance Industries Ltd", "Energy"),
    ("TCS.NS", "Tata Consultancy Services Ltd", "IT"),
    ("HDFCBANK.NS", "HDFC Bank Ltd", "Financial Services"),
    ("ICICIBANK.NS", "ICICI Bank Ltd", "Financial Services"),
    ("INFY.NS", "Infosys Ltd", "IT"),
    ("HINDUNILVR.NS", "Hindustan Unilever Ltd", "FMCG"),
    ("ITC.NS", "ITC Ltd", "FMCG"),
    ("SBIN.NS", "State Bank of India", "Financial Services"),
    ("BHARTIARTL.NS", "Bharti Airtel Ltd", "Telecom"),
    ("KOTAKBANK.NS", "Kotak Mahindra Bank Ltd", "Financial Services"),
    ("LT.NS", "Larsen & Toubro Ltd", "Construction"),
    ("AXISBANK.NS", "Axis Bank Ltd", "Financial Services"),
    ("BAJFINANCE.NS", "Bajaj Finance Ltd", "Financial Services"),
    ("ASIANPAINT.NS", "Asian Paints Ltd", "Consumer Durables"),
    ("MARUTI.NS", "Maruti Suzuki India Ltd", "Automobile"),
    ("TITAN.NS", "Titan Company Ltd", "Consumer Durables"),
    ("SUNPHARMA.NS", "Sun Pharmaceutical Industries Ltd", "Healthcare"),
    ("ULTRACEMCO.NS", "UltraTech Cement Ltd", "Cement"),
    ("NESTLEIND.NS", "Nestle India Ltd", "FMCG"),
    ("WIPRO.NS", "Wipro Ltd", "IT"),
    ("ONGC.NS", "Oil & Natural Gas Corporation Ltd", "Energy"),
    ("NTPC.NS", "NTPC Ltd", "Power"),
    ("POWERGRID.NS", "Power Grid Corporation of India Ltd", "Power"),
    ("M&M.NS", "Mahindra & Mahindra Ltd", "Automobile"),
    ("TATASTEEL.NS", "Tata Steel Ltd", "Metals"),
    ("JSWSTEEL.NS", "JSW Steel Ltd", "Metals"),
    ("ADANIENT.NS", "Adani Enterprises Ltd", "Diversified"),
    ("ADANIPORTS.NS", "Adani Ports and SEZ Ltd", "Infrastructure"),
    ("COALINDIA.NS", "Coal India Ltd", "Mining"),
    ("BAJAJFINSV.NS", "Bajaj Finserv Ltd", "Financial Services"),
    ("HCLTECH.NS", "HCL Technologies Ltd", "IT"),
    ("INDUSINDBK.NS", "IndusInd Bank Ltd", "Financial Services"),
    ("TECHM.NS", "Tech Mahindra Ltd", "IT"),
    ("GRASIM.NS", "Grasim Industries Ltd", "Cement"),
    ("HINDALCO.NS", "Hindalco Industries Ltd", "Metals"),
    ("DRREDDY.NS", "Dr. Reddy's Laboratories Ltd", "Healthcare"),
    ("CIPLA.NS", "Cipla Ltd", "Healthcare"),
    ("EICHERMOT.NS", "Eicher Motors Ltd", "Automobile"),
    ("BRITANNIA.NS", "Britannia Industries Ltd", "FMCG"),
    ("DIVISLAB.NS", "Divi's Laboratories Ltd", "Healthcare"),
    ("APOLLOHOSP.NS", "Apollo Hospitals Enterprise Ltd", "Healthcare"),
    ("HEROMOTOCO.NS", "Hero MotoCorp Ltd", "Automobile"),
    ("TATACONSUM.NS", "Tata Consumer Products Ltd", "FMCG"),
    ("BPCL.NS", "Bharat Petroleum Corporation Ltd", "Energy"),
    ("SBILIFE.NS", "SBI Life Insurance Company Ltd", "Insurance"),
    ("HDFCLIFE.NS", "HDFC Life Insurance Company Ltd", "Insurance"),
    ("SHRIRAMFIN.NS", "Shriram Finance Ltd", "Financial Services"),
    ("TATAMOTORS.NS", "Tata Motors Ltd", "Automobile"),
    ("UPL.NS", "UPL Ltd", "Chemicals"),
    ("BAJAJ-AUTO.NS", "Bajaj Auto Ltd", "Automobile"),
]


def seed_index_constituents(index_name=DEFAULT_INDEX):
    """Idempotent: create asset_metadata + stock_details rows for any Nifty50
    symbol not already known (no live yfinance call needed -- name/sector are
    static), and link them into market_index_constituents. Actual prices are
    populated by the existing scheduled/manual price sync (§4, jobs/price_sync.py)
    since these become ordinary price_source='LIVE' STOCK rows.
    """
    already_linked = {
        row.asset_id
        for row in MarketIndexConstituent.query.filter_by(index_name=index_name).all()
    }
    added = 0

    for symbol, name, sector in NIFTY50_CONSTITUENTS:
        asset = AssetMetadata.query.filter_by(symbol=symbol, asset_type="STOCK").first()
        if asset is None:
            asset = AssetMetadata(
                symbol=symbol, asset_type="STOCK", name=name, currency="INR", price_source="LIVE"
            )
            db.session.add(asset)
            db.session.flush()
            db.session.add(
                StockDetails(asset_id=asset.asset_id, exchange="NSE", sector=sector, country="India")
            )

        if asset.asset_id in already_linked:
            continue
        db.session.add(MarketIndexConstituent(asset_id=asset.asset_id, index_name=index_name))
        added += 1

    db.session.commit()
    return added


def _split_movers(items, limit):
    priced = [i for i in items if i["day_change_pct"] is not None]
    gainers = sorted(
        [i for i in priced if i["day_change_pct"] > 0], key=lambda i: i["day_change_pct"], reverse=True
    )[:limit]
    losers = sorted([i for i in priced if i["day_change_pct"] < 0], key=lambda i: i["day_change_pct"])[
        :limit
    ]
    return gainers, losers


def _to_item(asset, snapshot):
    return {
        "asset_id": asset.asset_id,
        "symbol": asset.symbol,
        "name": asset.name,
        "price": snapshot.price if snapshot else None,
        "day_change": snapshot.day_change if snapshot else None,
        "day_change_pct": snapshot.day_change_pct if snapshot else None,
    }


def get_portfolio_movers(limit=5):
    """Day-change movers computed purely from the user's own holdings' cached
    price_snapshot -- no extra fetch, reuses what price_service already synced.
    """
    holdings = Holding.query.all()
    items = [_to_item(h.asset, h.asset.price_snapshot) for h in holdings]
    gainers, losers = _split_movers(items, limit)
    return {"scope": "portfolio", "gainers": gainers, "losers": losers}


def get_index_movers(limit=5, index_name=DEFAULT_INDEX):
    """Day-change movers across the curated index basket, independent of what
    the user holds. Self-heals by seeding if the basket is empty (e.g. first
    request on a fresh DB before any scheduled job has run).
    """
    if MarketIndexConstituent.query.filter_by(index_name=index_name).count() == 0:
        seed_index_constituents(index_name)

    constituents = MarketIndexConstituent.query.filter_by(index_name=index_name).all()
    items = [_to_item(c.asset, c.asset.price_snapshot) for c in constituents]
    gainers, losers = _split_movers(items, limit)
    return {"scope": "index", "gainers": gainers, "losers": losers}
