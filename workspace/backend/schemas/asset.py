from marshmallow import Schema, fields


class AssetBriefSchema(Schema):
    asset_id = fields.Integer(dump_only=True)
    symbol = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    asset_type = fields.String(dump_only=True)
    currency = fields.String(dump_only=True)
