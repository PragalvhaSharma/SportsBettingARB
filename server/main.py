import json
from odds_api import getOdds

def main():
    print("Fetching NBA odds data...")
    odds_data = getOdds("basketball_nba")
    
    if odds_data:
        data = json.loads(odds_data)
        
        # Extract remaining requests info
        remaining_requests = data.pop()['remaining_requests']
        
        # Get a set of all bookmakers across all games
        all_bookmakers = set()
        for game in data:
            all_bookmakers.update(bookmaker['name'] for bookmaker in game['bookmakers'])
        
        # Process and display the odds data
        for game in data:
            print(f"\nGame: {game['away_team']} @ {game['home_team']}")
            print(f"Commence Time: {game['commence_time']}")
            print("Odds:")
            
            game_bookmakers = set()
            for bookmaker in game['bookmakers']:
                game_bookmakers.add(bookmaker['name'])
                print(f"  {bookmaker['name']}:")
                print(f"    Last Update: {bookmaker['last_update']}")
                for team, odds in bookmaker['odds'].items():
                    print(f"    {team}: {odds}")
            
            # Check for missing bookmakers
            missing_bookmakers = all_bookmakers - game_bookmakers
            if missing_bookmakers:
                print("  Missing bookmakers for this game:")
                for bookie in missing_bookmakers:
                    print(f"    - {bookie}")
        
        print(f"\nRemaining API requests: {remaining_requests}")
    else:
        print("Failed to retrieve odds data. Check the error message above.")

if __name__ == "__main__":
    main()
    # test_cache()