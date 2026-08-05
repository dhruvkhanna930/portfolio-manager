# Quick Start Guide

Get the stock recommendation system up and running in 5 minutes.

## 1. Install Dependencies (2 minutes)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

## 2. Verify Installation (1 minute)

```bash
python tests/test_recommendations.py
```

You should see a summary showing which dependencies are installed and the system status.

## 3. Try It Out (2 minutes)

### Option A: Python Script

Create `test_recommendations.py`:

```python
from stock_recommendation_system import get_portfolio_recommendations

# Get recommendations for a sample portfolio
recommendations = get_portfolio_recommendations(
    portfolio=['AAPL', 'MSFT', 'GOOGL'],
    use_ai=False  # Set to True for AI-enhanced recommendations
)

# Print similar stocks
print("Similar Stocks:")
for stock in recommendations['similar_stocks'][:5]:
    print(f"  {stock['symbol']}: {stock['final_score']:.2f}")

# Print complementary stocks
print("\nComplementary Stocks:")
for stock in recommendations['complementary_stocks'][:5]:
    print(f"  {stock['symbol']}: {stock['final_score']:.2f}")
```

Run it:
```bash
python test_recommendations.py
```

### Option B: Interactive Python

```python
>>> from stock_recommendation_system import recommend_stocks
>>> recommendations = recommend_stocks(['AAPL', 'MSFT'], use_ai=False)
>>> for stock in recommendations[:3]:
...     print(f"{stock['symbol']}: {stock['final_score']:.0f}")
```

## What's Next?

### To Learn More
- Read [README.md](README.md) for feature overview
- Check [docs/USAGE.md](docs/USAGE.md) for more examples
- See [docs/API.md](docs/API.md) for complete API reference

### To Integrate into Your App
- Django? See [examples/example_integration.py](examples/example_integration.py) (Django section)
- Flask/FastAPI? See [examples/example_integration.py](examples/example_integration.py) (Flask section)
- Python script? See [docs/USAGE.md](docs/USAGE.md) (Usage Guide section)

### To Enhance with AI
Set `use_ai=True` for AI-powered recommendations (slower but more accurate):

```python
recommendations = get_portfolio_recommendations(
    portfolio=['AAPL', 'MSFT'],
    use_ai=True  # Enables sentiment analysis and price forecasting
)
```

Takes ~30-60 seconds depending on your internet connection.

## Common Tasks

### Get recommendations for a risk profile (no portfolio needed)

```python
from stock_recommendation_system import get_initial_recommendations_by_risk_profile

conservative = get_initial_recommendations_by_risk_profile('Conservative')
balanced = get_initial_recommendations_by_risk_profile('Balanced')
aggressive = get_initial_recommendations_by_risk_profile('Aggressive')
```

### Filter recommendations

```python
recommendations = get_initial_recommendations_by_risk_profile('Balanced')

# High confidence picks
high_confidence = [s for s in recommendations if s['final_score'] > 70]

# Low P/E stocks
low_pe = [s for s in recommendations if 10 < s['pe_ratio'] < 20]

# Dividend stocks
dividend_stocks = [s for s in recommendations if s['dividend_yield'] > 0.02]
```

### Use with Django

In your `views.py`:

```python
from django_app.models import UserPortfolio
from stock_recommendation_system import get_portfolio_recommendations

def recommendations_view(request):
    portfolio = UserPortfolio.objects.get(user=request.user)
    stocks = [h.symbol for h in portfolio.holdings.all()]
    
    recommendations = get_portfolio_recommendations(portfolio=stocks)
    
    return JsonResponse(recommendations)
```

### Use with Flask

```python
from flask import Flask, jsonify, request
from stock_recommendation_system import get_portfolio_recommendations

app = Flask(__name__)

@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.json
    stocks = data.get('portfolio', [])
    
    recommendations = get_portfolio_recommendations(portfolio=stocks)
    return jsonify(recommendations)
```

## Troubleshooting

### "No recommendations generated"
- Ensure stock symbols are valid (e.g., 'AAPL' not 'Apple')
- Check internet connection for data fetching

### "Module not found"
- Make sure virtual environment is activated
- Re-run: `pip install -r requirements.txt`

### Slow recommendations
- Use `use_ai=False` for faster results
- Default AI takes 30-60 seconds for sentiment analysis
- Consider caching results for 1 hour

### TensorFlow/Model errors
- Not critical - system works without them
- For full ML model support, ensure TensorFlow is installed
- See [docs/INSTALLATION.md](docs/INSTALLATION.md) for detailed setup

## System Requirements

- **Python**: 3.8+
- **RAM**: 2GB minimum (4GB for ML models)
- **Disk**: 1GB (mostly for models)
- **Internet**: Required for stock data

## Performance

- **Without AI**: 5-10 seconds for 5-10 stocks
- **With AI**: 30-60 seconds for 5-10 stocks
- **Recommendations cached**: 1-3 seconds (if implemented)

## Key Functions

```python
# Main entry point
get_portfolio_recommendations(portfolio, num_recommendations=10, use_ai=True)

# Similar stocks
recommend_stocks(portfolio, num_recommendations=10, use_ai=True)

# Complementary stocks
recommend_complementary_stocks(portfolio, num_recommendations=10, use_ai=True)

# Risk-based (no portfolio needed)
get_initial_recommendations_by_risk_profile(risk_category, num_recommendations=10, use_ai=True)

# Individual stock data
get_stock_fundamentals(symbol)
```

## File Guide

| File | Purpose |
|------|---------|
| `recommendations.py` | Core recommendation engine |
| `trained_models.py` | ML model loading |
| `config.py` | Configuration settings |
| `tests/test_recommendations.py` | Verification script |
| `examples/example_integration.py` | Integration examples |
| `docs/USAGE.md` | Detailed usage guide |
| `docs/API.md` | Complete API reference |

## Getting Help

1. **Installation issues?** → [docs/INSTALLATION.md](docs/INSTALLATION.md)
2. **How to use?** → [docs/USAGE.md](docs/USAGE.md)
3. **API reference?** → [docs/API.md](docs/API.md)
4. **Integration examples?** → [examples/example_integration.py](examples/example_integration.py)
5. **Architecture?** → [FILE_STRUCTURE.md](FILE_STRUCTURE.md)

## Next Steps

1. ✅ Install dependencies
2. ✅ Verify with test script
3. ✅ Try the quick example
4. 📖 Read [docs/USAGE.md](docs/USAGE.md) for more examples
5. 🔧 Integrate into your application
6. 🚀 Deploy to production

Happy recommending! 🎯
