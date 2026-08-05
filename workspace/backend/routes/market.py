from flask.views import MethodView
from flask_smorest import Blueprint

from schemas.market import MoversQuerySchema, MoversResponseSchema
from services import market_service as svc

blp = Blueprint("market", __name__, url_prefix="/api/market", description="Market-wide data")


@blp.route("/movers")
class MarketMovers(MethodView):
    @blp.arguments(MoversQuerySchema, location="query")
    @blp.response(200, MoversResponseSchema)
    def get(self, args):
        limit = args["limit"]
        if args["scope"] == "portfolio":
            return svc.get_portfolio_movers(limit=limit)
        return svc.get_index_movers(limit=limit)
