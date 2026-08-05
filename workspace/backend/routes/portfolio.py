from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas.analytics import AllocationQuerySchema, AllocationResponseSchema, PortfolioSummarySchema
from schemas.portfolio import HoldingSchema, HoldingWithMetricsSchema
from services import analytics_service, portfolio_service as svc
from services.portfolio_service import HoldingNotFoundError

blp = Blueprint(
    "portfolio",
    __name__,
    url_prefix="/api/portfolio",
    description="Holdings (read-only -- derived from transactions)",
)


# v2: holdings are a derived cache of transactions, never directly written. There
# is deliberately no POST/PUT/DELETE here -- use /api/transactions instead (§7).
@blp.route("")
class PortfolioList(MethodView):
    @blp.response(200, HoldingWithMetricsSchema(many=True))
    def get(self):
        return svc.list_holdings()


@blp.route("/summary")
class PortfolioSummary(MethodView):
    @blp.response(200, PortfolioSummarySchema)
    def get(self):
        return analytics_service.get_portfolio_summary()


@blp.route("/allocation")
class PortfolioAllocation(MethodView):
    @blp.arguments(AllocationQuerySchema, location="query")
    @blp.response(200, AllocationResponseSchema)
    def get(self, args):
        return analytics_service.get_allocation(by=args["by"])


@blp.route("/<int:holding_id>")
class PortfolioDetail(MethodView):
    @blp.response(200, HoldingSchema)
    def get(self, holding_id):
        try:
            return svc.get_holding(holding_id)
        except HoldingNotFoundError:
            abort(404, message=f"Holding {holding_id} not found")
