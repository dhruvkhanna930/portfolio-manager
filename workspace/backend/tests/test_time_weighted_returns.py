"""Regression test for the Phase 14 time-weighting bug.

The first cut of get_portfolio_risk() derived returns by differencing the §6.8
portfolio *value* series. That series moves when the user contributes money, so
buying into a portfolio registered as a colossal one-day gain. On the real
seeded portfolio (most of it bought on a single day) it produced ~300%
annualized volatility, a Sortino of 26 and a Calmar of 27 -- numbers that look
authoritative and are pure artifact of the cash flow.

This test builds a portfolio where the market does nothing at all and the only
event is a purchase. The correct time-weighted return for every day is 0.
"""

from datetime import date, timedelta

import pytest

from app import create_app
from config import Config
from models import AssetMetadata, Holding, PriceHistory, Transaction, db
from services import risk_service as rs


class _TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True


@pytest.fixture()
def app_ctx():
    app = create_app(_TestConfig)
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


def _seed_flat_market_with_a_mid_window_purchase():
    """Two assets, both with a perfectly flat price for 120 days. The user holds
    A the whole time and buys B halfway through.
    """
    start = date(2026, 1, 1)
    asset_a = AssetMetadata(symbol="AAA.NS", asset_type="STOCK", name="Asset A", currency="INR")
    asset_b = AssetMetadata(symbol="BBB.NS", asset_type="STOCK", name="Asset B", currency="INR")
    db.session.add_all([asset_a, asset_b])
    db.session.flush()

    for asset, price in ((asset_a, 100), (asset_b, 500)):
        for i in range(120):
            db.session.add(
                PriceHistory(
                    asset_id=asset.asset_id,
                    price_date=start + timedelta(days=i),
                    close_price=price,
                    source="test",
                )
            )

    db.session.add(
        Transaction(
            asset_id=asset_a.asset_id, txn_type="BUY", quantity=10, price=100,
            fees=0, txn_date=start,
        )
    )
    # The contribution: a large buy partway through the window.
    db.session.add(
        Transaction(
            asset_id=asset_b.asset_id, txn_type="BUY", quantity=100, price=500,
            fees=0, txn_date=start + timedelta(days=60),
        )
    )
    db.session.add_all(
        [
            Holding(asset_id=asset_a.asset_id, quantity=10, avg_buy_price=100, first_bought=start),
            Holding(
                asset_id=asset_b.asset_id, quantity=100, avg_buy_price=500,
                first_bought=start + timedelta(days=60),
            ),
        ]
    )
    db.session.commit()


def test_contribution_does_not_register_as_a_return(app_ctx):
    _seed_flat_market_with_a_mid_window_purchase()

    returns_by_date, _index = rs.get_portfolio_return_series("ALL")

    assert returns_by_date, "expected a return series to be produced"
    worst = max(abs(v) for v in returns_by_date.values())
    assert worst == pytest.approx(0.0, abs=1e-12), (
        f"flat market with one purchase produced a non-zero daily return of {worst:.6f} -- "
        "the buy is being counted as performance"
    )


def test_flat_market_yields_zero_volatility_not_a_huge_number(app_ctx):
    _seed_flat_market_with_a_mid_window_purchase()

    _returns, index = rs.get_portfolio_return_series("ALL")
    metrics = rs.compute_metrics(index)

    assert metrics["volatility"] == pytest.approx(0.0, abs=1e-9)
    assert metrics["max_drawdown"] == pytest.approx(0.0, abs=1e-9)


def test_value_series_still_reflects_the_contribution(app_ctx):
    """The value series is *supposed* to jump on a purchase -- that's what makes
    it right for "what am I worth" and wrong for risk. Both behaviours coexist.
    """
    _seed_flat_market_with_a_mid_window_purchase()

    values = rs.get_portfolio_value_series("ALL")
    assert values, "expected a value series"
    assert max(values.values()) > min(values.values()), (
        "portfolio value should rise when the user buys more"
    )
