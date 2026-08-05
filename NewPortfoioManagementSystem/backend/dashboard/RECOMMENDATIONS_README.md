# Stock Recommendation System - Technical Documentation

## Overview

The Stock Recommendation Engine is a hybrid recommendation system that combines **rule-based analysis** with **AI/ML models** to provide personalized stock recommendations. The system adapts to two scenarios:

1. **Existing Portfolio**: User has stocks → Similar & Complementary stocks
2. **Cold-Start (No Portfolio)**: New user → Popular stocks across market caps

---

## Architecture & Models

### 1. **Primary Data Sources**

| Source | Purpose | Fallback |
|--------|---------|----------|
| **yfinance** | Real-time fundamentals, price data | Primary (no fallback needed) |
| **AlphaVantage API** | Company overview (disabled - rate limited) | Disabled (free tier: 25 req/day) |

### 2. **Core Models**

#### **A. NewsAnalyzer (DistilBERT)**
- **Model**: `distilbert-base-uncased-finetuned-sst-2-english` (from HuggingFace)
- **Purpose**: Sentiment analysis on recent financial news
- **Process**:
  1. Fetch 5 recent news headlines for the stock (from yfinance news API)
  2. Run sentiment classification on each headline
  3. Convert sentiment labels to 0-100 scores
     - POSITIVE: `score * 100`
     - NEGATIVE: `(1 - score) * 100`
  4. Average the scores across headlines
  5. Default to 50 (neutral) if no news available
- **Output**: `sentiment_score` (0-100)
- **Dependency**: `transformers` library (HuggingFace)

#### **B. StockForecastingModel (LSTM or Simple)**
- **Primary Model**: LSTM (Long Short-Term Memory) neural network
  - **Architecture**:
    ```
    Input: Last 90 days of daily closing prices
    ↓
    Normalize prices to [0, 1] range
    ↓
    Create sequences: 30-day windows → next day prediction
    ↓
    LSTM Layer: 32 units with dropout (0.2)
    ↓
    Dense Layer: 1 output
    ↓
    Train: 5 epochs, batch size 4 (quick training)
    ↓
    Predict: Next 30-day trend score (0-100)
    ```
  - **Output**: `forecast_score` (0-100, represents expected 30-day direction)

- **Fallback Model**: Simple Exponential Smoothing (if TensorFlow unavailable)
  - **Logic**:
    ```
    recent_trend = (price_now - price_30days_ago) / price_30days_ago
    older_trend = (price_30days_ago - price_90days_ago) / price_90days_ago
    momentum = (recent_trend - older_trend) * 100
    forecast_score = 50 + momentum (clamped 0-100)
    ```
  - **Intuition**: If recent momentum > older momentum, expect uptrend

- **Dependency**: `tensorflow` (TensorFlow/Keras) or falls back to numpy/pandas

---

## Recommendation Scenarios

### Scenario 1: **Similar Stocks** (User has portfolio)

**Flow**:
```
User Portfolio (e.g., AAPL, MSFT, GOOGL)
    ↓
Fetch Fundamentals for each stock
    ↓
Feature Matrix (5 features per stock):
  - P/E Ratio
  - Beta (volatility)
  - Dividend Yield
  - Profit Margin
  - Return on Equity (ROE)
    ↓
Normalize features (StandardScaler)
    ↓
Compute Cosine Similarity between all pairs
    ↓
For each stock in portfolio, score all other stocks
  by how similar they are
    ↓
Rank by similarity score
    ↓
Return top N stocks
```

**Key Calculation**:
```python
# Cosine similarity formula (scikit-learn)
similarity = cos(angle) between normalized feature vectors
# Range: [0, 1] where 1 = identical fundamentals, 0 = opposite

# Scoring rule:
rule_score = sum of cosine similarities to all portfolio stocks
```

**Example**:
- User holds: AAPL (mega-cap, P/E=25, Beta=1.2, Div=0.4%)
- Recommendation: MSFT (similar P/E, Beta, but slightly higher cap)
- Score: 0.87 (high similarity)

---

### Scenario 2: **Complementary Stocks** (User has portfolio)

**Flow**:
```
User Portfolio sectors & characteristics
    ↓
Extract Portfolio Profile:
  - Average Beta (risk)
  - Average P/E Ratio
  - Sectors held
    ↓
Search 200+ stock universe
    ↓
Score each non-portfolio stock on:
  - Sector diversity (+3 if different sector)
  - Lower beta than portfolio (+2 if less risky)
  - Dividend yield (+1 if pays dividend)
    ↓
Rank by complementary score
    ↓
Return top N stocks
```

**Key Calculation**:
```python
complementary_score = 0
if stock_sector not in user_sectors:
    complementary_score += 3  # Diversification bonus
if stock_beta < portfolio_avg_beta:
    complementary_score += 2  # Lower risk bonus
if stock_dividend_yield > 0:
    complementary_score += 1  # Income bonus
```

**Example**:
- User holds: 3 Tech stocks (AAPL, MSFT, NVDA) with avg Beta=1.4
- Recommendation: JNJ (Healthcare sector, Beta=0.6, Dividend=2.4%)
- Score: 6 (diversity + low risk + dividend income)

---

### Scenario 3: **Popular Stocks** (Cold-Start, No Portfolio)

**Flow**:
```
User has NO portfolio history
    ↓
Fallback to "Popular Stocks" list (200+ curated stocks)
    ↓
Fetch fundamentals for each stock
    ↓
Calculate Live Data Scores:

  1. POPULARITY SCORE (Market Cap):
     Mega-cap (>$2T)      → 100
     Large-cap ($500B-$2T) → 95
     Mid-cap ($100B-$500B) → 85
     Small-cap             → 70

  2. QUALITY SCORE (P/E Ratio):
     P/E < 15  (undervalued)    → 95
     P/E 15-25 (fair value)     → 85
     P/E 25-35 (premium)        → 75
     P/E > 35  (expensive)      → 60

  3. RISK SCORE (Beta):
     Beta < 0.8  (low risk)     → 95
     Beta 0.8-1.2 (medium risk) → 85
     Beta > 1.2  (high risk)    → 75

  4. DIVIDEND SCORE (Yield):
     score = min(yield * 500, 100) or 50 if no dividend
    ↓
Combine with weights:
rule_score = (
    popularity * 0.35 +
    quality * 0.35 +
    risk * 0.20 +
    dividend * 0.10
)
    ↓
Return top N stocks by score
```

**Example**:
- Stock: JNJ (Meta-cap, P/E=26, Beta=0.65, Div=2.5%)
- Scores: Popularity=95, Quality=85, Risk=95, Dividend=88
- Final: (95×0.35) + (85×0.35) + (95×0.20) + (88×0.10) = 90.6

---

## AI Score Blending

Once rule-based scores are computed, AI models enhance the recommendations:

```python
# Step 1: Get AI scores
sentiment_score = NewsAnalyzer.analyze_sentiment(symbol)  # 0-100
forecast_score = StockForecastingModel.predict_returns(symbol)  # 0-100
combined_ai_score = sentiment_score * 0.4 + forecast_score * 0.6

# Step 2: Blend with rule-based score
if has_historical_data:
    final_score = rule_score * 0.6 + combined_ai_score * 0.4  # Favor rules
else:
    final_score = combined_ai_score  # Pure AI for cold-start

# Step 3: Re-rank by final score
recommendations.sort(key=lambda x: x['final_score'], reverse=True)
```

**Weighting Rationale**:
- `Sentiment: 40%` - News reflects market sentiment, but can be noisy
- `Forecast: 60%` - Price trends more predictive of direction than raw sentiment
- When portfolio exists: `Rule: 60%, AI: 40%` (rule-based more reliable with real holdings)
- When cold-start: `AI: 100%` (no historical portfolio to anchor on)

---

## Response Structure

### API Endpoint: `/get-recommendations` (GET)

**Response Format**:
```json
{
  "similar_stocks": [
    {
      "symbol": "MSFT",
      "name": "Microsoft Corporation",
      "sector": "Technology",
      "industry": "Software—Infrastructure",
      "pe_ratio": 30.2,
      "beta": 0.9,
      "market_cap": 2800000000000,
      "dividend_yield": 0.008,
      "profit_margin": 0.35,
      "return_on_equity": 0.45,
      "fifty_two_week_high": 456.78,
      "fifty_two_week_low": 290.0,
      "rule_score": 0.87,
      "similarity_score": 0.87,
      "ai_sentiment": 72.5,
      "ai_forecast": 68.3,
      "final_score": 75.4
    },
    ...
  ],
  "complementary_stocks": [
    {
      "symbol": "JNJ",
      ...
      "rule_score": 6,
      "similarity_score": 6,
      "ai_sentiment": 65.0,
      "ai_forecast": 70.0,
      "final_score": 68.5
    },
    ...
  ]
}
```

**Field Explanations**:
| Field | Source | Meaning |
|-------|--------|---------|
| `symbol` | yfinance | Stock ticker |
| `name` | yfinance | Company legal name |
| `sector` | yfinance | Industry sector |
| `pe_ratio` | yfinance | Price-to-earnings ratio |
| `beta` | yfinance | Volatility vs market (1.0 = market) |
| `rule_score` | Cosine similarity / complementary scoring | 0-1 or 0-10 range |
| `ai_sentiment` | DistilBERT sentiment analysis | 0-100 (higher = more positive news) |
| `ai_forecast` | LSTM/Simple forecasting | 0-100 (higher = bullish trend) |
| `final_score` | Blended rule + AI | 0-100 (final recommendation strength) |

---

## Caching Strategy

### Cache Layer (Django Cache)

```python
# Cache key structure:
cache_key = f"recommendations_portfolio_{portfolio_id}"
cache_ttl = 86400  # 24 hours

# Check cache on every request
cached_result = cache.get(cache_key)
if cached_result:
    return cached_result  # Cache hit

# Otherwise compute (cache miss)
result = generate_recommendations()
cache.set(cache_key, result, 86400)
return result
```

**Benefits**:
- ✅ Reduces API calls (yfinance, news endpoints)
- ✅ Faster response time (sub-100ms cached vs 5-30s live)
- ✅ Reduces rate-limit risk
- ✅ 24-hour recalculation keeps data fresh

**Invalidation**: Cache automatically expires after 24h; user can refresh manually

---

## Rate Limiting & Performance

### Rate Limiting Strategy

```python
# Every 5 API calls → pause 0.5 seconds
if (request_count + 1) % 5 == 0:
    time.sleep(0.5)

# Between feature fetches → pause 0.1 seconds
time.sleep(0.1)
```

**Rationale**:
- yfinance: ~50-100 req/min (our approach: ~12 req/min average)
- AlphaVantage: 25 req/day (DISABLED - too restrictive)
- NewsAPI: Embedded in yfinance (no extra calls)

### Performance Benchmarks

| Scenario | Cache | Time | Notes |
|----------|-------|------|-------|
| Similar stocks (3 holdings) | Hit | ~50ms | Instant |
| Similar stocks (3 holdings) | Miss | 8-12s | 3 fetches + 2 AI models |
| Complementary stocks | Hit | ~50ms | Instant |
| Complementary stocks | Miss | 30-60s | 30+ stock fetches + AI |
| Cold-start (popular) | Hit | ~50ms | Instant |
| Cold-start (popular) | Miss | 60-120s | 200+ stock fetches + AI |

---

## Dependencies & Libraries

### Required Packages

```
numpy              # Numerical operations
pandas             # DataFrames for stock data
scikit-learn       # Cosine similarity, StandardScaler
transformers       # HuggingFace DistilBERT for sentiment
torch              # PyTorch (required by transformers)
tensorflow         # Keras/LSTM for forecasting
yfinance           # Stock data fetching
alpha_vantage      # Fallback (currently disabled)
```

### Optional: Graceful Degradation

```python
# If TensorFlow unavailable → use simple exponential smoothing
try:
    from tensorflow import keras
    use_lstm = True
except ImportError:
    use_lstm = False
    # Falls back to _simple_forecast()

# If transformers unavailable → return neutral sentiment (50)
try:
    from transformers import pipeline
    sentiment_available = True
except ImportError:
    sentiment_available = False
    # Returns 50 for all stocks
```

---

## Example: Full Recommendation Flow

**User**: Has 2 stocks in portfolio (AAPL, MSFT)

### Step 1: Fetch Portfolio Data
```python
holdings = StockHolding.objects.filter(portfolio=user_portfolio)
# Returns: [AAPL, MSFT]
```

### Step 2: Build Feature Matrix
```
         PE_RATIO  BETA  DIV_YIELD  PROFIT_MARGIN  ROE
AAPL     28.5      1.2   0.004      0.35          0.45
MSFT     30.2      0.9   0.008      0.35          0.40
```

### Step 3: Normalize Features
```
Apply StandardScaler → center + unit variance
```

### Step 4: Compute Similarity
```
cosine_similarity(AAPL, MSFT) = 0.94  (very similar)
```

### Step 5: Score Candidates
```
GOOGL: similarity to AAPL (0.88) + similarity to MSFT (0.91) = 1.79
NVDA: similarity to AAPL (0.75) + similarity to MSFT (0.82) = 1.57
AMD:  similarity to AAPL (0.68) + similarity to MSFT (0.74) = 1.42
```

### Step 6: Fetch AI Scores
```
GOOGL sentiment: 75.0, forecast: 68.3
  → combined = 75*0.4 + 68.3*0.6 = 71.0

NVDA sentiment: 72.0, forecast: 65.0
  → combined = 72*0.4 + 65*0.6 = 68.0
```

### Step 7: Blend Scores
```
GOOGL final = rule_score(1.79) * 0.6 + ai_score(71) * 0.4 = 73.4
NVDA final = rule_score(1.57) * 0.6 + ai_score(68) * 0.4 = 68.2
AMD final = rule_score(1.42) * 0.6 + ai_score(70) * 0.4 = 70.4
```

### Step 8: Return Ranked
```
Rank 1: GOOGL (73.4)
Rank 2: AMD (70.4)
Rank 3: NVDA (68.2)
```

---

## Monitoring & Debugging

### Server Logs

```
[INFO] recommend_stocks: Portfolio stocks: ['AAPL', 'MSFT']
[INFO] build_stock_features_dataframe: Successfully fetched data for: ['AAPL', 'MSFT']
[INFO] compute_stock_similarity: Similarity matrix computed
[INFO] Computing AI model scores...
[INFO] NewsAnalyzer: Fetched 5 headlines for GOOGL
[INFO] StockForecastingModel: LSTM trained on 60 sequences
[INFO] Returning 10 similar stock recommendations
[SOURCES] Cosine similarity + AI models (DistilBERT, LSTM)
```

### Cache Hits/Misses

```
[CACHE HIT] Using cached similar stocks recommendations
[CACHE MISS] Recomputing recommendations (cache expired)
```

---

## Future Enhancements

1. **Sector-specific models**: Train separate LSTM per sector
2. **Portfolio correlation**: Add correlation coefficient scoring
3. **Momentum indicators**: Include RSI, MACD, Bollinger Bands
4. **Earnings announcements**: Weight by upcoming earnings dates
5. **Social sentiment**: Integrate Twitter/Reddit sentiment analysis
6. **Backtesting engine**: Validate recommendations against historical data

---

## References

- **yfinance**: https://github.com/ranaroussi/yfinance
- **DistilBERT**: Hugging Face model card (distilbert-base-uncased-finetuned-sst-2-english)
- **LSTM**: Hochreiter & Schmidhuber (1997), "Long Short-Term Memory"
- **Cosine Similarity**: https://scikit-learn.org/stable/modules/metrics.pairwise.html
- **Django Caching**: https://docs.djangoproject.com/en/stable/topics/cache/
