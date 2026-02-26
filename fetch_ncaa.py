import pandas as pd
import cbbpy.mens_scraper as s
import requests
from bs4 import BeautifulSoup
import datetime

def get_live_seeds():
    """Scrapes 2026 Projected Seeds from a Bracketology source."""
    # Using a common 2026 data endpoint for bracketology
    url = "https://barttorvik.com/tranketology.php" 
    try:
        header = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=header)
        # Pulling the main bracket table
        df_seeds = pd.read_html(response.text)[0]
        # Standardizing column names for 2026 schema
        df_seeds = df_seeds[['Team', 'Seed', 'Conf']].copy()
        return df_seeds.head(68)
    except Exception as e:
        print(f"Seed scrape failed: {e}. Using fallback data.")
        return pd.DataFrame({'Team': ['Duke', 'Kansas'], 'Seed': [1, 1], 'Conf': ['ACC', 'B12']})

def fetch_2026_stats():
    """Pulls season-to-date player and team stats."""
    current_year = 2026
    # Fetches all game data for the 2025-26 season
    game_info, boxscore, pbp = s.get_games_season(current_year)
    
    # Aggregate player stats to team level for 'Cinderella' detection
    team_stats = boxscore.groupby('team_display_name').agg({
        'pts': 'mean',
        'tov': 'mean',
        'tp': 'mean' # 3-pointers made
    }).reset_index()
    team_stats.rename(columns={'team_display_name': 'Team'}, inplace=True)
    return team_stats

def main():
    print(f"--- Starting NCAA Data Refresh: {datetime.date.today()} ---")
    
    seeds = get_live_seeds()
    stats = fetch_2026_stats()
    
    # Merge datasets
    final_df = pd.merge(seeds, stats, on='Team', how='left')
    
    # Cinderella Logic: High Seed (11+) + High 3pt production + Low Turnovers
    final_df['Cinderella_Potential'] = "Low"
    mask = (final_df['Seed'] >= 11) & (final_df['tp'] > 8) & (final_df['tov'] < 12)
    final_df.loc[mask, 'Cinderella_Potential'] = "HIGH"
    
    # Export to CSV
    final_df.to_csv('ncaa_data.csv', index=False)
    print("Update Complete: ncaa_data.csv generated.")

if __name__ == "__main__":
    main()