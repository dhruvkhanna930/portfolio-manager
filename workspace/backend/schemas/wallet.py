from marshmallow import Schema, fields, validate


class WalletEntrySchema(Schema):
    ledger_id = fields.Integer(dump_only=True)
    entry_type = fields.String(dump_only=True)
    amount = fields.Decimal(as_string=True, dump_only=True)
    transaction_id = fields.Integer(dump_only=True, allow_none=True)
    note = fields.String(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True)


class WalletSchema(Schema):
    balance = fields.Decimal(as_string=True, dump_only=True)
    entries = fields.List(fields.Nested(WalletEntrySchema), dump_only=True)


class WalletMutationSchema(Schema):
    amount = fields.Decimal(
        required=True, as_string=True, validate=validate.Range(min=0, min_inclusive=False)
    )
    note = fields.String(allow_none=True, load_default=None)
