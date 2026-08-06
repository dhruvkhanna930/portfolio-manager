import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
import random
from .models import StockHolding


def get_stock_fundamentals(symbol):
    """Fetch fundamental data for a stock from yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}

        if not info or 'symbol' not in info and not info.get('shortName'):
            print(f"No data returned for {symbol}")
            return None

        pe_ratio = info.get('trailingPE') or info.get('forwardPE') or 0
        beta = info.get('beta', 0)
        market_cap = info.get('marketCap', 0)
        dividend_yield = info.get('dividendYield', 0)
        profit_margin = info.get('profitMargins', 0)
        return_on_equity = info.get('returnOnEquity', 0)

        return {
            'symbol': symbol,
            'name': info.get('longName', info.get('shortName', '')),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'pe_ratio': float(pe_ratio) if pe_ratio not in [None, 'None', 'N/A', ''] else 0,
            'beta': float(beta) if beta not in [None, 'None', 'N/A', ''] else 0,
            'market_cap': float(market_cap) if market_cap not in [None, 'None', 'N/A', ''] else 0,
            'dividend_yield': float(dividend_yield) if dividend_yield not in [None, 'None', 'N/A', ''] else 0,
            'profit_margin': float(profit_margin) if profit_margin not in [None, 'None', 'N/A', ''] else 0,
            'return_on_equity': float(return_on_equity) if return_on_equity not in [None, 'None', 'N/A', ''] else 0,
            'fifty_two_week_high': float(info.get('fiftyTwoWeekHigh', 0)) if info.get('fiftyTwoWeekHigh') not in [None, 'None', 'N/A', ''] else 0,
            'fifty_two_week_low': float(info.get('fiftyTwoWeekLow', 0)) if info.get('fiftyTwoWeekLow') not in [None, 'None', 'N/A', ''] else 0,
        }
    except Exception as e:
        print(f"Error fetching fundamentals for {symbol}: {str(e)}")
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


def get_sector_similarity(stock1_sector, stock2_sector):
    """Get similarity score based on sector match"""
    if stock1_sector == stock2_sector:
        return 0.3
    return 0


def recommend_stocks(portfolio, num_recommendations=10):
    """Recommend stocks based on user's portfolio"""
    try:
        holding_companies = StockHolding.objects.filter(portfolio=portfolio)

        if not holding_companies.exists():
            print("No holdings in portfolio")
            return []

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
                fundamentals['similarity_score'] = round(score, 3)
                recommendations.append(fundamentals)

        print(f"Returning {len(recommendations)} similar stock recommendations")
        return recommendations

    except Exception as e:
        print(f"Error in recommend_stocks: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def recommend_complementary_stocks(portfolio, num_recommendations=10):
    """Recommend stocks that complement the portfolio (different sectors, lower beta, etc.)"""
    try:
        holding_companies = StockHolding.objects.filter(portfolio=portfolio)

        if not holding_companies.exists():
            print("No holdings for complementary recommendations")
            return []

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
                        fundamentals['complementary_score'] = complementary_score
                        complementary_stocks.append(fundamentals)

        sorted_complementary = sorted(
            complementary_stocks,
            key=lambda x: x['complementary_score'],
            reverse=True
        )[:num_recommendations]

        print(f"Returning {len(sorted_complementary)} complementary stock recommendations")
        return sorted_complementary

    except Exception as e:
        print(f"Error in recommend_complementary_stocks: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def get_popular_stocks_list():
    """Return a list of popular stocks to recommend from"""
    popular_stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'WMT',
        'JNJ', 'PG', 'KO', 'PEP', 'MCD', 'DIS', 'NFLX', 'INTC', 'AMD', 'CRM',
        'ADBE', 'CSCO', 'ORCL', 'IBM', 'TM', 'BMW', 'F', 'GM', 'BABA', 'TSM',
        'XOM', 'CVX', 'MRK', 'ABBV', 'PFE', 'LLY', 'UNH', 'AbbVie', 'BA', 'GE'
    ]
    return popular_stocks


def get_portfolio_recommendations(portfolio):
    """Get both similar and complementary stock recommendations for a portfolio"""
    similar_stocks = recommend_stocks(portfolio, num_recommendations=8)
    complementary_stocks = recommend_complementary_stocks(portfolio, num_recommendations=8)

    return {
        'similar_stocks': similar_stocks,
        'complementary_stocks': complementary_stocks
    }
