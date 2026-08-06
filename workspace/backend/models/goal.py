from . import big_pk, db


class Goal(db.Model):
    """A savings target (§14.7). Deliberately minimal and NOT linked to specific
    holdings: progress is measured against whole-portfolio value, so this stays a
    savings target and never becomes net-worth tracking (§0.3 item 20).
    """

    __tablename__ = "goals"

    goal_id = big_pk()
    name = db.Column(db.String(120), nullable=False)
    target_amount = db.Column(db.Numeric(18, 2), nullable=False)
    target_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
