"""AI Suggestions endpoints (Phase 17).

POST rather than GET for the review: it spends a rate-limited external API call,
so it should be an explicit action the user takes, not something React Query can
refetch on window focus.
"""

from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas.ai import AIReviewQuerySchema, AIReviewResponseSchema, AIStatusSchema
from services import ai_insight_service
from services.ai_insight_service import AIUnavailable

blp = Blueprint(
    "ai",
    __name__,
    url_prefix="/api/ai",
    description="LLM commentary generated from the portfolio's own computed figures",
)


@blp.route("/status")
class AIStatus(MethodView):
    @blp.response(200, AIStatusSchema)
    def get(self):
        """Whether the model is configured, so the UI can say so before you click."""
        return ai_insight_service.status()


@blp.route("/portfolio-review")
class AIPortfolioReview(MethodView):
    @blp.arguments(AIReviewQuerySchema, location="query")
    @blp.response(200, AIReviewResponseSchema)
    def post(self, args):
        """Generate a plain-English review of the portfolio.

        The model receives only the fact sheet in `facts` and does no arithmetic
        of its own; that same fact sheet comes back in the response so every
        claim is checkable.
        """
        try:
            return ai_insight_service.get_review(
                period=args["period"], force=args["force"]
            )
        except AIUnavailable as exc:
            abort(503, message=str(exc))


@blp.route("/facts")
class AIFacts(MethodView):
    @blp.arguments(AIReviewQuerySchema, location="query")
    @blp.response(200)
    def get(self, args):
        """The fact sheet on its own -- no model call, no quota spent."""
        return ai_insight_service.build_facts(period=args["period"])
