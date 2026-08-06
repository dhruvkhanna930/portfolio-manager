from . import db


class BenchmarkPriceHistory(db.Model):
    """Cached benchmark index closes (§14.4).

    Deliberately NOT rows in asset_metadata: a benchmark is a comparison line,
    not something the user can hold, buy, or see P/L on. Keeping it in its own
    table means benchmarks can never leak into holdings/allocation queries.
    """

    __tablename__ = "benchmark_price_history"

    benchmark_code = db.Column(db.String(20), primary_key=True, nullable=False)
    price_date = db.Column(db.Date, primary_key=True)
    close_price = db.Column(db.Numeric(18, 4), nullable=False)
    fetched_at = db.Column(db.DateTime, server_default=db.func.now())


db.Index(
    "idx_benchmark_code_date",
    BenchmarkPriceHistory.benchmark_code,
    BenchmarkPriceHistory.price_date,
)
