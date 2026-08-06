from . import big_fk, big_pk, db


class NewsCache(db.Model):
    __tablename__ = "news_cache"
    __table_args__ = (
        db.Index("idx_news_asset", "asset_id"),
        db.Index("idx_news_published", "published_at"),
    )

    news_id = big_pk()
    asset_id = big_fk("asset_metadata.asset_id", nullable=True)  # NULL = general market news
    headline = db.Column(db.String(500), nullable=False)
    source_name = db.Column(db.String(120))
    url = db.Column(db.String(700), nullable=False, unique=True)
    published_at = db.Column(db.DateTime)
    sentiment = db.Column(db.String(10))  # 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
    thumbnail_url = db.Column(db.String(700))
    fetched_at = db.Column(db.DateTime, server_default=db.func.now())

    asset = db.relationship("AssetMetadata", back_populates="news")
