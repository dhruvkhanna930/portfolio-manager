"""
Example integration of the stock recommendation system into different frameworks.
Demonstrates various use cases and best practices.
"""

# ============================================================================
# EXAMPLE 1: Django Integration
# ============================================================================

"""
Django Integration Example
Place this in your Django app's views.py
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.cache import cache

import sys
import os

# Add the recommendation system to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from recommendations import (
    get_portfolio_recommendations,
    get_initial_recommendations_by_risk_profile
)


@login_required
@require_http_methods(["GET"])
def api_portfolio_recommendations(request):
    """Get recommendations based on user's portfolio"""
    try:
        user_portfolio = UserPortfolio.objects.get(user=request.user)
        stocks = [h.symbol for h in user_portfolio.holdings.all()]

        if not stocks:
            return JsonResponse({
                'error': 'Portfolio is empty',
                'recommendations': {'similar_stocks': [], 'complementary_stocks': []}
            }, status=400)

        # Use cache to avoid repeated computation
        cache_key = f'recommendations_{user_portfolio.id}'
        cached = cache.get(cache_key)

        if cached:
            return JsonResponse(cached)

        recommendations = get_portfolio_recommendations(
            portfolio=stocks,
            num_recommendations=10,
            use_ai=request.GET.get('use_ai', 'true') == 'true'
        )

        # Cache for 1 hour
        cache.set(cache_key, recommendations, 3600)

        return JsonResponse(recommendations)

    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'recommendations': {'similar_stocks': [], 'complementary_stocks': []}
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_risk_profile_recommendations(request):
    """Get recommendations based on risk profile"""
    try:
        risk_category = request.GET.get('risk', 'Balanced')

        valid_risks = ['Conservative', 'Balanced', 'Assertive', 'Aggressive']
        if risk_category not in valid_risks:
            return JsonResponse({
                'error': f'Invalid risk profile. Must be one of: {valid_risks}',
                'recommendations': []
            }, status=400)

        recommendations = get_initial_recommendations_by_risk_profile(
            risk_category=risk_category,
            num_recommendations=10,
            use_ai=request.GET.get('use_ai', 'true') == 'true'
        )

        return JsonResponse({
            'risk_profile': risk_category,
            'recommendations': recommendations,
            'count': len(recommendations)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# EXAMPLE 2: Flask/FastAPI Integration
# ============================================================================

"""
Flask Example
"""

from flask import Flask, jsonify, request
from functools import lru_cache
import time

app = Flask(__name__)

# Simple caching mechanism
_recommendation_cache = {}
_cache_ttl = 3600  # 1 hour


def get_cached_recommendations(stocks_tuple, use_ai=True):
    """Cache recommendations for a given portfolio"""
    key = (stocks_tuple, use_ai)
    cached = _recommendation_cache.get(key)

    if cached and time.time() - cached['time'] < _cache_ttl:
        return cached['data']

    recommendations = get_portfolio_recommendations(
        portfolio=list(stocks_tuple),
        use_ai=use_ai
    )

    _recommendation_cache[key] = {
        'data': recommendations,
        'time': time.time()
    }

    return recommendations


@app.route('/api/v1/recommendations', methods=['POST'])
def recommendations_endpoint():
    """
    POST endpoint for recommendations

    Request body:
    {
        "portfolio": ["AAPL", "MSFT", "GOOGL"],
        "use_ai": true,
        "limit": 10
    }
    """
    try:
        data = request.get_json()
        portfolio = data.get('portfolio', [])
        use_ai = data.get('use_ai', True)
        limit = data.get('limit', 10)

        if not portfolio:
            return jsonify({'error': 'Portfolio symbols required'}), 400

        recommendations = get_cached_recommendations(
            tuple(portfolio),
            use_ai=use_ai
        )

        # Limit results
        recommendations['similar_stocks'] = recommendations['similar_stocks'][:limit]
        recommendations['complementary_stocks'] = recommendations['complementary_stocks'][:limit]

        return jsonify(recommendations)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/recommendations/risk-profile', methods=['GET'])
def risk_profile_recommendations():
    """
    GET endpoint for risk profile recommendations

    Query parameters:
    - risk: Conservative, Balanced, Assertive, or Aggressive
    - use_ai: true/false
    - limit: number of recommendations
    """
    try:
        risk = request.args.get('risk', 'Balanced')
        use_ai = request.args.get('use_ai', 'true') == 'true'
        limit = int(request.args.get('limit', 10))

        recommendations = get_initial_recommendations_by_risk_profile(
            risk_category=risk,
            num_recommendations=limit,
            use_ai=use_ai
        )

        return jsonify({
            'risk_profile': risk,
            'recommendations': recommendations,
            'count': len(recommendations)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# EXAMPLE 3: Batch Processing
# ============================================================================

"""
Batch Processing Example
Process multiple portfolios and save results
"""

import json
from datetime import datetime


def batch_process_portfolios(portfolio_list):
    """
    Process multiple portfolios and return results

    Args:
        portfolio_list: List of dicts with 'user_id' and 'stocks' keys

    Returns:
        List of dicts with recommendations for each portfolio
    """
    results = []

    for portfolio in portfolio_list:
        user_id = portfolio['user_id']
        stocks = portfolio['stocks']

        try:
            recommendations = get_portfolio_recommendations(
                portfolio=stocks,
                use_ai=False  # Use False for faster batch processing
            )

            results.append({
                'user_id': user_id,
                'status': 'success',
                'similar_stocks': [s['symbol'] for s in recommendations['similar_stocks'][:3]],
                'complementary_stocks': [s['symbol'] for s in recommendations['complementary_stocks'][:3]],
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            results.append({
                'user_id': user_id,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

    return results


def save_batch_results(results, output_file='recommendations_batch.json'):
    """Save batch results to file"""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Saved {len(results)} results to {output_file}")


# Usage
if __name__ == '__main__':
    portfolios = [
        {'user_id': 'user_1', 'stocks': ['AAPL', 'MSFT', 'GOOGL']},
        {'user_id': 'user_2', 'stocks': ['JPM', 'BA', 'XOM']},
        {'user_id': 'user_3', 'stocks': ['JNJ', 'PG', 'KO']},
    ]

    results = batch_process_portfolios(portfolios)
    save_batch_results(results)


# ============================================================================
# EXAMPLE 4: Scheduled Recommendations (APScheduler)
# ============================================================================

"""
Scheduled Recommendations Example
Run recommendation generation on a schedule
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RecommendationScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def generate_daily_recommendations(self, user_portfolios):
        """Generate recommendations for all users daily"""
        print(f"[{datetime.now()}] Generating daily recommendations...")

        recommendations_log = []

        for user_id, stocks in user_portfolios.items():
            try:
                recommendations = get_portfolio_recommendations(
                    portfolio=stocks,
                    use_ai=True
                )

                # Save or send notifications
                self.save_recommendations(user_id, recommendations)

                # Get top recommendation
                if recommendations['similar_stocks']:
                    top_rec = recommendations['similar_stocks'][0]
                    recommendations_log.append({
                        'user_id': user_id,
                        'top_pick': top_rec['symbol'],
                        'score': top_rec['final_score']
                    })

            except Exception as e:
                logger.error(f"Error generating recommendations for {user_id}: {e}")

        return recommendations_log

    def save_recommendations(self, user_id, recommendations):
        """Save recommendations to database or file"""
        # Example: Save to file
        filename = f"recommendations_{user_id}_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w') as f:
            json.dump(recommendations, f, indent=2)

    def start(self):
        """Start the scheduler"""
        # Run daily at 9:30 AM
        self.scheduler.add_job(
            self.generate_daily_recommendations,
            'cron',
            hour=9,
            minute=30,
            args=[self.get_user_portfolios()]
        )
        self.scheduler.start()
        print("Recommendation scheduler started")

    def get_user_portfolios(self):
        """Fetch user portfolios from database"""
        # Example implementation
        return {
            'user_1': ['AAPL', 'MSFT'],
            'user_2': ['JPM', 'BA'],
        }


# ============================================================================
# EXAMPLE 5: Advanced Filtering
# ============================================================================

"""
Advanced Filtering Example
Filter and rank recommendations based on custom criteria
"""


class RecommendationFilter:
    @staticmethod
    def high_confidence(recommendations, threshold=70):
        """Filter stocks with high confidence scores"""
        return [s for s in recommendations if s['final_score'] >= threshold]

    @staticmethod
    def by_sector(recommendations, sectors):
        """Filter stocks by sector"""
        return [s for s in recommendations if s['sector'] in sectors]

    @staticmethod
    def by_dividend(recommendations, min_yield=0.02):
        """Filter stocks with minimum dividend yield"""
        return [s for s in recommendations if s['dividend_yield'] >= min_yield]

    @staticmethod
    def low_pe(recommendations, max_pe=25):
        """Filter stocks with P/E below threshold"""
        return [s for s in recommendations if 0 < s['pe_ratio'] <= max_pe]

    @staticmethod
    def low_volatility(recommendations, max_beta=1.0):
        """Filter stocks with beta below threshold"""
        return [s for s in recommendations if s['beta'] <= max_beta]

    @staticmethod
    def strong_fundamentals(recommendations):
        """Filter stocks with strong fundamental metrics"""
        return [
            s for s in recommendations
            if s['pe_ratio'] > 0 and s['pe_ratio'] < 30
            and s['beta'] > 0 and s['beta'] < 1.5
            and s['profit_margin'] > 0.05
        ]


# Usage example
if __name__ == '__main__':
    recommendations_list = get_portfolio_recommendations(['AAPL', 'MSFT'])
    all_stocks = (
        recommendations_list['similar_stocks'] +
        recommendations_list['complementary_stocks']
    )

    # Apply filters
    high_conf = RecommendationFilter.high_confidence(all_stocks, threshold=70)
    tech_stocks = RecommendationFilter.by_sector(high_conf, ['Technology'])
    dividend_stocks = RecommendationFilter.by_dividend(all_stocks, min_yield=0.02)
    low_pe = RecommendationFilter.low_pe(all_stocks, max_pe=20)

    print(f"High confidence: {len(high_conf)}")
    print(f"Tech + High confidence: {len(tech_stocks)}")
    print(f"Dividend stocks: {len(dividend_stocks)}")
    print(f"Low P/E (<20): {len(low_pe)}")


# ============================================================================
# EXAMPLE 6: Export Recommendations
# ============================================================================

"""
Export Recommendations Example
Export to various formats
"""

import csv
import pandas as pd


def export_to_csv(recommendations, filename='recommendations.csv'):
    """Export recommendations to CSV"""
    all_stocks = (
        recommendations['similar_stocks'] +
        recommendations['complementary_stocks']
    )

    with open(filename, 'w', newline='') as f:
        fieldnames = [
            'symbol', 'name', 'sector', 'pe_ratio', 'beta',
            'dividend_yield', 'rule_score', 'ai_score',
            'model_score', 'final_score'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        for stock in all_stocks:
            writer.writerow({
                'symbol': stock['symbol'],
                'name': stock['name'],
                'sector': stock['sector'],
                'pe_ratio': stock.get('pe_ratio', 0),
                'beta': stock.get('beta', 0),
                'dividend_yield': stock.get('dividend_yield', 0),
                'rule_score': stock.get('rule_score', 0),
                'ai_score': stock.get('ai_score', 0),
                'model_score': stock.get('trained_model_score', 0),
                'final_score': stock.get('final_score', 0)
            })


def export_to_excel(recommendations, filename='recommendations.xlsx'):
    """Export recommendations to Excel"""
    all_stocks = (
        recommendations['similar_stocks'] +
        recommendations['complementary_stocks']
    )

    df = pd.DataFrame(all_stocks)
    df.to_excel(filename, index=False)


def export_to_json(recommendations, filename='recommendations.json'):
    """Export recommendations to JSON"""
    with open(filename, 'w') as f:
        json.dump(recommendations, f, indent=2, default=str)


# ============================================================================
# EXAMPLE 7: Error Handling Best Practices
# ============================================================================

"""
Error Handling Example
Proper error handling and fallbacks
"""


def safe_get_recommendations(stocks, use_ai=True, fallback_to_fast=True):
    """
    Safely get recommendations with fallback

    Args:
        stocks: List of stock symbols
        use_ai: Whether to use AI models
        fallback_to_fast: Fall back to fast recommendations if AI fails

    Returns:
        Recommendations dict or None if all fail
    """
    try:
        # Try to get full recommendations
        return get_portfolio_recommendations(
            portfolio=stocks,
            use_ai=use_ai
        )

    except Exception as e:
        logger.warning(f"Failed to get AI recommendations: {e}")

        if fallback_to_fast:
            try:
                # Fall back to faster recommendations without AI
                return get_portfolio_recommendations(
                    portfolio=stocks,
                    use_ai=False
                )
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return None

        return None


# Usage with proper error handling
if __name__ == '__main__':
    stocks = ['AAPL', 'MSFT', 'GOOGL']

    recommendations = safe_get_recommendations(
        stocks=stocks,
        use_ai=True,
        fallback_to_fast=True
    )

    if recommendations:
        print(f"Got {len(recommendations['similar_stocks'])} recommendations")
    else:
        print("Could not generate recommendations")
