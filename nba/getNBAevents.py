import json
import re
from datetime import datetime, timezone
from pytz import timezone as pytz_timezone, utc
import requests
import os

# Load data from the specified file
file_path = 'jsonOutputs/gamma_events.json'
nbaFilePath = 'jsonOutputs/nbaEvents.json'

# Function to retrieve all NBA events and adjust time to EST
def get_nba_events_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)

        nba_events = []
        current_time = datetime.now(timezone.utc)
        est_timezone = pytz_timezone('US/Eastern')
        print("Time Zone", est_timezone)
        current_time_est = current_time.astimezone(est_timezone)
        print("Current Time EST", current_time_est)

        for event in data:
            pattern = r'\b(NBA|nba)\b'
            if any(re.search(pattern, str(event.get(field, ""))) 
                  for field in ["title", "ticker", "description"]):
                
                end_date = event.get("endDate")
                if end_date:
                    try:
                        # Try parsing with 'T' separator first
                        event_end_time = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S%z")
                    except ValueError:
                        try:
                            # If that fails, try parsing with space separator
                            event_end_time = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S%z")
                        except ValueError:
                            print(f"Warning: Could not parse date {end_date}")
                            continue

                    # Skip if event is in the past (using EST timezone)
                    event_end_time_est = event_end_time.astimezone(est_timezone)
                    if event_end_time_est < current_time_est:
                        continue
                    
                    # Convert end_date from UTC to EST
                    est_timezone = pytz_timezone('US/Eastern')
                    event_end_time_est = event_end_time.astimezone(est_timezone)
                    # Format consistently with space separator
                    formatted_end_date = event_end_time_est.strftime("%Y-%m-%d %H:%M:%S%z")
                else:
                    formatted_end_date = None

                nba_event_info = {
                    "id": event.get("id"),
                    "title": event.get("title"),
                    "ticker": event.get("ticker"),
                    "description": event.get("description"),
                    "endDate": formatted_end_date,
                    "markets": event.get("markets", [])
                }
                nba_events.append(nba_event_info)

        # Sorting by the endDate, closest to current time
        nba_events.sort(
            key=lambda x: abs((datetime.strptime(x["endDate"], "%Y-%m-%d %H:%M:%S%z") - current_time).total_seconds())
            if x.get("endDate") else float('inf')
        )

        return nba_events
    except FileNotFoundError:
        return "File not found. Please check the file path and try again."

# Function to write NBA events to nbaEvents.json
def write_nba_events_to_file(file_path, output_path='jsonOutputs/nbaEvents.json'):
    nba_events = get_nba_events_from_file(file_path)

    if isinstance(nba_events, list):  # Only proceed if we have a list of events
        with open(output_path, 'w') as outfile:
            json.dump(nba_events, outfile, indent=4)
        return "NBA events have been successfully written to nbaEvents.json."
    else:
        return nba_events  # Return the error message
    
def get_mira_nba_events():
    file_path = 'jsonOutputs/miraNBAEvents.json'
    
    try:
        # Create the jsonOutputs directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Clear the file if it exists by opening it in 'w' mode
        open(file_path, 'w').close()
        
        # Fetch new data
        response = requests.get('http://127.0.0.1:8080/api/basketball_nba/odds')
        response.raise_for_status()
        
        # Write new data to the file
        with open(file_path, 'w') as f:
            json.dump(response.json(), f, indent=4)
            
        return "NBA events have been successfully written to miraNBAEvents.json"
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching NBA events: {e}")
        return "Failed to fetch NBA events"
    except IOError as e:
        print(f"Error handling file operations: {e}")
        return "Failed to write to file"

# Attempt to retrieve NBA events and write to nbaEvents.json
if __name__ == "__main__":
    nba_events = get_nba_events_from_file(file_path)
    write_nba_events_to_file(file_path, nbaFilePath)