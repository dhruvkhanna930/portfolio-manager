from . import big_fk, big_pk, db


class Holding(db.Model):
    __tablename__ = "holdings"
    __table_args__ = (db.CheckConstraint("quantity >= 0", name="ck_holding_quantity_nonneg"),)

    holding_id = big_pk()
    asset_id = big_fk("asset_metadata.asset_id", nullable=False)
    quantity = db.Column(db.Numeric(18, 6), nullable=False)
    avg_buy_price = db.Column(db.Numeric(18, 4), nullable=False)
    first_bought = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    asset = db.relationship("AssetMetadata", back_populates="holdings")
    transactions = db.relationship("Transaction", back_populates="holding")
    tags = db.relationship("Tag", secondary="holding_tags", back_populates="holdings")


db.Index("idx_holdings_asset", Holding.asset_id)


class Sip(db.Model):
    __tablename__ = "sips"
    __table_args__ = (
        db.CheckConstraint(
            "frequency IN ('DAILY','WEEKLY','MONTHLY','QUARTERLY')", name="ck_sip_frequency"
        ),
    )

    sip_id = big_pk()
    asset_id = big_fk("asset_metadata.asset_id", nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    frequency = db.Column(db.String(15), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    day_of_cycle = db.Column(db.SmallInteger)
    is_active = db.Column(db.Boolean, default=True, server_default=db.true())
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    asset = db.relationship("AssetMetadata", back_populates="sips")
    transactions = db.relationship("Transaction", back_populates="sip")


class Transaction(db.Model):
    __tablename__ = "transactions"
    __table_args__ = (db.CheckConstraint("txn_type IN ('BUY','SELL','DIVIDEND')", name="ck_txn_type"),)

    transaction_id = big_pk()
    asset_id = big_fk("asset_metadata.asset_id", nullable=False)
    holding_id = big_fk("holdings.holding_id")
    sip_id = big_fk("sips.sip_id")
    txn_type = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Numeric(18, 6), nullable=False)
    price = db.Column(db.Numeric(18, 4), nullable=False)
    fees = db.Column(db.Numeric(12, 4), default=0, server_default="0")
    txn_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    asset = db.relationship("AssetMetadata", back_populates="transactions")
    holding = db.relationship("Holding", back_populates="transactions")
    sip = db.relationship("Sip", back_populates="transactions")


db.Index("idx_txn_asset", Transaction.asset_id)
db.Index("idx_txn_date", Transaction.txn_date)


class Watchlist(db.Model):
    __tablename__ = "watchlist"

    watchlist_id = big_pk()
    asset_id = big_fk("asset_metadata.asset_id", nullable=False, unique=True)
    added_at = db.Column(db.DateTime, server_default=db.func.now())

    asset = db.relationship("AssetMetadata", back_populates="watchlist_entries")


class Tag(db.Model):
    __tablename__ = "tags"

    tag_id = big_pk()
    name = db.Column(db.String(50), unique=True, nullable=False)

    holdings = db.relationship("Holding", secondary="holding_tags", back_populates="tags")


class HoldingTag(db.Model):
    __tablename__ = "holding_tags"

    holding_id = big_fk("holdings.holding_id", primary_key=True)
    tag_id = big_fk("tags.tag_id", primary_key=True)
