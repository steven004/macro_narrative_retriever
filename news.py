import os
import json
import time
import requests
import re
from datetime import datetime, timezone

MACRO_KEYWORDS = [
    # 1. Central Banks & Liquidity
    "Fed", "Powell", "FOMC", "ECB", "Lagarde", "BOJ", "PBOC", 
    "Interest Rate", "Bond Yield", "Treasury Yield", "Treasury", "Liquidity", "Stimulus", "Rate Cut", "Rate Hike", "Bonds",

    # 2. Inflation & Economic Indicators
    "Inflation", "CPI", "PPI", "PCE", "Deflation", "Stagflation", 
    "Unemployment", "Nonfarm", "NFP", "Payrolls", "GDP", "PMI", "Recession", "Soft Landing",

    # 3. Commodities & Energy Shock
    "Oil", "Crude", "Brent", "OPEC", "Energy", "Gas", "Copper", "Commodities",

    # 4. Geopolitics & Tail Risks
    "Geopolitical", "War", "Middle East", "Tariffs", "Sanctions", "Crisis", "Supply Chain",

    # 5. Portfolio Specific Anchors
    "Gold", "US Dollar", "DXY", "USD", "Bitcoin", "Crypto", "Housing Market", "Real Estate"
]

MICRO_BLACKLIST = [
    "Dividend", "Shares", "Bancorp", "Inc.", "Corp.", "Quarterly Earnings", 
    "Analyst Estimates", "Zacks", "Buy Rating", "Sell Rating", "Stake", "Position in"
]

MAX_AGE_SECONDS = 72 * 3600  # 72 hours window limit

def get_api_key():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "config", "api_keys.json")
    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
            return cfg.get("ALPHA_VANTAGE_KEY")
    except Exception as e:
        print(f"\033[91mFailed to load API key securely from {config_path}: {e}\033[0m")
        return None

def fetch_macro_news(max_items=15):
    """
    Fetches structured news articles from Alpha Vantage REST API.
    Strictly filters out >72hr old narratives, micro-stock noise using a black/whitelist cascade.
    """
    api_key = get_api_key()
    if not api_key:
        print("\033[91m[Alpha_Vantage] No API key found. Skipping news retrieval entirely.\033[0m\n")
        return []
        
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&topics=economy_macro&limit=50&apikey={api_key}"
    news_narratives = []
    
    macro_pattern = re.compile(r'\b(?:' + '|'.join(MACRO_KEYWORDS) + r')\b', re.IGNORECASE)
    blacklist_pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, MICRO_BLACKLIST)) + r')\b', re.IGNORECASE)
    ticker_pattern = re.compile(r'\$[A-Z]{1,4}\b')
    current_time_utc = datetime.now(timezone.utc)
    
    try:
        print("[Alpha_Vantage] Pinging REST API safely for Economy_Macro news...")
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            print(f"\033[91m[Alpha_Vantage] HTTP Error {response.status_code}\033[0m")
            return []
            
        data = response.json()
        
        if "Information" in data and "rate limit" in data["Information"].lower():
            print("\033[91m[Alpha_Vantage] API Rate Limit Exceeded.\033[0m\n")
            return []
            
        feed = data.get("feed", [])
        
        raw_count = len(feed)
        dropped_time = 0
        dropped_keyword = 0
        dropped_blacklist = 0
        dropped_empty = 0
        collected = 0
        
        for item in feed:
            if collected >= max_items:
                break
                
            summary = item.get("summary", "").strip()
            title = item.get("title", "").strip()
            pub_time_str = item.get("time_published", "")
            
            if not summary or not title or not pub_time_str:
                dropped_empty += 1
                continue
                
            try:
                article_dt = datetime.strptime(pub_time_str, "%Y%m%dT%H%M%S")
                article_dt = article_dt.replace(tzinfo=timezone.utc)
                age_seconds = (current_time_utc - article_dt).total_seconds()
                
                if age_seconds > MAX_AGE_SECONDS or age_seconds < -3600:
                    dropped_time += 1
                    continue
            except Exception:
                dropped_empty += 1
                continue
                
            combined_text = f"{title} {summary}"
            
            # Phase 1: Micro-Stock Blacklist & Ticker Filter
            if blacklist_pattern.search(combined_text) or ticker_pattern.search(title):
                dropped_blacklist += 1
                continue
                
            # Phase 2: Macro Whitelist Filter
            if not macro_pattern.search(combined_text):
                dropped_keyword += 1
                continue
                
            news_narratives.append({
                "source": item.get("source", "AlphaVantage"),
                "title": title,
                "published": pub_time_str,
                "summary": summary,
                "link": item.get("url", ""),
                "sentiment_score": item.get("overall_sentiment_score", "N/A"),
                "sentiment_label": item.get("overall_sentiment_label", "N/A")
            })
            collected += 1
            
        print(f"[Alpha_Vantage] Raw parsed REST API: {raw_count} | Dropped (Age > 72h): {dropped_time} | Dropped (Blacklist): {dropped_blacklist} | Dropped (No Keyword): {dropped_keyword} | Dropped (Empty/Format): {dropped_empty} | Kept: {collected}\n")
        
    except Exception as e:
        print(f"\033[91mError explicitly fetching from REST JSON API: {e}\033[0m\n")
            
    return news_narratives
