#!/usr/bin/env python3
"""Demo portfolio seed -- the dataset the screenshots and demo run on.

This is a *different* job from seed.py, and both exist on purpose:

  * ``seed.py``      seeds the reference catalog -- stocks, mutual funds with
                     fund houses and managers, bonds, tags. Broad schema
                     coverage, but it writes no prices, so every chart, risk
                     metric and analytics page comes up empty.
  * ``seed_demo.py`` (this file) seeds a *working portfolio*: priced holdings,
                     150 days of price history per asset, benchmark series,
                     a wallet ledger, SIPs and dividends. This is what makes
                     Analytics, Recommendations and AI Suggestions render.

Run this one for a demo. Run seed.py if you specifically want bonds and fund
house/manager records.

Design notes
------------
**Deterministic.** ``random.seed(SEED)`` at import, so two people running this
get byte-identical databases and can compare screenshots. Change SEED if you
want a different-looking portfolio.

**History is generated backwards.** Each series starts from the known current
price and random-walks *into the past*, so ``price_history[-1]`` always equals
the ``price_snapshot`` exactly. Walking forward from an arbitrary start would
leave today's cached price disagreeing with the last history bar, which shows
up as a visible discontinuity at the right edge of every chart.

**150 bars, not 90.** risk_service.MIN_OBSERVATIONS is 30, and the 1Y risk
window plus weekend gaps eats into the count. At 90 calendar days some
holdings fell under the threshold and silently dropped out of the risk/return
scatter; 150 clears it with margin for every asset.

**Volatility is per-asset and deliberate.** Each row carries its own ``vol``,
so the risk/return scatter spreads across a real range (~0.12 to ~0.30)
instead of clustering. Balanced funds are given lower vol than mid-caps,
which is what makes the chart legible as a chart.

**Benchmarks are not assets.** NIFTY50 / SENSEX / GOLD go into
``benchmark_price_history``, never ``asset_metadata`` -- the schema's
``ck_asset_type`` constraint only permits STOCK / MUTUAL_FUND / BOND, and a
benchmark is a comparison line, not something you can hold.

Run: python seed_demo.py
"""

import math
import random
from datetime import date, timedelta
from decimal import Decimal

from app import create_app
from models import (
    AssetMetadata,
    BenchmarkPriceHistory,
    Holding,
    MutualFundDetails,
    PriceHistory,
    PriceSnapshot,
    Sip,
    StockDetails,
    Transaction,
    WalletLedger,
    db,
)

SEED = 42
HISTORY_DAYS = 150
OPENING_DEPOSIT = Decimal("200000")

# buy vs price sets each holding's P/L; daily sets today's move (which is what
# the Home page movers rank on -- the two are independent on purpose, so the
# demo shows a stock that is up overall but down today).
STOCKS = [
    # symbol, name, sector, current price, avg buy, qty, annual vol, today's %
    ("RELIANCE.NS",  "Reliance Industries Ltd",       "Energy",          1302.70, 1100, 5, 0.22, -2.5),
    ("HCLTECH.NS",   "HCL Technologies Ltd",          "Technology",      1679.50, 1450, 2, 0.28, -1.8),
    ("HINDALCO.NS",  "Hindalco Industries Ltd",       "Basic Materials",  629.30,  550, 6, 0.26, -0.5),
    ("WIPRO.NS",     "WIPRO LTD",                     "Technology",       416.20,  380, 8, 0.24, -0.2),
    ("SBIN.NS",      "State Bank of India",           "Financials",       768.45,  700, 4, 0.25, -0.1),
    ("TCS.NS",       "Tata Consultancy Services Ltd", "Technology",      3945.20, 3600, 1, 0.20,  0.3),
    ("INFY.NS",      "Infosys Ltd",                   "Technology",      1450.00, 1600, 3, 0.23,  0.7),
    ("ICICIBANK.NS", "ICICI Bank Ltd",                "Financials",       900.00,  950, 3, 0.27,  1.0),
    ("MARUTI.NS",    "Maruti Suzuki India Ltd",       "Automotive",      9200.00, 9500, 1, 0.29,  1.5),
    ("NESTLEIND.NS", "Nestle India Ltd",              "Consumer",        2100.00, 2200, 1, 0.19,  2.1),
]

MUTUAL_FUNDS = [
    # scheme code, name, category, current NAV, avg buy NAV, units, vol, today's %
    ("100949", "Axis Bluechip Fund",             "Equity",   125.45, 95.00, 150, 0.18,  0.0),
    ("109068", "HDFC Growth Fund",               "Equity",    89.23, 72.00, 200, 0.20, -1.2),
    ("101238", "SBI Magnum Balanced Fund",       "Balanced",  25.00, 28.50, 300, 0.12,  1.8),
    ("110821", "Mirae Asset Large Cap Fund",     "Equity",    62.78, 50.00, 100, 0.21,  0.5),
    ("100209", "ICICI Prudential Balanced Plus", "Balanced",  45.12, 38.00, 250, 0.15, -0.8),
]

# benchmark_service.BENCHMARKS keys -- these codes must match or the comparison
# chart will request a series that does not exist.
BENCHMARKS = [
    ("NIFTY50", 23456.78, 0.16),
    ("SENSEX",  77890.12, 0.15),
    ("GOLD",     6234.50, 0.14),
]

# Assets that get a monthly SIP attached (1-indexed asset_ids in insert order:
# 1=RELIANCE, 2=HCLTECH, 11=Axis Bluechip, 12=HDFC Growth).
SIP_ASSET_IDS = (1, 2, 11, 12)
SIP_AMOUNT = Decimal("5000")


def backward_walk(end_price, annual_vol, days, drift=0.0004):
    """Random-walk backwards from today's price, oldest-first.

    Returns days+1 prices where the LAST element is exactly ``end_price``, so
    the generated history always agrees with the price_snapshot. Daily sigma is
    the annual volatility divided by sqrt(252), the same convention
    risk_service uses when it annualizes back the other way.
    """
    prices = [end_price]
    price = end_price
    for _ in range(days):
        daily_return = random.gauss(drift, annual_vol / math.sqrt(252))
        price = price / (1 + daily_return)
        prices.append(round(price, 2))
    prices.reverse()
    return prices


def write_history(asset_id, end_price, vol, source, drift=0.0004):
    walk = backward_walk(end_price, vol, HISTORY_DAYS, drift)
    for offset, price in enumerate(walk):
        db.session.add(
            PriceHistory(
                asset_id=asset_id,
                price_date=date.today() - timedelta(days=len(walk) - 1 - offset),
                close_price=Decimal(str(price)),
                source=source,
            )
        )


def write_snapshot(asset_id, price, daily_pct):
    """Today's cached quote. prev_close is derived from the day change so the
    two never contradict each other -- market_service ranks movers on
    day_change_pct, and a hand-set prev_close that disagrees produces a UI
    where the arrow and the percentage point opposite ways."""
    db.session.add(
        PriceSnapshot(
            asset_id=asset_id,
            price=Decimal(str(price)),
            prev_close=Decimal(str(round(price / (1 + daily_pct / 100), 2))),
            day_change=Decimal(str(round(price * daily_pct / 100, 2))),
            day_change_pct=Decimal(str(daily_pct)),
            as_of=date.today(),
        )
    )


def buy(asset_id, quantity, price, txn_date):
    """One BUY: the holding, its transaction, and the matching wallet debit.

    Written together because §5.2 requires the ledger row and the transaction
    to move as one -- a holding that exists without its cash entry makes the
    wallet balance wrong forever, since balance is SUM(ledger), not a field.
    """
    holding = Holding(
        asset_id=asset_id,
        quantity=Decimal(str(quantity)),
        avg_buy_price=Decimal(str(price)),
        first_bought=txn_date,
    )
    db.session.add(holding)
    db.session.flush()

    txn = Transaction(
        asset_id=asset_id,
        holding_id=holding.holding_id,
        txn_type="BUY",
        quantity=Decimal(str(quantity)),
        price=Decimal(str(price)),
        fees=Decimal("0"),
        txn_date=txn_date,
    )
    db.session.add(txn)
    db.session.flush()

    db.session.add(
        WalletLedger(
            entry_type="BUY",
            amount=-Decimal(str(quantity * price)),
            transaction_id=txn.transaction_id,
        )
    )
    return holding


def seed_demo():
    random.seed(SEED)

    db.drop_all()
    db.create_all()
    db.session.commit()

    print("Stocks")
    for index, (symbol, name, sector, price, buy_price, qty, vol, daily) in enumerate(STOCKS):
        asset = AssetMetadata(
            symbol=symbol, name=name, asset_type="STOCK",
            currency="INR", price_source="LIVE",
        )
        db.session.add(asset)
        db.session.flush()

        db.session.add(StockDetails(asset_id=asset.asset_id, exchange="NSE", sector=sector, country="India"))
        write_snapshot(asset.asset_id, price, daily)
        write_history(asset.asset_id, price, vol, "yfinance")
        buy(asset.asset_id, qty, buy_price, date.today() - timedelta(days=150 - index * 15))

        pl = (price - buy_price) / buy_price * 100
        print(f"  {symbol:14} P/L {pl:+7.2f}%   today {daily:+5.1f}%   vol {vol:.2f}")

    db.session.commit()

    print("\nMutual funds")
    for index, (code, name, category, nav, buy_nav, units, vol, daily) in enumerate(MUTUAL_FUNDS):
        asset = AssetMetadata(
            symbol=code, name=name, asset_type="MUTUAL_FUND",
            currency="INR", price_source="LIVE",
        )
        db.session.add(asset)
        db.session.flush()

        db.session.add(MutualFundDetails(
            asset_id=asset.asset_id, category=category,
            plan_type="DIRECT", option_type="GROWTH",
        ))
        write_snapshot(asset.asset_id, nav, daily)
        write_history(asset.asset_id, nav, vol, "mfapi", drift=0.0003)
        buy(asset.asset_id, units, buy_nav, date.today() - timedelta(days=150 - index * 30))

        pl = (nav - buy_nav) / buy_nav * 100
        print(f"  {code:8} {name:32} P/L {pl:+7.2f}%   vol {vol:.2f}")

    db.session.commit()

    print("\nSIPs, dividend, opening balance")
    for asset_id in SIP_ASSET_IDS:
        db.session.add(Sip(
            asset_id=asset_id, amount=SIP_AMOUNT, frequency="MONTHLY",
            start_date=date.today() - timedelta(days=60),
            day_of_cycle=15, is_active=True,
        ))
    print(f"  {len(SIP_ASSET_IDS)} monthly SIPs at Rs {SIP_AMOUNT:,}")

    dividend = Transaction(
        asset_id=1, txn_type="DIVIDEND", quantity=Decimal("0"),
        price=Decimal("0"), fees=Decimal("0"),
        txn_date=date.today() - timedelta(days=30),
    )
    db.session.add(dividend)
    db.session.flush()
    db.session.add(WalletLedger(
        entry_type="DIVIDEND", amount=Decimal("2500"),
        transaction_id=dividend.transaction_id,
    ))
    db.session.add(WalletLedger(entry_type="DEPOSIT", amount=OPENING_DEPOSIT))
    print(f"  1 dividend, Rs {OPENING_DEPOSIT:,} opening deposit")

    db.session.commit()

    print("\nBenchmarks")
    for code, level, vol in BENCHMARKS:
        walk = backward_walk(level, vol, HISTORY_DAYS, drift=0.00035)
        for offset, price in enumerate(walk):
            db.session.add(BenchmarkPriceHistory(
                benchmark_code=code,
                price_date=date.today() - timedelta(days=len(walk) - 1 - offset),
                close_price=Decimal(str(price)),
            ))
        print(f"  {code:8} {len(walk)} bars, latest {walk[-1]:,.2f}")

    db.session.commit()


def print_summary():
    from services import analytics_service

    summary = analytics_service.get_portfolio_summary()
    print("\nSeeded portfolio")
    print(f"  holdings         {summary['holdings_count']}")
    print(f"  invested         Rs {float(summary['total_invested']):>12,.0f}")
    print(f"  current value    Rs {float(summary['total_current']):>12,.0f}")
    print(f"  unrealised P/L   Rs {float(summary['total_pl']):>12,.0f}  "
          f"({float(summary['total_pl_pct']):+.2f}%)")
    print(f"\n  price history    {PriceHistory.query.count():,} rows")
    print(f"  benchmark bars   {BenchmarkPriceHistory.query.count():,} rows")
    print(f"  transactions     {Transaction.query.count()}")
    print("\nStart the API with:  flask --app app run --port 5000")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_demo()
        print_summary()
