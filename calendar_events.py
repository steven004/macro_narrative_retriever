import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# The standard free ForexFactory API endpoint for this week's events
FF_CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

def fetch_economic_calendar(min_impact="Medium"):
    """
    Fetches scheduled economic events structurally natively.
    Filters for events with Impact >= min_impact (High, Medium, Low, Non-Economic).
    Returns a list of event dictionaries mapping cleanly.
    """
    events_list = []
    acceptable_impacts = ["High"]
    if min_impact in ["Medium", "Low"]:
        acceptable_impacts.append("Medium")
    if min_impact == "Low":
        acceptable_impacts.append("Low")
        
    try:
        # User-Agent strictly avoids generic 403 Forbidden blocking
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(FF_CALENDAR_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for event in root.findall('event'):
                impact = event.find('impact').text if event.find('impact') is not None else ""
                
                # Only keep important market-moving events natively based on threshold
                if impact in acceptable_impacts:
                    date_str = event.find('date').text if event.find('date') is not None else ""
                    time_str = event.find('time').text if event.find('time') is not None else ""
                    title = event.find('title').text if event.find('title') is not None else ""
                    country = event.find('country').text if event.find('country') is not None else ""
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
