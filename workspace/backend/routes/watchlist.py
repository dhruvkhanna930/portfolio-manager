from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas.watchlist import WatchlistAddSchema, WatchlistEntrySchema
from services import watchlist_service as svc

blp = Blueprint("watchlist", __name__, url_prefix="/api/watchlist", description="Bookmarked assets")


@blp.route("")
class WatchlistList(MethodView):
    @blp.response(200, WatchlistEntrySchema(many=True))
    def get(self):
        return svc.list_watchlist()

    @blp.arguments(WatchlistAddSchema)
    @blp.response(201, WatchlistEntrySchema)
    def post(self, data):
        try:
            return svc.add_to_watchlist(data["asset_id"])
        except svc.AssetNotFoundError:
            abort(404, message=f"Asset {data['asset_id']} not found")
        except svc.AlreadyWatchlistedError:
            abort(422, message="This asset is already on your watchlist")


@blp.route("/<int:asset_id>")
class WatchlistDetail(MethodView):
    @blp.response(204)
    def delete(self, asset_id):
        try:
            svc.remove_from_watchlist(asset_id)
        except svc.WatchlistEntryNotFoundError:
            abort(404, message=f"Asset {asset_id} is not on your watchlist")
