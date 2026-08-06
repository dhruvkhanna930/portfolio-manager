"""Portfolio statistics (CLAUDE.md §14.5).

All computed from existing holdings/transactions -- no new tables, no fetching.
Realised P/L per trade is replayed from the transaction log using the same
weighted-average-cost basis as §6.4/§6.5, so "largest gain" here always agrees
with the realised P/L shown elsewhere.
"""

from datetime import date
from decimal import Decimal

from models import Holding, Transaction
from services import analytics_service


def _realised_trades():
    """Every SELL replayed into a booked gain/loss, in date order.

    Walks the full transaction history maintaining running quantity and weighted
    average cost per asset, exactly as §6.5 does, because a fully-sold position
    no longer has a holdings row to read a cost basis from.
    """
    transactions = Transaction.query.order_by(
        Transaction.txn_date, Transaction.transaction_id
    ).all()

    running = {}  # asset_id -> [qty, avg_cost]
    trades = []

    for txn in transactions:
        state = running.setdefault(txn.asset_id, [Decimal("0"), Decimal("0")])
        quantity = Decimal(txn.quantity)
        price = Decimal(txn.price)
        fees = Decimal(txn.fees or 0)

        if txn.txn_type == "BUY":
            new_qty = state[0] + quantity
            state[1] = (state[0] * state[1] + quantity * price) / new_qty if new_qty else Decimal("0")
            state[0] = new_qty
        elif txn.txn_type == "SELL":
            realised = (price - state[1]) * quantity - fees
            trades.append(
                {
                    "asset_id": txn.asset_id,
                    "symbol": txn.asset.symbol,
                    "name": txn.asset.name,
                    "txn_date": txn.txn_date,
                    "quantity": quantity,
                    "sell_price": price,
                    "cost_basis": state[1],
                    "realised_pl": realised,
                    "value": quantity * price,
                }
            )
            state[0] = max(state[0] - quantity, Decimal("0"))
        elif txn.txn_type == "DIVIDEND":
            trades.append(
                {
                    "asset_id": txn.asset_id,
                    "symbol": txn.asset.symbol,
                    "name": txn.asset.name,
                    "txn_date": txn.txn_date,
                    "quantity": quantity,
                    "sell_price": price,
                    "cost_basis": Decimal("0"),
                    "realised_pl": quantity * price,
                    "value": Decimal("0"),  # dividends aren't turnover
                }
            )

    return trades


def _holding_brief(row):
    holding = row["holding"]
    return {
        "asset_id": holding.asset_id,
        "symbol": holding.asset.symbol,
        "name": holding.asset.name,
        "profit_loss": row["profit_loss"],
        "profit_loss_pct": row["profit_loss_pct"],
        "current_value": row["current_value"],
    }


def get_statistics():
    holdings = Holding.query.all()
    rows = analytics_service.compute_holding_metrics(holdings)
    today = date.today()

    if not rows:
        return {
            "has_holdings": False,
            "holdings_count": 0,
            "best_performer": None,
            "worst_performer": None,
            "win_rate_pct": None,
            "winners_count": 0,
            "losers_count": 0,
            "avg_holding_period_days": None,
            "longest_held": None,
            "largest_gain": None,
            "largest_loss": None,
            "turnover_ratio": None,
            "realised_trades_count": 0,
        }

    # Unrealised performance is only meaningful for holdings we could actually
    # price; an unpriced holding sits at zero P/L by construction (§6.1) and would
    # otherwise masquerade as a break-even position in best/worst and win rate.
    priced = [r for r in rows if r["is_priced"]]
    ranked = sorted(priced, key=lambda r: r["profit_loss_pct"])

    winners = [r for r in priced if r["profit_loss"] > 0]
    win_rate = (Decimal(len(winners)) / Decimal(len(priced)) * 100) if priced else None

    with_dates = [r for r in rows if r["holding"].first_bought]
    avg_period = (
        sum((today - r["holding"].first_bought).days for r in with_dates) / len(with_dates)
        if with_dates
        else None
    )
    longest = min(with_dates, key=lambda r: r["holding"].first_bought) if with_dates else None

    trades = _realised_trades()
    gains = [t for t in trades if t["realised_pl"] > 0]
    losses = [t for t in trades if t["realised_pl"] < 0]

    # Turnover: sell value against average portfolio value over the period. Using
    # current value as the denominator (rather than a true time-average) keeps
    # this consistent with every other "current" figure in the app; it's labelled
    # as an approximation in the response.
    total_current = sum((r["current_value"] for r in rows), Decimal("0"))
    sell_value = sum((t["value"] for t in trades), Decimal("0"))
    turnover = (sell_value / total_current) if total_current > 0 else None

    return {
        "has_holdings": True,
        "holdings_count": len(rows),
        "priced_holdings_count": len(priced),
        "best_performer": _holding_brief(ranked[-1]) if ranked else None,
        "worst_performer": _holding_brief(ranked[0]) if ranked else None,
        "win_rate_pct": win_rate,
        "winners_count": len(winners),
        "losers_count": len(priced) - len(winners),
        "avg_holding_period_days": round(avg_period) if avg_period is not None else None,
        "longest_held": (
            {
                "asset_id": longest["holding"].asset_id,
                "symbol": longest["holding"].asset.symbol,
                "name": longest["holding"].asset.name,
                "first_bought": longest["holding"].first_bought,
                "days_held": (today - longest["holding"].first_bought).days,
            }
            if longest
            else None
        ),
        "largest_gain": max(gains, key=lambda t: t["realised_pl"]) if gains else None,
        "largest_loss": min(losses, key=lambda t: t["realised_pl"]) if losses else None,
        "realised_trades_count": len(trades),
        "turnover_ratio": turnover,
        "notes": {
            "win_rate": "Share of currently-priced holdings sitting at an unrealised gain.",
            "largest_gain_loss": "Realised, from actual SELL transactions -- not paper gains.",
            "turnover": "Approximate: total sell value divided by current portfolio value.",
        },
    }
