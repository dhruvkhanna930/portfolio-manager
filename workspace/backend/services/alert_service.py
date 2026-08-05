"""In-app alerts (§15.5).

Nothing here is a notification in the infrastructure sense: there is no auth, no
email address and no device token in this app, so there is nowhere to send
anything. Alerts are *derived state* -- recomputed from current prices, holdings
and SIP schedules every time the panel is opened. That means they can never go
stale, never need a "mark as read" table, and never claim something was
delivered.

Four sources, all from data we already own:
  - price targets the user set     -> price_targets vs. price_snapshot
  - allocation drift               -> holding weights vs. an even split
  - SIP instalments coming due     -> sips.frequency/day_of_cycle vs. today
  - invested-capital milestones    -> transactions
"""

from datetime import date, timedelta
from decimal import Decimal

from models import Holding, PriceTarget, Sip, Transaction

# A holding drifting past this share of the portfolio is worth surfacing. Same
# spirit as §14.3's sector alert, applied to single positions.
CONCENTRATION_ALERT_PCT = Decimal("35")

# How far ahead a SIP instalment counts as "coming up".
SIP_DUE_WINDOW_DAYS = 7

# Invested-capital milestones, in rupees.
MILESTONES = [Decimal(v) for v in (100_000, 250_000, 500_000, 1_000_000, 2_500_000, 5_000_000)]

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


def _price_target_alerts():
    alerts = []
    for target in PriceTarget.query.all():
        asset = target.asset
        snapshot = asset.price_snapshot if asset else None
        if snapshot is None or snapshot.price is None:
            continue
        price, want = Decimal(snapshot.price), Decimal(target.target_price)
        hit = price >= want if target.direction == "ABOVE" else price <= want
        if not hit:
            continue
        alerts.append(
            {
                "id": f"target-{target.target_id}",
                "kind": "PRICE_TARGET",
                "severity": "info",
                "title": f"{asset.symbol} hit your {target.direction.lower()} target",
                "body": (
                    f"Now ₹{price:,.2f}, target was ₹{want:,.2f}."
                    + (f" {target.note}" if target.note else "")
                ),
                "asset_id": asset.asset_id,
                "symbol": asset.symbol,
            }
        )
    return alerts


def _concentration_alerts():
    holdings = Holding.query.all()
    priced = []
    total = Decimal("0")
    for holding in holdings:
        snapshot = holding.asset.price_snapshot if holding.asset else None
        if snapshot is None or snapshot.price is None:
            continue
        value = Decimal(holding.quantity) * Decimal(snapshot.price)
        priced.append((holding, value))
        total += value
    if total <= 0 or len(priced) < 2:
        return []

    alerts = []
    for holding, value in priced:
        weight = value / total * 100
        if weight < CONCENTRATION_ALERT_PCT:
            continue
        alerts.append(
            {
                "id": f"drift-{holding.holding_id}",
                "kind": "ALLOCATION_DRIFT",
                "severity": "warning",
                "title": f"{holding.asset.symbol} is {weight:.0f}% of your portfolio",
                "body": (
                    f"Above the {CONCENTRATION_ALERT_PCT:.0f}% single-position threshold this app "
                    "flags at. Concentration isn't automatically wrong -- it just means more of "
                    "your outcome rides on one name."
                ),
                "asset_id": holding.asset_id,
                "symbol": holding.asset.symbol,
            }
        )
    return alerts


def _next_due(sip, today):
    """Next instalment date on or after today, or None if the SIP has ended.

    Approximates month-length differences by clamping the requested day-of-month
    to what the month actually has -- a SIP set to the 31st runs on the 30th in
    November rather than being skipped.
    """
    if not sip.is_active or sip.start_date > today + timedelta(days=SIP_DUE_WINDOW_DAYS):
        return sip.start_date if sip.is_active and sip.start_date >= today else None
    if sip.end_date and sip.end_date < today:
        return None

    if sip.frequency == "DAILY":
        return today
    if sip.frequency == "WEEKLY":
        target_dow = (sip.day_of_cycle - 1) % 7 if sip.day_of_cycle else sip.start_date.weekday()
        delta = (target_dow - today.weekday()) % 7
        return today + timedelta(days=delta)

    # MONTHLY / QUARTERLY both land on a day-of-month.
    day = sip.day_of_cycle or sip.start_date.day
    step = 3 if sip.frequency == "QUARTERLY" else 1

    def clamp(year, month):
        if month == 12:
            last = 31
        else:
            last = (date(year + (month // 12), (month % 12) + 1, 1) - timedelta(days=1)).day
        return date(year, month, min(day, last))

    candidate = clamp(today.year, today.month)
    if candidate < today:
        month = today.month + step
        year = today.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        candidate = clamp(year, month)
    if sip.end_date and candidate > sip.end_date:
        return None
    return candidate


def _sip_due_alerts():
    today = date.today()
    alerts = []
    for sip in Sip.query.filter_by(is_active=True).all():
        due = _next_due(sip, today)
        if due is None or due > today + timedelta(days=SIP_DUE_WINDOW_DAYS):
            continue
        days = (due - today).days
        when = "today" if days == 0 else "tomorrow" if days == 1 else f"in {days} days"
        alerts.append(
            {
                "id": f"sip-{sip.sip_id}",
                "kind": "SIP_DUE",
                "severity": "info",
                "title": f"{sip.asset.symbol} SIP due {when}",
                "body": (
                    f"₹{Decimal(sip.amount):,.2f} {sip.frequency.lower()} instalment on "
                    f"{due:%d %b}. SIPs here are simulated -- record it as a BUY when you "
                    "actually invest."
                ),
                "asset_id": sip.asset_id,
                "symbol": sip.asset.symbol,
            }
        )
    return alerts


def _milestone_alerts():
    invested = Decimal("0")
    for txn in Transaction.query.filter_by(txn_type="BUY").all():
        invested += Decimal(txn.quantity) * Decimal(txn.price)
    crossed = [m for m in MILESTONES if invested >= m]
    if not crossed:
        return []
    highest = max(crossed)
    return [
        {
            "id": f"milestone-{int(highest)}",
            "kind": "MILESTONE",
            "severity": "info",
            "title": f"You've invested over ₹{highest:,.0f}",
            "body": f"Total deployed across all BUY transactions is ₹{invested:,.2f}.",
            "asset_id": None,
            "symbol": None,
        }
    ]


def get_alerts():
    alerts = (
        _price_target_alerts() + _concentration_alerts() + _sip_due_alerts() + _milestone_alerts()
    )
    alerts.sort(key=lambda a: SEVERITY_ORDER.get(a["severity"], 9))
    return {
        "alerts": alerts,
        "count": len(alerts),
        "computed_at": date.today(),
        "note": (
            "Alerts are recomputed each time you open this panel -- they are in-app only. "
            "This app has no login or contact details, so nothing is emailed or pushed."
        ),
    }


def list_price_targets():
    return PriceTarget.query.order_by(PriceTarget.created_at.desc()).all()


def create_price_target(data):
    from models import db

    target = PriceTarget(
        asset_id=data["asset_id"],
        target_price=data["target_price"],
        direction=data.get("direction", "ABOVE"),
        note=data.get("note"),
    )
    db.session.add(target)
    db.session.commit()
    return target


def delete_price_target(target_id):
    from models import db

    target = db.session.get(PriceTarget, target_id)
    if target is None:
        return False
    db.session.delete(target)
    db.session.commit()
    return True
