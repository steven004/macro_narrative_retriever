import os
import json
import argparse
from datetime import datetime
from news import fetch_macro_news
from calendar_events import fetch_economic_calendar

def main():
    parser = argparse.ArgumentParser(description="Macro Narrative Retriever")
    parser.add_argument("--out-dir", type=str, default="data", help="Directory to store the JSON narrative files")
    args = parser.parse_args()
    
    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)
        
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_file = os.path.join(args.out_dir, f"narratives_{today_str}.json")
    
    print("Fetching Top Macro News and Narratives...")
    news_data = fetch_macro_news(max_items_per_feed=8)
    print(f"Retrieved {len(news_data)} top news articles.")
    
    print("Fetching Global Economic Calendar Events...")
    # Filter by 'Medium' to capture both High and Medium impact events structurally
    calendar_data = fetch_economic_calendar(min_impact="Medium")
    print(f"Retrieved {len(calendar_data)} high/medium impact calendar events for this week.")
    
    # Compile the final LLM-friendly dictionary payload uniquely mapping structurally
    payload = {
        "snapshot_date": today_str,
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
