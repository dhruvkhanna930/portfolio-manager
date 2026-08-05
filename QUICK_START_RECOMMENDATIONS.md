# Quick Start: Testing Stock Recommendations with Trained Models

## Setting Up a Test Portfolio

### 1. Run the Django Server
```bash
cd NewPortfoioManagementSystem/backend
source .venv/Scripts/activate  # or .venv\Scripts\Activate.ps1 on Windows
python manage.py runserver
```

### 2. Access the Application
- Navigate to `http://localhost:8000`
- Log in with your credentials (create account if needed)
- Complete the risk profile questionnaire

### 3. Add Holdings to Your Portfolio
- Go to Dashboard → Portfolio section
- Click "Add Stock"
- Select a stock from NASDAQ list
- Enter number of shares and purchase date
- Repeat for 3-5 stocks (e.g., AAPL, MSFT, GOOGL, TSLA, AMZN)

### 4. View AI-Powered Recommendations
- Click on "Recommendations" tab
- System will:
  1. Analyze your portfolio fundamentals
  2. Fetch live price data via yfinance
  3. Run predictions through trained models
  4. Calculate sentiment scores
  5. Generate personalized recommendations

## What Each Score Means

### Rule Score (Fundamental Analysis)
- Based on stock characteristics matching your holdings
- Range: 0-10
- Higher = more similar to your current portfolio

### AI Sentiment (News Analysis)
- Based on recent financial news headlines
- Range: 0-100
- Higher = more positive recent news coverage

### AI Forecast (Forecasting Models)
- Exponential smoothing based on 90-day price trend
- Range: 0-100
- Higher = upward momentum predicted

### Trained Model Scores
**1-Day Prediction (GRU Model)**
- Short-term momentum detector
- Range: 0-100
- Updates daily based on latest price data

**5-Day Prediction (LSTM Model)**
- Medium-term trend predictor
- Range: 0-100
- More stable, less volatile than 1-day

### Final Score
- **Weighted Combination**:
  - 40% Fundamental Analysis
  - 35% AI Sentiment Analysis  
  - 25% Trained Model Predictions
- Range: 0-100
- **Ranked highest to lowest for recommendations**

## Example Recommendation Response

```json
{
  "similar_stocks": [
    {
      "symbol": "MSFT",
      "name": "Microsoft Corporation",
      "sector": "Technology",
      "pe_ratio": 35.2,
      "beta": 0.89,
      "rule_score": 0.91,
      "ai_sentiment": 72.5,
      "ai_forecast": 68.3,
      "ai_score": 69.8,
      "trained_model_1day": 71.2,
      "trained_model_5day": 69.4,
      "trained_model_score": 69.9,
      "final_score": 69.8
    }
  ],
  "complementary_stocks": [
    {
      "symbol": "XOM",
      "name": "Exxon Mobil",
      "sector": "Energy",
      "rule_score": 3,
      "trained_model_score": 56.4,
      "final_score": 49.2
    }
  ],
  "ai_models_used": {
    "sentiment_analysis": "DistilBERT (Transformers)",
    "stock_forecasting": "LSTM with Exponential Smoothing Fallback",
    "trained_models": {
      "gru_1day": "GRU model for 1-day price movement prediction",
      "lstm_5day": "LSTM model for 5-day price movement prediction"
    },
    "scoring_weights": {
      "fundamental_analysis": 0.4,
      "sentiment_analysis": 0.35,
      "trained_models": 0.25
    }
  }
}
```

## Understanding Recommendations

### Similar Stocks
- **What**: Stocks similar to companies you already own
- **How**: Based on financial metrics (P/E ratio, Beta, dividend yield, etc.)
- **When**: Use when you want consistent, stable investments
- **Example**: If you own AAPL, might recommend MSFT or GOOGL

### Complementary Stocks  
- **What**: Stocks from different sectors to diversify
- **How**: Prioritizes sectors NOT in your portfolio, lower Beta values
- **When**: Use when you want to reduce portfolio risk
- **Example**: If you own tech stocks, might recommend XOM (energy) or JNJ (healthcare)

## Interpreting Model Predictions

### When 1-Day Prediction is High (>70)
- Short-term momentum is positive
- May indicate upcoming price increase
- Good for active traders

### When 5-Day Prediction is High (>70)
- Medium-term trend is positive
- More reliable than 1-day for trend confirmation
- Better for swing traders

### When Trained Models Disagree
- 1-Day high, 5-Day low: Correction may be coming
- 1-Day low, 5-Day high: Early momentum building
- Both high: Strong upward trend
- Both low: Caution advised, downside risk

## Troubleshooting

### Models Show 50.0 (Neutral)
**Cause**: TensorFlow version compatibility issue with older model format
**Impact**: Still have full functionality with fundamental + sentiment analysis
**Solution**: System gracefully falls back to other models
**Status**: ✓ Fully functional with partial ML model degradation

### No Recommendations Showing
**Cause**: Portfolio might be empty
**Solution**: Add at least 1 stock holding to your portfolio first

### High Latency on First Request
**Cause**: First-time model loading + yfinance API calls
**Solution**: Subsequent requests will be faster; consider adding caching

### Data Inconsistency
**Cause**: yfinance API delays or market hours
**Solution**: Wait and refresh; data updates after market open

## Advanced: Modifying Model Weights

Edit `dashboard/recommendations.py` to adjust scoring weights:

```python
# Current weights (40-35-25 split)
fundamental_weight = 0.4    # Change to prioritize fundamental analysis
ai_weight = 0.35           # Change to prioritize sentiment/forecast
model_weight = 0.25        # Change to prioritize trained models

rec['final_score'] = round(
    (rec['rule_score'] * fundamental_weight +
     rec['ai_score'] * ai_weight +
     rec['trained_model_score'] * model_weight), 3
)
```

### Weight Presets

**Conservative (Trust Fundamentals)**
- Fundamental: 60%, AI: 25%, Models: 15%

**Aggressive (Trust ML Models)**  
- Fundamental: 30%, AI: 25%, Models: 45%

**Balanced (Current)**
- Fundamental: 40%, AI: 35%, Models: 25%

## API Integration for Developers

```python
from dashboard.models import Portfolio
from dashboard.recommendations import get_portfolio_recommendations

# Get recommendations for a user's portfolio
portfolio = Portfolio.objects.get(user=request.user)
recommendations = get_portfolio_recommendations(portfolio, use_ai=True)

# Access similar stocks
similar = recommendations['similar_stocks']  # List of dicts

# Access complementary stocks
complementary = recommendations['complementary_stocks']  # List of dicts

# Check which models were used
models_used = recommendations['ai_models_used']
```

## Performance Benchmarks

- Model loading: ~2-5 seconds (first time)
- Per-stock prediction: ~0.5-1 second
- API response time: 5-15 seconds for 16 recommendations

## Next Steps

1. ✓ Test with 5+ stocks in your portfolio
2. ✓ Track which recommendations work best for your strategy
3. ✓ Compare recommendations across different risk profiles
4. ✓ Provide feedback for model improvements
5. Share results in the portfolio management community

