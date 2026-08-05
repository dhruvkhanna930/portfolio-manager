"""Goals (CLAUDE.md §14.7).

Deliberately minimal. Progress is measured against total portfolio value, and
goals are NOT linked to specific holdings -- that's what keeps this a savings
target rather than net-worth tracking (§0.3 item 20).
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from models import Goal, db

_PAISE = Decimal("0.01")


class GoalNotFoundError(Exception):
    pass


def _money(value):
    """Round to paise. Decimal division here otherwise yields ~28 significant
    digits, which serializes into the API as an absurdly precise rupee figure.
    """
    if value is None:
        return None
    return Decimal(value).quantize(_PAISE, rounding=ROUND_HALF_UP)


def _with_progress(goal, total_current):
    target = Decimal(goal.target_amount)
    progress_pct = (total_current / target * 100) if target > 0 else Decimal("0")
    remaining = target - total_current

    days_remaining = None
    required_monthly = None
    if goal.target_date:
        days_remaining = (goal.target_date - date.today()).days
        # Only meaningful while there's still time and still a shortfall.
        if days_remaining > 0 and remaining > 0:
            months = Decimal(days_remaining) / Decimal("30.44")
            if months > 0:
                required_monthly = remaining / months

    return {
        "goal_id": goal.goal_id,
        "name": goal.name,
        "target_amount": target,
        "target_date": goal.target_date,
        "created_at": goal.created_at,
        "current_amount": _money(total_current),
        "progress_pct": progress_pct.quantize(_PAISE, rounding=ROUND_HALF_UP),
        "remaining_amount": _money(remaining if remaining > 0 else Decimal("0")),
        "is_reached": total_current >= target,
        "days_remaining": days_remaining,
        # Straight-line requirement, no assumed return -- an assumed growth rate
        # here would be an invented number (§14 rule).
        "required_monthly_saving": _money(required_monthly),
    }


def _total_current():
    from services import analytics_service

    return analytics_service.get_portfolio_summary()["total_current"]


def list_goals():
    total_current = _total_current()
    goals = Goal.query.order_by(Goal.created_at.desc()).all()
    return [_with_progress(g, total_current) for g in goals]


def get_goal(goal_id):
    goal = db.session.get(Goal, goal_id)
    if goal is None:
        raise GoalNotFoundError(goal_id)
    return _with_progress(goal, _total_current())


def create_goal(name, target_amount, target_date=None):
    goal = Goal(name=name, target_amount=Decimal(str(target_amount)), target_date=target_date)
    db.session.add(goal)
    db.session.commit()
    return _with_progress(goal, _total_current())


def delete_goal(goal_id):
    goal = db.session.get(Goal, goal_id)
    if goal is None:
        raise GoalNotFoundError(goal_id)
    db.session.delete(goal)
    db.session.commit()
