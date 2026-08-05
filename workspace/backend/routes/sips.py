from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas.sip import SipCreateSchema, SipSchema, SipUpdateSchema
from services import sip_service as svc
from services.sip_service import AssetNotFoundError, InvalidSipAssetError, SipNotFoundError

blp = Blueprint("sips", __name__, url_prefix="/api/sips", description="Simulated SIP plans")


@blp.route("")
class SipList(MethodView):
    @blp.response(200, SipSchema(many=True))
    def get(self):
        return svc.list_sips()

    @blp.arguments(SipCreateSchema)
    @blp.response(201, SipSchema)
    def post(self, new_data):
        try:
            return svc.create_sip(new_data)
        except AssetNotFoundError:
            abort(422, message=f"asset_id {new_data['asset_id']} does not exist")
        except InvalidSipAssetError as err:
            abort(422, message=f"SIPs are only supported for mutual funds, not {err.args[0]}")


@blp.route("/<int:sip_id>")
class SipDetail(MethodView):
    @blp.response(200, SipSchema)
    def get(self, sip_id):
        try:
            return svc.get_sip(sip_id)
        except SipNotFoundError:
            abort(404, message=f"SIP {sip_id} not found")

    @blp.arguments(SipUpdateSchema)
    @blp.response(200, SipSchema)
    def put(self, update_data, sip_id):
        try:
            return svc.update_sip(sip_id, update_data)
        except SipNotFoundError:
            abort(404, message=f"SIP {sip_id} not found")

    @blp.response(204)
    def delete(self, sip_id):
        try:
            svc.delete_sip(sip_id)
        except SipNotFoundError:
            abort(404, message=f"SIP {sip_id} not found")
