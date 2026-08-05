from . import big_fk, big_pk, db


class WalletLedger(db.Model):
    """Append-only cash ledger. Balance is always SUM(amount) over this table --
    never a separately stored mutable field (CLAUDE.md §1 golden rule, §6.10).
    `amount` is signed: positive = credit, negative = debit.
    """

    __tablename__ = "wallet_ledger"
    __table_args__ = (
        db.CheckConstraint(
            "entry_type IN ('DEPOSIT','WITHDRAWAL','BUY','SELL','DIVIDEND','FEE')",
            name="ck_wallet_entry_type",
        ),
    )

    ledger_id = big_pk()
    entry_type = db.Column(db.String(15), nullable=False)
    amount = db.Column(db.Numeric(18, 2), nullable=False)
    transaction_id = big_fk("transactions.transaction_id")
    note = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    transaction = db.relationship("Transaction", back_populates="wallet_entry")


db.Index("idx_wallet_created", WalletLedger.created_at)
