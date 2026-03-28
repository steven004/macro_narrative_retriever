import akshare as ak
from datetime import datetime
import pandas as pd
import requests
import time
import json

MACRO_ENTITIES = [
    "央行", "美联储", "发改委", "财政部", "统计局", "证监会", "政治局", 
    "国务院", "外汇局", "欧洲央行", "日本央行", "OPEC", "住建部", "商社"
]

MACRO_ACTIONS = [
    "降息", "加息", "利率", "LPR", "MLF", "通胀", "CPI", "PPI", 
    "PMI", "非农", "GDP", "逆回购", "社融", "M2", "出口", "进口", 
    "关税", "外储", "降准", "美债", "国债", "外资", "救市", "刺激"
]

MACRO_CRITICAL = ["战争", "地缘", "制裁", "熔断", "金融危机", "主权评级", "黑天鹅"]

def is_macro_related(text):
    if not text or len(text) < 15: # Filter out extremely fragmented 1-liners
        return False
        
    has_entity = any(kw in text for kw in MACRO_ENTITIES)
    has_action = any(kw in text for kw in MACRO_ACTIONS)
    has_critical = any(kw in text for kw in MACRO_CRITICAL)
    
    # Only keep the news if it contains a massive global crisis word, OR combines a top authority with an economic action!
    if has_critical or (has_entity and has_action):
        return True
        
    return False

def fetch_yicai_news(max_items=10):
    """
    Fetches news from Yicai (First Financial).
    Targets CID 149 (Macro/Dazheng) and CID 25 (Chief Commentary).
    """
    # cid 49: 宏观, cid 440: 首席评论
    cids = [49, 440]
    candidates = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.yicai.com/",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    for cid in cids:
        try:
            print(f"[Yicai API] Fetching CID {cid}...")
            url = f"https://www.yicai.com/api/ajax/getlistbycid?cid={cid}&page=1&pagesize=30"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for item in data:
                    title = item.get("NewsTitle", "")
                    content = item.get("NewsNotes", "") # Often a summary or intro
                    # Yicai content can be short, we'll use NewsTitle + NewsNotes
                    candidates.append({
                        "source": "Yicai",
                        "title": title,
                        "summary": content,
                        "published": item.get("CreateDate", ""),
                        "link": f"https://www.yicai.com/news/{item.get('NewsID')}.html"
                    })
        except Exception as e:
            print(f"[Yicai API] Error on CID {cid}: {e}")
            
    return candidates

def fetch_cls_specialized_news(max_items=10):
    """
    Fetches Macro and Depth news from Cailianshe (CLS).
    Avoids the noisy Telegraph feed.
    """
    candidates = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.cls.cn/"
    }
    
    # 1. Macro Subject (subject_id 1001)
    try:
        print("[CLS API] Fetching Macro Subject...")
        # Note: CLS APIs sometimes require 'sign' for v3, but nodeapi often works for simple crawls
        url_macro = "https://www.cls.cn/nodeapi/telegraphList?app=CailianpressWeb&category=1001"
        r = requests.get(url_macro, headers=headers, timeout=10)
        if r.status_code == 200:
            items = r.json().get("data", {}).get("roll_data", [])
            for item in items:
                candidates.append({
                    "source": "Cailianshe (Macro)",
                    "title": item.get("title", ""),
                    "summary": item.get("content", ""),
                    "published": datetime.fromtimestamp(item.get("ctime")).strftime("%Y-%m-%d %H:%M:%S") if item.get("ctime") else "",
                    "link": f"https://www.cls.cn/detail/{item.get('id')}"
                })
    except Exception as e:
        print(f"[CLS API] Macro Error: {e}")

    # 2. Depth Articles (category 'depth')
    try:
        print("[CLS API] Fetching Depth Articles...")
        url_depth = "https://www.cls.cn/nodeapi/telegraphList?app=CailianpressWeb&category=depth"
        r = requests.get(url_depth, headers=headers, timeout=10)
        if r.status_code == 200:
            items = r.json().get("data", {}).get("roll_data", [])
            for item in items:
                candidates.append({
                    "source": "Cailianshe (Depth)",
                    "title": item.get("title", ""),
                    "summary": item.get("content", ""),
                    "published": datetime.fromtimestamp(item.get("ctime")).strftime("%Y-%m-%d %H:%M:%S") if item.get("ctime") else "",
                    "link": f"https://www.cls.cn/detail/{item.get('id')}"
                })
    except Exception as e:
        print(f"[CLS API] Depth Error: {e}")
        
    return candidates

def fetch_domestic_macro_news(max_items=8):
    """
    Fetches domestic macro news structurally.
    Combines CCTV, Yicai, and CLS specialized channels.
    """
    from news import filter_news_with_llm
    
    candidates = []
    today = datetime.now()
    today_str = today.strftime("%Y%m%d")
    
    # 1. CCTV News (Top-level Macro)
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
        print(f"[AkShare] CCTV Error: {e}")
        
    # 2. Yicai Macro & Chief
    yicai_news = fetch_yicai_news()
    candidates.extend(yicai_news)
    
    # 3. CLS Macro & Depth
    cls_news = fetch_cls_specialized_news()
    candidates.extend(cls_news)
        
    print(f"[Domestic Fetch] Total candidates collected from CCTV, Yicai, and CLS Depth/Macro: {len(candidates)}")
    
    if not candidates:
        return []
        
    # Filter through Gemini LLM
    final_news = filter_news_with_llm(candidates)
    return final_news[:max_items]
