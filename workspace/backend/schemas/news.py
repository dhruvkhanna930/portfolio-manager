from marshmallow import Schema, fields, validate


class NewsQuerySchema(Schema):
    asset_id = fields.Integer(allow_none=True, load_default=None)
    limit = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))
    refresh = fields.Boolean(load_default=False)


class NewsSchema(Schema):
    news_id = fields.Integer(dump_only=True)
    asset_id = fields.Integer(allow_none=True)
    headline = fields.String()
    source_name = fields.String()
    url = fields.String()
    published_at = fields.DateTime()
    sentiment = fields.String(allow_none=True)
    thumbnail_url = fields.String(allow_none=True)
    fetched_at = fields.DateTime(dump_only=True)
