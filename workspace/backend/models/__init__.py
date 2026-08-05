from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import BigInteger, Integer

db = SQLAlchemy()

# BIGSERIAL/BIGINT in Postgres (prod), plain INTEGER in SQLite (dev) so
# autoincrement rowid semantics keep working locally.
BigIntType = BigInteger().with_variant(Integer(), "sqlite")


def big_pk():
    return db.Column(BigIntType, primary_key=True, autoincrement=True)


def big_fk(target, **kwargs):
    return db.Column(BigIntType, db.ForeignKey(target), **kwargs)


from .asset import (  # noqa: E402,F401
    AssetMetadata,
    BondDetails,
    FundHouse,
    FundManager,
    FundManagerAssignment,
    MutualFundDetails,
    StockDetails,
)
from .price import AssetMetric, PriceHistory, PriceSnapshot  # noqa: E402,F401
from .news import NewsCache  # noqa: E402,F401
from .market import MarketIndexConstituent  # noqa: E402,F401
from .portfolio import (  # noqa: E402,F401
    Holding,
    HoldingTag,
    Sip,
    Tag,
    Transaction,
    Watchlist,
)
from .wallet import WalletLedger  # noqa: E402,F401
