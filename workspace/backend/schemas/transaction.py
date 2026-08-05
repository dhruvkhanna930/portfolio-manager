from marshmallow import Schema, fields, validate

from .asset import AssetBriefSchema


class TransactionSchema(Schema):
    transaction_id = fields.Integer(dump_only=True)
    asset_id = fields.Integer(dump_only=True)
    holding_id = fields.Integer(dump_only=True, allow_none=True)
    sip_id = fields.Integer(dump_only=True, allow_none=True)
    txn_type = fields.String(dump_only=True)
    quantity = fields.Decimal(as_string=True, dump_only=True)
    price = fields.Decimal(as_string=True, dump_only=True)
    fees = fields.Decimal(as_string=True, dump_only=True, allow_none=True)
    txn_date = fields.Date(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    asset = fields.Nested(AssetBriefSchema, dump_only=True)


class TransactionCreateSchema(Schema):
    asset_id = fields.Integer(required=True)
    txn_type = fields.String(required=True, validate=validate.OneOf(["BUY", "SELL", "DIVIDEND"]))
    quantity = fields.Decimal(
        required=True, as_string=True, validate=validate.Range(min=0, min_inclusive=False)
    )
    price = fields.Decimal(
        required=True, as_string=True, validate=validate.Range(min=0, min_inclusive=False)
    )
    fees = fields.Decimal(as_string=True, load_default=0, validate=validate.Range(min=0))
    txn_date = fields.Date(required=True)


class TransactionCreateResponseSchema(Schema):
    transaction = fields.Nested(TransactionSchema)
    realised_pl = fields.Decimal(as_string=True, allow_none=True)
    wallet_balance = fields.Decimal(as_string=True)
