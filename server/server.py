from flask import Flask, jsonify
from odds_api import getOdds
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
executor = ThreadPoolExecutor()

async def async_get_odds(sport):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, getOdds, sport)

@app.route('/api/<sport>/odds', methods=['GET'])
async def sport_odds(sport):
    print(f"Fetching {sport} odds data...")
    odds_data = await async_get_odds(sport)
    
    if odds_data:
        data = json.loads(odds_data)
        
        # Extract remaining requests info without modifying the original data
        remaining_requests = data[-1]['remaining_requests']
        game_data = data[:-1]  # Exclude the last item which contains remaining requests
        
        # Get a set of all bookmakers across all games
        all_bookmakers = set()
        for game in game_data:
            all_bookmakers.update(bookmaker['name'] for bookmaker in game['bookmakers'])
        
        # Process the odds data
        formatted_data = {}
        for index, game in enumerate(game_data, start=1):
            game_key = f"Game {index}"
            game_info = {
                "away_team": game['away_team'],
                "home_team": game['home_team'],
                "commence_time": game['commence_time'],
                "bookmakers": game['bookmakers'],
                "missing_bookmakers": list(all_bookmakers - set(bookmaker['name'] for bookmaker in game['bookmakers']))
            }
            formatted_data[game_key] = game_info
        
        response = {
            "odds_data": formatted_data,
            "remaining_requests": remaining_requests
        }
        
        return jsonify(response), 200
    else:
        return jsonify({"error": "Failed to retrieve odds data"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)