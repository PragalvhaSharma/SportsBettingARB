import requests
import json
import os

class KalshiAPI:
    def __init__(self):
        self.base_url = "https://trading-api.kalshi.com/trade-api/v2/events"
        self.output_file = 'jsonOutputs/kalshi_events.json'

    def fetch_and_save_kalshi_events(self):
        all_events = []
        cursor = None

        while True:
            url = f"{self.base_url}?limit=200&status=open&with_nested_markets=true"
            if cursor:
                url += f"&cursor={cursor}"

            response = requests.get(url)

            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text[:500]}...")  # Print first 500 characters

            try:
                data = response.json()
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                print(f"Full response content: {response.text}")
                break

            if response.status_code != 200:
                print(f"Error: {data.get('error', 'Unknown error')}")
                break

            all_events.extend(data.get('events', []))

            cursor = data.get('cursor')
            if not cursor:
                break
        
        print(f"Total number of events: {len(all_events)}")

        if os.path.exists(self.output_file):
            os.remove(self.output_file)
            print(f"Deleted existing {self.output_file}")

        with open(self.output_file, 'w') as f:
            json.dump(all_events, f, indent=2)

        print(f"All events have been saved to {self.output_file}")

    def getEventInfo(self, eventTicker):
        url = f"{self.base_url}/{eventTicker}"
        response = requests.get(url)
        return response.json()

    def extract_kalshi_event_and_markets(self):
        with open(self.output_file, 'r') as f:
            events = json.load(f)

        event_with_markets = []
        for event in events:
            event_info = {
                "event_ticker": event.get("event_ticker"),
                "event_title": event.get("title", "No title provided"),
                "sub_title": event.get("sub_title", "No subtitle"),
                "category": event.get("category", "No category"),
                "markets": []
            }

            for market in event.get("markets", []):
                market_info = {
                    "market_ticker": market.get("ticker"),
                    "market_type": market.get("market_type", "N/A"),
                    "open_time": market.get("open_time", "No open time provided"),
                    "close_time": market.get("close_time", "No close time provided"),
                    "rules_primary": market.get("rules_primary", "No primary rules provided"),
                }
                event_info["markets"].append(market_info)
            
            event_with_markets.append(event_info)
        
        return event_with_markets

if __name__ == "__main__":
    kalshi_api = KalshiAPI()
    # kalshi_api.fetch_and_save_kalshi_events()
    
    # # Example usage of the new method
    extracted_events = kalshi_api.extract_kalshi_event_and_markets()
    print(f"Extracted {len(extracted_events)} events with their markets")
    print(json.dumps(extracted_events[:2], indent=2))  # Print the first two events as an example
