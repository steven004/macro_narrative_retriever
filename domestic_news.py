import akshare as ak
from datetime import datetime, timedelta
import pandas as pd
import requests
import time

MACRO_KEYWORDS = [
    "央行", "美联储", "降息", "加息", "利率", "LPR", "MLF", "通胀", "CPI", "PPI", 
    "PMI", "非农", "GDP", "发改委", "财政部", "外汇", "人民币", "汇率", 
    "原油", "黄金", "OPEC", "地缘", "战争", "制裁", "关税", "贸易", "国务院", 
    "房地产", "逆回购", "社融", "M2", "出口", "进口", "统计局", "证监会", "政治局",
    "降准", "美债", "国债", "外储", "外资"
]

def is_macro_related(text):
    if not text:
        return False
    for kw in MACRO_KEYWORDS:
        if kw in text:
            return True
    return False

def fetch_domestic_macro_news(max_items=8):
    """
    Fetches domestic macro news structurally.
    Batches CCTV, Cailianshe (CLS), and Sina Global (30-hour pagination).
    Applies local Keyword Pre-filtration to avoid LLM overload.
    """
    from news import filter_news_with_llm
    
    candidates = []
    today = datetime.now()
    today_str = today.strftime("%Y%m%d")
    
    # 1. CCTV News (Top-level Macro, mostly kept)
    try:
        print("[AkShare] Fetching CCTV News...")
        df_cctv = ak.news_cctv(date=today_str)
        if hasattr(df_cctv, "empty") and not df_cctv.empty:
            for _, row in df_cctv.iterrows():
                candidates.append({
                    "source": "CCTV News",
                    "title": str(row.get("title", "")),
                    "summary": str(row.get("content", "")),
                    "published": today_str
                })
    except Exception as e:
        pass
        
    # 2. Cailianshe (CLS) Global Fast News
    try:
        print("[AkShare] Fetching Cailianshe (CLS) Fast News...")
        df_cls = ak.stock_info_global_cls()
        if hasattr(df_cls, "empty") and not df_cls.empty:
            for _, row in df_cls.head(100).iterrows():
                title = str(row.get("标题", ""))
                summary = str(row.get("内容", ""))
                if is_macro_related(title) or is_macro_related(summary):
                    candidates.append({
                        "source": "Cailianshe",
                        "title": title,
                        "summary": summary,
                        "published": f"{row.get('发布日期', '')} {row.get('发布时间', '')}"
                    })
    except Exception as e:
        pass
        
    # 3. Sina Global Fast News (30-Hour Rolling Pagination bypassing AkShare)
    try:
        print("[Sina API] Fetching Sina Global Fast News (30-hour rolling window)...")
        thirty_hours_ago = today - timedelta(hours=30)
        page = 1
        keep_fetching = True
        
        while keep_fetching and page <= 100: # Max 100 pages (approx 36 hours of news volume)
            url = f"https://zhibo.sina.com.cn/api/zhibo/feed?page={page}&page_size=50&zhibo_id=152"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(url, headers=headers, timeout=15)
            data = r.json()
            
            feed_list = data.get("result", {}).get("data", {}).get("feed", {}).get("list", [])
            if not feed_list:
                break
                
            for item in feed_list:
                pub_time_str = item.get("create_time", "")
                try:
                    pub_dt = datetime.strptime(pub_time_str, "%Y-%m-%d %H:%M:%S")
                    if pub_dt < thirty_hours_ago:
                        keep_fetching = False
                        break
                except Exception:
                    pass
                    
                content = item.get("rich_text", "")
                if content and keep_fetching:
                    if is_macro_related(content):
                        candidates.append({
                            "source": "Sina Finance",
                            "title": "",
                            "summary": str(content),
                            "published": pub_time_str
                        })
            page += 1
            time.sleep(0.5)
    except Exception as e:
        print(f"\033[93m[Sina API] fetch warning: {e}\033[0m")
        
    print(f"[Domestic Fetch] Keywords Pre-Filter caught {len(candidates)} high-potential macro candidates out of the massive 30h wire feed!")
    
    if not candidates:
        return []
        
    # Filter through Gemini LLM
    final_news = filter_news_with_llm(candidates)
    return final_news[:max_items]
