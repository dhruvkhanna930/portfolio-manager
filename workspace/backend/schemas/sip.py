from marshmallow import Schema, fields, validate

from .asset import AssetBriefSchema


class SipSchema(Schema):
    sip_id = fields.Integer(dump_only=True)
    asset_id = fields.Integer(dump_only=True)
    amount = fields.Decimal(as_string=True, dump_only=True)
    frequency = fields.String(dump_only=True)
    start_date = fields.Date(dump_only=True)
    end_date = fields.Date(dump_only=True, allow_none=True)
    day_of_cycle = fields.Integer(dump_only=True, allow_none=True)
    is_active = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    asset = fields.Nested(AssetBriefSchema, dump_only=True)


class SipCreateSchema(Schema):
    asset_id = fields.Integer(required=True)
    amount = fields.Decimal(
        required=True, as_string=True, validate=validate.Range(min=0, min_inclusive=False)
    )
    frequency = fields.String(
        required=True, validate=validate.OneOf(["DAILY", "WEEKLY", "MONTHLY", "QUARTERLY"])
    )
    start_date = fields.Date(required=True)
    end_date = fields.Date(allow_none=True, load_default=None)
    day_of_cycle = fields.Integer(allow_none=True, load_default=None)
