#!/usr/bin/env python3
"""Seed script for the local dev DB (CLAUDE.md §5 schema).

Wipes and repopulates every table with realistic-looking demo data: stocks,
mutual funds (with fund house + manager), bonds, holdings, transactions, one
active SIP, watchlist entries, and tags. Reference data only — no live price
fetch. Symbols/scheme codes/ISINs below are illustrative, not guaranteed to
be currently accurate real-world identifiers.

Run: python seed.py
"""
from datetime import date
from decimal import Decimal

from app import create_app
from models import (
    AssetMetadata,
    BondDetails,
    FundHouse,
    FundManager,
    FundManagerAssignment,
    Holding,
    HoldingTag,
    MutualFundDetails,
    Sip,
    StockDetails,
    Tag,
    Transaction,
    Watchlist,
    db,
)

STOCKS = [
    dict(symbol="RELIANCE.NS", name="Reliance Industries Ltd", sector="Energy", industry="Oil & Gas Refining & Marketing"),
    dict(symbol="TCS.NS", name="Tata Consultancy Services Ltd", sector="Technology", industry="IT Services & Consulting"),
    dict(symbol="HDFCBANK.NS", name="HDFC Bank Ltd", sector="Financial Services", industry="Private Sector Bank"),
    dict(symbol="INFY.NS", name="Infosys Ltd", sector="Technology", industry="IT Services & Consulting"),
    dict(symbol="ICICIBANK.NS", name="ICICI Bank Ltd", sector="Financial Services", industry="Private Sector Bank"),
    dict(symbol="HINDUNILVR.NS", name="Hindustan Unilever Ltd", sector="Consumer Goods", industry="FMCG"),
    dict(symbol="SBIN.NS", name="State Bank of India", sector="Financial Services", industry="Public Sector Bank"),
    dict(symbol="BHARTIARTL.NS", name="Bharti Airtel Ltd", sector="Telecom", industry="Telecom Services"),
    dict(symbol="TATAMOTORS.NS", name="Tata Motors Ltd", sector="Automobile", industry="Auto Manufacturers"),
    dict(symbol="SUNPHARMA.NS", name="Sun Pharmaceutical Industries Ltd", sector="Healthcare", industry="Pharmaceuticals"),
]

FUND_HOUSES = {
    "Axis Mutual Fund": "https://www.axismf.com",
    "Mirae Asset Mutual Fund": "https://www.miraeassetmf.co.in",
    "HDFC Mutual Fund": "https://www.hdfcfund.com",
    "ICICI Prudential Mutual Fund": "https://www.icicipruamc.com",
    "SBI Mutual Fund": "https://www.sbimf.com",
    "PPFAS Mutual Fund": "https://amc.ppfas.com",
}

MUTUAL_FUNDS = [
    dict(
        symbol="120503", name="Axis Bluechip Fund - Direct Plan - Growth",
        fund_house="Axis Mutual Fund", category="Equity", sub_category="Large Cap",
        plan_type="DIRECT", option_type="GROWTH", expense_ratio=Decimal("0.55"),
        aum=Decimal("32500.00"), risk_level="Moderately High", benchmark="Nifty 100 TRI",
        manager="Shreyash Devalkar",
    ),
    dict(
        symbol="118825", name="Mirae Asset Emerging Bluechip Fund - Direct - Growth",
        fund_house="Mirae Asset Mutual Fund", category="Equity", sub_category="Large & Mid Cap",
        plan_type="DIRECT", option_type="GROWTH", expense_ratio=Decimal("0.65"),
        aum=Decimal("38900.00"), risk_level="Very High", benchmark="NIFTY Large Midcap 250 TRI",
        manager="Neelesh Surana",
    ),
    dict(
        symbol="119551", name="HDFC Short Term Debt Fund - Direct Plan - Growth",
        fund_house="HDFC Mutual Fund", category="Debt", sub_category="Short Duration",
        plan_type="DIRECT", option_type="GROWTH", expense_ratio=Decimal("0.30"),
        aum=Decimal("12800.00"), risk_level="Moderate", benchmark="CRISIL Short Duration Debt Index",
        manager="Anil Bamboli",
    ),
    dict(
        symbol="120716", name="ICICI Prudential Balanced Advantage Fund - Direct - Growth",
        fund_house="ICICI Prudential Mutual Fund", category="Hybrid", sub_category="Dynamic Asset Allocation",
        plan_type="DIRECT", option_type="GROWTH", expense_ratio=Decimal("0.95"),
        aum=Decimal("54200.00"), risk_level="Moderately High", benchmark="CRISIL Hybrid 50+50 Moderate Index",
        manager="Sankaran Naren",
    ),
    dict(
        symbol="125497", name="SBI Small Cap Fund - Direct Plan - Growth",
        fund_house="SBI Mutual Fund", category="Equity", sub_category="Small Cap",
        plan_type="DIRECT", option_type="GROWTH", expense_ratio=Decimal("0.70"),
        aum=Decimal("28700.00"), risk_level="Very High", benchmark="Nifty Smallcap 250 TRI",
        manager="R. Srinivasan",
    ),
    dict(
        symbol="122639", name="Parag Parikh Flexi Cap Fund - Direct - Growth",
        fund_house="PPFAS Mutual Fund", category="Equity", sub_category="Flexi Cap",
        plan_type="DIRECT", option_type="GROWTH", expense_ratio=Decimal("0.63"),
        aum=Decimal("61300.00"), risk_level="Very High", benchmark="NIFTY 500 TRI",
        manager="Rajeev Thakkar",
    ),
]

BONDS = [
    dict(
        symbol="IN0020220013", isin="IN0020220013", name="7.10% GOI 2032",
        issuer="Government of India", coupon_rate=Decimal("7.100"),
        face_value=Decimal("100.00"), maturity_date=date(2032, 4, 8),
        credit_rating="SOV", payment_frequency="Semi-Annual",
    ),
    dict(
        symbol="IN0020230021", isin="IN0020230021", name="8.24% GOI 2033",
        issuer="Government of India", coupon_rate=Decimal("8.240"),
        face_value=Decimal("100.00"), maturity_date=date(2033, 11, 22),
        credit_rating="SOV", payment_frequency="Semi-Annual",
    ),
    dict(
        symbol="INE001A07123", isin="INE001A07123", name="HDFC Ltd 7.85% NCD 2026",
        issuer="HDFC Ltd", coupon_rate=Decimal("7.850"),
        face_value=Decimal("1000.00"), maturity_date=date(2026, 6, 15),
        credit_rating="AAA", payment_frequency="Annual",
    ),
    dict(
        symbol="INE020B07456", isin="INE020B07456", name="REC Limited 7.50% Bond 2031",
        issuer="REC Limited", coupon_rate=Decimal("7.500"),
        face_value=Decimal("1000.00"), maturity_date=date(2031, 3, 1),
        credit_rating="AAA", payment_frequency="Annual",
    ),
]


def weighted_avg_price(buys):
    """buys: list of (quantity, price) BUY legs. Mirrors CLAUDE.md §6.4."""
    total_qty = sum(qty for qty, _ in buys)
    total_cost = sum(qty * price for qty, price in buys)
    return (total_cost / total_qty).quantize(Decimal("0.0001"))


def wipe_all():
    for model in [
        HoldingTag, Transaction, Sip, Watchlist, Holding, Tag,
        FundManagerAssignment, StockDetails, MutualFundDetails, BondDetails,
        FundManager, FundHouse, AssetMetadata,
    ]:
        db.session.query(model).delete()
    db.session.commit()


def seed():
    wipe_all()

    # --- Stocks ---
    stock_assets = {}
    for s in STOCKS:
        asset = AssetMetadata(
            symbol=s["symbol"], asset_type="STOCK", name=s["name"],
            currency="INR", price_source="LIVE",
        )
        asset.stock_details = StockDetails(
            exchange="NSE", sector=s["sector"], industry=s["industry"], country="India",
        )
        db.session.add(asset)
        stock_assets[s["symbol"]] = asset

    # --- Fund houses & managers ---
    fund_houses = {}
    for name, website in FUND_HOUSES.items():
        fh = FundHouse(name=name, website=website)
        db.session.add(fh)
        fund_houses[name] = fh

    fund_managers = {}

    def get_manager(name):
        if name not in fund_managers:
            fm = FundManager(name=name, bio=f"Fund manager, {name}.")
            db.session.add(fm)
            fund_managers[name] = fm
        return fund_managers[name]

    # --- Mutual funds ---
    mf_assets = {}
    for mf in MUTUAL_FUNDS:
        asset = AssetMetadata(
            symbol=mf["symbol"], asset_type="MUTUAL_FUND", name=mf["name"],
            currency="INR", price_source="LIVE",
        )
        asset.mutual_fund_details = MutualFundDetails(
            fund_house=fund_houses[mf["fund_house"]],
            category=mf["category"], sub_category=mf["sub_category"],
            plan_type=mf["plan_type"], option_type=mf["option_type"],
            expense_ratio=mf["expense_ratio"], aum=mf["aum"],
            risk_level=mf["risk_level"], benchmark=mf["benchmark"],
        )
        db.session.add(asset)
        mf_assets[mf["symbol"]] = asset
        db.session.add(FundManagerAssignment(
            fund=asset.mutual_fund_details, manager=get_manager(mf["manager"]),
            since_date=date(2022, 4, 1),
        ))

    # --- Bonds ---
    bond_assets = {}
    for b in BONDS:
        asset = AssetMetadata(
            symbol=b["symbol"], isin=b["isin"], asset_type="BOND", name=b["name"],
            currency="INR", price_source="MANUAL",
        )
        asset.bond_details = BondDetails(
            issuer=b["issuer"], coupon_rate=b["coupon_rate"], face_value=b["face_value"],
            maturity_date=b["maturity_date"], credit_rating=b["credit_rating"],
            payment_frequency=b["payment_frequency"],
        )
        db.session.add(asset)
        bond_assets[b["symbol"]] = asset

    db.session.flush()

    # --- Holdings + transactions ---
    def make_holding(asset, buys, sells_qty, first_bought):
        quantity = sum(qty for qty, _ in buys) - sells_qty
        avg_buy_price = weighted_avg_price(buys)
        holding = Holding(asset=asset, quantity=quantity, avg_buy_price=avg_buy_price, first_bought=first_bought)
        db.session.add(holding)
        db.session.flush()
        return holding

    reliance = stock_assets["RELIANCE.NS"]
    h_reliance = make_holding(
        reliance, buys=[(Decimal("20"), Decimal("2400.0000")), (Decimal("20"), Decimal("2500.0000"))],
        sells_qty=Decimal("0"), first_bought=date(2024, 1, 15),
    )
    db.session.add_all([
        Transaction(asset=reliance, holding=h_reliance, txn_type="BUY",
                    quantity=Decimal("20"), price=Decimal("2400.0000"),
                    fees=Decimal("15.00"), txn_date=date(2024, 1, 15)),
        Transaction(asset=reliance, holding=h_reliance, txn_type="BUY",
                    quantity=Decimal("20"), price=Decimal("2500.0000"),
                    fees=Decimal("15.00"), txn_date=date(2024, 6, 10)),
    ])

    tcs = stock_assets["TCS.NS"]
    h_tcs = make_holding(
        tcs, buys=[(Decimal("10"), Decimal("3600.0000"))], sells_qty=Decimal("2"),
        first_bought=date(2024, 2, 1),
    )
    db.session.add_all([
        Transaction(asset=tcs, holding=h_tcs, txn_type="BUY",
                    quantity=Decimal("10"), price=Decimal("3600.0000"),
                    fees=Decimal("12.00"), txn_date=date(2024, 2, 1)),
        Transaction(asset=tcs, holding=h_tcs, txn_type="SELL",
                    quantity=Decimal("2"), price=Decimal("3800.0000"),
                    fees=Decimal("5.00"), txn_date=date(2024, 9, 1)),
    ])

    hdfcbank = stock_assets["HDFCBANK.NS"]
    h_hdfcbank = make_holding(
        hdfcbank, buys=[(Decimal("30"), Decimal("1550.0000")), (Decimal("15"), Decimal("1600.0000"))],
        sells_qty=Decimal("5"), first_bought=date(2023, 11, 20),
    )
    db.session.add_all([
        Transaction(asset=hdfcbank, holding=h_hdfcbank, txn_type="BUY",
                    quantity=Decimal("30"), price=Decimal("1550.0000"),
                    fees=Decimal("20.00"), txn_date=date(2023, 11, 20)),
        Transaction(asset=hdfcbank, holding=h_hdfcbank, txn_type="BUY",
                    quantity=Decimal("15"), price=Decimal("1600.0000"),
                    fees=Decimal("11.00"), txn_date=date(2024, 4, 18)),
        Transaction(asset=hdfcbank, holding=h_hdfcbank, txn_type="SELL",
                    quantity=Decimal("5"), price=Decimal("1650.0000"),
                    fees=Decimal("6.00"), txn_date=date(2025, 1, 10)),
    ])

    axis_bluechip = mf_assets["120503"]
    h_axis = make_holding(
        axis_bluechip, buys=[(Decimal("200"), Decimal("45.2000")), (Decimal("120.42"), Decimal("47.8000"))],
        sells_qty=Decimal("0"), first_bought=date(2024, 3, 5),
    )
    sip_axis = Sip(
        asset=axis_bluechip, amount=Decimal("5000.00"), frequency="MONTHLY",
        start_date=date(2024, 3, 5), day_of_cycle=5, is_active=True,
    )
    db.session.add(sip_axis)
    db.session.flush()
    db.session.add_all([
        Transaction(asset=axis_bluechip, holding=h_axis, txn_type="BUY",
                    quantity=Decimal("200"), price=Decimal("45.2000"),
                    fees=Decimal("0.00"), txn_date=date(2024, 3, 5)),
        Transaction(asset=axis_bluechip, holding=h_axis, sip=sip_axis, txn_type="BUY",
                    quantity=Decimal("120.42"), price=Decimal("47.8000"),
                    fees=Decimal("0.00"), txn_date=date(2024, 8, 12)),
    ])

    icici_bap = mf_assets["120716"]
    h_icici = make_holding(
        icici_bap, buys=[(Decimal("500"), Decimal("55.0000"))], sells_qty=Decimal("0"),
        first_bought=date(2024, 1, 10),
    )
    db.session.add(
        Transaction(asset=icici_bap, holding=h_icici, txn_type="BUY",
                    quantity=Decimal("500"), price=Decimal("55.0000"),
                    fees=Decimal("0.00"), txn_date=date(2024, 1, 10))
    )

    goi_2032 = bond_assets["IN0020220013"]
    h_bond = make_holding(
        goi_2032, buys=[(Decimal("10"), Decimal("98.5000"))], sells_qty=Decimal("0"),
        first_bought=date(2024, 5, 1),
    )
    db.session.add(
        Transaction(asset=goi_2032, holding=h_bond, txn_type="BUY",
                    quantity=Decimal("10"), price=Decimal("98.5000"),
                    fees=Decimal("25.00"), txn_date=date(2024, 5, 1))
    )

    # --- Watchlist ---
    db.session.add_all([
        Watchlist(asset=stock_assets["INFY.NS"]),
        Watchlist(asset=stock_assets["TATAMOTORS.NS"]),
        Watchlist(asset=mf_assets["125497"]),
    ])

    # --- Tags ---
    tag_core = Tag(name="Core")
    tag_conviction = Tag(name="High Conviction")
    tag_dividend = Tag(name="Dividend Play")
    db.session.add_all([tag_core, tag_conviction, tag_dividend])
    db.session.flush()

    h_reliance.tags.append(tag_core)
    h_hdfcbank.tags.append(tag_core)
    h_axis.tags.append(tag_conviction)
    h_icici.tags.append(tag_dividend)

    db.session.commit()


def print_summary():
    counts = {
        "asset_metadata (total)": AssetMetadata.query.count(),
        "  stocks": AssetMetadata.query.filter_by(asset_type="STOCK").count(),
        "  mutual_funds": AssetMetadata.query.filter_by(asset_type="MUTUAL_FUND").count(),
        "  bonds": AssetMetadata.query.filter_by(asset_type="BOND").count(),
        "stock_details": StockDetails.query.count(),
        "mutual_fund_details": MutualFundDetails.query.count(),
        "bond_details": BondDetails.query.count(),
        "fund_houses": FundHouse.query.count(),
        "fund_managers": FundManager.query.count(),
        "fund_manager_assignments": FundManagerAssignment.query.count(),
        "holdings": Holding.query.count(),
        "transactions": Transaction.query.count(),
        "sips": Sip.query.count(),
        "watchlist": Watchlist.query.count(),
        "tags": Tag.query.count(),
        "holding_tags": db.session.query(HoldingTag).count(),
    }
    print("\nSeed summary (row counts):")
    for k, v in counts.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed()
        print_summary()
