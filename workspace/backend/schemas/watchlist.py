from marshmallow import Schema, fields

from .asset import AssetBriefSchema


class WatchlistEntrySchema(Schema):
    watchlist_id = fields.Integer(dump_only=True)
    asset_id = fields.Integer(required=True)
    added_at = fields.DateTime(dump_only=True)
    asset = fields.Nested(AssetBriefSchema, dump_only=True)


class WatchlistAddSchema(Schema):
    asset_id = fields.Integer(required=True)
