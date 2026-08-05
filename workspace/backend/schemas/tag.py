from marshmallow import Schema, fields, validate


class TagSchema(Schema):
    tag_id = fields.Integer(dump_only=True)
    name = fields.String(dump_only=True)


class TagCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=50))


class HoldingTagAssignSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=50))
