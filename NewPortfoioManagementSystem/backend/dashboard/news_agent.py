import json
from datetime import datetime, timedelta
import requests
from django.conf import settings
from .models import StockHolding
import yfinance as yf


def get_portfolio_companies(portfolio):
    companies = []
    seen_symbols = set()
    for holding in StockHolding.objects.filter(portfolio=portfolio):
        symbol = holding.company_symbol.strip().upper()
        name = holding.company_name.strip() or symbol
        if symbol and symbol not in seen_symbols:
            seen_symbols.add(symbol)
            companies.append({
                'symbol': symbol,
                'name': name,
            })
    return companies


def save_portfolio_companies_to_file(companies):
    try:
        text_file = settings.BASE_DIR / 'portfolio_companies.txt'
        json_file = settings.BASE_DIR / 'portfolio_companies.json'

        with open(text_file, 'w', encoding='utf-8') as handle:
            handle.write('symbol\tname\n')
            for company in companies:
                handle.write(f"{company['symbol']}\t{company['name']}\n")

        with open(json_file, 'w', encoding='utf-8') as handle:
            json.dump(companies, handle, indent=2)
    except Exception as e:
        print(f"Unable to save portfolio companies: {e}")


def build_news_pairs(results):
    if not results:
        return []
    if len(results) % 2:
        results.append(["More headlines coming soon.", "", "#"])
    return list(zip(results[::2], results[1::2]))


def fetch_top_headlines():
    try:
        query_params = {
            'country': 'us',
            'category': 'business',
            'sortBy': 'publishedAt',
            'apiKey': settings.NEWSAPI_KEY,
            'pageSize': 8,
        }
        main_url = 'https://newsapi.org/v2/top-headlines'
        res = requests.get(main_url, params=query_params, timeout=6)

        if res.status_code != 200:
            print(f"NewsAPI error: {res.status_code}")
            return []

        payload = res.json()
        articles = payload.get('articles', [])
        results = []
        for article in articles:
            title = article.get('title')
            description = article.get('description', '')
            url = article.get('url')
            if title and url:
                results.append([title, description, url])

        return build_news_pairs(results)
    except Exception as e:
        print(f"Error fetching top headlines: {e}")
        return []


def fetch_news_for_companies(companies):
    if not companies:
        return []
    api_key = settings.NEWSAPI_KEY
    if not api_key:
        print('NEWSAPI_KEY is not configured.')
        return []

    trusted_sources = [
        'bbc-news',
        'cnbc',
        'the-wall-street-journal',
        'business-insider',
        'bloomberg',
    ]
    source_list = ','.join(trusted_sources)
    results = []
    seen_urls = set()

    def fetch_with_params(params):
        try:
            res = requests.get('https://newsapi.org/v2/everything', params=params, timeout=8)
            if res.status_code == 200:
                return res.json().get('articles', [])
            if res.status_code == 400:
                params.pop('sources', None)
                res = requests.get('https://newsapi.org/v2/everything', params=params, timeout=8)
                if res.status_code == 200:
                    return res.json().get('articles', [])
            print(f"NewsAPI request failed for query {params.get('q')} with status {res.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"NewsAPI request error for query {params.get('q')}: {e}")
        return []

    def add_articles(articles):
        for article in articles:
            title = article.get('title')
            description = article.get('description', '')
            url = article.get('url')
            if not title or not url:
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            source_name = article.get('source', {}).get('name', '')
            headline = f"{title} — {source_name}" if source_name else title
            results.append([headline, description, url])
            if len(results) >= 8:
                return True
        return False

    for company in companies:
        queries = [
            company['symbol'],
            f'"{company["name"]}"',
            f'"{company["name"]}" OR {company["symbol"]}',
        ]
        for query in queries:
            if len(results) >= 16:
                break
            params = {
                'q': query,
                'sortBy': 'publishedAt',
                'pageSize': 20,
                'apiKey': api_key,
                'language': 'en',
                'sources': source_list,
            }
            articles = fetch_with_params(params)
            if not articles:
                params.pop('sources', None)
                articles = fetch_with_params(params)
            if add_articles(articles):
                break
        if len(results) >= 8:
            break

    return build_news_pairs(results)


def fetch_yfinance_news(companies):
    results = []
    seen_urls = set()

    for company in companies:
        try:
            ticker = yf.Ticker(company['symbol'])
            articles = getattr(ticker, 'news', None)
            if not articles:
                continue
            for article in articles:
                title = article.get('title')
                url = article.get('link') or article.get('href') or article.get('url')
                summary = article.get('summary') or article.get('publisher') or ''
                source_name = article.get('publisher') or ''
                if not title or not url:
                    continue
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                headline = f"{title} — {source_name}" if source_name else title
                results.append([headline, summary, url])
                if len(results) >= 16:
                    break
            if len(results) >= 16:
                break
        except Exception as e:
            print(f"Error fetching yfinance news for {company['symbol']}: {e}")
            continue

    return build_news_pairs(results)


def fetch_portfolio_news(companies):
    if not companies:
        return []
    news = []
    api_key = settings.NEWSAPI_KEY
    if api_key:
        news = fetch_news_for_companies(companies)
    if news:
        return news

    return fetch_yfinance_news(companies) or fetch_top_headlines()
