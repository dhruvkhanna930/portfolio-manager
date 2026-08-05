# API Reference

## Overview

The stock recommendation system provides several core functions and utility functions for generating stock recommendations.

## Core Functions

### `get_portfolio_recommendations(portfolio, num_recommendations=10, use_ai=True)`

Get both similar and complementary stock recommendations for a portfolio.

**Parameters:**
- `portfolio` (list of str): List of stock symbols in the portfolio (e.g., ['AAPL', 'MSFT', 'GOOGL'])
- `num_recommendations` (int, optional): Number of recommendations per category. Default: 10
- `use_ai` (bool, optional): Whether to use AI models for enhanced scoring. Default: True

**Returns:**
- `dict`: Dictionary containing:
  - `similar_stocks` (list): Similar stocks to those in portfolio
  - `complementary_stocks` (list): Stocks that complement the portfolio
  - `ai_models_used` (dict): Information about AI models used (only if use_ai=True)

**Example:**
```python
recommendations = get_portfolio_recommendations(
    portfolio=['AAPL', 'MSFT'],
    num_recommendations=5,
    use_ai=True
)

print(f"Similar: {len(recommendations['similar_stocks'])}")
print(f"Complementary: {len(recommendations['complementary_stocks'])}")
```

**Raises:**
- No exceptions. Returns empty lists if no recommendations can be generated.

---

### `recommend_stocks(portfolio, num_recommendations=10, use_ai=True)`

Recommend stocks that are similar to those in the user's portfolio based on fundamental metrics.

**Parameters:**
- `portfolio` (list of str): List of stock symbols in the portfolio
- `num_recommendations` (int, optional): Number of recommendations. Default: 10
- `use_ai` (bool, optional): Whether to use AI models. Default: True

**Returns:**
- `list`: List of recommendation dictionaries. Each contains:
  - `symbol` (str): Stock symbol
  - `name` (str): Company name
  - `sector` (str): Industry sector
  - `pe_ratio` (float): Price-to-earnings ratio
  - `beta` (float): Stock volatility measure
  - `dividend_yield` (float): Annual dividend yield
  - `profit_margin` (float): Profit margin
  - `return_on_equity` (float): ROE
  - `fifty_two_week_high` (float): 52-week high price
  - `fifty_two_week_low` (float): 52-week low price
  - `rule_score` (float): Fundamental analysis score (0-100)
  - `ai_sentiment` (float): News sentiment score (0-100, if use_ai=True)
  - `ai_forecast` (float): Price forecast score (0-100, if use_ai=True)
  - `ai_score` (float): Combined AI score (0-100, if use_ai=True)
  - `trained_model_1day` (float): 1-day prediction score (0-100, if available)
  - `trained_model_5day` (float): 5-day prediction score (0-100, if available)
  - `trained_model_score` (float): Combined model score (0-100, if available)
  - `final_score` (float): Final blended score (0-100)

**Example:**
```python
similar = recommend_stocks(['AAPL', 'MSFT'], num_recommendations=5)
for stock in similar:
    print(f"{stock['symbol']}: {stock['final_score']:.2f}")
```

---

### `recommend_complementary_stocks(portfolio, num_recommendations=10, use_ai=True)`

Recommend stocks that complement the portfolio (different sectors, lower risk, etc.).

**Parameters:**
- `portfolio` (list of str): List of stock symbols in the portfolio
- `num_recommendations` (int, optional): Number of recommendations. Default: 10
- `use_ai` (bool, optional): Whether to use AI models. Default: True

**Returns:**
- `list`: List of recommendation dictionaries (same format as `recommend_stocks()`)

**Example:**
```python
complementary = recommend_complementary_stocks(['AAPL', 'MSFT'])
high_dividend = [s for s in complementary if s['dividend_yield'] > 0.03]
```

---

### `get_initial_recommendations_by_risk_profile(risk_category, num_recommendations=10, use_ai=True)`

Generate stock recommendations based on risk profile without requiring a portfolio.

**Parameters:**
- `risk_category` (str): Risk profile category. Options: 
  - `'Conservative'`: Low P/E, low beta, high dividend yield
  - `'Balanced'`: Moderate P/E and beta, solid profit margins
  - `'Assertive'`: Growth-oriented, higher P/E acceptable
  - `'Aggressive'`: High growth, high risk acceptable
- `num_recommendations` (int, optional): Number of recommendations. Default: 10
- `use_ai` (bool, optional): Whether to use AI models. Default: True

**Returns:**
- `list`: List of recommendation dictionaries (same format as `recommend_stocks()`)

**Example:**
```python
conservative_picks = get_initial_recommendations_by_risk_profile(
    risk_category='Conservative',
    num_recommendations=10
)

for stock in conservative_picks:
    print(f"{stock['symbol']}: P/E={stock['pe_ratio']:.1f}, Div={stock['dividend_yield']:.2%}")
```

---

## Utility Functions

### `get_stock_fundamentals(symbol)`

Fetch fundamental data for a single stock.

**Parameters:**
- `symbol` (str): Stock symbol (e.g., 'AAPL')

**Returns:**
- `dict`: Dictionary containing:
  - `symbol` (str)
  - `name` (str)
  - `sector` (str)
  - `industry` (str)
  - `pe_ratio` (float)
  - `beta` (float)
  - `market_cap` (float)
  - `dividend_yield` (float)
  - `profit_margin` (float)
  - `return_on_equity` (float)
  - `fifty_two_week_high` (float)
  - `fifty_two_week_low` (float)
- `None`: If data cannot be fetched

**Example:**
```python
fundamentals = get_stock_fundamentals('AAPL')
if fundamentals:
    print(f"{fundamentals['name']}: P/E = {fundamentals['pe_ratio']}")
```

---

### `build_stock_features_dataframe(symbols_list)`

Build a pandas DataFrame of stock features for multiple stocks.

**Parameters:**
- `symbols_list` (list of str): List of stock symbols

**Returns:**
- `tuple`: (dataframe, valid_symbols) where:
  - `dataframe` (pd.DataFrame): DataFrame with stock features or None if no data
  - `valid_symbols` (list): List of symbols with successfully fetched data

**Example:**
```python
df, valid_symbols = build_stock_features_dataframe(['AAPL', 'MSFT', 'INVALID'])
print(f"Fetched data for: {valid_symbols}")  # ['AAPL', 'MSFT']
```

---

### `compute_stock_similarity(stocks_df)`

Compute similarity matrix between stocks based on fundamental metrics.

**Parameters:**
- `stocks_df` (pd.DataFrame): DataFrame with stock fundamentals (from `build_stock_features_dataframe`)

**Returns:**
- `np.ndarray`: Similarity matrix (n_stocks x n_stocks) with values between 0 and 1

**Example:**
```python
df, symbols = build_stock_features_dataframe(['AAPL', 'MSFT', 'GOOGL'])
similarity = compute_stock_similarity(df)
print(f"AAPL-MSFT similarity: {similarity[0][1]:.2f}")
```

---

### `compute_ai_model_scores(symbols_list)`

Compute AI model scores (sentiment and forecasting) for a list of stocks.

**Parameters:**
- `symbols_list` (list of str): List of stock symbols

**Returns:**
- `dict`: Dictionary with symbol keys, each containing:
  - `sentiment` (float): News sentiment score (0-100)
  - `forecast` (float): Price forecast score (0-100)
  - `combined` (float): Combined AI score (0-100)

**Example:**
```python
ai_scores = compute_ai_model_scores(['AAPL', 'MSFT'])
for symbol, scores in ai_scores.items():
    print(f"{symbol}: Sentiment={scores['sentiment']:.0f}, Forecast={scores['forecast']:.0f}")
```

---

## Trained Models Functions

### `compute_trained_model_scores(symbols_list)`

Compute predictions from pre-trained LSTM/GRU models for a list of stocks.

**Parameters:**
- `symbols_list` (list of str): List of stock symbols

**Returns:**
- `dict`: Dictionary with symbol keys, each containing:
  - `1day` (float): 1-day prediction score (0-100)
  - `5day` (float): 5-day prediction score (0-100)
  - `combined` (float): Combined model score (0-100)
  - `available` (bool): Whether trained models were available

**Example:**
```python
from trained_models import compute_trained_model_scores

model_scores = compute_trained_model_scores(['AAPL', 'MSFT'])
for symbol, scores in model_scores.items():
    if scores['available']:
        print(f"{symbol}: 1-day={scores['1day']:.0f}, 5-day={scores['5day']:.0f}")
```

---

### `TrainedModelPredictor`

Class for loading and using pre-trained models.

**Constructor:**
```python
from trained_models import TrainedModelPredictor

predictor = TrainedModelPredictor()
```

**Methods:**

#### `predict_1day_return(ticker: str) -> float`
Predict 1-day return for a stock using GRU model.

**Parameters:**
- `ticker` (str): Stock symbol

**Returns:**
- `float`: Prediction score (0-100). Returns 50 if model unavailable.

---

#### `predict_5day_return(ticker: str) -> float`
Predict 5-day return for a stock using LSTM model.

**Parameters:**
- `ticker` (str): Stock symbol

**Returns:**
- `float`: Prediction score (0-100). Returns 50 if model unavailable.

---

#### `get_model_predictions(ticker: str) -> dict`
Get both 1-day and 5-day predictions for a stock.

**Parameters:**
- `ticker` (str): Stock symbol

**Returns:**
- `dict`:
  - `1day` (float): 1-day prediction score
  - `5day` (float): 5-day prediction score
  - `combined` (float): Combined score (40% 1-day + 60% 5-day)
  - `available` (bool): Whether models were successfully loaded

**Example:**
```python
predictor = TrainedModelPredictor()
predictions = predictor.get_model_predictions('AAPL')
print(f"1-day: {predictions['1day']}, 5-day: {predictions['5day']}")
```

---

## Data Models

### Recommendation Dictionary Format

Every recommendation returned includes the following fields:

```python
{
    # Identification
    'symbol': 'AAPL',           # Stock ticker symbol
    'name': 'Apple Inc.',       # Company name
    'sector': 'Technology',     # Industry sector
    'industry': 'Consumer Electronics',  # Specific industry
    
    # Fundamental Metrics
    'pe_ratio': 24.5,           # Price-to-earnings ratio
    'beta': 1.2,                # Volatility measure (1.0 = market)
    'market_cap': 2.8e12,       # Market capitalization in dollars
    'dividend_yield': 0.004,    # Annual dividend as % of price
    'profit_margin': 0.25,      # Net profit margin
    'return_on_equity': 0.85,   # Return on equity
    'fifty_two_week_high': 195.5,   # 52-week high price
    'fifty_two_week_low': 124.2,    # 52-week low price
    
    # Scoring
    'rule_score': 85.3,         # Fundamental analysis score (0-100)
    'ai_sentiment': 72.5,       # News sentiment score (0-100)
    'ai_forecast': 68.2,        # Price forecast score (0-100)
    'ai_score': 70.35,          # Combined AI score (0-100)
    'trained_model_1day': 65.2,    # 1-day prediction score (0-100)
    'trained_model_5day': 72.8,    # 5-day prediction score (0-100)
    'trained_model_score': 69.3,   # Combined model score (0-100)
    'final_score': 74.56        # Final blended score (0-100)
}
```

---

## Error Handling

All functions are designed with graceful error handling:

1. **Missing Data**: If fundamental data unavailable, returns default score of 50
2. **API Failures**: Automatically falls back to alternative data sources
3. **Model Loading**: Proceeds without models if TensorFlow unavailable
4. **Rate Limiting**: Implements key rotation for API calls

**Example of safe usage:**
```python
from recommendations import get_portfolio_recommendations

try:
    recommendations = get_portfolio_recommendations(['AAPL', 'INVALID'])
    if not recommendations['similar_stocks']:
        print("No recommendations generated - may indicate data issues")
except Exception as e:
    print(f"Error: {e}")
```

---

## Performance Characteristics

### Execution Time Estimates (5-10 stocks)

| Operation | Time | Notes |
|-----------|------|-------|
| Rule-based only | 5-10s | No AI or models |
| + AI Sentiment | +20-30s | Requires API calls |
| + AI Forecasting | +5-10s | Local computation |
| + Trained Models | +2-5s | Model predictions |
| Full (all features) | 30-60s | Depends on API availability |

### Memory Requirements

- **Models**: ~500MB (if TensorFlow loaded)
- **Data Processing**: ~100MB per 100 stocks
- **Recommendation Processing**: ~50MB baseline

---

## Configuration

### Environment Variables

```env
# Alpha Vantage API Keys (optional, for fallback data)
ALPHAVANTAGE_KEY1=YOUR_KEY
ALPHAVANTAGE_KEY2=YOUR_KEY
...

# Django-specific (if used)
DEBUG=False
ALLOWED_HOSTS=localhost,example.com
```

### Model Paths

Models are loaded from relative paths:
- GRU 1-day: `../Qantas_GRU_trained_model_oneday.h5`
- LSTM 5-day: `../Qantas_LSTM_trained_model_fivedays.h5`

Adjust in `trained_models.py` if moving model files.

---

## Versioning & Compatibility

**Current Version**: 1.0.0

**Python**: 3.8+
**TensorFlow**: 2.13.0+
**scikit-learn**: 1.2.0+
**pandas**: 1.5.0+

---

## See Also

- [INSTALLATION.md](INSTALLATION.md) - Setup instructions
- [USAGE.md](USAGE.md) - Usage examples
- [README.md](../README.md) - Project overview
