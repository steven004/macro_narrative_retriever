import requests
from datetime import datetime

def test_fetch():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.yicai.com/",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    # Yicai Macro
    print("--- Yicai Macro (CID 49) ---")
    url = "https://www.yicai.com/api/ajax/getlistbycid?cid=49&page=1&pagesize=5"
    r = requests.get(url, headers=headers)
    print(f"Status: {r.status_code}")
    print(r.json()[:2] if r.status_code == 200 and r.json() else "No data")

    # CLS Macro
    print("\n--- CLS Macro (Subject 1001) ---")
    url_macro = "https://www.cls.cn/nodeapi/telegraphList?app=CailianpressWeb&category=1001"
    r = requests.get(url_macro, headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        items = r.json().get("data", {}).get("roll_data", [])
        print(items[:2] if items else "No items")

if __name__ == "__main__":
    test_fetch()
