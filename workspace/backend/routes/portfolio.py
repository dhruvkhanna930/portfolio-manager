from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas.analytics import (
    AllocationQuerySchema,
    AllocationResponseSchema,
    PerformanceQuerySchema,
    PerformanceResponseSchema,
    PortfolioSummarySchema,
)
from schemas.portfolio import HoldingSchema, HoldingWithMetricsSchema
from schemas.tag import HoldingTagAssignSchema, TagSchema
from schemas.visual import SnapshotQuerySchema, SnapshotSchema, TimelineBoundsSchema
from services import analytics_service, portfolio_service as svc, snapshot_service, tag_service
from services.portfolio_service import HoldingNotFoundError
from services.tag_service import HoldingNotFoundError as TagHoldingNotFoundError, TagNotAssignedError

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


@blp.route("/performance")
class PortfolioPerformance(MethodView):
    @blp.arguments(PerformanceQuerySchema, location="query")
    @blp.response(200, PerformanceResponseSchema)
    def get(self, args):
        return analytics_service.get_portfolio_performance(period=args["period"])


@blp.route("/<int:holding_id>")
class PortfolioDetail(MethodView):
    @blp.response(200, HoldingSchema)
    def get(self, holding_id):
        try:
            return svc.get_holding(holding_id)
        except HoldingNotFoundError:
            abort(404, message=f"Holding {holding_id} not found")


@blp.route("/<int:holding_id>/tags")
class HoldingTags(MethodView):
    @blp.arguments(HoldingTagAssignSchema)
    @blp.response(200, TagSchema(many=True))
    def post(self, data, holding_id):
        """Assign a tag by name to a holding, creating the tag if it doesn't
        already exist -- one call does both (§10 tag management).
        """
        try:
            holding = tag_service.assign_tag_to_holding(holding_id, data["name"])
        except TagHoldingNotFoundError:
            abort(404, message=f"Holding {holding_id} not found")
        return holding.tags


@blp.route("/<int:holding_id>/tags/<int:tag_id>")
class HoldingTagDetail(MethodView):
    @blp.response(200, TagSchema(many=True))
    def delete(self, holding_id, tag_id):
        try:
            holding = tag_service.remove_tag_from_holding(holding_id, tag_id)
        except TagHoldingNotFoundError:
            abort(404, message=f"Holding {holding_id} not found")
        except TagNotAssignedError:
            abort(404, message=f"Tag {tag_id} is not assigned to holding {holding_id}")
        return holding.tags


@blp.route("/snapshot")
class PortfolioSnapshot(MethodView):
    @blp.arguments(SnapshotQuerySchema, location="query")
    @blp.response(200, SnapshotSchema)
    def get(self, args):
        """Portfolio state as it actually stood on a past date (§15 timeline
        scrubber) -- the same §6.8 replay, evaluated at one date and broken out
        per holding.
        """
        return snapshot_service.get_snapshot(args["on"])


@blp.route("/timeline-bounds")
class PortfolioTimelineBounds(MethodView):
    @blp.response(200, TimelineBoundsSchema)
    def get(self):
        return snapshot_service.get_timeline_bounds()
