from marshmallow import Schema, fields, validate

from .asset import AssetBriefSchema


class HoldingSchema(Schema):
    holding_id = fields.Integer(dump_only=True)
    asset_id = fields.Integer(required=True)
    quantity = fields.Decimal(required=True, as_string=True, validate=validate.Range(min=0))
    avg_buy_price = fields.Decimal(
        required=True, as_string=True, validate=validate.Range(min=0, min_inclusive=False)
    )
    first_bought = fields.Date(allow_none=True)
    notes = fields.String(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    asset = fields.Nested(AssetBriefSchema, dump_only=True)


class HoldingCreateSchema(Schema):
    asset_id = fields.Integer(required=True)
    quantity = fields.Decimal(required=True, as_string=True, validate=validate.Range(min=0))
    avg_buy_price = fields.Decimal(
        required=True, as_string=True, validate=validate.Range(min=0, min_inclusive=False)
    )
    first_bought = fields.Date(allow_none=True, load_default=None)
    notes = fields.String(allow_none=True, load_default=None)


class HoldingUpdateSchema(Schema):
    quantity = fields.Decimal(required=True, as_string=True, validate=validate.Range(min=0))
    avg_buy_price = fields.Decimal(
        required=True, as_string=True, validate=validate.Range(min=0, min_inclusive=False)
    )
    first_bought = fields.Date(allow_none=True, load_default=None)
    notes = fields.String(allow_none=True, load_default=None)
