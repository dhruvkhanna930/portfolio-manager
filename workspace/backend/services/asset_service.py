from models import AssetMetadata


def list_assets():
    return AssetMetadata.query.order_by(AssetMetadata.name).all()
