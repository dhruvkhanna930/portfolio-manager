"""AI Suggestions schemas (Phase 17)."""

from marshmallow import Schema, fields, validate


class AIReviewQuerySchema(Schema):
    period = fields.Str(
        load_default="1Y",
        validate=validate.OneOf(["1M", "6M", "1Y", "3Y", "5Y", "ALL"]),
    )
    # The free tier is rate-limited and the result is cached against a hash of
    # the portfolio's numbers, so regenerating is opt-in rather than automatic.
    force = fields.Bool(load_default=False)


class AIObservationSchema(Schema):
    title = fields.Str()
    body = fields.Str()
    sentiment = fields.Str()


class AIReviewBodySchema(Schema):
    headline = fields.Str()
    summary = fields.Str()
    observations = fields.List(fields.Nested(AIObservationSchema))
    questions_to_consider = fields.List(fields.Str())
    blind_spots = fields.List(fields.Str())


class AIUsageSchema(Schema):
    model = fields.Str()
    prompt_tokens = fields.Int(allow_none=True)
    completion_tokens = fields.Int(allow_none=True)
    total_tokens = fields.Int(allow_none=True)
    response_seconds = fields.Float(allow_none=True)


class AIReviewResponseSchema(Schema):
    available = fields.Bool()
    reason = fields.Str(required=False, allow_none=True)
    cached = fields.Bool(required=False)
    cache_age_seconds = fields.Int(required=False)
    generated_at = fields.Str(required=False)
    review = fields.Nested(AIReviewBodySchema, required=False)
    # The fact sheet the model was given, returned so the UI can show what every
    # sentence was grounded on rather than asking the reader to trust it.
    facts = fields.Dict()
    usage = fields.Nested(AIUsageSchema, required=False)
    unverified_figures = fields.List(fields.Str(), required=False)
    grounding_note = fields.Str(required=False)
    disclaimer = fields.Str()


class AIStatusSchema(Schema):
    configured = fields.Bool()
    model = fields.Str()
    provider = fields.Str()
    reason = fields.Str(allow_none=True)
    cache_ttl_seconds = fields.Int()
    disclaimer = fields.Str()
