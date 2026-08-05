from flask.views import MethodView
from flask_smorest import Blueprint

from schemas.asset import AssetBriefSchema, OwnSearchQuerySchema
from services import asset_service as svc

blp = Blueprint(
    "search",
    __name__,
    url_prefix="/api/search",
    description="Search your own already-added assets (distinct from /assets/search/live)",
)


@blp.route("")
class Search(MethodView):
    @blp.arguments(OwnSearchQuerySchema, location="query")
    @blp.response(200, AssetBriefSchema(many=True))
    def get(self, args):
        return svc.search_own_assets(args["q"])
