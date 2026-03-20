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

MACRO_KEYWORDS = [
    "Fed", "Powell", "Inflation", "CPI", "Rate", "Oil", "Crude", 
    "Geopolitical", "ECB", "Unemployment", "Yield", "OPEC", 
    "Recession", "Gold", "Dollar"
]

def fetch_macro_news(max_items_per_feed=15):
    """
    Fetches top news articles from financial RSS feeds.
    Filters out empty summaries and non-macro 'retail' noise.
    """
    news_narratives = []
    
    # Compile case-insensitive regex for whole word macro tracking
    keyword_pattern = re.compile(r'\b(?:' + '|'.join(MACRO_KEYWORDS) + r')\b', re.IGNORECASE)
    
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            collected = 0
            
            for entry in feed.entries:
                if collected >= max_items_per_feed:
                    break
                
                # Requirement A: Explicitly grab description or summary
                summary = entry.get("description", entry.get("summary", ""))
                
                # Strip HTML artifacts
                if "<" in summary and ">" in summary:
                    summary = re.sub('<[^<]+>', '', summary)
                summary = summary.strip()
                
                title = entry.get("title", "").strip()
                
                # Discard if summary is empty to keep LLM context pristine
                if not summary:
                    continue
                    
                # Requirement B: Whitelist filter for macro topics
                combined_text = f"{title} {summary}"
                if not keyword_pattern.search(combined_text):
                    continue
                    
                news_narratives.append({
                    "source": source,
                    "title": title,
                    "published": entry.get("published", ""),
                    "summary": summary,
                    "link": entry.get("link", "")
                })
                
                collected += 1
                
        except Exception as e:
            print(f"Error fetching from {source}: {e}")
            
    return news_narratives
