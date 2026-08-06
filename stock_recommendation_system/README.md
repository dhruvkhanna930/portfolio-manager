# Stock Recommendation System

A standalone, production-ready AI-powered stock recommendation system that provides intelligent stock recommendations using fundamental analysis, sentiment analysis, and ML-based price predictions.

## Features

### Core Recommendation Engine
- **Similar Stock Recommendations**: Find stocks similar to those in a user's portfolio based on fundamental metrics
- **Complementary Stock Recommendations**: Discover stocks that complement a portfolio (different sectors, lower volatility)
- **Risk Profile-Based Recommendations**: Generate recommendations based on risk profile (Conservative, Balanced, Assertive, Aggressive)

### AI Models & Analysis
- **Sentiment Analysis**: Uses DistilBERT transformer model for financial news sentiment analysis
- **LSTM Price Forecasting**: Deep learning model for 30-day return predictions
- **Trained ML Models**: 
  - GRU model for 1-day price movement prediction
  - LSTM model for 5-day price movement prediction
  - Trained on Qantas stock data, generalizable to other stocks

### Scoring System
Hybrid scoring approach combining:
- **Fundamental Analysis (40%)**: P/E ratio, Beta, dividend yield, profit margin, ROE
- **AI Sentiment (35%)**: News sentiment and price forecast analysis
- **Trained Models (25%)**: ML-based price movement predictions

## System Architecture

```
stock_recommendation_system/
├── recommendations.py          # Main recommendation logic
├── trained_models.py          # ML model loading and prediction
├── models/                    # Trained model files
│   ├── Qantas_GRU_trained_model_oneday.h5
│   └── Qantas_LSTM_trained_model_fivedays.h5
├── data/                      # Reference data
│   └── nasdaq-listed.csv
├── tests/                     # Test files
│   └── test_recommendations.py
├── examples/                  # Integration examples
│   └── example_integration.py
├── docs/                      # Documentation
│   ├── INSTALLATION.md
│   ├── USAGE.md
│   └── API.md
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Installation

See [INSTALLATION.md](docs/INSTALLATION.md) for detailed setup instructions.

### Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 3. Verify installation
python tests/test_recommendations.py
```

## Usage

### Basic Usage

```python
from recommendations import get_portfolio_recommendations

# Get recommendations for a portfolio
recommendations = get_portfolio_recommendations(
    portfolio_stocks=['AAPL', 'MSFT', 'GOOGL'],
    num_recommendations=10,
    use_ai=True
)

similar_stocks = recommendations['similar_stocks']
complementary_stocks = recommendations['complementary_stocks']

for stock in similar_stocks:
    print(f"{stock['symbol']}: {stock['final_score']:.2f} points")
```

### Advanced Usage

```python
from recommendations import (
    recommend_stocks,
    recommend_complementary_stocks,
    get_initial_recommendations_by_risk_profile
)

# Portfolio-based recommendations
similar = recommend_stocks(
    user_stocks=['AAPL', 'MSFT'],
    num_recommendations=5,
    use_ai=True
)

# Complementary recommendations
complementary = recommend_complementary_stocks(
    user_stocks=['AAPL', 'MSFT'],
    num_recommendations=5,
    use_ai=True
)

# Risk profile-based (no portfolio needed)
conservative_picks = get_initial_recommendations_by_risk_profile(
    risk_category='Conservative',
    num_recommendations=10,
    use_ai=True
)
```

See [USAGE.md](docs/USAGE.md) for more examples and [API.md](docs/API.md) for complete API documentation.

## Integration with Other Codebases

### Django Integration

```python
# In your Django app
from stock_recommendation_system.recommendations import get_portfolio_recommendations

def get_recommendations_view(request):
    user_portfolio = UserPortfolio.objects.get(user=request.user)
    stocks = [h.symbol for h in user_portfolio.holdings.all()]
    
    recommendations = get_portfolio_recommendations(
        portfolio_stocks=stocks,
        use_ai=True
    )
    
    return JsonResponse(recommendations)
```

### Standalone Python App

```python
import sys
sys.path.insert(0, '/path/to/stock_recommendation_system')

from recommendations import recommend_stocks

recommendations = recommend_stocks(
    user_stocks=['AAPL', 'MSFT'],
    use_ai=True
)
```

### Flask/FastAPI Integration

See [example_integration.py](examples/example_integration.py) for a complete FastAPI example.

## API Reference

### Main Functions

#### `get_portfolio_recommendations(portfolio_stocks, num_recommendations=10, use_ai=True)`
Get both similar and complementary recommendations for a portfolio.

**Parameters:**
- `portfolio_stocks` (list): List of stock symbols in the portfolio
- `num_recommendations` (int): Number of recommendations per category
- `use_ai` (bool): Whether to use AI models for enhanced scoring

**Returns:**
- `dict`: Contains `similar_stocks`, `complementary_stocks`, and `ai_models_used`

#### `recommend_stocks(portfolio_stocks, num_recommendations=10, use_ai=True)`
Recommend stocks similar to those in a portfolio.

**Parameters:**
- `portfolio_stocks` (list): List of stock symbols
- `num_recommendations` (int): Number of recommendations
- `use_ai` (bool): Enable AI enhancement

**Returns:**
- `list`: List of recommended stocks with scores

#### `recommend_complementary_stocks(portfolio_stocks, num_recommendations=10, use_ai=True)`
Recommend stocks that complement a portfolio.

**Parameters:**
- `portfolio_stocks` (list): List of stock symbols
- `num_recommendations` (int): Number of recommendations
- `use_ai` (bool): Enable AI enhancement

**Returns:**
- `list`: List of complementary stocks with scores

#### `get_initial_recommendations_by_risk_profile(risk_category, num_recommendations=10, use_ai=True)`
Get recommendations based on risk profile (no portfolio required).

**Parameters:**
- `risk_category` (str): One of 'Conservative', 'Balanced', 'Assertive', 'Aggressive'
- `num_recommendations` (int): Number of recommendations
- `use_ai` (bool): Enable AI enhancement

**Returns:**
- `list`: List of recommended stocks with scores

See [API.md](docs/API.md) for detailed API documentation.

## Recommendation Scores

Each recommendation includes multiple scores:

```python
{
    'symbol': 'AAPL',
    'name': 'Apple Inc.',
    'sector': 'Technology',
    'rule_score': 85.3,              # Fundamental analysis score (0-100)
    'ai_sentiment': 72.5,            # News sentiment score
    'ai_forecast': 68.2,             # Price forecast score
    'ai_score': 70.35,               # Combined AI score
    'trained_model_1day': 65.2,      # GRU 1-day prediction
    'trained_model_5day': 72.8,      # LSTM 5-day prediction
    'trained_model_score': 69.3,     # Combined model score
    'final_score': 74.56,            # Blended final score
    'pe_ratio': 24.5,
    'beta': 1.2,
    'dividend_yield': 0.004,
    # ... other fundamental metrics
}
```

## Model Information

### Trained Models
- **GRU 1-Day Model**: Predicts 1-day price movements using 30-day lookback window
- **LSTM 5-Day Model**: Predicts 5-day returns using 60-day lookback window
- **Training Data**: Qantas (QAN) historical price data
- **Normalization**: Min-max scaling within each prediction window

### AI Models
- **Sentiment Analysis**: DistilBERT (distilbert-base-uncased-finetuned-sst-2-english)
- **News Source**: Yahoo Finance news data via yfinance
- **LSTM Forecasting**: 32-unit LSTM with dropout, trained on recent price data

## Environment Variables

Create a `.env` file with:

```env
# Alpha Vantage API Keys (for fallback fundamental data)
ALPHAVANTAGE_KEY1=your_key_1
ALPHAVANTAGE_KEY2=your_key_2
ALPHAVANTAGE_KEY3=your_key_3
ALPHAVANTAGE_KEY4=your_key_4
ALPHAVANTAGE_KEY5=your_key_5
ALPHAVANTAGE_KEY6=your_key_6
ALPHAVANTAGE_KEY7=your_key_7

# Optional: Logging
LOG_LEVEL=INFO
```

Note: Alpha Vantage keys are optional. The system works with yfinance as the primary data source.

## Error Handling & Fallbacks

The system is designed with graceful fallbacks:

1. **Missing Data**: Returns default score of 50 if fundamental data unavailable
2. **Model Loading Failure**: Falls back to AI sentiment + forecasting if trained models unavailable
3. **Sentiment Analysis**: Uses default score if transformers library not installed
4. **Price Forecasting**: Uses exponential smoothing if TensorFlow not available
5. **API Rate Limits**: Implements random key rotation for Alpha Vantage

## Testing

Run the comprehensive test suite:

```bash
python tests/test_recommendations.py
```

This tests:
- Dependencies installation
- Stock data fetching
- Fundamentals retrieval
- Sentiment analysis
- Price forecasting
- Similarity scoring
- Hybrid score blending

## Performance Considerations

### Data Fetching
- Stock fundamentals: ~0.5-1 second per stock
- Historical prices: ~0.5 second per stock (cached by yfinance)
- News sentiment: ~2-3 seconds per stock (requires API calls)

### Model Predictions
- Trained models: ~0.1 second per stock
- LSTM forecasting: ~0.5 second per stock

### Optimization Tips
1. **Batch Processing**: Process multiple stocks in parallel
2. **Caching**: Cache fundamental data for 24 hours
3. **AI Model Toggle**: Use `use_ai=False` for faster recommendations
4. **Model Selection**: Use trained models only if TensorFlow available

## Troubleshooting

### Models Not Loading
```
⚠ GRU model skipped (TensorFlow compatibility)
```
**Solution**: Ensure TensorFlow version matches the model's training version. See INSTALLATION.md.

### Rate Limiting
```
429 Too Many Requests
```
**Solution**: The system automatically rotates API keys. Add more Alpha Vantage keys to `.env`.

### Memory Issues
```
MemoryError during sentiment analysis
```
**Solution**: Disable sentiment analysis (`use_ai=False`) or process fewer stocks at once.

## Contributing

To extend the system:

1. Add new scoring functions in `recommendations.py`
2. Integrate new data sources in `get_stock_fundamentals()`
3. Train new ML models and add to `trained_models.py`
4. Update documentation in the `docs/` directory

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or feature requests, please check:
1. [INSTALLATION.md](docs/INSTALLATION.md) - Setup issues
2. [USAGE.md](docs/USAGE.md) - How-to questions
3. [API.md](docs/API.md) - API reference
4. Test the system with `python tests/test_recommendations.py`

## Changelog

### Version 1.0.0
- Initial release with portfolio-based recommendations
- Sentiment analysis and price forecasting
- Trained GRU and LSTM models
- Risk profile-based recommendations
- Comprehensive documentation and examples
