from marshmallow import Schema, fields, validate

# Bonds are intentionally absent: there is no live search or historical price
# source for Indian retail bonds, so they stay a curated seed list (§4.1).
SEARCHABLE_ASSET_TYPES = ["STOCK", "MUTUAL_FUND"]


class AssetBriefSchema(Schema):
    asset_id = fields.Integer(dump_only=True)
    symbol = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    asset_type = fields.String(dump_only=True)
    currency = fields.String(dump_only=True)


class LiveSearchQuerySchema(Schema):
    q = fields.String(required=True, validate=validate.Length(min=1))
    type = fields.String(load_default="STOCK", validate=validate.OneOf(SEARCHABLE_ASSET_TYPES))


class LiveSearchResultSchema(Schema):
    symbol = fields.String()
    name = fields.String()
    exchange = fields.String(allow_none=True)
    asset_type = fields.String()
    source = fields.String()


class AssetResolveSchema(Schema):
    symbol = fields.String(required=True, validate=validate.Length(min=1))
    asset_type = fields.String(required=True, validate=validate.OneOf(SEARCHABLE_ASSET_TYPES))
    name = fields.String(allow_none=True, load_default=None)


class AssetResolveResponseSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    name = fields.String()
    asset_type = fields.String()
    currency = fields.String()
    created = fields.Boolean()
    history_rows_added = fields.Integer()
