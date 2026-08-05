from flask.views import MethodView
from flask_smorest import Blueprint

from schemas.asset import AssetBriefSchema
from services import asset_service as svc

blp = Blueprint("assets", __name__, url_prefix="/api/assets", description="Asset reference data")


@blp.route("")
class AssetList(MethodView):
    @blp.response(200, AssetBriefSchema(many=True))
    def get(self):
        return svc.list_assets()
