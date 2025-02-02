import json
import os
from datetime import datetime, timezone
import requests
from typing import Optional, Set, Dict, Any, List
import pytz
import glob

# Constants
POLYMARKET_NBA = "jsonOutputs/nbaEvents.json"
MIRA_NBA = "jsonOutputs/miraNBAEvents.json"
DEFAULT_EXCHANGE_RATE = 0.73
EXCHANGE_RATE_API = "https://api.exchangerate-api.com/v4/latest/CAD"

# Type aliases
GameData = Dict[str, Any]
ArbitrageOpportunity = Dict[str, Any]

def normalize_team_name(team_name: str) -> str:
    """
    Normalize team names to a common format by removing city/location names.
    """
    name_mapping = {
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

def get_teams_from_title(title: str) -> Set[str]:
    """
    Extract team names from Polymarket title (e.g., 'Clippers vs. Thunder')
    """
    teams = title.replace(' vs. ', ' ').split()
    if 'Trail' in teams and 'Blazers' in teams:
        teams.remove('Trail')
        teams.remove('Blazers')
        teams.append('Trail Blazers')
    return set(teams)

def decimal_to_implied_probability(decimal_odds: float) -> float:
    """Convert decimal odds to implied probability"""
    return round(1 / decimal_odds, 3)

def get_exchange_rate() -> float:
    """Get CAD to USD exchange rate from Exchange Rate API"""
    try:
        response = requests.get(EXCHANGE_RATE_API, timeout=5)
        if response.status_code == 200:
            return response.json()['rates']['USD']
    except Exception as e:
        print(f"Warning: Could not fetch exchange rate: {e}")
    
    print(f"Using default CAD/USD rate of {DEFAULT_EXCHANGE_RATE}")
    return DEFAULT_EXCHANGE_RATE

def calculate_arbitrage_bets(
    primary_prob: float, 
    poly_prob: float, 
    initial_bet: float = 100, 
    cad_to_usd_rate: Optional[float] = None
) -> Optional[Dict[str, float]]:
    """
    Calculate optimal bet amounts for arbitrage opportunities.
    
    Returns None if no arbitrage opportunity exists, otherwise returns a dict with:
    - primary_bet_cad: Amount to bet on primary market in CAD
    - polymarket_bet_cad: Amount to bet on Polymarket in CAD
    - polymarket_bet_usd: Amount to bet on Polymarket in USD
    - potential_profit_cad: Guaranteed profit in CAD
    """
    if primary_prob + poly_prob >= 1:
        return None
    
    cad_to_usd_rate = cad_to_usd_rate or get_exchange_rate()
    
    primary_decimal_odds = 1 / primary_prob
    poly_decimal_odds = 1 / poly_prob
    
    poly_bet_cad = (initial_bet * primary_decimal_odds) / poly_decimal_odds
    poly_bet_usd = poly_bet_cad * cad_to_usd_rate
    profit_cad = (initial_bet * primary_decimal_odds) - initial_bet - poly_bet_cad
    
    return {
        'primary_bet_cad': initial_bet,
        'polymarket_bet_cad': round(poly_bet_cad, 2),
        'polymarket_bet_usd': round(poly_bet_usd, 2),
        'potential_profit_cad': round(profit_cad, 2),
    }

def convert_to_est(date_str: str) -> datetime:
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
    
    est_tz = pytz.timezone('US/Eastern')
    return dt.astimezone(est_tz)

def process_arbitrage_opportunity(
    poly_team: str,
    poly_prob: float,
    opposing_team: str,
    primary_prob: float,
    bookmaker: str,
    poly_date: str,
    mira_date: str
) -> ArbitrageOpportunity:
    """Process and format an arbitrage opportunity"""
    poly_decimal = 1 / poly_prob
    primary_decimal = 1 / primary_prob
    bet_details = calculate_arbitrage_bets(primary_prob, poly_prob)
    
    return {
        'polymarket_team': poly_team,
        'polymarket_prob': poly_prob,
        'polymarket_decimal': poly_decimal,
        'primary_team': opposing_team,
        'primary_prob': primary_prob,
        'primary_decimal': primary_decimal,
        'bookmaker': bookmaker,
        'total_probability': poly_prob + primary_prob,
        'theoretical_profit': ((1 - (poly_prob + primary_prob)) * 100),
        'bet_details': bet_details,
        'polymarket_date': poly_date,
        'primary_date': mira_date
    }

def save_arbitrage_opportunities(opportunities: List[ArbitrageOpportunity]) -> None:
    """Save arbitrage opportunities to a file with improved visual formatting"""
    os.makedirs('arbOutput', exist_ok=True)
    
    # Clear previous files
    for file in glob.glob('arbOutput/arbitrage_opportunities_*.txt'):
        try:
            os.remove(file)
            print(f"Deleted previous file: {file}")
        except Exception as e:
            print(f"Error deleting file {file}: {e}")
    
    # Write new opportunities
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'arbOutput/arbitrage_opportunities_{timestamp}.txt'
    
    with open(filename, 'w') as f:
        f.write("╔══════════════════════════════════════════════════════════════╗\n")
        f.write("║                  ARBITRAGE OPPORTUNITIES                      ║\n")
        f.write("╚══════════════════════════════════════════════════════════════╝\n\n")
        
        # Add timestamp and scan summary
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"📅 Scan Time: {current_time}\n")
        f.write(f"📊 Opportunities Found: {len(opportunities)}\n")
        f.write("═" * 65 + "\n\n")

        if not opportunities:
            f.write("🔍 No arbitrage opportunities found in this scan.\n\n")
            f.write("💡 Possible reasons:\n")
            f.write("   • No matching games between markets\n")
            f.write("   • No profitable odds differences\n")
            f.write("   • All current games already started\n\n")
            f.write("╠" + "═" * 63 + "╣\n")
            return

        for idx, opp in enumerate(opportunities, 1):
            f.write(f"📊 Opportunity #{idx}\n")
            f.write("═" * 65 + "\n\n")
            
            # Event Details Section with enhanced matchup visibility
            f.write("🏀 EVENT DETAILS:\n")
            f.write("─" * 30 + "\n")
            f.write(f"Date: {opp['polymarket_date']}\n")
            f.write("\n")
            f.write("╭" + "─" * 40 + "╮\n")
            f.write("│" + " " * 40 + "│\n")
            f.write("│" + f"🏀  {opp['polymarket_team']} vs {opp['primary_team']}".center(40) + "│\n")
            f.write("│" + " " * 40 + "│\n")
            f.write("╰" + "─" * 40 + "╯\n\n")
            
            # Odds Section
            f.write("📈 ODDS COMPARISON:\n")
            f.write("─" * 30 + "\n")
            f.write(f"Polymarket ({opp['polymarket_team']}):\n")
            f.write(f"  • Decimal Odds: {opp['polymarket_decimal']:.2f}\n")
            f.write(f"  • Implied Probability: {opp['polymarket_prob']:.1%}\n\n")
            
            f.write(f"{opp['bookmaker']} ({opp['primary_team']}):\n")
            f.write(f"  • Decimal Odds: {opp['primary_decimal']:.2f}\n")
            f.write(f"  • Implied Probability: {opp['primary_prob']:.1%}\n\n")
            
            # Profit Analysis Section
            f.write("💰 PROFIT ANALYSIS:\n")
            f.write("─" * 30 + "\n")
            f.write(f"Total Market Probability: {opp['total_probability']:.1%}\n")
            f.write(f"Theoretical Edge: {opp['theoretical_profit']:.2f}%\n\n")
            
            # Betting Strategy Section
            f.write("🎯 RECOMMENDED BETS:\n")
            f.write("─" * 30 + "\n")
            f.write(f"Primary Market ({opp['bookmaker']}):\n")
            f.write(f"  • CAD ${opp['bet_details']['primary_bet_cad']:.2f}\n\n")
            f.write("Polymarket:\n")
            f.write(f"  • CAD ${opp['bet_details']['polymarket_bet_cad']:.2f}\n")
            f.write(f"  • USD ${opp['bet_details']['polymarket_bet_usd']:.2f}\n\n")
            
            f.write("Expected Profit:\n")
            f.write(f"  • CAD ${opp['bet_details']['potential_profit_cad']:.2f}\n")
            
            # Separator between opportunities
            f.write("\n" + "╠" + "═" * 63 + "╣\n\n")
        
        # Add summary footer
        f.write("╔══════════════════════════════════════════════════════════════╗\n")
        f.write(f"║ Total Opportunities: {len(opportunities)}".ljust(63) + "║\n")
        f.write("╚══════════════════════════════════════════════════════════════╝\n")

def find_matching_games():
    """Find matching games between Mira and Polymarket data and identify arbitrage opportunities"""
    print("\nStarting to find matching games...")
    
    # Load data files
    try:
        with open(MIRA_NBA, 'r') as f:
            mira_data = json.load(f)
        with open(POLYMARKET_NBA, 'r') as f:
            poly_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data files: {e}")
        return
    
    arbitrage_opportunities = []
    
    # Main matching logic
    for game_id, mira_game in mira_data['odds_data'].items():
        try:
            mira_date = datetime.strptime(mira_game['commence_time'], "%Y-%m-%d %H:%M:%S")
            mira_date = mira_date.replace(tzinfo=timezone.utc)  # Assume UTC if no timezone
            mira_date_est = mira_date.astimezone(pytz.timezone('US/Eastern'))
            
            if mira_date_est < datetime.now(pytz.timezone('US/Eastern')):
                continue
                
        except (ValueError, TypeError) as e:
            print(f"Error parsing date for game {game_id}: {e}")
            continue
        
        mira_teams = {normalize_team_name(team) for team in 
                     ([mira_game['away_team']] + list(mira_game['bookmakers'][0]['odds'].keys()))}
        print(f"\nLooking for match for Mira game: {mira_teams}")
        
        for poly_game in poly_data:
            try:
                poly_date = datetime.strptime(poly_game['endDate'], "%Y-%m-%d %H:%M:%S%z")
                poly_date_est = poly_date.astimezone(pytz.timezone('US/Eastern'))
                
                if poly_date_est < datetime.now(pytz.timezone('US/Eastern')):
                    continue
                
                if (poly_date_est.date() != mira_date_est.date() or 
                    abs((poly_date_est - mira_date_est).total_seconds()) > 3600):  # 1 hour tolerance
                    continue
                
                poly_teams = {normalize_team_name(team) for team in get_teams_from_title(poly_game['title'])}
                
                if mira_teams == poly_teams:
                    print(f"\nFound matching game!")
                    
                    best_primary_odds = {}
                    best_bookmakers = {}
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
                            if implied_prob < best_primary_odds[normalized_team]:
                                best_primary_odds[normalized_team] = implied_prob
                                best_bookmakers[normalized_team] = bookmaker['name']
                        print(f"Net implied probability: {total_implied_prob:.3f}")
                    
                    print(f"\nPolymarket odds:")
                    outcomes = eval(poly_game['markets'][0]['outcomes'])
                    prices = [float(price.strip('"')) for price in eval(poly_game['markets'][0]['outcomePrices'])]
                    poly_odds = {}
                    total_poly_prob = 0
                    for outcome, prob in zip(outcomes, prices):
                        print(f"{outcome}: {prob}")
                        poly_odds[outcome] = prob
                        total_poly_prob += prob
                    print(f"Net implied probability: {total_poly_prob}")
                    
                    for poly_team, poly_prob in poly_odds.items():
                        opposing_teams = mira_teams - {normalize_team_name(poly_team)}
                        if len(opposing_teams) != 1:
                            continue
                        opposing_team = list(opposing_teams)[0]
                        
                        primary_prob = best_primary_odds[opposing_team]
                        
                        if poly_prob + primary_prob < 1:
                            bet_details = calculate_arbitrage_bets(primary_prob, poly_prob)
                            poly_decimal = 1 / poly_prob
                            primary_decimal = 1 / primary_prob
                            
                            arb_opportunity = process_arbitrage_opportunity(
                                poly_team,
                                poly_prob,
                                opposing_team,
                                primary_prob,
                                best_bookmakers[opposing_team],
                                poly_game['endDate'],
                                mira_game['commence_time']
                            )
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

    save_arbitrage_opportunities(arbitrage_opportunities)

if __name__ == "__main__":
    find_matching_games()

