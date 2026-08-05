from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas.wallet import WalletMutationSchema, WalletSchema
from services import wallet_service as svc
from services.wallet_service import InsufficientFundsError

blp = Blueprint("wallet", __name__, url_prefix="/api/wallet", description="Simulated cash wallet")


@blp.route("")
class WalletDetail(MethodView):
    @blp.response(200, WalletSchema)
    def get(self):
        return svc.get_wallet()


@blp.route("/deposit")
class WalletDeposit(MethodView):
    @blp.arguments(WalletMutationSchema)
    @blp.response(200, WalletSchema)
    def post(self, data):
        svc.deposit(data["amount"], note=data.get("note"))
        return svc.get_wallet()


@blp.route("/withdraw")
class WalletWithdraw(MethodView):
    @blp.arguments(WalletMutationSchema)
    @blp.response(200, WalletSchema)
    def post(self, data):
        try:
            svc.withdraw(data["amount"], note=data.get("note"))
        except InsufficientFundsError as err:
            abort(
                422,
                message=(
                    f"Cannot withdraw ₹{err.required}: wallet balance is only ₹{err.balance}"
                ),
            )
        return svc.get_wallet()
