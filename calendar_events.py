import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# The standard free ForexFactory API endpoint for this week's events
FF_CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

TARGET_CURRENCIES = ["USD", "EUR", "CNY", "SGD", "HKD"]
POWELL_FOMC_KEYWORDS = ["Powell", "FOMC"]

def fetch_economic_calendar():
    """
    Fetches scheduled economic events structurally natively.
    Filters exclusively for High impact events and specific portfolio currencies.
    Exceptions apply inherently strictly inherently gracefully for Powell or FOMC events.
    """
    events_list = []
        
    try:
        # User-Agent strictly avoids generic 403 Forbidden blocking
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(FF_CALENDAR_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for event in root.findall('event'):
                country = event.find('country').text if event.find('country') is not None else ""
                
                # Filter entirely exclusively efficiently natively for target currencies
                if country not in TARGET_CURRENCIES:
                    continue
                    
                title = event.find('title').text if event.find('title') is not None else ""
                impact = event.find('impact').text if event.find('impact') is not None else ""
                
                # Check impact filter efficiently perfectly appropriately accurately
                is_high_impact = (impact == "High")
                is_exception = any(kw.lower() in title.lower() for kw in POWELL_FOMC_KEYWORDS)
                
                if not (is_high_impact or is_exception):
                    continue
                    
                date_str = event.find('date').text if event.find('date') is not None else ""
                time_str = event.find('time').text if event.find('time') is not None else ""
                forecast = event.find('forecast').text if event.find('forecast') is not None else ""
                previous = event.find('previous').text if event.find('previous') is not None else ""
                
                events_list.append({
                    "country": country,
                    "event": title,
                    "date": date_str,
                    "time": time_str,
                    "impact": impact,
                    "forecast": forecast,
                    "previous": previous
                })
    except Exception as e:
        print(f"Error fetching structural economic calendar securely: {e}")
        
    return events_list
