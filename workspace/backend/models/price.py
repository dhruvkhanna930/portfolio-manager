from . import big_fk, db


class PriceSnapshot(db.Model):
    __tablename__ = "price_snapshot"

    asset_id = big_fk("asset_metadata.asset_id", primary_key=True)
    price = db.Column(db.Numeric(18, 4), nullable=False)
    prev_close = db.Column(db.Numeric(18, 4))
    day_change = db.Column(db.Numeric(18, 4))
    day_change_pct = db.Column(db.Numeric(8, 4))
    is_stale = db.Column(db.Boolean, default=False, server_default=db.false())
    as_of = db.Column(db.DateTime, nullable=False)

    asset = db.relationship("AssetMetadata", back_populates="price_snapshot")


class PriceHistory(db.Model):
    __tablename__ = "price_history"

    asset_id = big_fk("asset_metadata.asset_id", primary_key=True)
    price_date = db.Column(db.Date, primary_key=True)
    close_price = db.Column(db.Numeric(18, 4), nullable=False)
    source = db.Column(db.String(20))
    fetched_at = db.Column(db.DateTime, server_default=db.func.now())

    asset = db.relationship("AssetMetadata", back_populates="price_history")


db.Index("idx_price_history_date", PriceHistory.asset_id, PriceHistory.price_date)


class AssetMetric(db.Model):
    __tablename__ = "asset_metrics"

    asset_id = big_fk("asset_metadata.asset_id", primary_key=True)
    metric_key = db.Column(db.String(40), primary_key=True, nullable=False)
    period = db.Column(db.String(10), primary_key=True)
    metric_value = db.Column(db.Numeric(18, 6))
    as_of = db.Column(db.DateTime)

    asset = db.relationship("AssetMetadata", back_populates="metrics")


db.Index("idx_metrics_key", AssetMetric.metric_key)
