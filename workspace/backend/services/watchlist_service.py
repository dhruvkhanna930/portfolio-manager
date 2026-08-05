from models import AssetMetadata, Watchlist, db


class AssetNotFoundError(Exception):
    pass


class AlreadyWatchlistedError(Exception):
    pass


class WatchlistEntryNotFoundError(Exception):
    pass


def list_watchlist():
    return Watchlist.query.order_by(Watchlist.added_at.desc()).all()


def add_to_watchlist(asset_id):
    asset = db.session.get(AssetMetadata, asset_id)
    if asset is None:
        raise AssetNotFoundError(asset_id)

    existing = Watchlist.query.filter_by(asset_id=asset_id).first()
    if existing is not None:
        raise AlreadyWatchlistedError(asset_id)

    entry = Watchlist(asset_id=asset_id)
    db.session.add(entry)
    db.session.commit()
    return entry


def remove_from_watchlist(asset_id):
    entry = Watchlist.query.filter_by(asset_id=asset_id).first()
    if entry is None:
        raise WatchlistEntryNotFoundError(asset_id)
    db.session.delete(entry)
    db.session.commit()
