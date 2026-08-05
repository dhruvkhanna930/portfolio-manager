from marshmallow import Schema, fields, validate


class PortfolioSummarySchema(Schema):
    total_invested = fields.Decimal(as_string=True)
    total_current = fields.Decimal(as_string=True)
    total_pl = fields.Decimal(as_string=True)
    total_pl_pct = fields.Decimal(as_string=True)
    day_pl = fields.Decimal(as_string=True)
    holdings_count = fields.Integer()
    unrealised_pl = fields.Decimal(as_string=True)
    realised_pl = fields.Decimal(as_string=True)


class AllocationQuerySchema(Schema):
    by = fields.String(load_default="type", validate=validate.OneOf(["type", "sector", "holding"]))


class AllocationItemSchema(Schema):
    label = fields.String()
    value = fields.Decimal(as_string=True)
    pct = fields.Decimal(as_string=True)


class AllocationResponseSchema(Schema):
    by = fields.String()
    total_current = fields.Decimal(as_string=True)
    items = fields.List(fields.Nested(AllocationItemSchema))


# No "1D" here -- per CLAUDE.md §4.2 portfolio-level intraday is out of scope,
# only the per-asset chart (Phase 8) gets a live 1D view.
PERFORMANCE_PERIODS = ["1W", "1M", "6M", "1Y", "3Y", "5Y", "ALL"]


class PerformanceQuerySchema(Schema):
    period = fields.String(load_default="1Y", validate=validate.OneOf(PERFORMANCE_PERIODS))


class PerformancePointSchema(Schema):
    date = fields.Date()
    value = fields.Decimal(as_string=True)


class PerformanceResponseSchema(Schema):
    period = fields.String()
    points = fields.List(fields.Nested(PerformancePointSchema))
