from flask.views import MethodView
from flask_smorest import Blueprint

from schemas.news import NewsQuerySchema, NewsSchema
from services import news_service as svc

blp = Blueprint("news", __name__, url_prefix="/api/news", description="News feed")


@blp.route("")
class NewsFeed(MethodView):
    @blp.arguments(NewsQuerySchema, location="query")
    @blp.response(200, NewsSchema(many=True))
    def get(self, args):
        """Get news: no asset_id = general market, asset_id = asset-filtered news."""
        asset_id = args.get("asset_id")
        limit = args.get("limit", 20)
        refresh = args.get("refresh", False)

        if asset_id:
            return svc.fetch_asset_news(asset_id, limit=limit, force_refresh=refresh)
        else:
            return svc.fetch_general_news(limit=limit, force_refresh=refresh)
