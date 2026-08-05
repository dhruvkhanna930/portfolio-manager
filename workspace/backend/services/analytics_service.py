import bisect
import math
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from models import Holding, PriceHistory, Transaction

VALID_ALLOCATION_DIMENSIONS = ("type", "sector", "holding")
VALID_PERFORMANCE_PERIODS = ("1W", "1M", "6M", "1Y", "3Y", "5Y", "ALL")

_PERFORMANCE_PERIOD_DELTA = {
    "1W": relativedelta(weeks=1),
    "1M": relativedelta(months=1),
    "6M": relativedelta(months=6),
    "1Y": relativedelta(years=1),
    "3Y": relativedelta(years=3),
    "5Y": relativedelta(years=5),
}

# §4.2: full daily resolution for short/medium windows, weekly-ish for 3Y/5Y,
# monthly-ish for ALL -- caps chosen as point budgets rather than exact
# calendar buckets, since trading calendars aren't evenly spaced anyway.
_PERFORMANCE_MAX_POINTS = {
    "1W": 400,
    "1M": 400,
    "6M": 400,
    "1Y": 400,
    "3Y": 250,
    "5Y": 250,
    "ALL": 200,
}


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


def _downsample_dates(dates, max_points):
    if len(dates) <= max_points:
        return dates
    stride = math.ceil(len(dates) / max_points)
    sampled = dates[::stride]
    if sampled[-1] != dates[-1]:
        sampled.append(dates[-1])
    return sampled


def get_portfolio_performance(period="1Y"):
    """Portfolio value over time per CLAUDE.md §6.8:

        value(D) = Σ over holdings [ units_held_on(D) × price_history[asset, D] ]

    units_held_on(D) is replayed from the transaction log (so a since-sold asset
    still contributes for the dates it was actually held). Prices are read
    entirely from the price_history cache -- this never calls yfinance/mfapi.in
    live. No 1D option: per §4.2 portfolio-level intraday is out of scope, only
    the per-asset chart (Phase 8) gets a live 1D view.
    """
    if period not in VALID_PERFORMANCE_PERIODS:
        raise ValueError(f"invalid performance period: {period}")

    transactions = Transaction.query.order_by(Transaction.txn_date, Transaction.transaction_id).all()
    if not transactions:
        return {"period": period, "points": []}

    asset_ids = sorted({t.asset_id for t in transactions})
    first_txn_date = min(t.txn_date for t in transactions)
    today = date.today()
    end_date = today

    if period == "ALL":
        start_date = first_txn_date
    else:
        start_date = max(today - _PERFORMANCE_PERIOD_DELTA[period], first_txn_date)

    # Per-asset cumulative quantity as of each transaction date (collapsing same-day
    # transactions to their end-of-day cumulative quantity).
    qty_dates = {asset_id: [] for asset_id in asset_ids}
    qty_values = {asset_id: [] for asset_id in asset_ids}
    running_qty = {asset_id: Decimal("0") for asset_id in asset_ids}
    for txn in transactions:
        if txn.txn_type == "BUY":
            running_qty[txn.asset_id] += Decimal(txn.quantity)
        elif txn.txn_type == "SELL":
            running_qty[txn.asset_id] -= Decimal(txn.quantity)
        # DIVIDEND doesn't change quantity held.
        dates, values = qty_dates[txn.asset_id], qty_values[txn.asset_id]
        if dates and dates[-1] == txn.txn_date:
            values[-1] = running_qty[txn.asset_id]
        else:
            dates.append(txn.txn_date)
            values.append(running_qty[txn.asset_id])

    # Per-asset price timeline, unbounded below end_date so early sample dates can
    # still forward-fill from whatever price predates them.
    price_rows = (
        PriceHistory.query.filter(
            PriceHistory.asset_id.in_(asset_ids), PriceHistory.price_date <= end_date
        )
        .order_by(PriceHistory.asset_id, PriceHistory.price_date)
        .all()
    )
    price_dates = {asset_id: [] for asset_id in asset_ids}
    price_values = {asset_id: [] for asset_id in asset_ids}
    sample_date_set = set()
    for row in price_rows:
        price_dates[row.asset_id].append(row.price_date)
        price_values[row.asset_id].append(Decimal(row.close_price))
        if start_date <= row.price_date <= end_date:
            sample_date_set.add(row.price_date)

    if not sample_date_set:
        return {"period": period, "points": []}

    sample_dates = _downsample_dates(sorted(sample_date_set), _PERFORMANCE_MAX_POINTS[period])

    def qty_on(asset_id, d):
        dates = qty_dates[asset_id]
        idx = bisect.bisect_right(dates, d) - 1
        return qty_values[asset_id][idx] if idx >= 0 else Decimal("0")

    def price_on(asset_id, d):
        dates = price_dates[asset_id]
        idx = bisect.bisect_right(dates, d) - 1
        return price_values[asset_id][idx] if idx >= 0 else None

    points = []
    for d in sample_dates:
        total = Decimal("0")
        for asset_id in asset_ids:
            qty = qty_on(asset_id, d)
            if qty == 0:
                continue
            price = price_on(asset_id, d)
            if price is None:
                continue
            total += qty * price
        points.append({"date": d, "value": total})

    return {"period": period, "points": points}


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


def historical_returns_calc(asset_id, invest_date, amount):
    """Historical Returns Calculator per CLAUDE.md §6.11: 'What if I had invested?'
    Given an asset, a past date, and an amount, looks up the actual price on or near
    that date from price_history, computes units bought, current value, returns.
    """
    from models import AssetMetadata, PriceHistory

    asset = AssetMetadata.query.get(asset_id)
    if not asset:
        raise ValueError(f"asset {asset_id} not found")

    snapshot = asset.price_snapshot
    if not snapshot or snapshot.price is None:
        raise ValueError(f"asset {asset_id} has no current price")

    current_price = Decimal(snapshot.price)
    current_date = snapshot.as_of.date() if snapshot.as_of else date.today()

    # Find the closest price_history row on or before invest_date
    price_row = (
        PriceHistory.query.filter(
            PriceHistory.asset_id == asset_id,
            PriceHistory.price_date <= invest_date,
        )
        .order_by(PriceHistory.price_date.desc())
        .first()
    )

    if not price_row:
        raise ValueError(f"no price history found for {asset_id} on or before {invest_date}")

    invest_price = Decimal(price_row.close_price)
    units_bought = Decimal(amount) / invest_price
    current_value = units_bought * current_price
    absolute_return = current_value - Decimal(amount)

    years_held = (current_date - invest_date).days / 365.0
    if years_held <= 0:
        cagr = Decimal("0")
    else:
        cagr_float = ((float(current_value) / float(amount)) ** (1.0 / years_held)) - 1.0
        cagr = Decimal(str(cagr_float))

    return {
        "invested_amount": Decimal(amount),
        "invest_date": invest_date,
        "invest_price": invest_price,
        "units_bought": units_bought,
        "current_price": current_price,
        "current_date": current_date,
        "current_value": current_value,
        "absolute_return": absolute_return,
        "absolute_return_pct": (absolute_return / Decimal(amount) * 100) if amount else Decimal("0"),
        "years_held": Decimal(str(years_held)),
        "cagr_pct": cagr * 100,
    }


def sip_calc_projected(monthly_amount, annual_return_pct, years, step_up_pct=None):
    """SIP Calculator (Projected mode) per CLAUDE.md §6.12 Mode A.
    Standard forward compounding: FV = P × [ ((1 + r)^n − 1) / r ] × (1 + r)
    With optional step_up_pct: monthly amount increases by step_up_pct annually.
    """
    monthly_amount = Decimal(monthly_amount)
    annual_return_pct = Decimal(annual_return_pct)
    years = Decimal(years)
    step_up_pct = Decimal(step_up_pct) if step_up_pct else Decimal("0")

    monthly_rate = annual_return_pct / 100 / 12
    months = int(years * 12)

    if monthly_rate == 0:
        # No growth: FV = P × n
        total_invested = monthly_amount * months
        final_value = total_invested
        xirr_equivalent = Decimal("0")
    else:
        # Standard formula with step-up: month-by-month loop
        total_invested = Decimal("0")
        final_value = Decimal("0")

        for month in range(1, months + 1):
            # Apply step-up: every 12 months, increase the base amount
            years_elapsed = (month - 1) // 12
            step_multiplier = (1 + step_up_pct / 100) ** years_elapsed
            monthly_pay = monthly_amount * step_multiplier

            total_invested += monthly_pay
            # Compound forward to end-of-period
            remaining_months = months - month
            growth_factor = (1 + monthly_rate) ** remaining_months
            final_value += monthly_pay * growth_factor

        # XIRR approximation: assume linear cashflows for projected mode
        # (real XIRR would need pyxirr, which requires actual dates)
        if total_invested > 0:
            ratio = float(final_value / total_invested)
            xirr_float = ((ratio) ** (1.0 / float(years)) - 1.0) * 100.0
            xirr_equivalent = Decimal(str(xirr_float))
        else:
            xirr_equivalent = Decimal("0")

    return {
        "mode": "projected",
        "monthly_amount": monthly_amount,
        "step_up_pct": step_up_pct,
        "annual_return_pct": annual_return_pct,
        "years": years,
        "months": months,
        "total_invested": total_invested,
        "final_value": final_value,
        "total_return": final_value - total_invested,
        "total_return_pct": (final_value - total_invested) / total_invested * 100 if total_invested else Decimal("0"),
    }


def sip_calc_historical(asset_id, monthly_amount, start_date, end_date=None, step_up_pct=None):
    """SIP Calculator (Historical mode) per CLAUDE.md §6.12 Mode B.
    Walks real price_history month-by-month, computing units bought and final XIRR.
    """
    from models import AssetMetadata, PriceHistory

    try:
        from pyxirr import xirr
    except ImportError:
        raise ImportError("pyxirr is required for historical SIP calculation")

    asset = AssetMetadata.query.get(asset_id)
    if not asset:
        raise ValueError(f"asset {asset_id} not found")

    snapshot = asset.price_snapshot
    if not snapshot or snapshot.price is None:
        raise ValueError(f"asset {asset_id} has no current price")

    current_price = Decimal(snapshot.price)
    current_date = snapshot.as_of.date() if snapshot.as_of else date.today()

    if end_date is None:
        end_date = current_date

    monthly_amount = Decimal(monthly_amount)
    step_up_pct = Decimal(step_up_pct) if step_up_pct else Decimal("0")

    # Collect all price_history rows in range
    price_rows = (
        PriceHistory.query.filter(
            PriceHistory.asset_id == asset_id,
            PriceHistory.price_date >= start_date,
            PriceHistory.price_date <= end_date,
        )
        .order_by(PriceHistory.price_date)
        .all()
    )

    if not price_rows:
        raise ValueError(f"no price history found for {asset_id} between {start_date} and {end_date}")

    # Walk month by month
    cashflows = []  # (date, amount) for XIRR
    total_invested = Decimal("0")
    total_units = Decimal("0")
    current_month_year = start_date.replace(day=1)
    month_idx = 0

    while current_month_year <= end_date:
        # Find first price in this calendar month
        month_start = current_month_year
        month_end = (current_month_year + relativedelta(months=1)) - relativedelta(days=1)

        price_in_month = None
        price_date_in_month = None
        for pr in price_rows:
            if month_start <= pr.price_date <= month_end:
                price_in_month = Decimal(pr.close_price)
                price_date_in_month = pr.price_date
                break

        if price_in_month is not None:
            # Calculate this month's investment (with step-up)
            years_elapsed = month_idx // 12
            step_multiplier = (1 + step_up_pct / 100) ** years_elapsed
            this_month_amount = monthly_amount * step_multiplier

            units_this_month = this_month_amount / price_in_month
            total_invested += this_month_amount
            total_units += units_this_month

            # Record cashflow for XIRR (negative = money out)
            cashflows.append((price_date_in_month, -float(this_month_amount)))

        current_month_year += relativedelta(months=1)
        month_idx += 1

    # Current value and XIRR
    current_value = total_units * current_price
    cashflows.append((current_date, float(current_value)))

    try:
        xirr_result = xirr(cashflows)
        xirr_pct = Decimal(str(xirr_result * 100))
    except Exception:
        # If xirr fails (e.g., all same sign), return None
        xirr_pct = None

    return {
        "mode": "historical",
        "asset_id": asset_id,
        "monthly_amount": monthly_amount,
        "step_up_pct": step_up_pct,
        "start_date": start_date,
        "end_date": end_date,
        "total_invested": total_invested,
        "total_units": total_units,
        "current_price": current_price,
        "current_date": current_date,
        "current_value": current_value,
        "total_return": current_value - total_invested,
        "total_return_pct": (current_value - total_invested) / total_invested * 100 if total_invested else Decimal("0"),
        "xirr_pct": xirr_pct,
    }
