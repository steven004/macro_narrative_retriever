import feedparser
import time
import calendar
import re
import ssl
import requests
from dateutil import parser as date_parser
from datetime import datetime, timezone

# Safely bypass generic macOS ssl verification issues for public generic RSS feeds
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

RSS_FEEDS = {
    "CNBC_Econ": "https://search.cnbc.com/rs/search/combinedcms/view.xml?profile=120000000&id=10000664",
    "WSJ_Business": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    "Fed_Press": "https://www.federalreserve.gov/feeds/press_all.xml"
}

MACRO_KEYWORDS = [
    "Fed", "Powell", "Inflation", "CPI", "Rate", "Oil", "Crude", 
    "Geopolitical", "ECB", "Unemployment", "Yield", "OPEC", 
    "Recession", "Gold", "Dollar"
]

MAX_AGE_SECONDS = 72 * 3600  # 72 hours window limit

def print_warning(msg):
    """Prints a red warning to the terminal for WAF 403 blocks."""
    print(f"\033[91m{msg}\033[0m")

def fetch_macro_news(max_items_per_feed=15):
    """
    Fetches top news articles from financial RSS feeds.
    Strictly filters out >72hr old narratives, empty summaries, and retail noise.
    """
    news_narratives = []
    
    keyword_pattern = re.compile(r'\b(?:' + '|'.join(MACRO_KEYWORDS) + r')\b', re.IGNORECASE)
    current_time_utc = datetime.now(timezone.utc)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/rdf+xml;q=0.8, application/xml;q=0.6, text/xml;q=0.4, */*;q=0.2'
    }
    
    for source, url in RSS_FEEDS.items():
        try:
            print(f"[{source}] Pinging feed: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print_warning(f"[{source}] HTTP Warning: Received status code {response.status_code}. The feed might be blocked.")
                continue
            else:
                print(f"[{source}] HTTP 200 OK. Parsing XML payload...")
                
            feed = feedparser.parse(response.content)
            
            raw_count = len(feed.entries)
            dropped_time = 0
            dropped_keyword = 0
            dropped_empty = 0
            collected = 0
            
            for entry in feed.entries:
                if collected >= max_items_per_feed:
                    break
                    
                pub_date_str = entry.get("published", entry.get("pubDate", ""))
                if not pub_date_str:
                    dropped_empty += 1
                    continue
                    
                try:
                    article_dt = date_parser.parse(pub_date_str)
                    
                    if article_dt.tzinfo is None:
                        article_dt = article_dt.replace(tzinfo=timezone.utc)
                        
                    age_seconds = (current_time_utc - article_dt).total_seconds()
                    
                    if age_seconds > MAX_AGE_SECONDS or age_seconds < -3600:
                        dropped_time += 1
                        continue
                except Exception as parse_e:
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        article_time_utc = calendar.timegm(entry.published_parsed)
                        age_sec = current_time_utc.timestamp() - article_time_utc
                        if age_sec > MAX_AGE_SECONDS:
                            dropped_time += 1
                            continue
                    else:
                        dropped_empty += 1
                        continue
                
                summary = entry.get("description", entry.get("summary", ""))
                
                if "<" in summary and ">" in summary:
                    summary = re.sub('<[^<]+>', '', summary)
                summary = summary.strip()
                
                title = entry.get("title", "").strip()
                
                if not summary:
                    dropped_empty += 1
                    continue
                    
                combined_text = f"{title} {summary}"
                if not keyword_pattern.search(combined_text):
                    dropped_keyword += 1
                    continue
                    
                news_narratives.append({
                    "source": source,
                    "title": title,
                    "published": pub_date_str,
                    "summary": summary,
                    "link": entry.get("link", "")
                })
                
                collected += 1
                
            print(f"[{source}] Raw parsed: {raw_count} | Dropped (Age > 72h): {dropped_time} | Dropped (No Keyword): {dropped_keyword} | Dropped (Empty/No Date): {dropped_empty} | Kept: {collected}\n")
                
        except Exception as e:
            print_warning(f"Error fetching from {source}: {e}\n")
            
    return news_narratives
