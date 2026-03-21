import os
import json
import requests
from datetime import datetime, timezone
import warnings

warnings.filterwarnings("ignore")

from google import genai
from google.genai import types

MAX_AGE_SECONDS = 72 * 3600  # 72 hours window limit

def get_api_keys():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "config", "api_keys.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"\033[91mFailed to load API keys securely from {config_path}: {e}\033[0m")
        return {}

def filter_news_with_llm(news_list):
    """
    Passes the raw news array to Gemini to act as a semantic judge.
    Returns a sorted list of structurally purified 'macro only' news based on importance.
    """
    if not news_list:
        return []
        
    keys = get_api_keys()
    gemini_key = keys.get("GEMINI_KEY")
    if not gemini_key:
        print("\033[91m[LLM_Filter] No Gemini API key found. Skipping LLM filter.\033[0m")
        return news_list
        
    client = genai.Client(api_key=gemini_key)
    
    llm_payload = []
    for i, news in enumerate(news_list):
        llm_payload.append({
            "id": i,
            "title": news.get("title", ""),
            "summary": news.get("summary", "")
        })
        
    prompt = """
    你是一个经验丰富的宏观对冲基金数据审核员。你的任务是从混合新闻流中，精准提取出【宏观经济与大类资产新闻】，并剔除纯粹的【微观个股噪音】。

    【判定为 is_macro: TRUE 的标准（包含宏观传导）】：
    1. 纯粹宏观： 探讨国家经济、通胀、美联储/央行政策、地缘政治、大宗商品（原油/黄金总量）、主权债券等。
    2. 宏观向微观的传导（重要！）： 如果新闻的核心是探讨宏观事件（如利率变化、经济数据发布）如何广泛影响某个行业板块（如银行业、科技股）或大盘指数。注意：即使这类新闻中拿了具体的公司（如苹果、英伟达）作为举例，只要其核心叙事是宏观驱动的，依然必须判定为 TRUE！

    【判定为 is_macro: FALSE 的绝对红线（纯微观噪音）】：
    新闻的绝对核心只围绕 1-2 家单体公司的内部事件（如：某公司发财报、换CEO、个股评级上调/下调、内部人员买卖股票、具体的产品发布会）。

    【打分标准 (importance_score 1-10)】：
    10分：核弹级全球宏观转向（如战争爆发、美联储意外加降息）。
    7-9分：重要宏观数据发布（CPI、非农）或重要地缘/板块动荡。
    4-6分：日常宏观经济评论或二线经济体数据。
    1-3分：边缘宏观噪音。
    (如果 is_macro 为 false，importance_score 直接写 0)

    请直接返回一个严格的 JSON 数组，格式为：[{"id": 0, "is_macro": true, "importance_score": 8, "reason": "简短原因"}]

    以下是需要判定的新闻列表：
    """ + json.dumps(llm_payload, ensure_ascii=False)
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        judgments = json.loads(response.text)
        judgment_map = {item["id"]: item for item in judgments if "id" in item}
        
        filtered_news = []
        dropped_llm = 0
        for i, news in enumerate(news_list):
            judge = judgment_map.get(i)
            if judge and judge.get("is_macro"):
                news["llm_reason"] = judge.get("reason", "")
                news["importance_score"] = judge.get("importance_score", 0)
                filtered_news.append(news)
            else:
                dropped_llm += 1
                
        # Sort aggressively by importance score (highest to lowest)
        filtered_news.sort(key=lambda x: x.get("importance_score", 0), reverse=True)
                
        print(f"[LLM_Filter] Gemini evaluated {len(news_list)} items | Dropped (Micro Noise): {dropped_llm} | Kept (Pure Macro): {len(filtered_news)}")
        return filtered_news
        
    except Exception as e:
        print(f"\033[91m[LLM_Filter] Gemini API Failure: {e}\033[0m")
        return news_list

def fetch_macro_news(max_items=8):
    """
    Fetches structured news articles from Alpha Vantage REST API.
    Uses Gemini LLM to filter and rank macro relevance.
    """
    keys = get_api_keys()
    api_key = keys.get("ALPHA_VANTAGE_KEY")
    if not api_key:
        print("\033[91m[Alpha_Vantage] No API key found. Skipping news retrieval entirely.\033[0m\n")
        return []
        
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&topics=economy_macro&limit=50&apikey={api_key}"
    
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
        dropped_empty = 0
        
        current_time_utc = datetime.now(timezone.utc)
        pre_llm_candidates = []
        
        for item in feed:
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
                
            pre_llm_candidates.append({
                "source": item.get("source", "AlphaVantage"),
                "title": title,
                "published": pub_time_str,
                "summary": summary,
                "link": item.get("url", ""),
                "sentiment_score": item.get("overall_sentiment_score", "N/A"),
                "sentiment_label": item.get("overall_sentiment_label", "N/A")
            })
            
        print(f"[Alpha_Vantage] Raw parsed REST API: {raw_count} | Dropped (Age > 72h): {dropped_time} | Dropped (Empty/Format): {dropped_empty} | Candidates for LLM: {len(pre_llm_candidates)}")
        
        # Pass candidates to the Gemini Judge and Ranker
        final_news = filter_news_with_llm(pre_llm_candidates)
        
        # Cap the output at max_items (already sorted highest to lowest internally)
        return final_news[:max_items]
        
    except Exception as e:
        print(f"\033[91mError extracting macro news from API: {e}\033[0m\n")
            
    return []
