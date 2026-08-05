from models import Holding, db
from services.analytics_service import compute_holding_metrics


class HoldingNotFoundError(Exception):
    pass


def list_holdings():
    holdings = Holding.query.order_by(Holding.created_at.desc()).all()
    for row in compute_holding_metrics(holdings):
        holding = row["holding"]
        holding.current_price = row["current_price"]
        holding.invested_value = row["invested_value"]
        holding.current_value = row["current_value"]
        holding.profit_loss = row["profit_loss"]
        holding.profit_loss_pct = row["profit_loss_pct"]
        holding.day_change_value = row["day_change_value"]
        holding.weight_pct = row["weight_pct"]
        holding.is_priced = row["is_priced"]
    return holdings


def get_holding(holding_id):
    holding = db.session.get(Holding, holding_id)
    if holding is None:
        raise HoldingNotFoundError(holding_id)
    return holding


# v2: holdings are created, grown, shrunk, and removed exclusively by
# transaction_service (BUY/SELL). There are deliberately no create/update/delete
# functions here -- see CLAUDE.md §0.1 item 11.
