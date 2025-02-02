from secondaryMarkets.polymarket.polymarket import PolymarketAPI
from secondaryMarkets.kalshi.kalshi import KalshiAPI
from nba.nbaSimSearch import find_matching_games
from nba.getNBAevents import get_nba_events_from_file, write_nba_events_to_file, get_mira_nba_events
import requests
import glob
import os
from datetime import datetime
import time

polymarket_api = PolymarketAPI()
file_path = 'jsonOutputs/gamma_events.json'
nbaFilePath = 'jsonOutputs/nbaEvents.json'

DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1306538886515785750/JIm5CjrQ49Yj5E8MBGOGTGrWvIbojn05jiG3jiGlJs5zlzWt30PZufR_72KI9yidpsGv"

def send_to_discord(content, code_block=True):
    if not content.strip():
        return
    
    # Split content into chunks of approximately 1900 characters (Discord limit is 2000)
    max_length = 1900
    chunks = []
    current_chunk = ""
    
    for line in content.split('\n'):
        if len(current_chunk) + len(line) + 2 > max_length:  # +2 for newline chars
            chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += (line + '\n')
    
    if current_chunk:
        chunks.append(current_chunk)
    
    # Send each chunk
    for chunk in chunks:
        payload = {
            "content": f"```{chunk}```" if code_block else chunk
        }
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code != 204:
            print(f"Failed to send Discord message: {response.status_code}")
        time.sleep(1)  # Add delay between messages to avoid rate limiting

def send_arbitrage_opportunities():
    # Get the most recent arbitrage file
    list_of_files = glob.glob('arbOutput/arbitrage_opportunities_*.txt')
    if not list_of_files:
        return
    latest_file = max(list_of_files, key=os.path.getctime)
    
    # Send current date and time first
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_to_discord(f"🔍 New Arbitrage Opportunities Found at: {current_time}", code_block=False)
    
    with open(latest_file, 'r') as file:
        content = file.read()
        # Split by the delimiter and filter out empty strings
        opportunities = [opp.strip() for opp in content.split('--------------------------------------------------') if opp.strip()]
        
        # Send header separately
        if opportunities and "ARBITRAGE OPPORTUNITIES" in opportunities[0]:
            header = opportunities.pop(0)
            send_to_discord(header)
        
        # Send each opportunity as a separate message
        for opportunity in opportunities:
            # Add some spacing and formatting
            formatted_opp = f"\n{opportunity}\n"
            send_to_discord(formatted_opp)
            time.sleep(0.5)  # Small delay between opportunities
    
    # Send footer
    footer = "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📊 End of Arbitrage Report 📊\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    send_to_discord(footer, code_block=False)

def fetch_polymarket_events():
    polymarket_api.get_and_save_all_events()

if __name__ == "__main__":
    fetch_polymarket_events()
    nba_events = get_nba_events_from_file(file_path)
    print("Writing NBA events from polymarket to file")
    write_nba_events_to_file(file_path, nbaFilePath)
    get_mira_nba_events()
    find_matching_games()
    send_arbitrage_opportunities()
    print("program finished")



