from marshmallow import Schema, fields, validate


class MoversQuerySchema(Schema):
    scope = fields.String(load_default="portfolio", validate=validate.OneOf(["portfolio", "index"]))
    limit = fields.Integer(load_default=5, validate=validate.Range(min=1, max=20))


class MoverItemSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    name = fields.String()
    price = fields.Decimal(as_string=True, allow_none=True)
    day_change = fields.Decimal(as_string=True, allow_none=True)
    day_change_pct = fields.Decimal(as_string=True, allow_none=True)


class MoversResponseSchema(Schema):
    scope = fields.String()
    gainers = fields.List(fields.Nested(MoverItemSchema))
    losers = fields.List(fields.Nested(MoverItemSchema))
