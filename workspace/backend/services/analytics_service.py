from decimal import Decimal

from models import Holding, Transaction

VALID_ALLOCATION_DIMENSIONS = ("type", "sector", "holding")


def _sector_label(asset):
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


def compute_holding_metrics(holdings):
    """Per-holding calculations per CLAUDE.md §6.1. Returns a list of dicts, each
    keyed by "holding" (the ORM object) plus every computed field. A holding whose
    asset has no price_snapshot yet (never synced, or a bond with no manual price
    entered) falls back to current_price = avg_buy_price, i.e. zero unrealised P/L
    until it's actually priced — never crashes, never fabricates a gain/loss.
    """
    rows = []
    for holding in holdings:
        asset = holding.asset
        snapshot = asset.price_snapshot
        quantity = Decimal(holding.quantity)
        avg_buy_price = Decimal(holding.avg_buy_price)
        invested_value = quantity * avg_buy_price

        if snapshot is not None and snapshot.price is not None:
            current_price = Decimal(snapshot.price)
            day_change = Decimal(snapshot.day_change) if snapshot.day_change is not None else Decimal("0")
            is_priced = True
        else:
            current_price = avg_buy_price
            day_change = Decimal("0")
            is_priced = False

        current_value = quantity * current_price
        profit_loss = current_value - invested_value
        profit_loss_pct = (profit_loss / invested_value * 100) if invested_value else Decimal("0")
        day_change_value = quantity * day_change

        rows.append(
            {
                "holding": holding,
                "current_price": current_price,
                "invested_value": invested_value,
                "current_value": current_value,
                "profit_loss": profit_loss,
                "profit_loss_pct": profit_loss_pct,
                "day_change_value": day_change_value,
                "is_priced": is_priced,
            }
        )

    total_current = sum((r["current_value"] for r in rows), Decimal("0"))
    for r in rows:
        r["weight_pct"] = (r["current_value"] / total_current * 100) if total_current else Decimal("0")

    return rows


def get_realised_pl():
    """Realised P/L per CLAUDE.md §6.5: booked on each SELL as
    (sell_price − avg_buy_price) × sold_qty, net of fees.

    Replayed from the transaction log rather than read off holdings, because a
    fully-sold position deletes its holding row -- its realised gain must survive
    that deletion.
    """
    transactions = Transaction.query.order_by(
        Transaction.txn_date, Transaction.transaction_id
    ).all()

    running = {}  # asset_id -> [quantity, avg_buy_price]
    realised = Decimal("0")

    for txn in transactions:
        asset_id = txn.asset_id
        quantity = Decimal(txn.quantity)
        price = Decimal(txn.price)
        fees = Decimal(txn.fees or 0)
        state = running.setdefault(asset_id, [Decimal("0"), Decimal("0")])

        if txn.txn_type == "BUY":
            new_qty = state[0] + quantity
            state[1] = (
                (state[0] * state[1] + quantity * price) / new_qty if new_qty else Decimal("0")
            )
            state[0] = new_qty
        elif txn.txn_type == "SELL":
            realised += (price - state[1]) * quantity - fees
            state[0] = max(state[0] - quantity, Decimal("0"))
        elif txn.txn_type == "DIVIDEND":
            realised += quantity * price

    return realised


def get_portfolio_summary():
    """Portfolio totals per CLAUDE.md §6.2, plus the realised/unrealised split (§6.5)."""
    holdings = Holding.query.all()
    rows = compute_holding_metrics(holdings)

    total_invested = sum((r["invested_value"] for r in rows), Decimal("0"))
    total_current = sum((r["current_value"] for r in rows), Decimal("0"))
    total_pl = total_current - total_invested
    total_pl_pct = (total_pl / total_invested * 100) if total_invested else Decimal("0")
    day_pl = sum((r["day_change_value"] for r in rows), Decimal("0"))

    return {
        "total_invested": total_invested,
        "total_current": total_current,
        "total_pl": total_pl,
        "total_pl_pct": total_pl_pct,
        "day_pl": day_pl,
        "holdings_count": len(rows),
        "unrealised_pl": total_pl,
        "realised_pl": get_realised_pl(),
    }


def get_allocation(by="type"):
    """Allocation breakdown per CLAUDE.md §6.3. `by` is one of type|sector|holding."""
    if by not in VALID_ALLOCATION_DIMENSIONS:
        raise ValueError(f"invalid allocation dimension: {by}")

    holdings = Holding.query.all()
    rows = compute_holding_metrics(holdings)
    total_current = sum((r["current_value"] for r in rows), Decimal("0"))

    if by == "holding":
        # each holding is already a unique bucket -- no aggregation needed
        raw_items = [(r["holding"].asset.name, r["current_value"]) for r in rows]
    else:
        buckets = {}
        for r in rows:
            asset = r["holding"].asset
            label = asset.asset_type if by == "type" else _sector_label(asset)
            buckets[label] = buckets.get(label, Decimal("0")) + r["current_value"]
        raw_items = list(buckets.items())

    items = [
        {
            "label": label,
            "value": value,
            "pct": (value / total_current * 100) if total_current else Decimal("0"),
        }
        for label, value in raw_items
    ]
    items.sort(key=lambda i: i["value"], reverse=True)

    return {"by": by, "total_current": total_current, "items": items}


def compute_weighted_avg_buy_price(old_qty, old_avg, buy_qty, buy_price):
    """Weighted-average buy price on a BUY, per CLAUDE.md §6.4. Pure function --
    not wired to transaction CRUD yet (Phase 6), but the math is stable now.
    """
    old_qty = Decimal(old_qty)
    old_avg = Decimal(old_avg)
    buy_qty = Decimal(buy_qty)
    buy_price = Decimal(buy_price)
    new_qty = old_qty + buy_qty
    if new_qty == 0:
        return Decimal("0")
    return (old_qty * old_avg + buy_qty * buy_price) / new_qty
