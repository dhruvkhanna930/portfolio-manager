import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from django.conf import settings
import random
import warnings
warnings.filterwarnings('ignore')
from .models import StockHolding

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
    """Get a random AlphaVantage API key from settings"""
    if not ALPHA_VANTAGE_AVAILABLE:
        return None
    try:
        alphavantage_keys = [
            settings.ALPHAVANTAGE_KEY1,
            settings.ALPHAVANTAGE_KEY2,
            settings.ALPHAVANTAGE_KEY3,
            settings.ALPHAVANTAGE_KEY4,
            settings.ALPHAVANTAGE_KEY5,
            settings.ALPHAVANTAGE_KEY6,
            settings.ALPHAVANTAGE_KEY7,
        ]
        return random.choice(alphavantage_keys)
    except:
        return None


def get_stock_fundamentals(symbol):
    """Fetch fundamental data for a stock from yfinance (primary) or AlphaVantage (fallback)"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

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
        print(f"Error fetching fundamentals for {symbol}: {str(e)}")
        if ALPHA_VANTAGE_AVAILABLE:
            return _get_fundamentals_alpha_vantage(symbol)
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

        for symbol in stock_universe:
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
                        complementary_stocks.append(fundamentals)

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


def recommend_popular_stocks(num_recommendations=10, use_ai=True):
    """Fallback: Recommend popular stocks for cold-start users (no portfolio history)"""
    print(f"\n[COLD-START FALLBACK] No portfolio found - recommending top {num_recommendations} popular stocks\n")

    popular_list = get_popular_stocks_list()
    recommendations = []

    for symbol in popular_list[:num_recommendations * 2]:
        try:
            fundamentals = get_stock_fundamentals(symbol)
            if fundamentals:
                ticker = yf.Ticker(symbol)
                info = ticker.info

                market_cap = float(info.get('marketCap', 0)) or 0
                pe_ratio = float(info.get('trailingPE', 0)) or 0

                popularity_score = min((market_cap / 1e12) * 100, 100)
                quality_score = min(100 / (pe_ratio + 1), 100) if pe_ratio > 0 else 50

                rule_score = (popularity_score * 0.6 + quality_score * 0.4)
                fundamentals['rule_score'] = round(rule_score, 2)
                fundamentals['source'] = 'cold_start_fallback'
                recommendations.append(fundamentals)
        except Exception as e:
            print(f"Error with {symbol}: {e}")
            continue

    if use_ai:
        print("Computing AI model scores for popular stocks...")
        ai_scores = compute_ai_model_scores([r['symbol'] for r in recommendations])
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

    print(f"[FALLBACK] Returning {len(recommendations[:num_recommendations])} popular stock recommendations")
    return recommendations[:num_recommendations]


def get_popular_stocks_list():
    """Return a list of popular stocks to recommend from"""
    popular_stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'WMT',
        'JNJ', 'PG', 'KO', 'PEP', 'MCD', 'DIS', 'NFLX', 'INTC', 'AMD', 'CRM',
        'ADBE', 'CSCO', 'ORCL', 'IBM', 'TM', 'BMW', 'F', 'GM', 'BABA', 'TSM',
        'XOM', 'CVX', 'MRK', 'ABBV', 'PFE', 'LLY', 'UNH', 'BA', 'GE', 'RTX'
    ]
    return popular_stocks


def get_portfolio_recommendations(portfolio, use_ai=True):
    """Get both similar and complementary stock recommendations for a portfolio"""
    similar_stocks = recommend_stocks(portfolio, num_recommendations=8, use_ai=use_ai)
    complementary_stocks = recommend_complementary_stocks(portfolio, num_recommendations=8, use_ai=use_ai)

    return {
        'similar_stocks': similar_stocks,
        'complementary_stocks': complementary_stocks,
        'ai_models_used': {
            'sentiment_analysis': 'DistilBERT (Transformers)',
            'stock_forecasting': 'LSTM with Exponential Smoothing Fallback'
        } if use_ai else None
    }
