from decimal import Decimal

from models import WalletLedger, db


class InsufficientFundsError(Exception):
    def __init__(self, balance, required):
        self.balance = balance
        self.required = required
        super().__init__(f"insufficient funds: balance {balance}, required {required}")


def get_balance():
    """Balance is always SUM(amount) -- never a stored mutable field (§6.10)."""
    total = db.session.query(db.func.coalesce(db.func.sum(WalletLedger.amount), 0)).scalar()
    return Decimal(total)


def list_entries(limit=25):
    return (
        WalletLedger.query.order_by(WalletLedger.created_at.desc(), WalletLedger.ledger_id.desc())
        .limit(limit)
        .all()
    )


def get_wallet(limit=25):
    return {"balance": get_balance(), "entries": list_entries(limit)}


def add_entry(entry_type, amount, note=None, transaction_id=None, commit=True):
    """Append a ledger row. `amount` must already be signed by the caller."""
    entry = WalletLedger(
        entry_type=entry_type,
        amount=Decimal(amount),
        note=note,
        transaction_id=transaction_id,
    )
    db.session.add(entry)
    if commit:
        db.session.commit()
    return entry


def deposit(amount, note=None):
    return add_entry("DEPOSIT", Decimal(amount), note=note or "Cash deposit")


def withdraw(amount, note=None):
    amount = Decimal(amount)
    balance = get_balance()
    if amount > balance:
        raise InsufficientFundsError(balance, amount)
    return add_entry("WITHDRAWAL", -amount, note=note or "Cash withdrawal")
