import csv
import logging
import time
from pathlib import Path

import requests
import yfinance as yf

logger = logging.getLogger(__name__)

MFAPI_SEARCH_URL = "https://api.mfapi.in/mf/search"
NSE_FALLBACK_CSV = Path(__file__).resolve().parent.parent / "data" / "nse_symbols.csv"

# yfinance's search is an unofficial scraped endpoint -- cache briefly so repeated
# keystrokes on the same query don't hammer it (CLAUDE.md §4.1).
_CACHE_TTL_SECONDS = 300
_cache = {}

_nse_fallback_rows = None


class UnsupportedAssetTypeError(Exception):
    pass


def _cache_get(key):
    hit = _cache.get(key)
    if hit is None:
        return None
    cached_at, value = hit
    if time.time() - cached_at > _CACHE_TTL_SECONDS:
        _cache.pop(key, None)
        return None
    return value


def _cache_put(key, value):
    _cache[key] = (time.time(), value)


def _load_nse_fallback():
    global _nse_fallback_rows
    if _nse_fallback_rows is None:
        rows = []
        try:
            with open(NSE_FALLBACK_CSV, newline="") as fh:
                for row in csv.DictReader(fh):
                    rows.append({"symbol": row["symbol"], "name": row["name"]})
        except OSError:
            logger.exception("Could not read NSE fallback CSV at %s", NSE_FALLBACK_CSV)
        _nse_fallback_rows = rows
    return _nse_fallback_rows


def _search_nse_fallback(query, limit):
    q = query.strip().lower()
    results = []
    for row in _load_nse_fallback():
        if q in row["symbol"].lower() or q in row["name"].lower():
            results.append(
                {
                    "symbol": f"{row['symbol']}.NS",
                    "name": row["name"],
                    "exchange": "NSE",
                    "asset_type": "STOCK",
                    "source": "fallback",
                }
            )
        if len(results) >= limit:
            break
    return results


def search_stocks(query, limit=10):
    """Live stock search via yfinance, restricted to Indian listings (.NS/.BO).
    Falls back to the bundled NSE CSV if Yahoo throttles or errors -- search must
    never go dead mid-demo (§4.1).
    """
    cache_key = ("STOCK", query.lower(), limit)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        quotes = yf.Search(query, max_results=limit * 3).quotes
        results = []
        for q in quotes:
            symbol = q.get("symbol") or ""
            if not symbol.endswith((".NS", ".BO")):
                continue
            if q.get("quoteType") != "EQUITY":
                continue
            results.append(
                {
                    "symbol": symbol,
                    "name": q.get("shortname") or q.get("longname") or symbol,
                    "exchange": "NSE" if symbol.endswith(".NS") else "BSE",
                    "asset_type": "STOCK",
                    "source": "yfinance",
                }
            )
            if len(results) >= limit:
                break
        if results:
            _cache_put(cache_key, results)
            return results
        logger.info("yfinance search returned no Indian equities for %r, using fallback", query)
    except Exception:
        logger.warning("yfinance search failed for %r, using bundled NSE fallback", query, exc_info=True)

    results = _search_nse_fallback(query, limit)
    _cache_put(cache_key, results)
    return results


def search_mutual_funds(query, limit=10):
    """MF search via mfapi.in's own search endpoint -- a real search API, not
    scraped, so no offline fallback is needed (§4.1).
    """
    cache_key = ("MUTUAL_FUND", query.lower(), limit)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    resp = requests.get(MFAPI_SEARCH_URL, params={"q": query}, timeout=8)
    resp.raise_for_status()
    results = [
        {
            "symbol": str(item["schemeCode"]),
            "name": item["schemeName"],
            "exchange": None,
            "asset_type": "MUTUAL_FUND",
            "source": "mfapi",
        }
        for item in resp.json()[:limit]
    ]
    _cache_put(cache_key, results)
    return results


def search_live(query, asset_type):
    if asset_type == "STOCK":
        return search_stocks(query)
    if asset_type == "MUTUAL_FUND":
        return search_mutual_funds(query)
    # Bonds are deliberately excluded: there is no live search API for Indian
    # retail bonds, so they stay a curated seed list (§4.1). Surfaced as an
    # explicit error rather than silently returning [].
    raise UnsupportedAssetTypeError(asset_type)
