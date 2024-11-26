import json
from odds_api import getOdds, get_cached_odds, odds_cache

'''
This function is just for testing if the cache is working properly
def test_cache():
    print("\n=== Testing Cache ===")
    
    # First call - should fetch from API
    print("\nFirst call:")
    odds1 = odds_cache.get_cached_odds("basketball_nba")
    
    # Second call within 5 minutes - should use cache
    print("\nSecond call (should use cache):")
    odds2 = odds_cache.get_cached_odds("basketball_nba")
    
    # Third call with different sport - should fetch new
    print("\nThird call (different sport):")
    odds3 = odds_cache.get_cached_odds("basketball_ncaab")
    
    # Fourth call to first sport - should still use cache
    print("\nFourth call (back to NBA, should use cache):")
    odds4 = odds_cache.get_cached_odds("basketball_nba")
'''

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