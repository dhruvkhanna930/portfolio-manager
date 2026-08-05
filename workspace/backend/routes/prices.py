from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas.price import ManualPriceUpdateSchema, PriceSnapshotSchema, SyncResponseSchema
from services import price_service as svc
from services.price_service import AssetNotFoundError, PriceNotFoundError

blp = Blueprint("prices", __name__, url_prefix="/api/prices", description="Price sync and lookup")


@blp.route("/sync")
class PriceSync(MethodView):
    @blp.response(200, SyncResponseSchema)
    def post(self):
        return svc.sync_all_live_assets()


@blp.route("/<int:asset_id>")
class PriceDetail(MethodView):
    @blp.response(200, PriceSnapshotSchema)
    def get(self, asset_id):
        try:
            return svc.get_price(asset_id)
        except AssetNotFoundError:
            abort(404, message=f"Asset {asset_id} not found")
        except PriceNotFoundError:
            abort(404, message=f"No price data for asset {asset_id} yet")


@blp.route("/<int:asset_id>/manual")
class PriceManualUpdate(MethodView):
    @blp.arguments(ManualPriceUpdateSchema)
    @blp.response(200, PriceSnapshotSchema)
    def put(self, update_data, asset_id):
        try:
            return svc.set_manual_price(asset_id, update_data["price"])
        except AssetNotFoundError:
            abort(404, message=f"Asset {asset_id} not found")
