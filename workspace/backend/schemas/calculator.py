from marshmallow import Schema, fields, validate


class HistoricalReturnsQuerySchema(Schema):
    asset_id = fields.Int(required=True)
    invest_date = fields.Date(required=True)
    amount = fields.Decimal(required=True, places=2)


class HistoricalReturnsResultSchema(Schema):
    invested_amount = fields.Decimal()
    invest_date = fields.Date()
    invest_price = fields.Decimal()
    units_bought = fields.Decimal()
    current_price = fields.Decimal()
    current_date = fields.Date()
    current_value = fields.Decimal()
    absolute_return = fields.Decimal()
    absolute_return_pct = fields.Decimal()
    years_held = fields.Decimal()
    cagr_pct = fields.Decimal()


class SipProjectedQuerySchema(Schema):
    mode = fields.Str(required=True, validate=validate.OneOf(["projected"]))
    monthly_amount = fields.Decimal(required=True, places=2)
    annual_return_pct = fields.Decimal(required=True, places=2)
    years = fields.Decimal(required=True, places=2)
    step_up_pct = fields.Decimal(places=2, allow_none=True)


class SipProjectedResultSchema(Schema):
    mode = fields.Str()
    monthly_amount = fields.Decimal()
    step_up_pct = fields.Decimal()
    annual_return_pct = fields.Decimal()
    years = fields.Decimal()
    months = fields.Int()
    total_invested = fields.Decimal()
    final_value = fields.Decimal()
    total_return = fields.Decimal()
    total_return_pct = fields.Decimal()


class SipHistoricalQuerySchema(Schema):
    mode = fields.Str(required=True, validate=validate.OneOf(["historical"]))
    asset_id = fields.Int(required=True)
    monthly_amount = fields.Decimal(required=True, places=2)
    start_date = fields.Date(required=True)
    end_date = fields.Date(allow_none=True)
    step_up_pct = fields.Decimal(places=2, allow_none=True)


class SipHistoricalResultSchema(Schema):
    mode = fields.Str()
    asset_id = fields.Int()
    monthly_amount = fields.Decimal()
    step_up_pct = fields.Decimal()
    start_date = fields.Date()
    end_date = fields.Date()
    total_invested = fields.Decimal()
    total_units = fields.Decimal()
    current_price = fields.Decimal()
    current_date = fields.Date()
    current_value = fields.Decimal()
    total_return = fields.Decimal()
    total_return_pct = fields.Decimal()
    xirr_pct = fields.Decimal(allow_none=True)


class SipQuerySchema(Schema):
    mode = fields.Str(required=True, validate=validate.OneOf(["projected", "historical"]))
    monthly_amount = fields.Decimal(required=True, places=2)
    annual_return_pct = fields.Decimal(places=2, allow_none=True)
    years = fields.Decimal(places=2, allow_none=True)
    asset_id = fields.Int(allow_none=True)
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    step_up_pct = fields.Decimal(places=2, allow_none=True)


class SipResultSchema(Schema):
    mode = fields.Str()
    monthly_amount = fields.Decimal()
    step_up_pct = fields.Decimal()
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    total_invested = fields.Decimal()
    final_value = fields.Decimal(allow_none=True)
    current_value = fields.Decimal(allow_none=True)
    total_units = fields.Decimal(allow_none=True)
    total_return = fields.Decimal()
    total_return_pct = fields.Decimal()
    xirr_pct = fields.Decimal(allow_none=True)
    years = fields.Decimal(allow_none=True)
    months = fields.Int(allow_none=True)
