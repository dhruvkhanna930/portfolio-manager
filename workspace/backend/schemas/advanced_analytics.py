"""Schemas for the §14 Advanced Analytics layer.

Risk/score figures are plain Floats rather than Decimal-as-string: they're
computed statistics (ratios, correlations), not money. Currency amounts stay
Decimal-as-string, consistent with the rest of the API.
"""

from marshmallow import Schema, fields, validate

from services.benchmark_service import BENCHMARKS
from services.risk_service import VALID_PERIODS

RISK_PERIODS = list(VALID_PERIODS)
BENCHMARK_CODES = list(BENCHMARKS.keys())


# --------------------------------------------------------------------- §14.1
class RiskQuerySchema(Schema):
    scope = fields.String(load_default="portfolio", validate=validate.OneOf(["portfolio", "asset"]))
    asset_id = fields.Integer(load_default=None)
    period = fields.String(load_default="1Y", validate=validate.OneOf(RISK_PERIODS))
    benchmark_code = fields.String(
        load_default="NIFTY50", validate=validate.OneOf(BENCHMARK_CODES)
    )
    risk_free_rate_pct = fields.Float(load_default=None)


class RiskMetricsSchema(Schema):
    scope = fields.String()
    asset_id = fields.Integer(allow_none=True)
    period = fields.String()
    benchmark_code = fields.String()
    risk_free_rate_pct = fields.Decimal(as_string=True)
    observations = fields.Integer()
    sufficient_data = fields.Boolean()

    volatility = fields.Float(allow_none=True)
    annualized_return = fields.Float(allow_none=True)
    sharpe = fields.Float(allow_none=True)
    sortino = fields.Float(allow_none=True)
    max_drawdown = fields.Float(allow_none=True)
    var_95 = fields.Float(allow_none=True)
    calmar = fields.Float(allow_none=True)
    beta = fields.Float(allow_none=True)
    tracking_error = fields.Float(allow_none=True)


# --------------------------------------------------------------------- §14.2
class CorrelationQuerySchema(Schema):
    period = fields.String(load_default="1Y", validate=validate.OneOf(RISK_PERIODS))


class CorrelationAssetSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    name = fields.String()
    observations = fields.Integer()


class CorrelationResponseSchema(Schema):
    period = fields.String()
    assets = fields.List(fields.Nested(CorrelationAssetSchema))
    matrix = fields.List(fields.List(fields.Float(allow_none=True)))
    note = fields.String()


# --------------------------------------------------------------------- §14.3
class HealthQuerySchema(Schema):
    period = fields.String(load_default="1Y", validate=validate.OneOf(RISK_PERIODS))


class HealthInsightsSchema(Schema):
    strengths = fields.List(fields.String())
    watchouts = fields.List(fields.String())
    suggestions = fields.List(fields.String())


class HealthScoreSchema(Schema):
    health_score = fields.Integer(allow_none=True)
    band = fields.String(allow_none=True)
    period = fields.String()
    insufficient_data = fields.Boolean()
    reason = fields.String()
    excluded_components = fields.List(fields.String())
    # Component shapes differ per component (each carries its own explanatory
    # fields), so this stays a raw mapping rather than a forced-uniform schema.
    components = fields.Raw()
    insights = fields.Nested(HealthInsightsSchema)
    disclaimer = fields.String()


# --------------------------------------------------------------------- §14.4
class BenchmarkQuerySchema(Schema):
    codes = fields.String(load_default="NIFTY50")
    period = fields.String(
        load_default="1Y", validate=validate.OneOf(["1M", "6M", "1Y", "3Y", "5Y", "ALL"])
    )
    fd_rate_pct = fields.Float(load_default=None)
    inflation_rate_pct = fields.Float(load_default=None)


class BenchmarkPointSchema(Schema):
    date = fields.Date()
    value = fields.Decimal(as_string=True)


class BenchmarkSeriesSchema(Schema):
    code = fields.String()
    label = fields.String()
    is_assumption = fields.Boolean()
    points = fields.List(fields.Nested(BenchmarkPointSchema))


class BenchmarkResponseSchema(Schema):
    period = fields.String()
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    fd_rate_pct = fields.Decimal(as_string=True)
    inflation_rate_pct = fields.Decimal(as_string=True)
    note = fields.String()
    series = fields.List(fields.Nested(BenchmarkSeriesSchema))


# --------------------------------------------------------------------- §14.5
class HoldingBriefSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    name = fields.String()
    profit_loss = fields.Decimal(as_string=True)
    profit_loss_pct = fields.Decimal(as_string=True)
    current_value = fields.Decimal(as_string=True)


class LongestHeldSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    name = fields.String()
    first_bought = fields.Date()
    days_held = fields.Integer()


class RealisedTradeSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    name = fields.String()
    txn_date = fields.Date()
    quantity = fields.Decimal(as_string=True)
    sell_price = fields.Decimal(as_string=True)
    cost_basis = fields.Decimal(as_string=True)
    realised_pl = fields.Decimal(as_string=True)
    value = fields.Decimal(as_string=True)


class StatisticsSchema(Schema):
    has_holdings = fields.Boolean()
    holdings_count = fields.Integer()
    priced_holdings_count = fields.Integer()
    best_performer = fields.Nested(HoldingBriefSchema, allow_none=True)
    worst_performer = fields.Nested(HoldingBriefSchema, allow_none=True)
    win_rate_pct = fields.Decimal(as_string=True, allow_none=True)
    winners_count = fields.Integer()
    losers_count = fields.Integer()
    avg_holding_period_days = fields.Integer(allow_none=True)
    longest_held = fields.Nested(LongestHeldSchema, allow_none=True)
    largest_gain = fields.Nested(RealisedTradeSchema, allow_none=True)
    largest_loss = fields.Nested(RealisedTradeSchema, allow_none=True)
    realised_trades_count = fields.Integer()
    turnover_ratio = fields.Decimal(as_string=True, allow_none=True)
    notes = fields.Raw()


# --------------------------------------------------------------------- §14.6
class MonteCarloRequestSchema(Schema):
    horizon_days = fields.Integer(load_default=252, validate=validate.Range(min=1, max=2520))
    n_simulations = fields.Integer(load_default=1000, validate=validate.Range(min=100, max=2000))
    period = fields.String(load_default="ALL", validate=validate.OneOf(RISK_PERIODS))
    seed = fields.Integer(load_default=None)


class MonteCarloBandSchema(Schema):
    day = fields.Integer()
    p10 = fields.Decimal(as_string=True)
    p50 = fields.Decimal(as_string=True)
    p90 = fields.Decimal(as_string=True)


class MonteCarloResponseSchema(Schema):
    insufficient_data = fields.Boolean()
    reason = fields.String()
    observations = fields.Integer()
    start_value = fields.Decimal(as_string=True)
    horizon_days = fields.Integer()
    n_simulations = fields.Integer()
    method = fields.String()
    bands = fields.List(fields.Nested(MonteCarloBandSchema))
    final = fields.Raw()
    probability_of_loss_pct = fields.Decimal(as_string=True)
    disclaimer = fields.String()


# --------------------------------------------------------------------- §14.7
class GoalCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    target_amount = fields.Decimal(required=True, as_string=True)
    target_date = fields.Date(load_default=None, allow_none=True)


class GoalSchema(Schema):
    goal_id = fields.Integer()
    name = fields.String()
    target_amount = fields.Decimal(as_string=True)
    target_date = fields.Date(allow_none=True)
    created_at = fields.DateTime()
    current_amount = fields.Decimal(as_string=True)
    progress_pct = fields.Decimal(as_string=True)
    remaining_amount = fields.Decimal(as_string=True)
    is_reached = fields.Boolean()
    days_remaining = fields.Integer(allow_none=True)
    required_monthly_saving = fields.Decimal(as_string=True, allow_none=True)


# --------------------------------------------------------------------- §14.8
class RebalanceRequestSchema(Schema):
    # {asset_id: weight_fraction}; validated in the service so the error message
    # can explain the fractions-vs-percentages rule.
    target_weights = fields.Dict(
        keys=fields.String(), values=fields.Float(), required=True
    )
    period = fields.String(load_default="1Y", validate=validate.OneOf(RISK_PERIODS))
    benchmark_code = fields.String(
        load_default="NIFTY50", validate=validate.OneOf(BENCHMARK_CODES)
    )


class RebalanceChangeSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    name = fields.String()
    current_value = fields.Decimal(as_string=True)
    current_weight_pct = fields.Decimal(as_string=True)
    target_value = fields.Decimal(as_string=True)
    target_weight_pct = fields.Decimal(as_string=True)
    value_change = fields.Decimal(as_string=True)


class RebalanceExclusionSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    reason = fields.String()


class RebalanceResponseSchema(Schema):
    period = fields.String()
    benchmark_code = fields.String()
    total_current = fields.Decimal(as_string=True)
    current = fields.Raw()
    hypothetical = fields.Raw()
    excluded_from_simulation = fields.List(fields.Nested(RebalanceExclusionSchema))
    changes = fields.List(fields.Nested(RebalanceChangeSchema))
    note = fields.String()
    disclaimer = fields.String()


# --------------------------------------------------------------------- §14.9
class MarketMoodSchema(Schema):
    index_name = fields.String()
    score = fields.Integer(allow_none=True)
    band = fields.String(allow_none=True)
    insufficient_data = fields.Boolean()
    reason = fields.String()
    constituents_count = fields.Integer()
    excluded_components = fields.List(fields.String())
    components = fields.Raw()
    methodology = fields.String()
    disclaimer = fields.String()
