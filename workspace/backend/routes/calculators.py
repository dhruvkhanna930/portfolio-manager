from datetime import date

from flask import request
from flask_smorest import Blueprint, abort

from schemas.calculator import (
    HistoricalReturnsQuerySchema,
    HistoricalReturnsResultSchema,
    SipHistoricalQuerySchema,
    SipHistoricalResultSchema,
    SipProjectedQuerySchema,
    SipProjectedResultSchema,
    SipQuerySchema,
    SipResultSchema,
)
from services.analytics_service import (
    historical_returns_calc,
    sip_calc_historical,
    sip_calc_projected,
)

blp = Blueprint("calculators", "calculators", url_prefix="/api/calculators", description="Calculators")


@blp.route("/historical-returns", methods=["POST"])
@blp.arguments(HistoricalReturnsQuerySchema, location="json")
@blp.response(200, HistoricalReturnsResultSchema)
def calc_historical_returns(args):
    """Historical Returns Calculator: 'What if I had invested?'
    Given asset_id, past invest_date, and amount, computes units bought and CAGR.
    """
    try:
        result = historical_returns_calc(args["asset_id"], args["invest_date"], args["amount"])
        return result
    except ValueError as e:
        abort(400, message=str(e))
    except Exception as e:
        abort(500, message=f"calculation error: {str(e)}")


@blp.route("/sip", methods=["POST"])
@blp.arguments(SipQuerySchema, location="json")
def calc_sip(args):
    """SIP Calculator: Projected (assumed return) or Historical (real price history) mode.
    Projected mode: monthly_amount, annual_return_pct, years (+ optional step_up_pct)
    Historical mode: asset_id, monthly_amount, start_date, end_date (+ optional step_up_pct)
    """
    mode = args.get("mode")

    try:
        if mode == "projected":
            monthly_amount = args.get("monthly_amount")
            annual_return_pct = args.get("annual_return_pct")
            years = args.get("years")
            step_up_pct = args.get("step_up_pct")

            if not monthly_amount or annual_return_pct is None or not years:
                abort(400, message="projected mode requires monthly_amount, annual_return_pct, years")

            result = sip_calc_projected(
                monthly_amount=monthly_amount,
                annual_return_pct=annual_return_pct,
                years=years,
                step_up_pct=step_up_pct,
            )
            return {"data": result}, 200

        elif mode == "historical":
            asset_id = args.get("asset_id")
            monthly_amount = args.get("monthly_amount")
            start_date = args.get("start_date")
            end_date = args.get("end_date")
            step_up_pct = args.get("step_up_pct")

            if not asset_id or not monthly_amount or not start_date:
                abort(400, message="historical mode requires asset_id, monthly_amount, start_date")

            result = sip_calc_historical(
                asset_id=asset_id,
                monthly_amount=monthly_amount,
                start_date=start_date,
                end_date=end_date,
                step_up_pct=step_up_pct,
            )
            return {"data": result}, 200

        else:
            abort(400, message="mode must be 'projected' or 'historical'")

    except ValueError as e:
        abort(400, message=str(e))
    except Exception as e:
        abort(500, message=f"calculation error: {str(e)}")
