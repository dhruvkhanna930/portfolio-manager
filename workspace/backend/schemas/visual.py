"""Schemas for the §15 visual layer's supporting read endpoints.

Same convention as the rest of the API: money is Decimal-as-string, computed
statistics are plain Floats.
"""

from marshmallow import Schema, fields, validate

from services.risk_service import VALID_PERIODS

RISK_PERIODS = list(VALID_PERIODS)


# ------------------------------------------------- timeline snapshot (§15 #3)
class SnapshotQuerySchema(Schema):
    on = fields.Date(required=True)


class SnapshotItemSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    name = fields.String()
    asset_type = fields.String()
    sector = fields.String()
    quantity = fields.Decimal(as_string=True)
    avg_buy_price = fields.Decimal(as_string=True)
    price = fields.Decimal(as_string=True)
    invested_value = fields.Decimal(as_string=True)
    current_value = fields.Decimal(as_string=True)
    profit_loss = fields.Decimal(as_string=True)
    profit_loss_pct = fields.Decimal(as_string=True, allow_none=True)
    weight_pct = fields.Decimal(as_string=True)


class SnapshotSectorSchema(Schema):
    label = fields.String()
    value = fields.Decimal(as_string=True)
    pct = fields.Decimal(as_string=True)


class SnapshotUnpricedSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    name = fields.String()


class SnapshotSchema(Schema):
    date = fields.Date()
    has_data = fields.Boolean()
    total_invested = fields.Decimal(as_string=True)
    total_current = fields.Decimal(as_string=True)
    total_pl = fields.Decimal(as_string=True)
    total_pl_pct = fields.Decimal(as_string=True, allow_none=True)
    holdings_count = fields.Integer()
    items = fields.List(fields.Nested(SnapshotItemSchema))
    sectors = fields.List(fields.Nested(SnapshotSectorSchema))
    unpriced = fields.List(fields.Nested(SnapshotUnpricedSchema))


class TimelineBoundsSchema(Schema):
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    has_data = fields.Boolean()


# ------------------------------------------------ risk/return scatter (§15 #2)
class RiskReturnQuerySchema(Schema):
    period = fields.String(load_default="1Y", validate=validate.OneOf(RISK_PERIODS))


class RiskReturnPointSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    name = fields.String()
    asset_type = fields.String()
    volatility = fields.Float(allow_none=True)
    annualized_return = fields.Float(allow_none=True)
    current_value = fields.Decimal(as_string=True, allow_none=True)
    weight_pct = fields.Decimal(as_string=True, allow_none=True)
    observations = fields.Integer()


class RiskReturnExcludedSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    reason = fields.String()


class RiskReturnSchema(Schema):
    period = fields.String()
    points = fields.List(fields.Nested(RiskReturnPointSchema))
    excluded = fields.List(fields.Nested(RiskReturnExcludedSchema))
    note = fields.String()


# ------------------------------------------------------ peer ranking (§15 #4)
class PeerRankQuerySchema(Schema):
    period = fields.String(load_default="1Y", validate=validate.OneOf(RISK_PERIODS))


class PeerRowSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    name = fields.String()
    return_pct = fields.Float()
    observations = fields.Integer()
    rank = fields.Integer()
    is_current = fields.Boolean()


class PeerRankSchema(Schema):
    asset_id = fields.Integer()
    period = fields.String()
    rank = fields.Integer(allow_none=True)
    total = fields.Integer()
    peers = fields.List(fields.Nested(PeerRowSchema))
    comparison_basis = fields.String()
    scope_note = fields.String()
    reason = fields.String()


# ----------------------------------------------------------- alerts (§15 #7)
class AlertSchema(Schema):
    id = fields.String()
    kind = fields.String()
    severity = fields.String()
    title = fields.String()
    body = fields.String()
    asset_id = fields.Integer(allow_none=True)
    symbol = fields.String(allow_none=True)


class AlertsResponseSchema(Schema):
    alerts = fields.List(fields.Nested(AlertSchema))
    count = fields.Integer()
    computed_at = fields.Date()
    note = fields.String()


class PriceTargetSchema(Schema):
    target_id = fields.Integer(dump_only=True)
    asset_id = fields.Integer()
    target_price = fields.Decimal(as_string=True)
    direction = fields.String()
    note = fields.String(allow_none=True)
    created_at = fields.DateTime(dump_only=True)


class PriceTargetCreateSchema(Schema):
    asset_id = fields.Integer(required=True)
    target_price = fields.Decimal(required=True, validate=validate.Range(min=0, min_inclusive=False))
    direction = fields.String(load_default="ABOVE", validate=validate.OneOf(["ABOVE", "BELOW"]))
    note = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=255))
