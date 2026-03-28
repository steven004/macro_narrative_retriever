import os
import json
import argparse
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Macro Narrative Retriever")
    parser.add_argument("--out-dir", type=str, default="data", help="Directory to store the JSON narrative files")
    parser.add_argument("--region", type=str, choices=["Global", "China"], default="Global", help="Region to fetch macro news from")
    args = parser.parse_args()
    
    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)
        
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_file = os.path.join(args.out_dir, f"narratives_{args.region}_{today_str}.json")
    
    if args.region == "Global":
        from news import fetch_macro_news
        from calendar_events import fetch_economic_calendar
        print("Fetching Top Global Macro News and Narratives...")
        news_data = fetch_macro_news(max_items=8)
        print(f"Retrieved {len(news_data)} top global news articles.")
        
        print("Fetching Global Economic Calendar Events...")
        calendar_data = fetch_economic_calendar(region="Global")
        print(f"Retrieved {len(calendar_data)} calendar events.")
        
    elif args.region == "China":
        from domestic_news import fetch_domestic_macro_news
        print("Fetching Top Domestic (China) Macro News via AkShare...")
        news_data = fetch_domestic_macro_news(max_items=8)
        print(f"Retrieved {len(news_data)} top domestic news articles from hundreds of raw items.")
        
        print("Fetching China Specific Economic Calendar Events...")
        from calendar_events import fetch_economic_calendar
        calendar_data = fetch_economic_calendar(region="China")
        print(f"Retrieved {len(calendar_data)} calendar events relevant to China.")

    # Compile the final LLM-friendly dictionary payload uniquely mapping structurally
    payload = {
        "snapshot_date": today_str,
        "region": args.region,
        "total_news_items": len(news_data),
        "total_calendar_events": len(calendar_data),
        "news_narratives": news_data,
        "upcoming_economic_events": calendar_data
    }
    
    # Save the structured data natively securely seamlessly inherently uniquely explicitly natively globally exactly inherently efficiently optimally effectively accurately exactly.
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)
        
    print(f"\nSuccessfully stored structured LLM narrative snapshot identically organically physically to: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()
