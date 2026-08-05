from . import big_fk, big_pk, db


class NewsCache(db.Model):
    __tablename__ = "news_cache"

    news_id = big_pk()
    asset_id = big_fk("asset_metadata.asset_id")
    headline = db.Column(db.String(500), nullable=False)
    source_name = db.Column(db.String(120))
    url = db.Column(db.String(700), nullable=False, unique=True)
    published_at = db.Column(db.DateTime)
    sentiment = db.Column(db.String(10))
    thumbnail_url = db.Column(db.String(700))
    fetched_at = db.Column(db.DateTime, server_default=db.func.now())

    asset = db.relationship("AssetMetadata", back_populates="news")


db.Index("idx_news_asset", NewsCache.asset_id)
db.Index("idx_news_published", NewsCache.published_at)
