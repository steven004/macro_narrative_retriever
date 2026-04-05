import traceback

TARGET_CURRENCIES = ["USD", "EUR", "CNY", "SGD", "HKD"]
POWELL_FOMC_KEYWORDS = ["Powell", "FOMC"]

def fetch_economic_calendar(region="Global"):
    """
    Fetches scheduled economic events structurally natively.
    Filters exclusively for High impact events and specific portfolio currencies.
    Retrieves this week and next week via cURL-cffi to bypass Cloudflare.
    """
    events_list = []
    
    try:
        from curl_cffi import requests
        from bs4 import BeautifulSoup
        
        urls = [
            "https://www.forexfactory.com/calendar?week=this",
            "https://www.forexfactory.com/calendar?week=next"
        ]
        
        for url in urls:
            response = requests.get(url, impersonate="chrome110", timeout=20)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                rows = soup.find_all("tr", class_="calendar__row")
                current_date = ""
                current_time = ""
                
                for row in rows:
                    date_el = row.find("td", class_="calendar__date")
                    if date_el and date_el.text.strip():
                        # ForexFactory usually outputs texts like 'Mon Apr 6 Apr 6'
                        raw_date = " ".join(date_el.text.split())
                        tokens = raw_date.split()
                        # Uniquify tokens cleanly (Mon, Apr, 6, etc)
                        seen = set()
                        clean_tokens = []
                        for t in tokens:
                            if t not in seen:
                                clean_tokens.append(t)
                                seen.add(t)
                        current_date = " ".join(clean_tokens)
                        
                    time_el = row.find("td", class_="calendar__time")
                    if time_el and time_el.text.strip():
                        current_time = time_el.text.strip()
                        
                    currency_el = row.find("td", class_="calendar__currency")
                    if not currency_el:
                        continue
                    country = currency_el.text.strip()
                    if not country:
                        continue
                        
                    if region == "China" and country != "CNY":
                        continue
                    elif region == "Global" and country not in TARGET_CURRENCIES:
                        continue
                        
                    impact_el = row.find("td", class_="calendar__impact")
                    if impact_el:
                        span = impact_el.find("span")
                        impactClass = span.get("class", []) if span else []
                    else:
                        impactClass = []
                        
                    impact = "Low"
                    if "icon--ff-impact-red" in impactClass:
                        impact = "High"
                    elif "icon--ff-impact-ora" in impactClass:
                        impact = "Medium"
                    elif "icon--ff-impact-yel" in impactClass:
                        impact = "Low"
                    elif "icon--ff-impact-gre" in impactClass:
                        impact = "Non-Economic"
                        
                    event_el = row.find("td", class_="calendar__event")
                    title = event_el.text.strip() if event_el else ""
                    
                    forecast_el = row.find("td", class_="calendar__forecast")
                    forecast = forecast_el.text.strip() if forecast_el else ""
                    
                    previous_el = row.find("td", class_="calendar__previous")
                    previous = previous_el.text.strip() if previous_el else ""
                    
                    if region == "China":
                        is_valid_impact = True
                        is_exception = False
                    else:
                        is_valid_impact = (impact == "High")
                        is_exception = any(kw.lower() in title.lower() for kw in POWELL_FOMC_KEYWORDS)
                        
                    if not (is_valid_impact or is_exception):
                        continue
                        
                    events_list.append({
                        "country": country,
                        "event": title,
                        "date": current_date,
                        "time": current_time,
                        "impact": impact,
                        "forecast": forecast,
                        "previous": previous
                    })
    except Exception as e:
        print(f"Error scraping economic calendar: {e}")
        traceback.print_exc()
        
    return events_list
