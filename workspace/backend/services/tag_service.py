from models import Holding, Tag, db


class HoldingNotFoundError(Exception):
    pass


class TagAlreadyAssignedError(Exception):
    pass


class TagNotAssignedError(Exception):
    pass


def list_tags():
    return Tag.query.order_by(Tag.name).all()


def create_tag(name):
    name = name.strip()
    existing = Tag.query.filter_by(name=name).first()
    if existing is not None:
        return existing
    tag = Tag(name=name)
    db.session.add(tag)
    db.session.commit()
    return tag


def assign_tag_to_holding(holding_id, name):
    """Get-or-create the tag by name, then link it to the holding. Idempotent by
    design -- assigning a tag that's already on the holding is a no-op success,
    not an error, since the UI just wants "this tag is on this holding" to be
    true after the call.
    """
    holding = db.session.get(Holding, holding_id)
    if holding is None:
        raise HoldingNotFoundError(holding_id)

    tag = create_tag(name)
    if tag not in holding.tags:
        holding.tags.append(tag)
        db.session.commit()
    return holding


def remove_tag_from_holding(holding_id, tag_id):
    holding = db.session.get(Holding, holding_id)
    if holding is None:
        raise HoldingNotFoundError(holding_id)

    tag = next((t for t in holding.tags if t.tag_id == tag_id), None)
    if tag is None:
        raise TagNotAssignedError(tag_id)

    holding.tags.remove(tag)
    db.session.commit()
    return holding
