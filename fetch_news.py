import os
import xml.etree.ElementTree as ET
import requests
import yfinance as yf

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

TICKER = "BABA"
MAX_ARTICLES = 5
RSS_URL = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={TICKER}&region=US&lang=en-US"


def fetch_via_yfinance():
    """Fetch news using the yfinance library."""
    ticker = yf.Ticker(TICKER)
    articles = []
    for item in ticker.news[:MAX_ARTICLES]:
        title = item.get("content", {}).get("title") or item.get("title", "No title")
        url = (
            item.get("content", {}).get("canonicalUrl", {}).get("url")
            or item.get("link")
            or item.get("url")
            or "No link"
        )
        articles.append({"title": title, "url": url})
    return articles


def fetch_via_rss():
    """Fetch news from Yahoo Finance RSS feed (fallback)."""
    response = requests.get(RSS_URL, timeout=10)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    articles = []
    for item in root.findall(".//item")[:MAX_ARTICLES]:
        title_el = item.find("title")
        link_el = item.find("link")
        title = title_el.text if title_el is not None else "No title"
        url = link_el.text if link_el is not None else "No link"
        articles.append({"title": title, "url": url})
    return articles


def fetch_baba_news():
    """Try yfinance first; fall back to RSS on any error."""
    try:
        articles = fetch_via_yfinance()
        if articles:
            return articles
    except Exception as exc:
        print(f"yfinance failed ({exc}), falling back to RSS feed…")
    return fetch_via_rss()


def send_to_discord(articles):
    if not articles:
        print("No news articles found.")
        return
    if not WEBHOOK_URL:
        raise ValueError("DISCORD_WEBHOOK_URL is missing or empty.")

    lines = [f"**📰 Latest {TICKER} News from Yahoo Finance**\n"]
    for i, article in enumerate(articles, start=1):
        lines.append(f"{i}. [{article['title']}]({article['url']})")

    message = "\n".join(lines)

    response = requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)
    response.raise_for_status()
    print(f"Message sent successfully (HTTP {response.status_code})")


if __name__ == "__main__":
    articles = fetch_baba_news()
    send_to_discord(articles)
