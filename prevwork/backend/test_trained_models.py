#!/usr/bin/env python
"""Test script to verify trained models integration"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_management_system.settings')
django.setup()

from dashboard.trained_models import TrainedModelPredictor, compute_trained_model_scores

def test_model_loading():
    """Test if trained models can be loaded"""
    print("=" * 60)
    print("Testing Trained Model Loading")
    print("=" * 60)

    predictor = TrainedModelPredictor()

    if predictor.models_loaded:
        print("✓ Models loaded successfully!")
        if predictor.lstm_5day_model:
            print("  ✓ LSTM 5-day model loaded")
        if predictor.gru_1day_model:
            print("  ✓ GRU 1-day model loaded")
    else:
        print("✗ Failed to load models (might be due to TensorFlow version compatibility)")

    print()


def test_predictions():
    """Test predictions on sample stocks"""
    print("=" * 60)
    print("Testing Stock Predictions")
    print("=" * 60)

    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']

    model_scores = compute_trained_model_scores(test_tickers)

    for ticker, scores in model_scores.items():
        print(f"\n{ticker}:")
        print(f"  1-day prediction:  {scores['1day']}")
        print(f"  5-day prediction:  {scores['5day']}")
        print(f"  Combined score:    {scores['combined']}")
        print(f"  Models available:  {scores['available']}")

    print()


def test_recommendation_integration():
    """Test if recommendations include trained model scores"""
    print("=" * 60)
    print("Testing Recommendation Integration")
    print("=" * 60)

    from dashboard.models import Portfolio
    from django.contrib.auth import get_user_model
    from dashboard.recommendations import get_portfolio_recommendations

    User = get_user_model()

    try:
        # Try to get a test user's portfolio
        test_user = User.objects.first()

        if test_user:
            portfolio = Portfolio.objects.filter(user=test_user).first()

            if portfolio:
                print(f"\nTesting with user: {test_user.username}")
                print(f"Portfolio total investment: ${portfolio.total_investment}")

                recommendations = get_portfolio_recommendations(portfolio, use_ai=True)

                print(f"\nSimilar stocks recommendations: {len(recommendations.get('similar_stocks', []))}")
                if recommendations.get('similar_stocks'):
                    rec = recommendations['similar_stocks'][0]
                    print(f"  Top recommendation: {rec.get('symbol', 'N/A')}")
                    if 'trained_model_score' in rec:
                        print(f"    Trained model score: {rec['trained_model_score']}")
                    if 'final_score' in rec:
                        print(f"    Final score: {rec['final_score']}")

                print(f"\nComplementary stocks recommendations: {len(recommendations.get('complementary_stocks', []))}")
                if recommendations.get('complementary_stocks'):
                    rec = recommendations['complementary_stocks'][0]
                    print(f"  Top recommendation: {rec.get('symbol', 'N/A')}")
                    if 'trained_model_score' in rec:
                        print(f"    Trained model score: {rec['trained_model_score']}")
                    if 'final_score' in rec:
                        print(f"    Final score: {rec['final_score']}")

                print("\nModels used in recommendations:")
                if recommendations.get('ai_models_used'):
                    models = recommendations['ai_models_used']
                    if 'trained_models' in models:
                        print(f"  ✓ Trained models integrated:")
                        for model, desc in models['trained_models'].items():
                            print(f"    - {model}: {desc}")
                    if 'scoring_weights' in models:
                        print(f"\n  Scoring weights:")
                        for weight, value in models['scoring_weights'].items():
                            print(f"    - {weight}: {value * 100}%")
            else:
                print("No portfolio found for the test user")
        else:
            print("No users found in database")

    except Exception as e:
        print(f"Error testing recommendation integration: {str(e)}")
        import traceback
        traceback.print_exc()

    print()


if __name__ == '__main__':
    test_model_loading()
    test_predictions()
    test_recommendation_integration()

    print("=" * 60)
    print("Testing Complete!")
    print("=" * 60)
