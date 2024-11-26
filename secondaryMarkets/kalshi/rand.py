import requests
import json

url = "https://trading-api.kalshi.com/trade-api/v2/events?limit=200&status=open"

headers = {"accept": "application/json"}

response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    
    # Pretty print the JSON with indentation
    print(json.dumps(data, indent=4))
else:
    print(f"Error: {response.status_code}")
    print(response.text)
