from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from xml.etree import ElementTree

import yfinance as yf


MARKET_SYMBOLS = (
    ("S&P 500", "SPY"),
    ("Nasdaq 100", "QQQ"),
    ("Volatility", "VXX"),
    ("Bitcoin", "BTC-USD"),
)

SECTOR_SYMBOLS = (
    ("Communication", "XLC"),
    ("Consumer Discretionary", "XLY"),
    ("Consumer Staples", "XLP"),
    ("Energy", "XLE"),
    ("Financials", "XLF"),
    ("Health Care", "XLV"),
    ("Industrials", "XLI"),
    ("Materials", "XLB"),
    ("Real Estate", "XLRE"),
    ("Technology", "XLK"),
    ("Utilities", "XLU"),
)


def get_quote(ticker):
    """Return the latest close and movement from the prior close."""
    try:
        history = yf.Ticker(ticker).history(period="5d")
        if history.empty:
            return None
        current_price = float(history["Close"].iloc[-1])
        previous_close = float(history["Close"].iloc[-2]) if len(history) > 1 else current_price
        dollar_change = current_price - previous_close
        percent_change = (dollar_change / previous_close) * 100 if previous_close else 0
        return {
            "price": round(current_price, 2),
            "dollar": round(dollar_change, 2),
            "percent": round(percent_change, 2),
        }
    except Exception:
        return None


def get_current_price(ticker):
    """
    Returns the latest market price.
    """

    quote = get_quote(ticker)
    return quote["price"] if quote else None


def get_daily_change(ticker):
    """
    Returns today's dollar and percent change.
    """

    quote = get_quote(ticker)
    if not quote:
        return None
    return {
        "dollar": quote["dollar"],
        "percent": quote["percent"],
        "current_price": quote["price"],
    }


def get_market_summary():
    """Fetch the benchmark and sector snapshots used by the Markets page."""
    def collect(symbols):
        rows = []
        for name, ticker in symbols:
            quote = get_quote(ticker)
            if quote:
                rows.append({"name": name, "ticker": ticker, **quote})
            else:
                rows.append({"name": name, "ticker": ticker, "price": None, "dollar": None, "percent": None})
        return rows

    return {"benchmarks": collect(MARKET_SYMBOLS), "sectors": collect(SECTOR_SYMBOLS)}


def _get_yahoo_news(ticker, limit):
    """Return normalized ticker-specific stories supplied through Yahoo Finance."""
    try:
        raw_news = yf.Ticker(ticker).news or []
    except Exception:
        return []

    stories = []
    for story in raw_news[:limit]:
        content = story.get("content", story)
        title = content.get("title") or story.get("title")
        if not title:
            continue
        provider = content.get("provider", {})
        publisher = provider.get("displayName") or story.get("publisher") or "Yahoo Finance"
        url = (
            (content.get("clickThroughUrl") or {}).get("url")
            or (content.get("canonicalUrl") or {}).get("url")
            or story.get("link")
        )
        published = content.get("pubDate") or story.get("providerPublishTime")
        if isinstance(published, (int, float)):
            published = datetime.fromtimestamp(published).strftime("%b %d, %Y · %I:%M %p")
        elif isinstance(published, str):
            try:
                published = datetime.fromisoformat(published.replace("Z", "+00:00")).strftime("%b %d, %Y · %I:%M %p")
            except ValueError:
                pass
        stories.append({
            "title": title,
            "publisher": publisher,
            "published": published or "Recent",
            "url": url,
            "summary": content.get("summary") or story.get("summary") or "",
        })
    return stories


def _get_google_market_news(query, limit):
    """Read the public Google News RSS market feed and preserve each publisher."""
    url = "https://news.google.com/rss/search?q={}&hl=en-US&gl=US&ceid=US:en".format(quote_plus(query))
    try:
        request = Request(url, headers={"User-Agent": "HELIX market-news reader"})
        document = urlopen(request, timeout=10).read()
        root = ElementTree.fromstring(document)
    except Exception:
        return []

    stories = []
    for item in root.findall("./channel/item")[:limit]:
        title = item.findtext("title")
        if not title:
            continue
        source = item.find("source")
        published = item.findtext("pubDate") or "Recent"
        try:
            published = parsedate_to_datetime(published).strftime("%b %d, %Y · %I:%M %p")
        except (TypeError, ValueError):
            pass
        stories.append({
            "title": title,
            "publisher": source.text if source is not None and source.text else "Google News",
            "published": published,
            "url": item.findtext("link"),
            "summary": "",
        })
    return stories


def get_company_news(ticker="MARKET", limit=14):
    """Blend Yahoo ticker stories and a multi-publisher market-news RSS feed."""
    symbol = ticker.strip().upper() or "MARKET"
    is_market_feed = symbol == "MARKET"
    yahoo_stories = _get_yahoo_news("SPY" if is_market_feed else symbol, limit)
    query = "US stock market" if is_market_feed else f"{symbol} stock"
    blended = yahoo_stories + _get_google_market_news(query, limit)

    unique = []
    titles = set()
    for story in blended:
        title_key = story["title"].strip().lower()
        if title_key in titles:
            continue
        titles.add(title_key)
        unique.append(story)
        if len(unique) == limit:
            break
    return unique
if __name__ == "__main__":

    print(get_current_price("META"))

    print(get_daily_change("META"))
