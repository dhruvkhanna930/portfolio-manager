from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas.asset import (
    AssetBriefSchema,
    AssetDetailSchema,
    AssetResolveResponseSchema,
    AssetResolveSchema,
    LiveSearchQuerySchema,
    LiveSearchResultSchema,
    SimilarAssetSchema,
)
from services import asset_search_service, asset_service as svc

blp = Blueprint("assets", __name__, url_prefix="/api/assets", description="Asset reference data")


@blp.route("")
class AssetList(MethodView):
    @blp.response(200, AssetBriefSchema(many=True))
    def get(self):
        return svc.list_assets()


@blp.route("/search/live")
class AssetLiveSearch(MethodView):
    @blp.arguments(LiveSearchQuerySchema, location="query")
    @blp.response(200, LiveSearchResultSchema(many=True))
    def get(self, args):
        try:
            return asset_search_service.search_live(args["q"], args["type"])
        except asset_search_service.UnsupportedAssetTypeError:
            abort(
                422,
                message=(
                    "Bonds are not searchable -- no live search API exists for Indian "
                    "retail bonds, so they stay a curated list. Use STOCK or MUTUAL_FUND."
                ),
            )
        except Exception:
            abort(503, message="Asset search is temporarily unavailable, please retry")


@blp.route("/resolve")
class AssetResolve(MethodView):
    @blp.arguments(AssetResolveSchema)
    @blp.response(200, AssetResolveResponseSchema)
    def post(self, data):
        try:
            asset, created, history_rows = svc.resolve_asset(
                data["symbol"], data["asset_type"], data.get("name")
            )
        except svc.UnsupportedAssetTypeError:
            abort(
                422,
                message=(
                    "Bonds cannot be resolved from search -- they are a curated list "
                    "with no live price or history source."
                ),
            )
        return {
            "asset_id": asset.asset_id,
            "symbol": asset.symbol,
            "name": asset.name,
            "asset_type": asset.asset_type,
            "currency": asset.currency,
            "created": created,
            "history_rows_added": history_rows,
        }


@blp.route("/<int:asset_id>")
class AssetDetail(MethodView):
    @blp.response(200, AssetDetailSchema)
    def get(self, asset_id):
        try:
            return svc.get_asset_detail(asset_id)
        except svc.AssetNotFoundError:
            abort(404, message=f"Asset {asset_id} not found")


@blp.route("/<int:asset_id>/similar")
class AssetSimilar(MethodView):
    @blp.response(200, SimilarAssetSchema(many=True))
    def get(self, asset_id):
        try:
            return svc.get_similar_assets(asset_id)
        except svc.AssetNotFoundError:
            abort(404, message=f"Asset {asset_id} not found")
