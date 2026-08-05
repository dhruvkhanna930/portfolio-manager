"""Advanced analytics endpoints (CLAUDE.md §14.10).

Additive and read-only (except goals), per §13's guardrail that this layer must
not refactor earlier phases' contracts.
"""

from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas.advanced_analytics import (
    BenchmarkQuerySchema,
    BenchmarkResponseSchema,
    CorrelationQuerySchema,
    CorrelationResponseSchema,
    HealthQuerySchema,
    HealthScoreSchema,
    MonteCarloRequestSchema,
    MonteCarloResponseSchema,
    RebalanceRequestSchema,
    RebalanceResponseSchema,
    RiskMetricsSchema,
    RiskQuerySchema,
    StatisticsSchema,
)
from schemas.visual import RiskReturnQuerySchema, RiskReturnSchema
from services import (
    benchmark_service,
    health_service,
    montecarlo_service,
    rebalance_service,
    risk_service,
    statistics_service,
)
from services.rebalance_service import InvalidWeightsError

blp = Blueprint(
    "analytics",
    __name__,
    url_prefix="/api/analytics",
    description="Advanced analytics: risk, correlation, health score, benchmarks, projections",
)


@blp.route("/risk")
class Risk(MethodView):
    @blp.arguments(RiskQuerySchema, location="query")
    @blp.response(200, RiskMetricsSchema)
    def get(self, args):
        """§14.1 risk metrics, for the whole portfolio or a single asset."""
        if args["scope"] == "asset":
            if not args.get("asset_id"):
                abort(422, message="asset_id is required when scope=asset")
            return risk_service.get_asset_risk(
                args["asset_id"],
                period=args["period"],
                benchmark_code=args["benchmark_code"],
                risk_free_rate_pct=args.get("risk_free_rate_pct"),
            )
        return risk_service.get_portfolio_risk(
            period=args["period"],
            benchmark_code=args["benchmark_code"],
            risk_free_rate_pct=args.get("risk_free_rate_pct"),
        )


@blp.route("/correlation")
class Correlation(MethodView):
    @blp.arguments(CorrelationQuerySchema, location="query")
    @blp.response(200, CorrelationResponseSchema)
    def get(self, args):
        """§14.2 pairwise correlation across current holdings."""
        return risk_service.get_correlation_matrix(period=args["period"])


@blp.route("/health-score")
class HealthScore(MethodView):
    @blp.arguments(HealthQuerySchema, location="query")
    @blp.response(200, HealthScoreSchema)
    def get(self, args):
        """§14.3 Portfolio Health Score -- replaces the old insights panel."""
        return health_service.get_health_score(period=args["period"])


@blp.route("/benchmark")
class Benchmark(MethodView):
    @blp.arguments(BenchmarkQuerySchema, location="query")
    @blp.response(200, BenchmarkResponseSchema)
    def get(self, args):
        """§14.4 portfolio vs. indices, plus labelled FD/inflation assumptions."""
        codes = [c.strip().upper() for c in args["codes"].split(",") if c.strip()]
        return benchmark_service.compare(
            codes=codes,
            period=args["period"],
            fd_rate_pct=args.get("fd_rate_pct"),
            inflation_rate_pct=args.get("inflation_rate_pct"),
        )


@blp.route("/statistics")
class Statistics(MethodView):
    @blp.response(200, StatisticsSchema)
    def get(self):
        """§14.5 portfolio statistics."""
        return statistics_service.get_statistics()


@blp.route("/monte-carlo")
class MonteCarlo(MethodView):
    @blp.arguments(MonteCarloRequestSchema)
    @blp.response(200, MonteCarloResponseSchema)
    def post(self, data):
        """§14.6 bootstrap projection. POST because it takes a body, not because
        it writes anything -- nothing here is stored.
        """
        return montecarlo_service.run_projection(
            horizon_days=data["horizon_days"],
            n_simulations=data["n_simulations"],
            period=data["period"],
            seed=data.get("seed"),
        )


@blp.route("/rebalance-preview")
class RebalancePreview(MethodView):
    @blp.arguments(RebalanceRequestSchema)
    @blp.response(200, RebalanceResponseSchema)
    def post(self, data):
        """§14.8 what-if reweighting. Never persisted, never places a trade."""
        try:
            return rebalance_service.preview(
                data["target_weights"],
                period=data["period"],
                benchmark_code=data["benchmark_code"],
            )
        except InvalidWeightsError as e:
            abort(422, message=str(e))


@blp.route("/risk-return")
class RiskReturnScatter(MethodView):
    @blp.arguments(RiskReturnQuerySchema, location="query")
    @blp.response(200, RiskReturnSchema)
    def get(self, args):
        """Per-holding volatility, return and position size in one pass, for
        §15.2's bubble scatter. Convenience shape over metrics §14.1 already
        defines -- no new statistics.
        """
        return risk_service.get_risk_return_scatter(period=args["period"])
