import os
from datetime import datetime, timedelta
import requests
from models import db, NewsCache, AssetMetadata


class NewsProviderError(Exception):
    pass


def _get_newsdata_headlines(q=None, limit=20):
    """Fetch from NewsData.io free tier (100 req/day). q is search query (symbol, fund name, etc)"""
    api_key = os.getenv("NEWS_API_KEY", "").strip()
    if not api_key:
        raise NewsProviderError("NEWS_API_KEY not configured")

    url = "https://newsdata.io/api/1/news"
    params = {
        "apikey": api_key,
        "language": "en",
        "country": "in",
        "category": "business",
        "size": min(limit, 50),  # newsdata max is 50 per request
    }
    if q:
        params["q"] = q

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "error":
            raise NewsProviderError(f"NewsData.io error: {data.get('message', 'unknown')}")
        return data.get("results", [])
    except requests.exceptions.RequestException as e:
        raise NewsProviderError(f"NewsData.io request failed: {e}")


def _normalize_newsdata_article(article):
    """Convert NewsData.io article format to our cache schema"""
    # Parse pubDate from ISO format string to datetime
    pub_date_str = article.get("pubDate")
    published_at = None
    if pub_date_str:
        try:
            # pubDate comes as ISO string with timezone, e.g. "2026-08-05T10:30:00+00:00"
            # Parse and strip timezone for SQLite compatibility
            published_at = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

    return {
        "headline": article.get("title", ""),
        "source_name": article.get("source_id", "").replace("_", " ").title(),
        "url": article.get("link", ""),
        "published_at": published_at,
        "sentiment": None,  # NewsData.io free tier doesn't include sentiment
        "thumbnail_url": article.get("image_url"),
    }


def fetch_general_news(limit=20, force_refresh=False):
    """Fetch general market/business news. Cache for 1 hour if available."""
    # Check cache freshness
    if not force_refresh:
        cached = (
            NewsCache.query.filter_by(asset_id=None)
            .order_by(NewsCache.fetched_at.desc())
            .limit(limit)
            .all()
        )
        if cached and (datetime.utcnow() - cached[0].fetched_at).total_seconds() < 3600:
            return cached

    # Fetch fresh
    try:
        articles = _get_newsdata_headlines(q="India stock market", limit=limit)
    except NewsProviderError:
        # Fall back to stale cache if available
        return (
            NewsCache.query.filter_by(asset_id=None)
            .order_by(NewsCache.published_at.desc())
            .limit(limit)
            .all()
        )

    # Store new articles
    for article in articles:
        normalized = _normalize_newsdata_article(article)
        # Avoid duplicates by URL
        existing = NewsCache.query.filter_by(url=normalized["url"]).first()
        if not existing:
            news = NewsCache(
                asset_id=None,
                headline=normalized["headline"],
                source_name=normalized["source_name"],
                url=normalized["url"],
                published_at=normalized["published_at"],
                sentiment=normalized["sentiment"],
                thumbnail_url=normalized["thumbnail_url"],
                fetched_at=datetime.utcnow(),
            )
            db.session.add(news)
    db.session.commit()

    # Return fresh
    return (
        NewsCache.query.filter_by(asset_id=None)
        .order_by(NewsCache.published_at.desc())
        .limit(limit)
        .all()
    )


def fetch_asset_news(asset_id, limit=20, force_refresh=False):
    """Fetch news for a specific asset (by symbol/name for stocks, fund name for MF)."""
    asset = db.session.get(AssetMetadata, asset_id)
    if not asset:
        return []

    # Check cache freshness
    if not force_refresh:
        cached = (
            NewsCache.query.filter_by(asset_id=asset_id)
            .order_by(NewsCache.fetched_at.desc())
            .limit(limit)
            .all()
        )
        if cached and (datetime.utcnow() - cached[0].fetched_at).total_seconds() < 3600:
            return cached

    # Determine search query
    if asset.asset_type == "STOCK":
        # Search by symbol (e.g. "RELIANCE" from "RELIANCE.NS")
        query = asset.symbol.split(".")[0]
    elif asset.asset_type == "MUTUAL_FUND":
        # Search by fund name
        query = asset.name
    else:
        # Bonds: no specific news
        query = None

    if not query:
        return []

    # Fetch fresh
    try:
        articles = _get_newsdata_headlines(q=query, limit=limit)
    except NewsProviderError:
        # Fall back to stale cache
        return (
            NewsCache.query.filter_by(asset_id=asset_id)
            .order_by(NewsCache.published_at.desc())
            .limit(limit)
            .all()
        )

    # Store new articles
    for article in articles:
        normalized = _normalize_newsdata_article(article)
        existing = NewsCache.query.filter_by(url=normalized["url"]).first()
        if not existing:
            news = NewsCache(
                asset_id=asset_id,
                headline=normalized["headline"],
                source_name=normalized["source_name"],
                url=normalized["url"],
                published_at=normalized["published_at"],
                sentiment=normalized["sentiment"],
                thumbnail_url=normalized["thumbnail_url"],
                fetched_at=datetime.utcnow(),
            )
            db.session.add(news)
    db.session.commit()

    # Return fresh
    return (
        NewsCache.query.filter_by(asset_id=asset_id)
        .order_by(NewsCache.published_at.desc())
        .limit(limit)
        .all()
    )


def cleanup_old_news(days=14):
    """Delete news_cache rows older than ~14 days. Call this periodically."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    deleted = NewsCache.query.filter(NewsCache.fetched_at < cutoff).delete()
    db.session.commit()
    return deleted
