"""
Stock Recommendation System
A standalone, production-ready AI-powered stock recommendation engine.

Features:
- Similar stock recommendations based on portfolio
- Complementary stock recommendations
- Risk profile-based recommendations
- Sentiment analysis and price forecasting
- Trained ML models for price prediction
- Hybrid scoring system
"""

__version__ = '1.0.0'
__author__ = 'Stock Recommendation Team'

# Import main functions for easier access
from .recommendations import (
    get_portfolio_recommendations,
    recommend_stocks,
    recommend_complementary_stocks,
    get_initial_recommendations_by_risk_profile,
    get_stock_fundamentals,
    build_stock_features_dataframe,
    compute_stock_similarity,
    compute_ai_model_scores,
)

from .trained_models import (
    TrainedModelPredictor,
    compute_trained_model_scores,
    evaluate_trained_model,
)

from .config import get_config_summary, validate_config

__all__ = [
    # Core recommendation functions
    'get_portfolio_recommendations',
    'recommend_stocks',
    'recommend_complementary_stocks',
    'get_initial_recommendations_by_risk_profile',

    # Utility functions
    'get_stock_fundamentals',
    'build_stock_features_dataframe',
    'compute_stock_similarity',
    'compute_ai_model_scores',

    # Model functions
    'TrainedModelPredictor',
    'compute_trained_model_scores',
    'evaluate_trained_model',

    # Configuration
    'get_config_summary',
    'validate_config',
]
