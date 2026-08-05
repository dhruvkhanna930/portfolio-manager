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


class HoldingWithMetricsSchema(HoldingSchema):
    current_price = fields.Decimal(as_string=True, dump_only=True, allow_none=True)
    invested_value = fields.Decimal(as_string=True, dump_only=True)
    current_value = fields.Decimal(as_string=True, dump_only=True)
    profit_loss = fields.Decimal(as_string=True, dump_only=True)
    profit_loss_pct = fields.Decimal(as_string=True, dump_only=True)
    day_change_value = fields.Decimal(as_string=True, dump_only=True)
    weight_pct = fields.Decimal(as_string=True, dump_only=True)
    is_priced = fields.Boolean(dump_only=True)


# v2: HoldingCreateSchema / HoldingUpdateSchema removed along with
# POST/PUT /api/portfolio -- holdings are derived from transactions (§0.1 item 11).
