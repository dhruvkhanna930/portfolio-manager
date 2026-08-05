from marshmallow import Schema, fields, validate


class PriceSnapshotSchema(Schema):
    asset_id = fields.Integer(dump_only=True)
    price = fields.Decimal(as_string=True, dump_only=True)
    prev_close = fields.Decimal(as_string=True, dump_only=True, allow_none=True)
    day_change = fields.Decimal(as_string=True, dump_only=True, allow_none=True)
    day_change_pct = fields.Decimal(as_string=True, dump_only=True, allow_none=True)
    is_stale = fields.Boolean(dump_only=True)
    as_of = fields.DateTime(dump_only=True)


class ManualPriceUpdateSchema(Schema):
    price = fields.Decimal(required=True, as_string=True, validate=validate.Range(min=0, min_inclusive=False))


class SyncResultSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    status = fields.String()
    price = fields.String(allow_none=True)
    as_of = fields.String(allow_none=True)
    is_stale = fields.Boolean(load_default=False)
    message = fields.String(allow_none=True)


class SyncSummarySchema(Schema):
    total = fields.Integer()
    updated = fields.Integer()
    stale = fields.Integer()
    failed = fields.Integer()


class SyncResponseSchema(Schema):
    summary = fields.Nested(SyncSummarySchema)
    results = fields.List(fields.Nested(SyncResultSchema))
