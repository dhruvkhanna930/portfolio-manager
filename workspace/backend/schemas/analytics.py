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
