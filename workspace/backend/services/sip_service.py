from decimal import Decimal

from models import AssetMetadata, Sip, db


class AssetNotFoundError(Exception):
    pass


class InvalidSipAssetError(Exception):
    pass


class SipNotFoundError(Exception):
    pass


def list_sips():
    return Sip.query.order_by(Sip.created_at.desc()).all()


def get_sip(sip_id):
    sip = db.session.get(Sip, sip_id)
    if sip is None:
        raise SipNotFoundError(sip_id)
    return sip


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


def update_sip(sip_id, data):
    """Update a SIP plan's mutable fields. Since SIPs are simulated (no auto-debit,
    no transaction history tied to real executions), amount/frequency/end_date and
    the is_active flag (pause/resume) are all safely editable in place -- there's
    no ledger to reconcile.
    """
    sip = db.session.get(Sip, sip_id)
    if sip is None:
        raise SipNotFoundError(sip_id)

    if "amount" in data:
        sip.amount = Decimal(data["amount"])
    if "frequency" in data:
        sip.frequency = data["frequency"]
    if "end_date" in data:
        sip.end_date = data["end_date"]
    if "day_of_cycle" in data:
        sip.day_of_cycle = data["day_of_cycle"]
    if "is_active" in data:
        sip.is_active = data["is_active"]

    db.session.commit()
    return sip


def delete_sip(sip_id):
    sip = db.session.get(Sip, sip_id)
    if sip is None:
        raise SipNotFoundError(sip_id)
    db.session.delete(sip)
    db.session.commit()
