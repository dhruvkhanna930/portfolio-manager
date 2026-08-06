from decimal import Decimal

from models import AssetMetadata, Holding, Transaction, db
from services import wallet_service
from services.analytics_service import compute_weighted_avg_buy_price


class AssetNotFoundError(Exception):
    pass


class InsufficientFundsError(Exception):
    def __init__(self, balance, required):
        self.balance = balance
        self.required = required
        super().__init__(f"insufficient funds: balance {balance}, required {required}")


class InsufficientQuantityError(Exception):
    def __init__(self, held, requested):
        self.held = held
        self.requested = requested
        super().__init__(f"insufficient quantity: held {held}, requested {requested}")


class NoHoldingError(Exception):
    pass


def list_transactions():
    return Transaction.query.order_by(
        Transaction.txn_date.desc(), Transaction.transaction_id.desc()
    ).all()


def _apply_buy(asset, data):
    quantity = Decimal(data["quantity"])
    price = Decimal(data["price"])
    fees = Decimal(data.get("fees") or 0)
    cost = quantity * price + fees

    balance = wallet_service.get_balance()
    if cost > balance:
        raise InsufficientFundsError(balance, cost)

    holding = Holding.query.filter_by(asset_id=asset.asset_id).first()
    if holding is None:
        holding = Holding(
            asset_id=asset.asset_id,
            quantity=quantity,
            avg_buy_price=price,
            first_bought=data["txn_date"],
        )
        db.session.add(holding)
    else:
        holding.avg_buy_price = compute_weighted_avg_buy_price(
            holding.quantity, holding.avg_buy_price, quantity, price
        )
        holding.quantity = Decimal(holding.quantity) + quantity
        if holding.first_bought is None or data["txn_date"] < holding.first_bought:
            holding.first_bought = data["txn_date"]

    db.session.flush()
    return holding, -cost, None


def _apply_sell(asset, data):
    quantity = Decimal(data["quantity"])
    price = Decimal(data["price"])
    fees = Decimal(data.get("fees") or 0)

    holding = Holding.query.filter_by(asset_id=asset.asset_id).first()
    if holding is None:
        raise NoHoldingError(asset.asset_id)

    held = Decimal(holding.quantity)
    if quantity > held:
        raise InsufficientQuantityError(held, quantity)

    # Realised P/L is booked against the average cost at the moment of sale, and
    # avg_buy_price itself is left untouched by a SELL (§6.4, §6.5).
    realised_pl = (price - Decimal(holding.avg_buy_price)) * quantity - fees
    proceeds = quantity * price - fees

    remaining = held - quantity
    holding.quantity = remaining
    db.session.flush()

    if remaining == 0:
        # A holding is a derived cache -- at zero quantity it simply ceases to
        # exist, rather than lingering as an empty row (§5.2).
        holding_id = holding.holding_id
        Transaction.query.filter_by(holding_id=holding_id).update({"holding_id": None})
        db.session.delete(holding)
        db.session.flush()
        holding = None

    return holding, proceeds, realised_pl


def _apply_dividend(asset, data):
    # DIVIDEND never touches quantity or avg_buy_price -- it is pure cash in.
    amount = Decimal(data["quantity"]) * Decimal(data["price"])
    holding = Holding.query.filter_by(asset_id=asset.asset_id).first()
    return holding, amount, None


def create_transaction(data):
    """The only way to BUY, SELL, or record a DIVIDEND. Drives holdings and the
    wallet ledger together in one DB transaction so they can never drift (§5.2).
    """
    asset = db.session.get(AssetMetadata, data["asset_id"])
    if asset is None:
        raise AssetNotFoundError(data["asset_id"])

    txn_type = data["txn_type"]
    if txn_type == "BUY":
        holding, wallet_amount, realised_pl = _apply_buy(asset, data)
    elif txn_type == "SELL":
        holding, wallet_amount, realised_pl = _apply_sell(asset, data)
    else:
        holding, wallet_amount, realised_pl = _apply_dividend(asset, data)

    txn = Transaction(
        asset_id=asset.asset_id,
        holding_id=holding.holding_id if holding is not None else None,
        txn_type=txn_type,
        quantity=Decimal(data["quantity"]),
        price=Decimal(data["price"]),
        fees=Decimal(data.get("fees") or 0),
        txn_date=data["txn_date"],
    )
    db.session.add(txn)
    db.session.flush()

    wallet_service.add_entry(
        txn_type,
        wallet_amount,
        note=f"{txn_type} {data['quantity']} {asset.symbol}",
        transaction_id=txn.transaction_id,
        commit=False,
    )

    db.session.commit()
    return txn, realised_pl
