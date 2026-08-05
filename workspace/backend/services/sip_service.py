from decimal import Decimal

from models import AssetMetadata, Sip, db


class AssetNotFoundError(Exception):
    pass


class InvalidSipAssetError(Exception):
    pass


def list_sips():
    return Sip.query.order_by(Sip.created_at.desc()).all()


def create_sip(data):
    """Create a simulated SIP plan. No wallet debit and no transaction row --
    SIPs are not executed, they're a plan plus a projection (§5.2). Full
    list/management UI lands in Phase 10.
    """
    asset = db.session.get(AssetMetadata, data["asset_id"])
    if asset is None:
        raise AssetNotFoundError(data["asset_id"])
    if asset.asset_type != "MUTUAL_FUND":
        raise InvalidSipAssetError(asset.asset_type)

    sip = Sip(
        asset_id=asset.asset_id,
        amount=Decimal(data["amount"]),
        frequency=data["frequency"],
        start_date=data["start_date"],
        end_date=data.get("end_date"),
        day_of_cycle=data.get("day_of_cycle"),
        is_active=True,
    )
    db.session.add(sip)
    db.session.commit()
    return sip
