from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas.portfolio import HoldingCreateSchema, HoldingSchema, HoldingUpdateSchema
from services import portfolio_service as svc
from services.portfolio_service import AssetNotFoundError, HoldingNotFoundError

blp = Blueprint("portfolio", __name__, url_prefix="/api/portfolio", description="Holdings CRUD")


@blp.route("")
class PortfolioList(MethodView):
    @blp.response(200, HoldingSchema(many=True))
    def get(self):
        return svc.list_holdings()

    @blp.arguments(HoldingCreateSchema)
    @blp.response(201, HoldingSchema)
    def post(self, new_data):
        try:
            return svc.create_holding(new_data)
        except AssetNotFoundError:
            abort(422, message=f"asset_id {new_data['asset_id']} does not exist")


@blp.route("/<int:holding_id>")
class PortfolioDetail(MethodView):
    @blp.response(200, HoldingSchema)
    def get(self, holding_id):
        try:
            return svc.get_holding(holding_id)
        except HoldingNotFoundError:
            abort(404, message=f"Holding {holding_id} not found")

    @blp.arguments(HoldingUpdateSchema)
    @blp.response(200, HoldingSchema)
    def put(self, update_data, holding_id):
        try:
            return svc.update_holding(holding_id, update_data)
        except HoldingNotFoundError:
            abort(404, message=f"Holding {holding_id} not found")

    @blp.response(204)
    def delete(self, holding_id):
        try:
            svc.delete_holding(holding_id)
        except HoldingNotFoundError:
            abort(404, message=f"Holding {holding_id} not found")
