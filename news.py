import feedparser
from datetime import datetime
import re
import ssl

# Safely bypass generic macOS ssl verification issues for public generic RSS feeds
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

RSS_FEEDS = {
    "Yahoo_Finance": "https://finance.yahoo.com/news/rssindex",
    "CNBC_Macro": "https://search.cnbc.com/rs/search/combinedcms/view.xml?profile=120000000&id=100003114",
    "WSJ_Markets": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"
}

def fetch_macro_news(max_items_per_feed=8):
    """
    Fetches the top news articles natively from standard financial RSS feeds.
    Returns a list of structurally isolated dictionaries specifically optimized for LLM token ingestion securely.
    """
    news_narratives = []
    
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for i, entry in enumerate(feed.entries):
                if i >= max_items_per_feed:
                    break
                
                # Cleanup summary intelligently to absolutely eliminate raw HTML artifacts wasting LLM tokens organically
                summary = entry.get("summary", "")
                if "<" in summary and ">" in summary:
                    summary = re.sub('<[^<]+>', '', summary)
                    
                news_narratives.append({
                    "source": source,
                    "title": entry.get("title", ""),
                    "published": entry.get("published", ""),
                    "summary": summary.strip(),
                    "link": entry.get("link", "")
                })
        except Exception as e:
            print(f"Error rapidly fetching from {source}: {e}")
            
    return news_narratives
