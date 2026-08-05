from . import big_fk, db


class MarketIndexConstituent(db.Model):
    __tablename__ = "market_index_constituents"

    asset_id = big_fk("asset_metadata.asset_id", primary_key=True)
    index_name = db.Column(db.String(30), primary_key=True, nullable=False)

    asset = db.relationship("AssetMetadata", back_populates="index_memberships")
