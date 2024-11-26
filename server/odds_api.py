import requests
import os
import json
from datetime import datetime, timedelta
from functools import lru_cache

# env
from dotenv import load_dotenv
load_dotenv()
ODDS_API = os.getenv('ODDSAPI')

# Implementing caching to reduce the number of requests to the API
class Cache:
    def __init__(self):
        # Cache will just be a dictionary with the sport as the key and the value as the timestamp and the data
        self.cache = {}
        self.cache_duration = timedelta(minutes=15) # Cache for 15 minutes

    def get_cached_odds(self, sport):
        # Get the current time
        current_time = datetime.now()

        # Check if the sport is in the cache and if it has expired
        if sport in self.cache:
            # Getting the data and timestamp from our dictionary (cache)
            data, timestamp = self.cache[sport]

            # Check if the cache has expired
            if current_time - timestamp < self.cache_duration:
                print(f"Returning cached data for {sport}")
                return data

        # If the cache has expired, get fresh data from the API, just need to call our getOdds function
        print("Fetching new data...")
        new_data = getOdds(sport)
        if new_data:
            self.cache[sport] = (new_data, current_time)
        return new_data

def getOdds(sport):
    url = "https://api.the-odds-api.com/v4/sports/" + sport + "/odds"
    params = {
        "apiKey": ODDS_API,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        data = response.json()
        formatted_data = []

        for game in data:
            game_data = {
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "commence_time": datetime.fromisoformat(game["commence_time"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S"),
                "bookmakers": []
            }

            for bookmaker in game["bookmakers"]:
                bookmaker_data = {
                    "name": bookmaker["title"],
                    "last_update": datetime.fromisoformat(bookmaker["last_update"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S"),
                    "odds": {}
                }

                # Check if the bookmaker has a valid market
                if bookmaker["markets"] and bookmaker["markets"][0]:
                    for outcome in bookmaker["markets"][0]["outcomes"]:
                        bookmaker_data["odds"][outcome["name"]] = outcome["price"]

                game_data["bookmakers"].append(bookmaker_data)
                
            formatted_data.append(game_data)

        # Add remaining requests information
        remaining_requests = response.headers.get('x-requests-remaining', 'Unknown')
        formatted_data.append({"remaining_requests": remaining_requests})

        return json.dumps(formatted_data, indent=2)

    # Handle hella excpetions
    except requests.exceptions.RequestException as e:
        if isinstance(e, requests.exceptions.HTTPError):
            if e.response.status_code == 401:
                print("Error: Invalid API key")
            elif e.response.status_code == 429:
                print("Error: API request limit exceeded")
            else:
                print(f"HTTP Error: {e}")
        elif isinstance(e, requests.exceptions.ConnectionError):
            print("Error: Unable to connect to the API")
        elif isinstance(e, requests.exceptions.Timeout):
            print("Error: API request timed out")
        else:
            print(f"An unexpected error occurred: {e}")
        return None
    except json.JSONDecodeError:
        print("Error: Unable to parse API response")
        return None
    except KeyError as e:
        print(f"Error: Expected data not found in API response: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

odds_cache = Cache()

# Get the cached odds for the sport
def get_cached_odds(sport):
    return odds_cache.get_cached_odds(sport)