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


class OwnSearchQuerySchema(Schema):
    q = fields.String(required=True, validate=validate.Length(min=1))


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


class AssetDetailSchema(Schema):
    """Which fields are populated depends on asset_type (§4) -- the rest come
    back as null. Frontend renders only the subset relevant to what it got.
    """

    asset_id = fields.Integer()
    symbol = fields.String()
    name = fields.String()
    asset_type = fields.String()
    currency = fields.String()
    logo_url = fields.String(allow_none=True)
    last_synced_at = fields.DateTime(allow_none=True)

    current_price = fields.Decimal(as_string=True, allow_none=True)
    prev_close = fields.Decimal(as_string=True, allow_none=True)
    day_change = fields.Decimal(as_string=True, allow_none=True)
    day_change_pct = fields.Decimal(as_string=True, allow_none=True)
    is_stale = fields.Boolean(allow_none=True)
    as_of = fields.DateTime(allow_none=True)

    # STOCK
    exchange = fields.String(allow_none=True)
    sector = fields.String(allow_none=True)
    industry = fields.String(allow_none=True)
    country = fields.String(allow_none=True)
    market_cap = fields.Number(allow_none=True)
    pe_ratio = fields.Number(allow_none=True)
    week52_high = fields.Number(allow_none=True)
    week52_low = fields.Number(allow_none=True)
    description = fields.String(allow_none=True)

    # MUTUAL_FUND
    fund_house = fields.String(allow_none=True)
    category = fields.String(allow_none=True)
    sub_category = fields.String(allow_none=True)
    plan_type = fields.String(allow_none=True)
    option_type = fields.String(allow_none=True)
    expense_ratio = fields.Decimal(as_string=True, allow_none=True)
    aum = fields.Decimal(as_string=True, allow_none=True)
    risk_level = fields.String(allow_none=True)
    benchmark = fields.String(allow_none=True)

    # BOND
    issuer = fields.String(allow_none=True)
    coupon_rate = fields.Decimal(as_string=True, allow_none=True)
    face_value = fields.Decimal(as_string=True, allow_none=True)
    maturity_date = fields.Date(allow_none=True)
    credit_rating = fields.String(allow_none=True)
    payment_frequency = fields.String(allow_none=True)
    current_yield = fields.Decimal(as_string=True, allow_none=True)

    is_held = fields.Boolean()
    is_watchlisted = fields.Boolean()


class SimilarAssetSchema(Schema):
    asset_id = fields.Integer()
    symbol = fields.String()
    name = fields.String()
    asset_type = fields.String()
    currency = fields.String()
