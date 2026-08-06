# Usage Guide

## Quick Start

### 1. Basic Portfolio Recommendations

```python
from recommendations import get_portfolio_recommendations

# Define your portfolio
portfolio_stocks = ['AAPL', 'MSFT', 'GOOGL']

# Get recommendations
recommendations = get_portfolio_recommendations(
    portfolio_stocks=portfolio_stocks,
    num_recommendations=10,
    use_ai=True
)

# Access recommendations
similar_stocks = recommendations['similar_stocks']
complementary_stocks = recommendations['complementary_stocks']

print("Similar Stocks:")
for stock in similar_stocks:
    print(f"  {stock['symbol']}: {stock['final_score']:.2f}")

print("\nComplementary Stocks:")
for stock in complementary_stocks:
    print(f"  {stock['symbol']}: {stock['final_score']:.2f}")
```

### 2. Get Recommendations without Portfolio

```python
from recommendations import get_initial_recommendations_by_risk_profile

# Conservative investor recommendations
recommendations = get_initial_recommendations_by_risk_profile(
    risk_category='Conservative',
    num_recommendations=10,
    use_ai=True
)

for stock in recommendations:
    print(f"{stock['symbol']}: {stock['final_score']:.2f}")
```

## Advanced Usage

### 3. Separate Similar and Complementary Stocks

```python
from recommendations import recommend_stocks, recommend_complementary_stocks

portfolio = ['AAPL', 'MSFT', 'JPM']

# Get only similar stocks
similar = recommend_stocks(
    portfolio_stocks=portfolio,
    num_recommendations=5,
    use_ai=False  # Faster, without AI enhancement
)

# Get only complementary stocks
complementary = recommend_complementary_stocks(
    portfolio_stocks=portfolio,
    num_recommendations=5,
    use_ai=True
)
```

### 4. Working with Recommendation Scores

Each recommendation includes detailed scoring information:

```python
from recommendations import recommend_stocks

recommendations = recommend_stocks(['AAPL', 'MSFT'])

for stock in recommendations:
    print(f"\n{stock['symbol']} - {stock['name']}")
    print(f"  Sector: {stock['sector']}")
    print(f"  Rule Score (Fundamentals): {stock['rule_score']:.2f}")
    print(f"  AI Sentiment: {stock['ai_sentiment']:.2f}")
    print(f"  AI Forecast: {stock['ai_forecast']:.2f}")
    print(f"  AI Score: {stock['ai_score']:.2f}")
    print(f"  Trained Model 1-Day: {stock['trained_model_1day']:.2f}")
    print(f"  Trained Model 5-Day: {stock['trained_model_5day']:.2f}")
    print(f"  Model Score: {stock['trained_model_score']:.2f}")
    print(f"  Final Score: {stock['final_score']:.2f}")
    
    # Fundamental metrics
    print(f"  P/E Ratio: {stock['pe_ratio']:.2f}")
    print(f"  Beta: {stock['beta']:.2f}")
    print(f"  Dividend Yield: {stock['dividend_yield']:.2%}")
```

### 5. Filtering and Sorting Recommendations

```python
from recommendations import get_portfolio_recommendations

recommendations = get_portfolio_recommendations(['AAPL', 'MSFT'])
all_stocks = recommendations['similar_stocks'] + recommendations['complementary_stocks']

# Filter by score threshold
high_confidence = [s for s in all_stocks if s['final_score'] > 70]

# Filter by sector
tech_stocks = [s for s in all_stocks if s['sector'] == 'Technology']

# Filter by fundamentals
low_pe = [s for s in all_stocks if s['pe_ratio'] < 20 and s['pe_ratio'] > 0]

# Sort by different criteria
by_score = sorted(all_stocks, key=lambda x: x['final_score'], reverse=True)
by_pe = sorted(all_stocks, key=lambda x: x['pe_ratio'])
by_dividend = sorted(all_stocks, key=lambda x: x['dividend_yield'], reverse=True)
```

### 6. Risk Profile Based Recommendations

```python
from recommendations import get_initial_recommendations_by_risk_profile

risk_profiles = ['Conservative', 'Balanced', 'Assertive', 'Aggressive']

for risk in risk_profiles:
    recommendations = get_initial_recommendations_by_risk_profile(
        risk_category=risk,
        num_recommendations=5,
        use_ai=False  # Faster
    )
    
    print(f"\n{risk} Portfolio:")
    for stock in recommendations:
        print(f"  {stock['symbol']}: {stock['final_score']:.2f}")
```

## Integration Examples

### 7. Flask/FastAPI Web Service

```python
from flask import Flask, jsonify, request
from recommendations import get_portfolio_recommendations

app = Flask(__name__)

@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.json
    stocks = data.get('portfolio', [])
    use_ai = data.get('use_ai', True)
    
    recommendations = get_portfolio_recommendations(
        portfolio_stocks=stocks,
        use_ai=use_ai
    )
    
    return jsonify(recommendations)

@app.route('/api/recommend-by-risk', methods=['GET'])
def recommend_by_risk():
    risk = request.args.get('risk', 'Balanced')
    
    from recommendations import get_initial_recommendations_by_risk_profile
    recommendations = get_initial_recommendations_by_risk_profile(
        risk_category=risk,
        num_recommendations=10
    )
    
    return jsonify({
        'risk_profile': risk,
        'recommendations': recommendations
    })

if __name__ == '__main__':
    app.run(debug=True)
```

### 8. Django Integration

In your Django view:

```python
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from stock_recommendation_system.recommendations import get_portfolio_recommendations

@login_required
def get_user_recommendations(request):
    user_portfolio = UserPortfolio.objects.get(user=request.user)
    stocks = [h.symbol for h in user_portfolio.holdings.all()]
    
    recommendations = get_portfolio_recommendations(
        portfolio_stocks=stocks,
        use_ai=request.GET.get('use_ai', 'true') == 'true'
    )
    
    return JsonResponse({
        'similar': recommendations['similar_stocks'],
        'complementary': recommendations['complementary_stocks'],
        'ai_models': recommendations['ai_models_used']
    })
```

### 9. Batch Processing Multiple Portfolios

```python
from recommendations import get_portfolio_recommendations
import json

portfolios = {
    'user1': ['AAPL', 'MSFT', 'GOOGL'],
    'user2': ['JPM', 'BA', 'XOM'],
    'user3': ['JNJ', 'PG', 'KO']
}

results = {}
for user_id, stocks in portfolios.items():
    recommendations = get_portfolio_recommendations(
        portfolio_stocks=stocks,
        use_ai=False  # Faster for batch
    )
    results[user_id] = {
        'similar': [s['symbol'] for s in recommendations['similar_stocks'][:3]],
        'complementary': [s['symbol'] for s in recommendations['complementary_stocks'][:3]]
    }

# Save results
with open('recommendations.json', 'w') as f:
    json.dump(results, f, indent=2)
```

### 10. Scheduled Recommendations

Using APScheduler:

```python
from apscheduler.schedulers.background import BackgroundScheduler
from recommendations import get_portfolio_recommendations
import json
from datetime import datetime

scheduler = BackgroundScheduler()

def generate_daily_recommendations():
    user_portfolios = load_user_portfolios()  # Your function
    
    for user_id, stocks in user_portfolios.items():
        recommendations = get_portfolio_recommendations(
            portfolio_stocks=stocks,
            use_ai=True
        )
        
        # Save or send recommendations
        save_recommendations(user_id, recommendations, datetime.now())
        send_notification(user_id, recommendations)

scheduler.add_job(generate_daily_recommendations, 'cron', hour=9, minute=30)
scheduler.start()
```

## Performance Optimization

### 11. Faster Recommendations (Disable AI)

For speed-critical applications:

```python
from recommendations import recommend_stocks

# Skip AI models - much faster
recommendations = recommend_stocks(
    portfolio_stocks=['AAPL', 'MSFT', 'GOOGL'],
    use_ai=False  # Skip sentiment and forecasting
)
```

**Speed comparison:**
- With AI: 30-60 seconds (5-10 stocks)
- Without AI: 5-10 seconds (5-10 stocks)

### 12. Caching Recommendations

```python
import functools
import time
from recommendations import get_portfolio_recommendations

# Simple cache decorator
recommendations_cache = {}

def cache_recommendations(stocks_tuple, use_ai=True, ttl=3600):
    key = (stocks_tuple, use_ai)
    cached = recommendations_cache.get(key)
    
    if cached and cached['time'] + ttl > time.time():
        return cached['data']
    
    recommendations = get_portfolio_recommendations(
        portfolio_stocks=list(stocks_tuple),
        use_ai=use_ai
    )
    
    recommendations_cache[key] = {
        'data': recommendations,
        'time': time.time()
    }
    
    return recommendations

# Usage
portfolio = ('AAPL', 'MSFT', 'GOOGL')
recommendations = cache_recommendations(tuple(portfolio), use_ai=True, ttl=3600)
```

### 13. Parallel Processing

Process multiple portfolios in parallel:

```python
from concurrent.futures import ThreadPoolExecutor
from recommendations import get_portfolio_recommendations

portfolios = [
    ['AAPL', 'MSFT', 'GOOGL'],
    ['JPM', 'BA', 'XOM'],
    ['JNJ', 'PG', 'KO']
]

def process_portfolio(stocks):
    return get_portfolio_recommendations(stocks, use_ai=False)

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_portfolio, portfolios))

for stocks, result in zip(portfolios, results):
    print(f"Portfolio {stocks}: {len(result['similar_stocks'])} recommendations")
```

## Error Handling

### 14. Robust Error Handling

```python
from recommendations import get_portfolio_recommendations

def safe_get_recommendations(portfolio_stocks):
    try:
        recommendations = get_portfolio_recommendations(
            portfolio_stocks=portfolio_stocks,
            use_ai=True
        )
        
        if not recommendations.get('similar_stocks'):
            print("Warning: No recommendations generated")
            return None
        
        return recommendations
        
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        
        # Fallback to faster recommendations without AI
        try:
            return get_portfolio_recommendations(
                portfolio_stocks=portfolio_stocks,
                use_ai=False
            )
        except Exception as fallback_error:
            print(f"Fallback also failed: {fallback_error}")
            return None

# Usage
recommendations = safe_get_recommendations(['AAPL', 'MSFT'])
```

### 15. Handling Missing Data

```python
from recommendations import recommend_stocks

recommendations = recommend_stocks(['AAPL', 'MSFT', 'INVALID'])

# Filter out stocks with missing data (score = 50)
valid_recommendations = [
    s for s in recommendations 
    if s['final_score'] != 50 and s.get('pe_ratio', 0) > 0
]

print(f"Valid recommendations: {len(valid_recommendations)}")
```

## Data Export

### 16. Export Recommendations to CSV

```python
import csv
from recommendations import get_portfolio_recommendations

recommendations = get_portfolio_recommendations(['AAPL', 'MSFT'])
all_stocks = recommendations['similar_stocks'] + recommendations['complementary_stocks']

with open('recommendations.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'symbol', 'name', 'sector', 'pe_ratio', 'beta', 
        'dividend_yield', 'rule_score', 'ai_score', 
        'trained_model_score', 'final_score'
    ])
    
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
            'trained_model_score': stock.get('trained_model_score', 0),
            'final_score': stock.get('final_score', 0)
        })

print("Recommendations exported to recommendations.csv")
```

### 17. Export to JSON

```python
import json
from recommendations import get_portfolio_recommendations

recommendations = get_portfolio_recommendations(['AAPL', 'MSFT'])

with open('recommendations.json', 'w') as f:
    json.dump(recommendations, f, indent=2, default=str)

print("Recommendations exported to recommendations.json")
```

## Troubleshooting

### Issue: "No recommendations generated"

```python
from recommendations import build_stock_features_dataframe

stocks = ['AAPL', 'MSFT', 'INVALID']
df, valid_symbols = build_stock_features_dataframe(stocks)

print(f"Symbols with data: {valid_symbols}")
# Output: Symbols with data: ['AAPL', 'MSFT']
```

### Issue: Slow recommendations

```python
# 1. Check which operation is slow
import time
from recommendations import compute_ai_model_scores

stocks = ['AAPL', 'MSFT', 'GOOGL']
start = time.time()
ai_scores = compute_ai_model_scores(stocks)
print(f"AI scoring took {time.time() - start:.1f}s")

# 2. If AI scoring is slow, disable it
from recommendations import recommend_stocks

recommendations = recommend_stocks(stocks, use_ai=False)
```

## Next Steps

- Check [API.md](API.md) for detailed function documentation
- See [../examples/](../examples/) for more complete examples
- Review [INSTALLATION.md](INSTALLATION.md) if you have setup issues
