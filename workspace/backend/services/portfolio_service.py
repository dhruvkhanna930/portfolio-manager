from models import AssetMetadata, Holding, db


class HoldingNotFoundError(Exception):
    pass


class AssetNotFoundError(Exception):
    pass


def list_holdings():
    return Holding.query.order_by(Holding.created_at.desc()).all()


def get_holding(holding_id):
    holding = db.session.get(Holding, holding_id)
    if holding is None:
        raise HoldingNotFoundError(holding_id)
    return holding


def create_holding(data):
    asset = db.session.get(AssetMetadata, data["asset_id"])
    if asset is None:
        raise AssetNotFoundError(data["asset_id"])

    holding = Holding(
        asset_id=data["asset_id"],
        quantity=data["quantity"],
        avg_buy_price=data["avg_buy_price"],
        first_bought=data.get("first_bought"),
        notes=data.get("notes"),
    )
    db.session.add(holding)
    db.session.commit()
    return holding


def update_holding(holding_id, data):
    holding = get_holding(holding_id)
    holding.quantity = data["quantity"]
    holding.avg_buy_price = data["avg_buy_price"]
    holding.first_bought = data.get("first_bought")
    holding.notes = data.get("notes")
    db.session.commit()
    return holding


def delete_holding(holding_id):
    holding = get_holding(holding_id)
    db.session.delete(holding)
    db.session.commit()
