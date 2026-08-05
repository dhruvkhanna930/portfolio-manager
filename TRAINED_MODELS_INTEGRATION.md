# Trained Models Integration - Stock Recommendation System

## Overview
The portfolio management system now integrates pre-trained LSTM and GRU models for enhanced stock price movement prediction, combining it with existing fundamental analysis and sentiment analysis for comprehensive recommendations.

## Trained Models Included

### 1. **LSTM 5-Day Model** (`Qantas_LSTM_trained_model_fivedays.h5`)
   - **Purpose**: Predicts 5-day stock price movements
   - **Input**: Normalized historical price sequences (60-day lookback)
   - **Output**: Price movement prediction score (0-100)
   - **Use Case**: Mid-term trend prediction

### 2. **GRU 1-Day Model** (`Qantas_GRU_trained_model_oneday.h5`)
   - **Purpose**: Predicts 1-day stock price movements  
   - **Input**: Normalized historical price sequences (30-day lookback)
   - **Output**: Price movement prediction score (0-100)
   - **Use Case**: Short-term momentum detection

## Architecture

### New Module: `dashboard/trained_models.py`
- **TrainedModelPredictor Class**: 
  - Loads both trained models on initialization
  - Fetches live historical data using `yfinance`
  - Normalizes price data for model input
  - Generates predictions with error handling
  - Returns 50.0 (neutral score) if models are unavailable

- **Key Methods**:
  - `prepare_sequence_data()`: Fetches 3-month historical data and normalizes it
  - `predict_1day_return()`: GRU-based prediction
  - `predict_5day_return()`: LSTM-based prediction
  - `get_model_predictions()`: Combined prediction with availability flag

### Updated: `dashboard/recommendations.py`
- Imports the trained models integration
- Enhanced `recommend_stocks()` function:
  - Computes trained model predictions for all recommended stocks
  - Blends scores: Fundamental (40%) + AI Sentiment (35%) + Trained Models (25%)
  
- Enhanced `recommend_complementary_stocks()` function:
  - Same scoring weights and blending strategy
  
- Updated `get_portfolio_recommendations()`:
  - Returns metadata about all AI models used
  - Includes scoring weights for transparency

## Recommendation Scoring Formula

```
Final Score = (Fundamental Score × 0.40) + 
              (AI Sentiment Score × 0.35) + 
              (Trained Model Score × 0.25)

Where:
- Fundamental Score: Based on cosine similarity of stock fundamentals
- AI Sentiment Score: DistilBERT sentiment + LSTM forecast blend
- Trained Model Score: Combined 1-day (40%) + 5-day (60%) predictions
```

## Data Flow for Stock Recommendations

```
1. User requests recommendations via /dashboard/get-recommendations/
2. System gets user's portfolio holdings
3. For each stock:
   a. Fetch fundamentals from yfinance
   b. Calculate cosine similarity scores
   c. Fetch historical prices from yfinance
   d. Normalize price sequences
   e. Run through trained LSTM/GRU models
   f. Analyze sentiment from recent news
   g. Blend all scores with specified weights
4. Return top recommendations sorted by final score
```

## Response Format

Each recommendation includes:

```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "sector": "Technology",
  "pe_ratio": 28.5,
  "beta": 1.2,
  "rule_score": 0.85,
  "ai_sentiment": 65.3,
  "ai_forecast": 72.1,
  "ai_score": 70.2,
  "trained_model_1day": 65.0,
  "trained_model_5day": 68.5,
  "trained_model_score": 67.1,
  "final_score": 68.9
}
```

## Features

### ✓ Live API Integration
- Fetches real-time stock data from yfinance
- Normalizes data for model input
- Updates predictions on each request

### ✓ Graceful Degradation
- If models fail to load, returns neutral score (50.0)
- If data unavailable, falls back to fundamental analysis
- Maintains recommendations even if any component fails

### ✓ Transparent Scoring
- All sub-scores visible in API response
- Clear weighting of different factors
- Users can understand recommendation rationale

### ✓ Scalable Design
- Easy to add new models
- Configurable weight parameters
- Supports multiple ML approaches simultaneously

## Testing

Run the test script to verify integration:
```bash
cd NewPortfoioManagementSystem/backend
python test_trained_models.py
```

This will test:
1. Model loading and availability
2. Prediction generation on sample stocks
3. Integration with recommendation system
4. Response format with all model scores

## Handling TensorFlow Version Compatibility

The trained models were created with an older TensorFlow version. The integration includes:
- Graceful error handling for loading failures
- Fallback to neutral predictions (50.0)
- Continued functionality of fundamental + sentiment analysis
- Future model updates can replace the H5 files without code changes

To load models with newer TensorFlow versions, consider:
1. Converting models to SavedModel format
2. Retraining with current TensorFlow version
3. Using ONNX for format-agnostic inference

## Performance Considerations

- **Model Loading**: Done once per request (can be optimized with caching)
- **Data Fetching**: yfinance API calls are made for each stock prediction
- **Prediction Time**: < 1 second per stock (depends on network)

### Future Optimization
- Cache model instances in Django cache
- Batch predictions for multiple stocks
- Async model predictions with Celery

## API Endpoint

**GET** `/dashboard/get-recommendations/`

Returns comprehensive recommendations including:
- Similar stocks (based on portfolio holdings)
- Complementary stocks (for diversification)
- All model metadata and weights

## Environment Requirements

Ensure `.env` file contains:
```
ALPHAVANTAGE_KEY=your_api_key
NEWSAPI_KEY=your_api_key
```

## Next Steps

1. **Add more trained models**: Customize for different sectors/time horizons
2. **Optimize model loading**: Use model caching to reduce latency
3. **Add backtesting**: Validate recommendation performance historically
4. **Implement feedback loop**: Track recommendation accuracy for users
5. **Mobile app integration**: Expose recommendations via REST API
