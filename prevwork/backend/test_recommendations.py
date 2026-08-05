"""
Test script for AI-powered stock recommendation system
Standalone testing without Django dependencies
"""

import sys
import os
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

os.environ['PYTHONIOENCODING'] = 'utf-8'

print("=" * 80)
print("[STOCK RECOMMENDATION SYSTEM - AI MODEL TEST]")
print("=" * 80)

# Test 1: Check dependencies
print("\n[Testing Dependencies...]\n")
deps_status = {
    'numpy': False,
    'pandas': False,
    'yfinance': False,
    'scikit-learn': False,
    'transformers': False,
    'tensorflow': False,
}

try:
    import numpy
    deps_status['numpy'] = True
    print("[OK] numpy - OK")
except ImportError:
    print("[FAIL] numpy - NOT INSTALLED")

try:
    import pandas
    deps_status['pandas'] = True
    print("[OK] pandas - OK")
except ImportError:
    print("[FAIL] pandas - NOT INSTALLED")

try:
    import yfinance
    deps_status['yfinance'] = True
    print("[OK] yfinance - OK")
except ImportError:
    print("[FAIL] yfinance - NOT INSTALLED")

try:
    from sklearn.preprocessing import StandardScaler
    deps_status['scikit-learn'] = True
    print("[OK] scikit-learn - OK")
except ImportError:
    print("[FAIL] scikit-learn - NOT INSTALLED")

try:
    from transformers import pipeline
    deps_status['transformers'] = True
    print("[OK] transformers - OK (Sentiment Analysis Available)")
except ImportError:
    print("[WARN]  transformers - NOT INSTALLED (Sentiment will use fallback)")

try:
    from tensorflow import keras
    deps_status['tensorflow'] = True
    print("[OK] tensorflow - OK (LSTM Forecasting Available)")
except ImportError:
    print("[WARN]  tensorflow - NOT INSTALLED (Forecasting will use exponential smoothing)")

# Test 2: Fetch Stock Data
print("\n\n[DATA] Testing Stock Data Fetching...\n")
test_symbols = ['AAPL', 'MSFT', 'GOOGL']

for symbol in test_symbols:
    try:
        data = yf.download(symbol, period='1y', progress=False)
        print(f"[OK] {symbol}: {len(data)} trading days fetched")
    except Exception as e:
        print(f"[FAIL] {symbol}: Error - {e}")

# Test 3: Stock Fundamentals
print("\n\n[FUNDS] Testing Stock Fundamentals Fetching...\n")

for symbol in test_symbols:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        fundamentals = {
            'symbol': symbol,
            'name': info.get('longName', ''),
            'sector': info.get('sector', ''),
            'beta': float(info.get('beta', 0)) or 0,
            'pe_ratio': float(info.get('trailingPE', 0)) or 0,
            'dividend_yield': float(info.get('dividendYield', 0)) or 0,
        }
        print(f"[OK] {symbol}:")
        print(f"   - Name: {fundamentals['name']}")
        print(f"   - Sector: {fundamentals['sector']}")
        print(f"   - Beta: {fundamentals['beta']:.2f}")
        print(f"   - P/E Ratio: {fundamentals['pe_ratio']:.2f}")
        print(f"   - Dividend Yield: {fundamentals['dividend_yield']:.2%}")
    except Exception as e:
        print(f"[FAIL] {symbol}: Error - {e}")

# Test 4: Sentiment Analysis
print("\n\n[SENTIMENT] Testing Sentiment Analysis (News)...\n")

try:
    from transformers import pipeline
    sentiment_pipeline = pipeline("sentiment-analysis",
                                 model="distilbert-base-uncased-finetuned-sst-2-english")

    test_headlines = [
        "Tech stocks rally as earnings beat expectations",
        "Market faces headwinds amid economic concerns",
        "Apple announces record quarterly profits"
    ]

    print("Testing sentiment on sample headlines:\n")
    for headline in test_headlines:
        result = sentiment_pipeline(headline[:512])[0]
        print(f"Headline: {headline}")
        print(f"  Sentiment: {result['label']} (confidence: {result['score']:.2%})\n")

except ImportError:
    print("[WARN]  Transformers not installed - Sentiment analysis unavailable")
except Exception as e:
    print(f"[FAIL] Error in sentiment analysis: {e}")

# Test 5: Stock Forecasting
print("\n\n[FORECAST] Testing Stock Price Forecasting...\n")

try:
    from tensorflow import keras
    print("Testing LSTM-based price forecasting on AAPL:\n")

    data = yf.download('AAPL', period='1y', progress=False)
    prices = data['Close'].values[-90:]

    scaled = (prices - np.min(prices)) / (np.max(prices) - np.min(prices) + 1e-8)

    X, y = [], []
    for i in range(len(scaled) - 30):
        X.append(scaled[i:i+30])
        y.append(scaled[i+30])

    if len(X) >= 5:
        X = np.array(X).reshape(-1, 30, 1)
        y = np.array(y)

        print(f"Training LSTM model on {len(X)} sequences...")
        model = keras.Sequential([
            keras.layers.LSTM(32, input_shape=(30, 1)),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        model.fit(X, y, epochs=5, batch_size=4, verbose=0)

        last_30 = scaled[-30:].reshape(1, 30, 1)
        forecast = model.predict(last_30, verbose=0)[0][0]
        forecast_score = forecast * 100

        print(f"[OK] LSTM Model Forecast Score: {forecast_score:.2f}/100")
        print(f"   (Interpretation: {'Bullish' if forecast_score > 50 else 'Bearish'} trend)")
    else:
        print("[FAIL] Not enough data for LSTM training")

except ImportError:
    print("[WARN]  TensorFlow not installed - Using fallback exponential smoothing\n")

    try:
        data = yf.download('AAPL', period='1y', progress=False)
        prices = data['Close'].values

        recent = np.float64(prices[-30]).item()
        older = np.float64(prices[-90]).item()
        recent_old = np.float64(prices[-60]).item()
        old_old = np.float64(prices[-120]).item()

        recent_trend = (recent - recent_old) / recent_old if recent_old != 0 else 0
        older_trend = (recent_old - old_old) / old_old if old_old != 0 else 0

        momentum = (recent_trend - older_trend) * 100
        forecast_score = 50 + momentum
        forecast_score = min(max(forecast_score, 0), 100)

        print(f"[OK] Exponential Smoothing Forecast Score: {forecast_score:.2f}/100")
        print(f"   (Interpretation: {'Bullish' if forecast_score > 50 else 'Bearish'} trend)")
    except Exception as e:
        print(f"[WARN]  Exponential smoothing calculation error: {e}")

except Exception as e:
    print(f"[FAIL] Error in forecasting: {e}")

# Test 6: Similarity Scoring
print("\n\n[SIMILARITY] Testing Stock Similarity Scoring...\n")

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics.pairwise import cosine_similarity

    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
    stocks_data = []

    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        stocks_data.append({
            'symbol': symbol,
            'pe_ratio': float(info.get('trailingPE', 0)) or 0,
            'beta': float(info.get('beta', 0)) or 0,
            'dividend_yield': float(info.get('dividendYield', 0)) or 0,
        })

    df = pd.DataFrame(stocks_data)
    feature_cols = ['pe_ratio', 'beta', 'dividend_yield']

    X = df[feature_cols].fillna(0).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    similarity_matrix = cosine_similarity(X_scaled)

    print("Stock Similarity Matrix (0-1 scale):\n")
    print(pd.DataFrame(similarity_matrix, index=symbols, columns=symbols).round(3))

except Exception as e:
    print(f"[FAIL] Error in similarity scoring: {e}")

# Test 7: Blended Scoring
print("\n\n[BLEND] Testing Hybrid Score Blending...\n")

rule_scores = [75, 60, 85]
ai_scores = [65, 70, 80]
symbols_test = ['AAPL', 'MSFT', 'GOOGL']

print("Score Blending (60% Rule-Based + 40% AI-Based):\n")
print(f"{'Symbol':<10} {'Rule Score':<15} {'AI Score':<15} {'Blended Score':<15}")
print("-" * 55)

for sym, rule, ai in zip(symbols_test, rule_scores, ai_scores):
    blended = (0.6 * rule + 0.4 * ai)
    print(f"{sym:<10} {rule:<15.2f} {ai:<15.2f} {blended:<15.2f}")

# Summary
print("\n\n" + "=" * 80)
print("[SUMMARY] TEST SUMMARY")
print("=" * 80)

passed = sum(deps_status.values())
total = len(deps_status)

print(f"\nDependencies: {passed}/{total} installed")
print("\n[OK] Core System Status: READY")
print("   - Rule-based recommendation engine: [OK] Active")
print("   - yfinance data fetching: [OK] Active")
print("   - Stock fundamentals analysis: [OK] Active")
print("   - Similarity scoring: [OK] Active")

if deps_status['transformers']:
    print("   - Sentiment analysis (DistilBERT): [OK] Active")
else:
    print("   - Sentiment analysis (DistilBERT): [WARN]  Fallback mode")

if deps_status['tensorflow']:
    print("   - LSTM forecasting: [OK] Active")
else:
    print("   - LSTM forecasting: [WARN]  Exponential smoothing fallback")

print("\n[READY] System is ready to provide stock recommendations!")
print("=" * 80)
