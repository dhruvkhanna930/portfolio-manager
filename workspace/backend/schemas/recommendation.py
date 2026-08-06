"""Recommendation model schemas (Phase 16)."""

from marshmallow import Schema, fields, validate

from services.recommendation_service import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    VALID_MODES,
    VALID_RISK_PROFILES,
)


class RecommendationQuerySchema(Schema):
    mode = fields.Str(load_default="similar", validate=validate.OneOf(VALID_MODES))
    risk_profile = fields.Str(
        load_default="balanced", validate=validate.OneOf(VALID_RISK_PROFILES)
    )
    limit = fields.Int(load_default=DEFAULT_LIMIT, validate=validate.Range(min=1, max=MAX_LIMIT))
    use_ml = fields.Bool(load_default=True)


class ComponentScoresSchema(Schema):
    """Each component is 0-100, or null when there wasn't enough data for it."""

    fit = fields.Float(allow_none=True)
    momentum = fields.Float(allow_none=True)
    sentiment = fields.Float(allow_none=True)
    ml = fields.Float(allow_none=True)


class ReasonSchema(Schema):
    factor = fields.Str()
    direction = fields.Str()
    score = fields.Float()


class FundamentalsSchema(Schema):
    pe_ratio = fields.Float(allow_none=True)
    beta = fields.Float(allow_none=True)
    dividend_yield = fields.Float(allow_none=True)
    profit_margin = fields.Float(allow_none=True)
    return_on_equity = fields.Float(allow_none=True)
    market_cap = fields.Float(allow_none=True)


class RecommendationItemSchema(Schema):
    asset_id = fields.Int()
    symbol = fields.Str()
    name = fields.Str()
    sector = fields.Str(allow_none=True)
    final_score = fields.Float()
    components = fields.Nested(ComponentScoresSchema)
    weights_applied = fields.Dict(keys=fields.Str(), values=fields.Float())
    coverage = fields.Float()
    confidence = fields.Str()
    reasons = fields.List(fields.Nested(ReasonSchema))
    fundamentals = fields.Nested(FundamentalsSchema)
    ml_detail = fields.Dict(allow_none=True)


class ModelStatusSchema(Schema):
    trained_models_available = fields.Bool()
    gru_1day_loaded = fields.Bool()
    lstm_5day_loaded = fields.Bool()
    reason = fields.Str(allow_none=True)
    fallback = fields.Str(allow_none=True)
    runtime = fields.Str()
    model_dir = fields.Str()
    expected_input_shape = fields.List(fields.Int())
    architecture = fields.Dict()
    disclaimer = fields.Str()


class RecommendationResponseSchema(Schema):
    mode = fields.Str()
    risk_profile = fields.Str(allow_none=True)
    recommendations = fields.List(fields.Nested(RecommendationItemSchema))
    candidates_considered = fields.Int(required=False)
    holdings_compared = fields.Int(required=False)
    weights = fields.Dict(keys=fields.Str(), values=fields.Float())
    model = fields.Nested(ModelStatusSchema, allow_none=True)
    note = fields.Str(required=False)
    disclaimer = fields.Str()


class ForecastQuerySchema(Schema):
    asset_id = fields.Int(required=True)


class ForecastResponseSchema(Schema):
    asset_id = fields.Int()
    symbol = fields.Str()
    forecast = fields.Dict()
    model = fields.Nested(ModelStatusSchema)
