import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
import time
import warnings
warnings.filterwarnings('ignore')
from .models import StockHolding
import json


def convert_to_json_serializable(obj):
    """Convert numpy/pandas types to JSON serializable Python types"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    return obj

try:
    from alpha_vantage.fundamentaldata import FundamentalData
    ALPHA_VANTAGE_AVAILABLE = True
except ImportError:
    ALPHA_VANTAGE_AVAILABLE = False


class NewsAnalyzer:
    """AI Model: Sentiment analysis on financial news using transformers"""

    def __init__(self):
        try:
            from transformers import pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            self.available = True
        except ImportError:
            self.available = False

    def analyze_sentiment(self, ticker: str) -> float:
        """Analyze news sentiment for a stock (0-100 score)"""
        if not self.available:
            return 50

        try:
            news_headlines = self._fetch_news_headlines(ticker)
            if not news_headlines:
                return 50

            sentiments = []
            for headline in news_headlines[:5]:
                try:
                    result = self.sentiment_pipeline(headline[:512])[0]
                    score = result['score']
                    if result['label'] == 'POSITIVE':
                        sentiments.append(score * 100)
                    else:
                        sentiments.append((1 - score) * 100)
                except:
                    continue

            return np.mean(sentiments) if sentiments else 50
        except Exception as e:
            print(f"Error analyzing sentiment for {ticker}: {e}")
            return 50

    def _fetch_news_headlines(self, ticker: str):
        """Fetch news headlines for a ticker"""
        try:
            ticker_obj = yf.Ticker(ticker)
            news = ticker_obj.news
            if news:
                return [item.get('title', '') for item in news[:5]]
            return []
        except:
            return []


class StockForecastingModel:
    """AI Model: LSTM-based stock price forecasting"""

    def __init__(self):
        self.use_lstm = False
        try:
            from tensorflow import keras
            self.keras = keras
            self.use_lstm = True
        except ImportError:
            pass

    def predict_returns(self, ticker: str, prices: np.ndarray) -> float:
        """Predict next 30-day returns (0-100 score)"""
        if len(prices) < 60:
            return 50

        if self.use_lstm:
            return self._lstm_forecast(prices)
        else:
            return self._simple_forecast(prices)

    def _lstm_forecast(self, prices: np.ndarray) -> float:
        """LSTM-based price prediction"""
        try:
            data = prices[-90:]
            scaled = (data - np.min(data)) / (np.max(data) - np.min(data) + 1e-8)

            X, y = [], []
            for i in range(len(scaled) - 30):
                X.append(scaled[i:i+30])
                y.append(scaled[i+30])

            if len(X) < 5:
                return 50

            X = np.array(X).reshape(-1, 30, 1)
            y = np.array(y)

            model = self.keras.Sequential([
                self.keras.layers.LSTM(32, input_shape=(30, 1)),
                self.keras.layers.Dropout(0.2),
                self.keras.layers.Dense(1)
            ])
            model.compile(optimizer='adam', loss='mse')
            model.fit(X, y, epochs=5, batch_size=4, verbose=0)

            last_30 = scaled[-30:].reshape(1, 30, 1)
            forecast = model.predict(last_30, verbose=0)[0][0]

            forecast_score = forecast * 100
            return min(max(forecast_score, 0), 100)
        except Exception as e:
            print(f"LSTM forecast error: {e}")
            return 50

    def _simple_forecast(self, prices: np.ndarray) -> float:
        """Simple exponential smoothing forecast"""
        recent = prices[-30:]
        older = prices[-90:-30]

        recent_trend = (recent[-1] - recent[0]) / recent[0] if recent[0] != 0 else 0
        older_trend = (older[-1] - older[0]) / older[0] if older[0] != 0 else 0

        momentum = (recent_trend - older_trend) * 100
        forecast_score = 50 + momentum

        return min(max(forecast_score, 0), 100)


def get_alphavantage_key():
    """Get AlphaVantage API key from settings"""
    if not ALPHA_VANTAGE_AVAILABLE:
        return None
    try:
        return settings.ALPHAVANTAGE_KEY
    except:
        return None


def get_stock_fundamentals(symbol):
    """Fetch fundamental data for a stock from yfinance (primary) or AlphaVantage (fallback)"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Check if we got valid data - must have currentPrice or regularMarketPrice
        if not info or info is None or ('currentPrice' not in info and 'regularMarketPrice' not in info):
            raise ValueError(f"No valid data returned for {symbol}")

        return {
            'symbol': symbol,
            'name': info.get('longName', ''),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'pe_ratio': float(info.get('trailingPE', 0)) or 0,
            'beta': float(info.get('beta', 0)) or 0,
            'market_cap': float(info.get('marketCap', 0)) or 0,
            'dividend_yield': float(info.get('dividendYield', 0)) or 0,
            'profit_margin': float(info.get('profitMargins', 0)) or 0,
            'return_on_equity': float(info.get('returnOnEquity', 0)) or 0,
            'fifty_two_week_high': float(info.get('fiftyTwoWeekHigh', 0)) or 0,
            'fifty_two_week_low': float(info.get('fiftyTwoWeekLow', 0)) or 0,
        }
    except Exception as e:
        return None


def _get_fundamentals_alpha_vantage(symbol):
    """Fallback to AlphaVantage if yfinance fails"""
    try:
        key = get_alphavantage_key()
        if not key:
            return None
        fd = FundamentalData(key=key, output_format='json')
        data, meta_data = fd.get_company_overview(symbol=symbol)

        if not data or 'Symbol' not in data:
            return None

        return {
            'symbol': symbol,
            'name': data.get('Name', ''),
            'sector': data.get('Sector', ''),
            'industry': data.get('Industry', ''),
            'pe_ratio': float(data.get('PERatio', 0)) if data.get('PERatio') not in ['None', 'N/A', ''] else 0,
            'beta': float(data.get('Beta', 0)) if data.get('Beta') not in ['None', 'N/A', ''] else 0,
            'market_cap': float(data.get('MarketCapitalization', 0)) if data.get('MarketCapitalization') not in ['None', 'N/A', ''] else 0,
            'dividend_yield': float(data.get('DividendYield', 0)) if data.get('DividendYield') not in ['None', 'N/A', ''] else 0,
            'profit_margin': float(data.get('ProfitMargin', 0)) if data.get('ProfitMargin') not in ['None', 'N/A', ''] else 0,
            'return_on_equity': float(data.get('ReturnOnEquityTTM', 0)) if data.get('ReturnOnEquityTTM') not in ['None', 'N/A', ''] else 0,
            'fifty_two_week_high': float(data.get('52WeekHigh', 0)) if data.get('52WeekHigh') not in ['None', 'N/A', ''] else 0,
            'fifty_two_week_low': float(data.get('52WeekLow', 0)) if data.get('52WeekLow') not in ['None', 'N/A', ''] else 0,
        }
    except Exception as e:
        print(f"AlphaVantage fallback failed: {e}")
        return None


def build_stock_features_dataframe(symbols_list):
    """Build a feature dataframe for a list of stock symbols"""
    stocks_data = []
    valid_symbols = []

    for symbol in symbols_list:
        fundamentals = get_stock_fundamentals(symbol)
        if fundamentals:
            stocks_data.append(fundamentals)
            valid_symbols.append(symbol)

    if not stocks_data:
        return None, None

    df = pd.DataFrame(stocks_data)
    return df, valid_symbols


def compute_stock_similarity(stocks_df):
    """Compute similarity matrix between stocks based on fundamentals"""
    feature_cols = ['pe_ratio', 'beta', 'dividend_yield', 'profit_margin', 'return_on_equity']

    X = stocks_df[feature_cols].fillna(0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    similarity_matrix = cosine_similarity(X_scaled)

    return similarity_matrix


def compute_ai_model_scores(symbols_list):
    """Compute AI model scores for stocks using sentiment and forecasting"""
    news_analyzer = NewsAnalyzer()
    forecaster = StockForecastingModel()
    model_scores = {}

    for ticker in symbols_list:
        sentiment_score = news_analyzer.analyze_sentiment(ticker)

        try:
            data = yf.download(ticker, period='1y', progress=False)
            if len(data) > 0:
                forecast_score = forecaster.predict_returns(ticker, data['Close'].values)
            else:
                forecast_score = 50
        except:
            forecast_score = 50

        combined_ai_score = (sentiment_score * 0.4 + forecast_score * 0.6)
        model_scores[ticker] = {
            'sentiment': sentiment_score,
            'forecast': forecast_score,
            'combined': combined_ai_score
        }

    return model_scores


def blend_scores(rule_score, model_score, has_history=False):
    """Blend rule-based and model-based scores"""
    alpha = 0.6 if has_history else 1.0
    beta = 1.0 - alpha
    return (alpha * rule_score + beta * model_score)


def recommend_stocks(portfolio, num_recommendations=10, use_ai=True):
    """Recommend stocks based on user's portfolio with optional AI enhancement"""
    try:
        holding_companies = StockHolding.objects.filter(portfolio=portfolio)

        if not holding_companies.exists():
            print("No holdings in portfolio - using FALLBACK (popular stocks)")
            return recommend_popular_stocks(num_recommendations, use_ai=use_ai)

        user_stock_symbols = [h.company_symbol for h in holding_companies]
        print(f"Portfolio stocks: {user_stock_symbols}")

        stocks_df, valid_symbols = build_stock_features_dataframe(user_stock_symbols)

        if stocks_df is None or len(valid_symbols) == 0:
            print(f"Could not fetch data for portfolio stocks")
            return []

        print(f"Successfully fetched data for: {valid_symbols}")

        stocks_df.set_index('symbol', inplace=True)
        similarity_matrix = compute_stock_similarity(stocks_df)

        recommendation_scores = {}

        for i, symbol in enumerate(valid_symbols):
            for j, compare_symbol in enumerate(valid_symbols):
                if i != j:
                    if symbol not in recommendation_scores:
                        recommendation_scores[symbol] = 0
                    recommendation_scores[symbol] += similarity_matrix[i][j]
            time.sleep(0.1)

        sorted_recommendations = sorted(
            recommendation_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:num_recommendations]

        recommendations = []
        for symbol, score in sorted_recommendations:
            fundamentals = get_stock_fundamentals(symbol)
            if fundamentals:
                fundamentals['rule_score'] = round(score, 3)
                fundamentals['similarity_score'] = round(score, 3)
                recommendations.append(fundamentals)

        if use_ai:
            print("Computing AI model scores...")
            ai_scores = compute_ai_model_scores([r['symbol'] for r in recommendations])
            for rec in recommendations:
                if rec['symbol'] in ai_scores:
                    ai_data = ai_scores[rec['symbol']]
                    rec['ai_sentiment'] = round(ai_data['sentiment'], 2)
                    rec['ai_forecast'] = round(ai_data['forecast'], 2)
                    rec['final_score'] = round(
                        blend_scores(rec['rule_score'], ai_data['combined'], has_history=True), 3
                    )
                else:
                    rec['final_score'] = rec['rule_score']

            recommendations.sort(key=lambda x: x.get('final_score', x['rule_score']), reverse=True)

        print(f"Returning {len(recommendations)} similar stock recommendations")
        return recommendations

    except Exception as e:
        print(f"Error in recommend_stocks: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def recommend_complementary_stocks(portfolio, num_recommendations=10, use_ai=True):
    """Recommend stocks that complement the portfolio (different sectors, lower beta, etc.)"""
    try:
        holding_companies = StockHolding.objects.filter(portfolio=portfolio)

        if not holding_companies.exists():
            print("No holdings for complementary recommendations - using FALLBACK (popular stocks)")
            return recommend_popular_stocks(num_recommendations, use_ai=use_ai)

        user_sectors = [h.sector for h in holding_companies if h.sector]
        portfolio_avg_beta = 0
        portfolio_avg_pe = 0

        print(f"User sectors: {user_sectors}")

        stocks_df, valid_symbols = build_stock_features_dataframe([h.company_symbol for h in holding_companies])

        if stocks_df is not None:
            portfolio_avg_beta = stocks_df['beta'].mean()
            portfolio_avg_pe = stocks_df['pe_ratio'].mean()
            print(f"Portfolio avg beta: {portfolio_avg_beta}, avg PE: {portfolio_avg_pe}")

        complementary_stocks = []
        stock_universe = get_popular_stocks_list()
        print(f"Searching {len(stock_universe)} stocks from universe")

        for i, symbol in enumerate(stock_universe):
            if symbol not in valid_symbols:
                fundamentals = get_stock_fundamentals(symbol)
                if fundamentals:
                    complementary_score = 0

                    if fundamentals['sector'] not in user_sectors:
                        complementary_score += 3

                    if fundamentals['beta'] > 0 and portfolio_avg_beta > 0:
                        if fundamentals['beta'] < portfolio_avg_beta:
                            complementary_score += 2

                    if fundamentals['dividend_yield'] > 0:
                        complementary_score += 1

                    if complementary_score > 0:
                        fundamentals['rule_score'] = complementary_score
                        fundamentals['similarity_score'] = complementary_score
                        complementary_stocks.append(fundamentals)

                # Rate limiting: small delay every 5 requests
                if (i + 1) % 5 == 0:
                    time.sleep(0.5)

        sorted_complementary = sorted(
            complementary_stocks,
            key=lambda x: x['rule_score'],
            reverse=True
        )[:num_recommendations]

        if use_ai:
            print("Computing AI model scores for complementary stocks...")
            ai_scores = compute_ai_model_scores([s['symbol'] for s in sorted_complementary])
            for stock in sorted_complementary:
                if stock['symbol'] in ai_scores:
                    ai_data = ai_scores[stock['symbol']]
                    stock['ai_sentiment'] = round(ai_data['sentiment'], 2)
                    stock['ai_forecast'] = round(ai_data['forecast'], 2)
                    stock['final_score'] = round(
                        blend_scores(stock['rule_score'], ai_data['combined'], has_history=True), 3
                    )
                else:
                    stock['final_score'] = stock['rule_score']

            sorted_complementary.sort(key=lambda x: x.get('final_score', x['rule_score']), reverse=True)

        print(f"Returning {len(sorted_complementary)} complementary stock recommendations")
        return sorted_complementary

    except Exception as e:
        print(f"Error in recommend_complementary_stocks: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def recommend_popular_stocks(num_recommendations=10, use_ai=True, preferred_sectors=None):
    """Fallback: Recommend from 200+ stocks for cold-start users (no portfolio history)

    Uses live data to score and rank stocks by:
    - Market cap (popularity/stability)
    - P/E ratio (valuation/quality)
    - Sector preference (if provided)
    """
    # Cache key for popular stocks recommendations (cache for 24 hours)
    cache_key = "recommendations_popular_stocks"

    # Check if recommendations are cached
    cached_recommendations = cache.get(cache_key)
    if cached_recommendations:
        print(f"\n[CACHE HIT] Using cached popular stocks recommendations\n")
        return cached_recommendations

    print(f"\n[COLD-START FALLBACK] No portfolio found")
    print(f"[STRATEGY] Fetching live data for 200+ stocks from comprehensive list\n")

    popular_list = get_popular_stocks_list()
    print(f"[INFO] Analyzing {len(popular_list)} stocks across all sectors/market caps\n")

    recommendations = []

    for i, symbol in enumerate(popular_list):
        try:
            fundamentals = get_stock_fundamentals(symbol)
            if fundamentals is None:
                continue

            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or info is None:
                continue

            market_cap = float(info.get('marketCap', 0)) or 0
            pe_ratio = float(info.get('trailingPE', 0)) or 0
            beta = float(info.get('beta', 1.0)) or 1.0
            dividend_yield = float(info.get('dividendYield', 0)) or 0

            # LIVE DATA SCORING:
            # Market Cap Score (Popularity/Stability)
            if market_cap >= 2e12:
                popularity_score = 100  # Mega-cap
            elif market_cap >= 500e9:
                popularity_score = 95   # Large-cap
            elif market_cap >= 100e9:
                popularity_score = 85   # Mid-cap
            else:
                popularity_score = 70   # Small-cap

            # P/E Quality Score
            if pe_ratio > 0:
                if pe_ratio < 15:
                    quality_score = 95  # Undervalued
                elif pe_ratio < 25:
                    quality_score = 85  # Fair value
                elif pe_ratio < 35:
                    quality_score = 75  # Premium
                else:
                    quality_score = 60  # Very premium
            else:
                quality_score = 50

            # Risk Score (Beta)
            if beta < 0.8:
                risk_score = 95  # Low risk
            elif beta < 1.2:
                risk_score = 85  # Medium risk
            else:
                risk_score = 75  # Higher risk

            # Dividend Score
            dividend_score = min(dividend_yield * 500, 100) if dividend_yield > 0 else 50

            # Combined Rule Score (LIVE data weighted)
            rule_score = (
                popularity_score * 0.35 +
                quality_score * 0.35 +
                risk_score * 0.20 +
                dividend_score * 0.10
            )

            fundamentals['rule_score'] = round(rule_score, 2)
            fundamentals['similarity_score'] = round(rule_score, 2)
            fundamentals['source'] = 'cold_start_fallback_live'
            fundamentals['market_cap_category'] = 'Mega' if market_cap >= 2e12 else 'Large' if market_cap >= 500e9 else 'Mid' if market_cap >= 100e9 else 'Small'
            recommendations.append(fundamentals)

            # Rate limiting: small delay every 5 requests
            if (i + 1) % 5 == 0:
                time.sleep(0.5)
        except Exception as e:
            continue

    print(f"[LIVE DATA] Scored {len(recommendations)} stocks from comprehensive list\n")

    if use_ai and len(recommendations) > 0:
        print("[AI ENHANCEMENT] Computing sentiment & forecast for top candidates...\n")
        ai_scores = compute_ai_model_scores([r['symbol'] for r in recommendations[:num_recommendations * 3]])
        for rec in recommendations:
            if rec['symbol'] in ai_scores:
                ai_data = ai_scores[rec['symbol']]
                rec['ai_sentiment'] = round(ai_data['sentiment'], 2)
                rec['ai_forecast'] = round(ai_data['forecast'], 2)
                rec['final_score'] = round(
                    blend_scores(rec['rule_score'], ai_data['combined'], has_history=False), 3
                )
            else:
                rec['final_score'] = rec['rule_score']

        recommendations.sort(key=lambda x: x.get('final_score', x['rule_score']), reverse=True)

    result = recommendations[:num_recommendations]

    # Convert numpy types to JSON serializable Python types
    result = convert_to_json_serializable(result)

    # Cache popular stocks recommendations for 24 hours
    cache.set("recommendations_popular_stocks", result, 86400)

    print(f"[RESULT] Returning {min(len(result), num_recommendations)} recommendations from {len(popular_list)} stocks")
    print("[SOURCES] Live market data (yfinance) + AI models (DistilBERT, LSTM)\n")
    return result


def get_popular_stocks_list():
    """Return a comprehensive list of 200+ stocks across all sectors and market caps

    Organized by:
    - Mega-cap (>$2T)
    - Large-cap ($500B-$2T)
    - Mid-cap ($100B-$500B)
    - Small-cap ($10B-$100B)

    Covers 9 major sectors + diversified industries
    """
    stocks = {
        'MEGA_CAP': [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK.B',
        ],
        'LARGE_CAP_TECH': [
            'INTC', 'AMD', 'CRM', 'ADBE', 'CSCO', 'ORCL', 'AVGO', 'QCOM',
            'IBM', 'NFLX', 'ASML', 'TSM', 'AMAT', 'LRCX',
        ],
        'LARGE_CAP_FINANCE': [
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'COIN',
            'AXP', 'USB', 'PNC', 'COF', 'MET', 'ICE',
        ],
        'LARGE_CAP_HEALTHCARE': [
            'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'MRK', 'LLY', 'AMGN',
            'MDT', 'CVS', 'ELV', 'VRTX', 'REGN', 'CRWD',
        ],
        'LARGE_CAP_CONSUMER': [
            'WMT', 'PG', 'KO', 'PEP', 'MCD', 'DIS', 'NKE', 'SBUX',
            'LOW', 'HD', 'TJX', 'COST', 'ORLY', 'ROST',
        ],
        'LARGE_CAP_INDUSTRIAL': [
            'BA', 'CAT', 'GE', 'LMT', 'RTX', 'HON', 'ITW', 'MMM',
            'AZO', 'URI', 'EMR', 'ETN', 'NOC', 'DE',
        ],
        'LARGE_CAP_ENERGY': [
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX',
            'OXY', 'MAR', 'HAL', 'FANG', 'LNG', 'RIG',
        ],
        'LARGE_CAP_UTILITIES': [
            'NEE', 'DUK', 'SO', 'EXC', 'AWK', 'AEP', 'DTE', 'EIX',
            'SRE', 'WEC', 'PNW', 'AES', 'CMS', 'PPL',
        ],
        'LARGE_CAP_REAL_ESTATE': [
            'AMT', 'PLD', 'EQIX', 'DLR', 'CCI', 'VICI', 'WELL', 'AVB',
            'EQR', 'SPG', 'PSA', 'UMH', 'PTC', 'SBAC',
        ],
        'LARGE_CAP_MATERIALS': [
            'NEM', 'FCX', 'TECK', 'SCCO', 'RIO', 'VALE', 'CLF',
            'MOS', 'CF', 'WRK', 'APD', 'ECL', 'SHW',
        ],
        'MID_CAP_TECH': [
            'SPLK', 'DDOG', 'CRWD', 'NET', 'OKTA', 'FTNT', 'CYBR', 'SIEM',
            'SE', 'UPST', 'SNOW', 'DKNG', 'ROKU', 'PINS',
        ],
        'MID_CAP_FINANCE': [
            'SOFI', 'SQ', 'PYPL', 'HOOD', 'MSTR', 'INTU', 'TROW', 'CME',
            'NDAQ', 'KEYS', 'DFS', 'EFX', 'LYV', 'MPWR',
        ],
        'MID_CAP_HEALTHCARE': [
            'ZTS', 'VRTX', 'VEEV', 'DXCM', 'ALGN', 'XRAY', 'PODD',
            'RARE', 'DNLI', 'RGEN', 'TXMD', 'GNRC', 'INCY',
        ],
        'MID_CAP_CONSUMER': [
            'ULTA', 'FIVE', 'DECK', 'LULU', 'LMND', 'BKNG', 'ETSY', 'ABNB',
            'DASH', 'LYG', 'LEG', 'WHR', 'ZBH', 'SKX',
        ],
        'MID_CAP_INDUSTRIAL': [
            'GWW', 'ODFL', 'EXPD', 'JBLU', 'XPO', 'UPS', 'FDX', 'AXON',
            'CDNA', 'LPX', 'IEX', 'WCC', 'FLR', 'MAS',
        ],
        'SMALL_CAP_GROWTH': [
            'COIN', 'RIOT', 'MARA', 'HOOD', 'CLSK', 'CORE', 'IREN', 'LCID',
            'RIVN', 'NIO', 'XPEV', 'LI', 'KNBE', 'BGCP',
        ],
        'SMALL_CAP_VALUE': [
            'PHM', 'RBLX', 'ATRC', 'GLPI', 'CEMP', 'JMIA', 'UPLD', 'VRSN',
            'ZM', 'TTD', 'AVPT', 'STLA', 'VRM',
        ],
        'DIVIDEND_STOCKS': [
            'O', 'SCHD', 'VYM', 'DGRO', 'KMI', 'ENB', 'TRP', 'LYB',
            'PBA', 'OKE', 'NTR', 'MO', 'PM', 'STWD',
        ],
        'DEFENSIVE_STOCKS': [
            'PG', 'KO', 'MO', 'CL', 'ADP', 'CHD', 'SJM', 'HSY',
            'FMX', 'TSN', 'BGS', 'CTAS', 'IDXX', 'CBPO',
        ],
    }

    flat_list = []
    for category, symbol_list in stocks.items():
        flat_list.extend(symbol_list)

    return flat_list


def get_portfolio_recommendations(portfolio, use_ai=True):
    """Get both similar and complementary stock recommendations for a portfolio"""
    # Cache key for this portfolio's recommendations (cache for 24 hours)
    cache_key = f"recommendations_portfolio_{portfolio.id}"

    # Check if recommendations are cached
    cached_recommendations = cache.get(cache_key)
    if cached_recommendations:
        print(f"[CACHE HIT] Using cached recommendations for portfolio {portfolio.id}")
        return cached_recommendations

    print(f"[CACHE MISS] Computing fresh recommendations for portfolio {portfolio.id}")
    similar_stocks = recommend_stocks(portfolio, num_recommendations=8, use_ai=use_ai)
    complementary_stocks = recommend_complementary_stocks(portfolio, num_recommendations=8, use_ai=use_ai)

    recommendations = {
        'similar_stocks': similar_stocks,
        'complementary_stocks': complementary_stocks,
        'ai_models_used': {
            'sentiment_analysis': 'DistilBERT (Transformers)',
            'stock_forecasting': 'LSTM with Exponential Smoothing Fallback'
        } if use_ai else None
    }

    # Convert numpy types to JSON serializable Python types
    recommendations = convert_to_json_serializable(recommendations)

    # Cache recommendations for 24 hours (86400 seconds)
    cache.set(cache_key, recommendations, 86400)

    return recommendations
