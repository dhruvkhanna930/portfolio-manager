import os
import re
from datetime import datetime, timedelta
import requests
from models import db, NewsCache, AssetMetadata


class NewsProviderError(Exception):
    pass


def _get_newsdata_headlines(q=None, limit=20, title_only=False):
    """Fetch from NewsData.io free tier (200 req/day). q is search query (symbol, fund name, etc).

    The free tier ignores/rejects a `size` param (paid-tier only -- passing it
    made every call return status="error" and silently fall back to whatever
    was already cached, which is why the feed looked stuck at a handful of
    articles). Free tier always returns a fixed page of 10, so to honor `limit`
    we page through `nextPage` cursors until we have enough or run out.

    `title_only` sends `qInTitle` instead of `q` -- NewsData.io's plain `q`
    does a loose full-text match across the whole article body, which for a
    specific company/fund name mostly returns unrelated noise (verified: `q`
    for "RELIANCE" pulled in China/BSE/EV-charging stories that don't mention
    it in the title at all). `qInTitle` requires the term to actually be in
    the headline, which is what "news about this asset" should mean.
    """
    api_key = os.getenv("NEWS_API_KEY", "").strip()
    if not api_key:
        raise NewsProviderError("NEWS_API_KEY not configured")

    url = "https://newsdata.io/api/1/news"
    base_params = {
        "apikey": api_key,
        "language": "en",
        "country": "in",
        "category": "business",
    }
    if q:
        base_params["qInTitle" if title_only else "q"] = q

    articles = []
    next_page = None
    max_pages = 6  # 6 * 10 = up to 60 articles, plenty of headroom over any realistic `limit`

    for _ in range(max_pages):
        if len(articles) >= limit:
            break
        params = dict(base_params)
        if next_page:
            params["page"] = next_page
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            if articles:
                break  # keep whatever we already fetched rather than discarding it
            raise NewsProviderError(f"NewsData.io request failed: {e}")

        if data.get("status") == "error":
            message = data.get("results", {}).get("message", "unknown") if isinstance(
                data.get("results"), dict
            ) else data.get("message", "unknown")
            if articles:
                break
            raise NewsProviderError(f"NewsData.io error: {message}")

        articles.extend(data.get("results", []))
        next_page = data.get("nextPage")
        if not next_page:
            break

    return articles[:limit]


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

    # Determine search query. Verified against the live API: the ticker symbol
    # (e.g. "TATAELXSI", "HDFCBANK", "BAJFINANCE") almost never appears in a
    # real headline -- those are written with the spaced-out company name
    # ("Tata Elxsi", "HDFC Bank"). qInTitle=HDFCBANK returned 0 results;
    # qInTitle="HDFC Bank" returned 31. So we search on the cleaned name, not
    # the ticker.
    if asset.asset_type == "STOCK":
        clean_name = re.sub(r"\s+(Ltd\.?|Limited)\s*$", "", asset.name, flags=re.IGNORECASE).strip()
    elif asset.asset_type == "MUTUAL_FUND":
        # The full scheme name (e.g. "ICICI Prudential Balanced Advantage Fund
        # - Direct - Growth") is too specific to ever appear verbatim in a
        # headline -- qInTitle with the full name returns zero results.
        # Fund house name is what news actually gets written about; strip the
        # generic "Mutual Fund" suffix to keep it a tight search term.
        fund_house = None
        if asset.mutual_fund_details and asset.mutual_fund_details.fund_house:
            fund_house = asset.mutual_fund_details.fund_house.name
        clean_name = (fund_house or asset.name).replace(" Mutual Fund", "").strip()
    else:
        # Bonds: no specific news
        clean_name = None

    if not clean_name:
        return []

    # Fetch fresh, from most to least precise, stopping at the first tier that
    # actually returns something rather than always taking the loosest match:
    #   1. qInTitle, first two words   -- e.g. "HDFC Bank", "Bajaj Finance"
    #   2. qInTitle, first word only   -- broader ("Reliance", "HDFC"); can be
    #      generic for group names like "Tata", but still finance headlines
    #   3. plain q (full-text, not just title), first two words -- last resort
    words = clean_name.split()
    two_word = " ".join(words[:2])
    one_word = words[0]
    attempts = [
        (two_word, True),
        (one_word, True) if one_word != two_word else None,
        (two_word, False),
    ]

    try:
        articles = []
        for attempt in attempts:
            if attempt is None:
                continue
            term, title_only = attempt
            articles = _get_newsdata_headlines(q=term, limit=limit, title_only=title_only)
            if articles:
                break
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
