import json
import os
from datetime import datetime, timezone
import requests
from typing import Optional
import pytz
import glob

polymarketNBA = "jsonOutputs/nbaEvents.json"
miraNBA = "jsonOutputs/miraNBAEvents.json"

def normalize_team_name(team_name):
    """Normalize team names to a common format"""
    name_mapping = {
        # Cities/Locations removed
        "Philadelphia 76ers": "76ers",
        "Golden State Warriors": "Warriors",
        "Los Angeles Lakers": "Lakers",
        "Los Angeles Clippers": "Clippers",
        "New York Knicks": "Knicks",
        "Brooklyn Nets": "Nets",
        "New Orleans Pelicans": "Pelicans",
        "San Antonio Spurs": "Spurs",
        "Portland Trail Blazers": "Trail Blazers",
        "Oklahoma City Thunder": "Thunder",
        "Charlotte Hornets": "Hornets",
        "Milwaukee Bucks": "Bucks",
        "Phoenix Suns": "Suns",
        "Miami Heat": "Heat",
        "Detroit Pistons": "Pistons",
        "Boston Celtics": "Celtics",
        "Toronto Raptors": "Raptors",
        "Denver Nuggets": "Nuggets",
        "Minnesota Timberwolves": "Timberwolves",
        "Sacramento Kings": "Kings",
        "Memphis Grizzlies": "Grizzlies",
        "Cleveland Cavaliers": "Cavaliers",
        "Indiana Pacers": "Pacers",
        "Chicago Bulls": "Bulls",
        "Atlanta Hawks": "Hawks",
        "Dallas Mavericks": "Mavericks",
        "Houston Rockets": "Rockets",
        "Washington Wizards": "Wizards",
        "Utah Jazz": "Jazz",
    }
    return name_mapping.get(team_name, team_name)

def get_teams_from_title(title):
    """Extract team names from Polymarket title (e.g., 'Clippers vs. Thunder')"""
    teams = title.replace(' vs. ', ' ').split()
    # Handle special case for Trail Blazers
    if 'Trail' in teams and 'Blazers' in teams:
        teams.remove('Trail')
        teams.remove('Blazers')
        teams.append('Trail Blazers')
    return set(teams)

def decimal_to_implied_probability(decimal_odds):
    """Convert decimal odds to implied probability"""
    return round(1 / decimal_odds, 3)

def get_exchange_rate() -> float:
    """
    Get CAD to USD exchange rate from Exchange Rate API.
    Falls back to default rate if API fails.
    """
    DEFAULT_RATE = 0.73
    API_URL = "https://api.exchangerate-api.com/v4/latest/CAD"
    
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data['rates']['USD']
    except Exception as e:
        print(f"Warning: Could not fetch exchange rate: {e}")
    
    print(f"Using default CAD/USD rate of {DEFAULT_RATE}")
    return DEFAULT_RATE

def calculate_arbitrage_bets(primary_prob: float, poly_prob: float, initial_bet: float = 100, 
                           cad_to_usd_rate: Optional[float] = None) -> Optional[dict]:
    """
    Calculate optimal bet amounts for arbitrage opportunities.
    
    Args:
        primary_prob: Implied probability from primary market sportsbook
        poly_prob: Implied probability from Polymarket
        initial_bet: Amount to bet on primary market sportsbook in CAD (default $100)
        cad_to_usd_rate: CAD to USD conversion rate (optional, will fetch current rate if None)
    """
    if primary_prob + poly_prob >= 1:
        return None  # No arbitrage opportunity
    
    # Get current exchange rate if not provided
    if cad_to_usd_rate is None:
        cad_to_usd_rate = get_exchange_rate()
    
    # Calculate decimal odds from probabilities
    primary_decimal_odds = 1 / primary_prob
    poly_decimal_odds = 1 / poly_prob
    
    # Calculate optimal bet for Polymarket based on $100 CAD primary market bet
    poly_bet_cad = (initial_bet * primary_decimal_odds) / poly_decimal_odds
    poly_bet_usd = poly_bet_cad * cad_to_usd_rate
    
    # Calculate guaranteed profit in CAD
    profit_cad = (initial_bet * primary_decimal_odds) - initial_bet - poly_bet_cad
    
    
    return {
        'primary_bet_cad': initial_bet,
        'polymarket_bet_cad': round(poly_bet_cad, 2),
        'polymarket_bet_usd': round(poly_bet_usd, 2),
        'potential_profit_cad': round(profit_cad, 2),
    }

def convert_to_est(date_str):
    """Convert date string to EST datetime object"""
    try:
        # Try parsing with timezone
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S%z")
    except ValueError:
        try:
            # Try parsing without timezone and assume UTC
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Warning: Could not parse date {date_str}")
            raise
    
    # Convert to EST
    est_tz = pytz.timezone('US/Eastern')
    return dt.astimezone(est_tz)

def find_matching_games():
    print("\nStarting to find matching games...")  # Debug print
    
    # Check if files exist
    if not os.path.exists(miraNBA):
        print(f"Error: {miraNBA} not found")
        return
    
    if not os.path.exists(polymarketNBA):
        print(f"Error: {polymarketNBA} not found")
        return
    
    print("Found both input files, attempting to read...")  # Debug print
    
    try:
        with open(miraNBA, 'r') as f:
            mira_data = json.load(f)
            print(f"Successfully loaded Mira data with {len(mira_data['odds_data'])} games")  # Debug print
    except json.JSONDecodeError as e:
        print(f"Error decoding {miraNBA}: {e}")
        return
    except Exception as e:
        print(f"Error reading {miraNBA}: {e}")
        return
    
    try:
        with open(polymarketNBA, 'r') as f:
            poly_data = json.load(f)
            print(f"Successfully loaded Polymarket data with {len(poly_data)} games")  # Debug print
    except json.JSONDecodeError as e:
        print(f"Error decoding {polymarketNBA}: {e}")
        return
    except Exception as e:
        print(f"Error reading {polymarketNBA}: {e}")
        return
    
    # Create a list to store arbitrage opportunities
    arbitrage_opportunities = []
    
    # Loop through each Mira game
    for game_id, mira_game in mira_data['odds_data'].items():
        # Convert and check game date
        try:
            mira_date = datetime.strptime(mira_game['commence_time'], "%Y-%m-%d %H:%M:%S")
            mira_date = mira_date.replace(tzinfo=timezone.utc)  # Assume UTC if no timezone
            mira_date_est = mira_date.astimezone(pytz.timezone('US/Eastern'))
            
            # Skip if game is in the past
            if mira_date_est < datetime.now(pytz.timezone('US/Eastern')):
                continue
                
        except (ValueError, TypeError) as e:
            print(f"Error parsing date for game {game_id}: {e}")
            continue
        
        # Normalize Mira team names
        mira_teams = {normalize_team_name(team) for team in 
                     ([mira_game['away_team']] + list(mira_game['bookmakers'][0]['odds'].keys()))}
        print(f"\nLooking for match for Mira game: {mira_teams}")
        
        # Look for matching game in Polymarket data
        for poly_game in poly_data:
            try:
                poly_date = datetime.strptime(poly_game['endDate'], "%Y-%m-%d %H:%M:%S%z")
                poly_date_est = poly_date.astimezone(pytz.timezone('US/Eastern'))
                
                # Skip if Polymarket game is in the past
                if poly_date_est < datetime.now(pytz.timezone('US/Eastern')):
                    continue
                
                # Compare dates in EST timezone - must be the same day and within 1 hour
                if (poly_date_est.date() != mira_date_est.date() or 
                    abs((poly_date_est - mira_date_est).total_seconds()) > 3600):  # 1 hour tolerance
                    continue
                
                poly_teams = {normalize_team_name(team) for team in get_teams_from_title(poly_game['title'])}
                
                # If teams match (ignoring order)
                if mira_teams == poly_teams:
                    print(f"\nFound matching game!")
                    
                    # Store best primary market odds for each team
                    best_primary_odds = {}
                    best_bookmakers = {}  # New dict to track which bookmaker has best odds
                    for team in mira_teams:
                        best_primary_odds[team] = float('inf')
                    
                    print(f"Mira odds:")
                    for bookmaker in mira_game['bookmakers']:
                        print(f"\n{bookmaker['name']}:")
                        total_implied_prob = 0
                        for team, odds in bookmaker['odds'].items():
                            normalized_team = normalize_team_name(team)
                            implied_prob = decimal_to_implied_probability(odds)
                            total_implied_prob += implied_prob
                            print(f"{team}: {odds} (implied prob: {implied_prob:.3f})")
                            # Update best odds and bookmaker if current odds are better
                            if implied_prob < best_primary_odds[normalized_team]:
                                best_primary_odds[normalized_team] = implied_prob
                                best_bookmakers[normalized_team] = bookmaker['name']
                        print(f"Net implied probability: {total_implied_prob:.3f}")
                    
                    print(f"\nPolymarket odds:")
                    outcomes = eval(poly_game['markets'][0]['outcomes'])
                    # Convert string prices to float while preserving precision
                    prices = [float(price.strip('"')) for price in eval(poly_game['markets'][0]['outcomePrices'])]
                    poly_odds = {}
                    total_poly_prob = 0
                    for outcome, prob in zip(outcomes, prices):
                        print(f"{outcome}: {prob}")  # Print full precision
                        poly_odds[outcome] = prob
                        total_poly_prob += prob
                    print(f"Net implied probability: {total_poly_prob}")
                    
                    # Check for arbitrage opportunities
                    for poly_team, poly_prob in poly_odds.items():
                        # Find the opposing team
                        opposing_teams = mira_teams - {normalize_team_name(poly_team)}
                        if len(opposing_teams) != 1:
                            continue
                        opposing_team = list(opposing_teams)[0]
                        
                        primary_prob = best_primary_odds[opposing_team]
                        
                        # If sum of probabilities is less than 1, we have positive arbitrage
                        if poly_prob + primary_prob < 1:
                            bet_details = calculate_arbitrage_bets(primary_prob, poly_prob)
                            # Calculate decimal odds
                            poly_decimal = 1 / poly_prob
                            primary_decimal = 1 / primary_prob
                            
                            arb_opportunity = {
                                'polymarket_team': poly_team,
                                'polymarket_prob': poly_prob,
                                'polymarket_decimal': poly_decimal,
                                'primary_team': opposing_team,
                                'primary_prob': primary_prob,
                                'primary_decimal': primary_decimal,
                                'bookmaker': best_bookmakers[opposing_team],
                                'total_probability': poly_prob + primary_prob,
                                'theoretical_profit': ((1 - (poly_prob + primary_prob)) * 100),
                                'bet_details': bet_details,
                                'polymarket_date': poly_game['endDate'],
                                'primary_date': mira_game['commence_time']
                            }
                            arbitrage_opportunities.append(arb_opportunity)
                            
                            print(f"\nARBITRAGE OPPORTUNITY FOUND!")
                            print(f"Polymarket Team: {poly_team} (odds: {poly_decimal:.2f}, prob: {poly_prob:.3f})")
                            print(f"Bookmaker: {best_bookmakers[opposing_team]}")
                            print(f"Primary Market Team: {opposing_team} (odds: {primary_decimal:.2f}, prob: {primary_prob:.3f})")
                            print(f"Total probability: {poly_prob + primary_prob:.3f}")
                            print(f"Theoretical profit: {((1 - (poly_prob + primary_prob)) * 100):.2f}%")
                            print(f"Bet Details:")
                            print(f"  Primary Market Bet (CAD): ${bet_details['primary_bet_cad']:.2f}")
                            print(f"  Polymarket Bet (CAD): ${bet_details['polymarket_bet_cad']:.2f}")
                            print(f"  Polymarket Bet (USD): ${bet_details['polymarket_bet_usd']:.2f}")
                            print(f"  Theoretical Profit (CAD): ${bet_details['potential_profit_cad']:.2f}")
                    
                    print("-" * 50)
                
            except (ValueError, TypeError, AttributeError) as e:
                print(f"Error processing dates for game {poly_game.get('title', 'Unknown')}: {e}")
                continue

    # If arbitrage opportunities were found, save them to a file
    if arbitrage_opportunities:
        # Create arbOutput directory if it doesn't exist
        os.makedirs('arbOutput', exist_ok=True)
        
        # Delete all existing files in arbOutput directory
        for file in glob.glob('arbOutput/arbitrage_opportunities_*.txt'):
            try:
                os.remove(file)
                print(f"Deleted previous file: {file}")
            except Exception as e:
                print(f"Error deleting file {file}: {e}")
        
        # Get current timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'arbOutput/arbitrage_opportunities_{timestamp}.txt'
        
        # Write new opportunities to file
        with open(filename, 'w') as f:
            f.write("ARBITRAGE OPPORTUNITIES\n\n")
            for opp in arbitrage_opportunities:
                f.write(f"Polymarket Team: {opp['polymarket_team']} (odds: {opp['polymarket_decimal']:.2f}, prob: {opp['polymarket_prob']:.3f})\n")
                f.write(f"Polymarket Event Date: {opp['polymarket_date']}\n")
                f.write(f"Bookmaker: {opp['bookmaker']}\n")
                f.write(f"Primary Market Team: {opp['primary_team']} (odds: {opp['primary_decimal']:.2f}, prob: {opp['primary_prob']:.3f})\n")
                f.write(f"Primary Market Event Date: {opp['primary_date']}\n")
                f.write(f"Total probability: {opp['total_probability']:.3f}\n")
                f.write(f"Theoretical profit: {opp['theoretical_profit']:.2f}%\n")
                f.write("\nBet Details:\n")
                f.write(f"Primary Market Bet (CAD): ${opp['bet_details']['primary_bet_cad']:.2f}\n")
                f.write(f"Polymarket Bet (CAD): ${opp['bet_details']['polymarket_bet_cad']:.2f}\n")
                f.write(f"Polymarket Bet (USD): ${opp['bet_details']['polymarket_bet_usd']:.2f}\n")
                f.write(f"Theoretical Profit (CAD): ${opp['bet_details']['potential_profit_cad']:.2f}\n")
                f.write("-" * 50 + "\n\n")
        
        print(f"Wrote new arbitrage opportunities to {filename}")
    else:
        print("-" * 50)
        print("No arbitrage opportunities found")
        print("-" * 50)

if __name__ == "__main__":
    find_matching_games()

