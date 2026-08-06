"""Recommendation model endpoints (Phase 16).

Read-only and additive, per §13: these add new endpoints rather than changing
any existing contract. Nothing here places an order or writes user data.
"""

from flask.views import MethodView
from flask_smorest import Blueprint, abort

from models import AssetMetadata, db
from schemas.recommendation import (
    ForecastResponseSchema,
    ModelStatusSchema,
    RecommendationQuerySchema,
    RecommendationResponseSchema,
)
from services import ml_forecast_service, recommendation_service

blp = Blueprint(
    "recommendations",
    __name__,
    url_prefix="/api/recommendations",
    description="Rule-based stock recommendations with an optional LSTM/GRU signal",
)


@blp.route("")
class RecommendationList(MethodView):
    @blp.arguments(RecommendationQuerySchema, location="query")
    @blp.response(200, RecommendationResponseSchema)
    def get(self, args):
        try:
            return recommendation_service.recommend(
                mode=args["mode"],
                risk_profile=args["risk_profile"],
                limit=args["limit"],
                use_ml=args["use_ml"],
            )
        except ValueError as exc:
            abort(422, message=str(exc))


@blp.route("/model")
class ModelStatus(MethodView):
    @blp.response(200, ModelStatusSchema)
    def get(self):
        """Which prediction path is live -- trained network or momentum fallback."""
        return ml_forecast_service.model_status()


@blp.route("/forecast/<int:asset_id>")
class AssetForecast(MethodView):
    @blp.response(200, ForecastResponseSchema)
    def get(self, asset_id):
        """Raw model output for a single asset, for inspection."""
        asset = db.session.get(AssetMetadata, asset_id)
        if asset is None:
            abort(404, message=f"Asset {asset_id} not found")

        return {
            "asset_id": asset.asset_id,
            "symbol": asset.symbol,
            "forecast": ml_forecast_service.forecast(asset.symbol, asset.asset_id),
            "model": ml_forecast_service.model_status(),
        }
