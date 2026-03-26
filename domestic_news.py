import akshare as ak
from datetime import datetime
import pandas as pd

def fetch_domestic_macro_news(max_items=8):
    """
    Fetches domestic macro news structurally using akshare.
    Batches CCTV, Cailianshe (CLS), and Sina Global data and uses Gemini for macro filtration.
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
        print(f"\033[93m[AkShare] CCTV fetch warning: {e}\033[0m")
        
    # 2. Cailianshe (CLS) Global Fast News
    try:
        print("[AkShare] Fetching Cailianshe (CLS) Fast News...")
        df_cls = ak.stock_info_global_cls()
        if hasattr(df_cls, "empty") and not df_cls.empty:
            for _, row in df_cls.head(100).iterrows():  # Top 100 to save some tokens
                candidates.append({
                    "source": "Cailianshe",
                    "title": str(row.get("标题", "")),
                    "summary": str(row.get("内容", "")),
                    "published": f"{row.get('发布日期', '')} {row.get('发布时间', '')}"
                })
    except Exception as e:
        print(f"\033[93m[AkShare] CLS fetch warning: {e}\033[0m")
        
    # 3. Sina Global Fast News
    try:
        print("[AkShare] Fetching Sina Global Fast News...")
        df_sina = ak.stock_info_global_sina()
        if hasattr(df_sina, "empty") and not df_sina.empty:
            for _, row in df_sina.head(100).iterrows():
                candidates.append({
                    "source": "Sina Finance",
                    "title": "",
                    "summary": str(row.get("内容", "")),
                    "published": str(row.get("时间", ""))
                })
    except Exception as e:
        print(f"\033[93m[AkShare] Sina fetch warning: {e}\033[0m")
        
    print(f"[AkShare] Gathered {len(candidates)} domestic news candidates for Gemini batch processing.")
    
    if not candidates:
        return []
        
    # Filter through Gemini LLM
    final_news = filter_news_with_llm(candidates)
    return final_news[:max_items]
