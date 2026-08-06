"""Portfolio state as it actually stood on an arbitrary past date (§15 item 3).

This is the read-side of the timeline scrubber: drag to a date, see what you
really held and what it was really worth that day. It is the same replay math
as §6.8 -- units_held_on(D) from the transaction log, price from the
price_history cache, forward-filled -- just evaluated at one date and broken out
per holding instead of collapsed to a single total per date.

Cost basis is replayed the same way (§6.4's weighted average, applied
transaction by transaction) rather than read off today's holdings row, because
today's avg_buy_price reflects every BUY since -- including ones that hadn't
happened yet on the date being viewed.
"""

import bisect
from datetime import date
from decimal import Decimal

from models import AssetMetadata, PriceHistory, Transaction
from services.analytics_service import _sector_label


def _replay_to(transactions, on_date):
    """Walk the log up to on_date, returning {asset_id: (quantity, avg_cost)}.

    SELLs reduce quantity and leave the average alone (§6.4/§6.5) -- the realised
    part is booked separately and doesn't change the basis of what's still held.
    """
    state = {}
    for txn in transactions:
        if txn.txn_date > on_date:
            break
        qty, avg = state.get(txn.asset_id, (Decimal("0"), Decimal("0")))
        if txn.txn_type == "BUY":
            buy_qty, buy_price = Decimal(txn.quantity), Decimal(txn.price)
            new_qty = qty + buy_qty
            avg = ((qty * avg) + (buy_qty * buy_price)) / new_qty if new_qty > 0 else Decimal("0")
            qty = new_qty
        elif txn.txn_type == "SELL":
            qty -= Decimal(txn.quantity)
        # DIVIDEND changes neither quantity nor basis.
        state[txn.asset_id] = (qty, avg)
    return state


def get_snapshot(on_date):
    """Holdings, totals and sector split as of on_date.

    Assets whose price history doesn't reach back that far are reported in
    `unpriced` rather than silently valued at zero -- a missing price is not the
    same fact as a worthless position.
    """
    transactions = Transaction.query.order_by(
        Transaction.txn_date, Transaction.transaction_id
    ).all()
    if not transactions:
        return {
            "date": on_date,
            "has_data": False,
            "total_invested": Decimal("0"),
            "total_current": Decimal("0"),
            "total_pl": Decimal("0"),
            "total_pl_pct": None,
            "holdings_count": 0,
            "items": [],
            "sectors": [],
            "unpriced": [],
        }

    first_txn_date = min(t.txn_date for t in transactions)
    state = _replay_to(transactions, on_date)
    held = {aid: (q, a) for aid, (q, a) in state.items() if q > 0}

    if not held:
        return {
            "date": on_date,
            "has_data": on_date >= first_txn_date,
            "total_invested": Decimal("0"),
            "total_current": Decimal("0"),
            "total_pl": Decimal("0"),
            "total_pl_pct": None,
            "holdings_count": 0,
            "items": [],
            "sectors": [],
            "unpriced": [],
        }

    # One query for every price at or before the date; take the last per asset.
    rows = (
        PriceHistory.query.filter(
            PriceHistory.asset_id.in_(list(held)), PriceHistory.price_date <= on_date
        )
        .order_by(PriceHistory.asset_id, PriceHistory.price_date)
        .all()
    )
    dates_by_asset, prices_by_asset = {}, {}
    for row in rows:
        dates_by_asset.setdefault(row.asset_id, []).append(row.price_date)
        prices_by_asset.setdefault(row.asset_id, []).append(Decimal(row.close_price))

    def price_on(asset_id):
        dates = dates_by_asset.get(asset_id)
        if not dates:
            return None
        idx = bisect.bisect_right(dates, on_date) - 1
        return prices_by_asset[asset_id][idx] if idx >= 0 else None

    assets = {
        a.asset_id: a
        for a in AssetMetadata.query.filter(AssetMetadata.asset_id.in_(list(held))).all()
    }

    items, unpriced = [], []
    total_invested = total_current = Decimal("0")
    for asset_id, (qty, avg) in held.items():
        asset = assets.get(asset_id)
        if asset is None:
            continue
        invested = qty * avg
        price = price_on(asset_id)
        if price is None:
            unpriced.append({"asset_id": asset_id, "symbol": asset.symbol, "name": asset.name})
            continue
        current = qty * price
        total_invested += invested
        total_current += current
        items.append(
            {
                "asset_id": asset_id,
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "sector": _sector_label(asset),
                "quantity": qty,
                "avg_buy_price": avg,
                "price": price,
                "invested_value": invested,
                "current_value": current,
                "profit_loss": current - invested,
                "profit_loss_pct": ((current - invested) / invested * 100) if invested > 0 else None,
            }
        )

    items.sort(key=lambda i: i["current_value"], reverse=True)
    for item in items:
        item["weight_pct"] = (
            (item["current_value"] / total_current * 100) if total_current > 0 else Decimal("0")
        )

    by_sector = {}
    for item in items:
        by_sector[item["sector"]] = by_sector.get(item["sector"], Decimal("0")) + item["current_value"]
    sectors = sorted(
        (
            {
                "label": label,
                "value": value,
                "pct": (value / total_current * 100) if total_current > 0 else Decimal("0"),
            }
            for label, value in by_sector.items()
        ),
        key=lambda s: s["value"],
        reverse=True,
    )

    total_pl = total_current - total_invested
    return {
        "date": on_date,
        "has_data": True,
        "total_invested": total_invested,
        "total_current": total_current,
        "total_pl": total_pl,
        "total_pl_pct": (total_pl / total_invested * 100) if total_invested > 0 else None,
        "holdings_count": len(items),
        "items": items,
        "sectors": sectors,
        "unpriced": unpriced,
    }


def get_timeline_bounds():
    """Earliest and latest dates the scrubber can meaningfully address."""
    first = Transaction.query.order_by(Transaction.txn_date).first()
    return {
        "start_date": first.txn_date if first else None,
        "end_date": date.today(),
        "has_data": first is not None,
    }
