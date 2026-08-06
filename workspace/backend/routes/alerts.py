"""In-app alerts and the price targets that feed them (CLAUDE.md §15.5).

Alerts are computed on read, never stored -- see alert_service for why.
"""

from flask.views import MethodView
from flask_smorest import Blueprint, abort

from models import AssetMetadata, db
from schemas.visual import AlertsResponseSchema, PriceTargetCreateSchema, PriceTargetSchema
from services import alert_service

blp = Blueprint(
    "alerts",
    __name__,
    url_prefix="/api",
    description="In-app alerts (computed on read) and user-set price targets",
)


@blp.route("/alerts")
class AlertList(MethodView):
    @blp.response(200, AlertsResponseSchema)
    def get(self):
        return alert_service.get_alerts()


@blp.route("/price-targets")
class PriceTargetList(MethodView):
    @blp.response(200, PriceTargetSchema(many=True))
    def get(self):
        return alert_service.list_price_targets()

    @blp.arguments(PriceTargetCreateSchema)
    @blp.response(201, PriceTargetSchema)
    def post(self, data):
        if db.session.get(AssetMetadata, data["asset_id"]) is None:
            abort(422, message=f"asset_id {data['asset_id']} does not exist")
        return alert_service.create_price_target(data)


@blp.route("/price-targets/<int:target_id>")
class PriceTargetDetail(MethodView):
    @blp.response(204)
    def delete(self, target_id):
        if not alert_service.delete_price_target(target_id):
            abort(404, message=f"Price target {target_id} not found")
