from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas.transaction import (
    TransactionCreateResponseSchema,
    TransactionCreateSchema,
    TransactionSchema,
)
from services import transaction_service as svc, wallet_service
from services.transaction_service import (
    AssetNotFoundError,
    InsufficientFundsError,
    InsufficientQuantityError,
    NoHoldingError,
)

blp = Blueprint(
    "transactions",
    __name__,
    url_prefix="/api/transactions",
    description="Transaction history and the only way to BUY/SELL/record DIVIDEND",
)


@blp.route("")
class TransactionList(MethodView):
    @blp.response(200, TransactionSchema(many=True))
    def get(self):
        return svc.list_transactions()

    @blp.arguments(TransactionCreateSchema)
    @blp.response(201, TransactionCreateResponseSchema)
    def post(self, new_data):
        try:
            txn, realised_pl = svc.create_transaction(new_data)
        except AssetNotFoundError:
            abort(422, message=f"asset_id {new_data['asset_id']} does not exist")
        except InsufficientFundsError as err:
            abort(
                422,
                message=(
                    f"Insufficient wallet balance: this BUY costs ₹{err.required:.2f} "
                    f"but your wallet has only ₹{err.balance:.2f}. Deposit more cash first."
                ),
            )
        except InsufficientQuantityError as err:
            abort(
                422,
                message=(
                    f"Cannot sell {err.requested} units -- you only hold {err.held}."
                ),
            )
        except NoHoldingError:
            abort(422, message="You do not hold this asset, so it cannot be sold")

        return {
            "transaction": txn,
            "realised_pl": realised_pl,
            "wallet_balance": wallet_service.get_balance(),
        }
