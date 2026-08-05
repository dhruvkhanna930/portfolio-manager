from . import big_fk, big_pk, db


class AssetMetadata(db.Model):
    __tablename__ = "asset_metadata"
    __table_args__ = (
        db.CheckConstraint("asset_type IN ('STOCK','MUTUAL_FUND','BOND')", name="ck_asset_type"),
        db.CheckConstraint("price_source IN ('LIVE','MANUAL')", name="ck_price_source"),
        db.UniqueConstraint("symbol", "asset_type", name="uq_asset_symbol_type"),
    )

    asset_id = big_pk()
    symbol = db.Column(db.String(30), nullable=False)
    isin = db.Column(db.String(12), unique=True)
    asset_type = db.Column(db.String(15), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    logo_url = db.Column(db.String(500))
    currency = db.Column(db.CHAR(3), nullable=False, default="INR", server_default="INR")
    price_source = db.Column(db.String(10), nullable=False, default="LIVE", server_default="LIVE")
    last_synced_at = db.Column(db.DateTime)

    stock_details = db.relationship(
        "StockDetails", back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )
    mutual_fund_details = db.relationship(
        "MutualFundDetails", back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )
    bond_details = db.relationship(
        "BondDetails", back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )
    price_snapshot = db.relationship(
        "PriceSnapshot", back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )
    price_history = db.relationship(
        "PriceHistory", back_populates="asset", cascade="all, delete-orphan"
    )
    metrics = db.relationship("AssetMetric", back_populates="asset", cascade="all, delete-orphan")
    news = db.relationship("NewsCache", back_populates="asset", cascade="all, delete-orphan")
    holdings = db.relationship("Holding", back_populates="asset")
    transactions = db.relationship("Transaction", back_populates="asset")
    sips = db.relationship("Sip", back_populates="asset")
    watchlist_entries = db.relationship("Watchlist", back_populates="asset")


db.Index("idx_meta_type", AssetMetadata.asset_type)


class FundHouse(db.Model):
    __tablename__ = "fund_houses"

    fund_house_id = big_pk()
    name = db.Column(db.String(150), nullable=False, unique=True)
    logo_url = db.Column(db.String(500))
    website = db.Column(db.String(255))

    funds = db.relationship("MutualFundDetails", back_populates="fund_house")


class FundManager(db.Model):
    __tablename__ = "fund_managers"

    manager_id = big_pk()
    name = db.Column(db.String(150), nullable=False)
    bio = db.Column(db.Text)


class StockDetails(db.Model):
    __tablename__ = "stock_details"

    asset_id = big_fk("asset_metadata.asset_id", primary_key=True)
    exchange = db.Column(db.String(20))
    sector = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    country = db.Column(db.String(60))

    asset = db.relationship("AssetMetadata", back_populates="stock_details")


class MutualFundDetails(db.Model):
    __tablename__ = "mutual_fund_details"
    __table_args__ = (
        db.CheckConstraint("plan_type IN ('DIRECT','REGULAR')", name="ck_mf_plan_type"),
        db.CheckConstraint("option_type IN ('GROWTH','IDCW')", name="ck_mf_option_type"),
    )

    asset_id = big_fk("asset_metadata.asset_id", primary_key=True)
    fund_house_id = big_fk("fund_houses.fund_house_id")
    category = db.Column(db.String(80))
    sub_category = db.Column(db.String(80))
    plan_type = db.Column(db.String(10))
    option_type = db.Column(db.String(10))
    expense_ratio = db.Column(db.Numeric(5, 2))
    aum = db.Column(db.Numeric(18, 2))
    risk_level = db.Column(db.String(20))
    benchmark = db.Column(db.String(120))

    asset = db.relationship("AssetMetadata", back_populates="mutual_fund_details")
    fund_house = db.relationship("FundHouse", back_populates="funds")
    manager_assignments = db.relationship(
        "FundManagerAssignment", back_populates="fund", cascade="all, delete-orphan"
    )


class FundManagerAssignment(db.Model):
    __tablename__ = "fund_manager_assignments"

    asset_id = big_fk("mutual_fund_details.asset_id", primary_key=True)
    manager_id = big_fk("fund_managers.manager_id", primary_key=True)
    since_date = db.Column(db.Date)

    fund = db.relationship("MutualFundDetails", back_populates="manager_assignments")
    manager = db.relationship("FundManager")


class BondDetails(db.Model):
    __tablename__ = "bond_details"

    asset_id = big_fk("asset_metadata.asset_id", primary_key=True)
    issuer = db.Column(db.String(150))
    coupon_rate = db.Column(db.Numeric(6, 3))
    face_value = db.Column(db.Numeric(14, 2))
    maturity_date = db.Column(db.Date)
    credit_rating = db.Column(db.String(10))
    payment_frequency = db.Column(db.String(15))

    asset = db.relationship("AssetMetadata", back_populates="bond_details")
