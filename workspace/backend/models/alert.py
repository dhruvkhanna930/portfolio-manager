from . import big_fk, big_pk, db


class PriceTarget(db.Model):
    """A price the user wants to be told about (§15.5).

    This is the only *stored* part of the alerts feature -- it's a user
    intention, so it's source-of-truth data. Whether a target has been hit is
    never stored: it's recomputed from the current price on each read, so it can
    never go stale or need invalidating.

    `direction` records which way the user cares about: ABOVE fires when price
    rises to the target, BELOW when it falls to it.
    """

    __tablename__ = "price_targets"

    target_id = big_pk()
    asset_id = big_fk("asset_metadata.asset_id", nullable=False)
    target_price = db.Column(db.Numeric(18, 4), nullable=False)
    direction = db.Column(db.String(5), nullable=False, default="ABOVE")
    note = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        db.CheckConstraint("direction IN ('ABOVE','BELOW')", name="ck_price_target_direction"),
        db.Index("idx_price_target_asset", "asset_id"),
    )

    asset = db.relationship("AssetMetadata")
