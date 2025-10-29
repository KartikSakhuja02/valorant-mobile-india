"""
Test script for aligning player leaderboard text positions
Run this to verify text placement on Individual-Leaderboard.jpg template
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / 'imports' / 'leaderboard'
FONT_DIR = BASE_DIR / 'imports' / 'font'

# Font settings
FONT_PATH = FONT_DIR / 'Lato-Bold.ttf'
ROW_FONT_SIZE = 75

# Text Colors
RANK_COLOR = "#000000"      # Black for rank numbers
PLAYER_NAME_COLOR = "#ffff23" # Bright yellow for player names
KILLS_COLOR = "#ffff23"     # Bright yellow for kills
DEATHS_COLOR = "#ffff23"    # Bright yellow for deaths
ASSISTS_COLOR = "#ffff23"   # Bright yellow for assists
MVP_COLOR = "#ffff23"       # Bright yellow for MVP count
POINTS_COLOR = "#ffff23"    # Bright yellow for points

# Template path
TEMPLATE_PATH = TEMPLATE_DIR / 'Individual_Leaderboard.jpg'

# Player Configuration - 14 rows of sample data
# Adjust these X and Y coordinates to align text properly on your template
# Fields: Rank, Name, Kills, Deaths, Assists, MVP, Points
PLAYER_CONFIG = {
    'rows': [
        # Row 1
        {'rank': 1, 'rank_x': 450, 'rank_y': 960, 'player_name_x': 825, 'player_name_y': 955,
         'kills_x': 1510, 'kills_y': 955, 'deaths_x': 1950, 'deaths_y': 955,
         'assists_x': 2400, 'assists_y': 955, 'mvp_x': 2900, 'mvp_y': 955, 'points_x': 3300, 'points_y': 955},
        # Row 2
        {'rank': 2, 'rank_x': 450, 'rank_y': 1100, 'player_name_x': 825, 'player_name_y': 1100,
         'kills_x': 1510, 'kills_y': 1100, 'deaths_x': 1950, 'deaths_y': 1100,
         'assists_x': 2400, 'assists_y': 1100, 'mvp_x': 2900, 'mvp_y': 1100, 'points_x': 3300, 'points_y': 1100},
        # Row 3
        {'rank': 3, 'rank_x': 450, 'rank_y': 1250, 'player_name_x': 825, 'player_name_y': 1245,
         'kills_x': 1510, 'kills_y': 1245, 'deaths_x': 1950, 'deaths_y': 1245,
         'assists_x': 2400, 'assists_y': 1245, 'mvp_x': 2900, 'mvp_y': 1245, 'points_x': 3300, 'points_y': 1245},
        # Row 4
        {'rank': 4, 'rank_x': 450, 'rank_y': 1400, 'player_name_x': 825, 'player_name_y': 1395,
         'kills_x': 1510, 'kills_y': 1395, 'deaths_x': 1950, 'deaths_y': 1395,
         'assists_x': 2400, 'assists_y': 1395, 'mvp_x': 2900, 'mvp_y': 1395, 'points_x': 3300, 'points_y': 1395},
        # Row 5
        {'rank': 5, 'rank_x': 450, 'rank_y': 1550, 'player_name_x': 825, 'player_name_y': 1545,
         'kills_x': 1510, 'kills_y': 1545, 'deaths_x': 1950, 'deaths_y': 1545,
         'assists_x': 2400, 'assists_y': 1545, 'mvp_x': 2900, 'mvp_y': 1545, 'points_x': 3300, 'points_y': 1545},
        # Row 6
        {'rank': 6, 'rank_x': 450, 'rank_y': 1690, 'player_name_x': 825, 'player_name_y': 1685,
         'kills_x': 1510, 'kills_y': 1685, 'deaths_x': 1950, 'deaths_y': 1685,
         'assists_x': 2400, 'assists_y': 1685, 'mvp_x': 2900, 'mvp_y': 1685, 'points_x': 3300, 'points_y': 1685},
        # Row 7
        {'rank': 7, 'rank_x': 450, 'rank_y': 1845, 'player_name_x': 825, 'player_name_y': 1840,
         'kills_x': 1510, 'kills_y': 1840, 'deaths_x': 1950, 'deaths_y': 1840,
         'assists_x': 2400, 'assists_y': 1840, 'mvp_x': 2900, 'mvp_y': 1840, 'points_x': 3300, 'points_y': 1840},
        # Row 8
        {'rank': 8, 'rank_x': 450, 'rank_y': 1990, 'player_name_x': 825, 'player_name_y': 1985,
         'kills_x': 1510, 'kills_y': 1985, 'deaths_x': 1950, 'deaths_y': 1985,
         'assists_x': 2400, 'assists_y': 1985, 'mvp_x': 2900, 'mvp_y': 1985, 'points_x': 3300, 'points_y': 1985},
        # Row 9
        {'rank': 9, 'rank_x': 450, 'rank_y': 2130, 'player_name_x': 825, 'player_name_y': 2125,
         'kills_x': 1510, 'kills_y': 2125, 'deaths_x': 1950, 'deaths_y': 2125,
         'assists_x': 2400, 'assists_y': 2125, 'mvp_x': 2900, 'mvp_y': 2125, 'points_x': 3300, 'points_y': 2125},
        # Row 10
        {'rank': 10, 'rank_x': 450, 'rank_y': 2280, 'player_name_x': 825, 'player_name_y': 2280,
         'kills_x': 1510, 'kills_y': 2280, 'deaths_x': 1950, 'deaths_y': 2280,
         'assists_x': 2400, 'assists_y': 2280, 'mvp_x': 2900, 'mvp_y': 2280, 'points_x': 3300, 'points_y': 2280},
        # Row 11
        {'rank': 11, 'rank_x': 450, 'rank_y': 2430, 'player_name_x': 825, 'player_name_y': 2425,
         'kills_x': 1510, 'kills_y': 2425, 'deaths_x': 1950, 'deaths_y': 2425,
         'assists_x': 2400, 'assists_y': 2425, 'mvp_x': 2900, 'mvp_y': 2425, 'points_x': 3300, 'points_y': 2425},
        # Row 12
        {'rank': 12, 'rank_x': 450, 'rank_y': 2580, 'player_name_x': 825, 'player_name_y': 2575,
         'kills_x': 1510, 'kills_y': 2575, 'deaths_x': 1950, 'deaths_y': 2575,
         'assists_x': 2400, 'assists_y': 2575, 'mvp_x': 2900, 'mvp_y': 2575, 'points_x': 3300, 'points_y': 2575},
        # Row 13
        {'rank': 13, 'rank_x': 450, 'rank_y': 2730, 'player_name_x': 825, 'player_name_y': 2725,
         'kills_x': 1510, 'kills_y': 2725, 'deaths_x': 1950, 'deaths_y': 2725,
         'assists_x': 2400, 'assists_y': 2725, 'mvp_x': 2900, 'mvp_y': 2725, 'points_x': 3300, 'points_y': 2725},
        # Row 14
        {'rank': 14, 'rank_x': 450, 'rank_y': 2880, 'player_name_x': 825, 'player_name_y': 2875,
         'kills_x': 1510, 'kills_y': 2875, 'deaths_x': 1950, 'deaths_y': 2875,
         'assists_x': 2400, 'assists_y': 2875, 'mvp_x': 2900, 'mvp_y': 2875, 'points_x': 3300, 'points_y': 2875},
    ]
}

# Sample player data for testing
SAMPLE_PLAYERS = [
    {'rank': 1, 'ign': 'Player One', 'kills': 245, 'deaths': 89, 'assists': 156, 'mvps': 12, 'points': 856.5},
    {'rank': 2, 'ign': 'PlayerTwo', 'kills': 198, 'deaths': 102, 'assists': 145, 'mvps': 9, 'points': 742.0},
    {'rank': 3, 'ign': 'ProGamer123', 'kills': 187, 'deaths': 95, 'assists': 134, 'mvps': 8, 'points': 698.3},
    {'rank': 4, 'ign': 'EliteShooter', 'kills': 176, 'deaths': 98, 'assists': 128, 'mvps': 7, 'points': 654.7},
    {'rank': 5, 'ign': 'TopFragger', 'kills': 165, 'deaths': 91, 'assists': 119, 'mvps': 6, 'points': 612.8},
    {'rank': 6, 'ign': 'AcePlayer', 'kills': 154, 'deaths': 87, 'assists': 112, 'mvps': 5, 'points': 578.2},
    {'rank': 7, 'ign': 'SkillMaster', 'kills': 143, 'deaths': 83, 'assists': 105, 'mvps': 5, 'points': 545.6},
    {'rank': 8, 'ign': 'Headshot99', 'kills': 132, 'deaths': 79, 'assists': 98, 'mvps': 4, 'points': 512.9},
    {'rank': 9, 'ign': 'Champion007', 'kills': 121, 'deaths': 75, 'assists': 91, 'mvps': 4, 'points': 481.3},
    {'rank': 10, 'ign': 'VictoryKing', 'kills': 110, 'deaths': 71, 'assists': 84, 'mvps': 3, 'points': 449.7},
    {'rank': 11, 'ign': 'RisingStar', 'kills': 99, 'deaths': 67, 'assists': 77, 'mvps': 3, 'points': 418.1},
    {'rank': 12, 'ign': 'LegendSlayer', 'kills': 88, 'deaths': 63, 'assists': 70, 'mvps': 2, 'points': 386.5},
    {'rank': 13, 'ign': 'BattleHero', 'kills': 77, 'deaths': 59, 'assists': 63, 'mvps': 2, 'points': 354.9},
    {'rank': 14, 'ign': 'WarriorX', 'kills': 66, 'deaths': 55, 'assists': 56, 'mvps': 1, 'points': 323.3},
]


def generate_test_image():
    """Generate test image with sample player data"""
    
    # Check if template exists
    if not TEMPLATE_PATH.exists():
        print(f"❌ Template not found: {TEMPLATE_PATH}")
        print(f"Please create the Individual-Leaderboard.jpg template first!")
        return
    
    print(f"📂 Loading template: {TEMPLATE_PATH}")
    
    # Load template
    img = Image.open(TEMPLATE_PATH)
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    
    # Load font
    try:
        font = ImageFont.truetype(str(FONT_PATH), ROW_FONT_SIZE)
        print(f"✅ Font loaded: {FONT_PATH}")
    except Exception as e:
        print(f"⚠️  Could not load font {FONT_PATH}: {e}")
        font = ImageFont.load_default()
    
    print(f"\n🎨 Drawing {len(SAMPLE_PLAYERS)} players...")
    
    # Draw each player
    for idx, player in enumerate(SAMPLE_PLAYERS):
        if idx >= len(PLAYER_CONFIG['rows']):
            break
            
        row_config = PLAYER_CONFIG['rows'][idx]
        
        # Rank (Black)
        rank_text = str(player['rank'])
        draw.text((row_config['rank_x'], row_config['rank_y']), 
                 rank_text, font=font, fill=RANK_COLOR)
        
        # Player IGN (Yellow)
        ign_text = player['ign']
        draw.text((row_config['player_name_x'], row_config['player_name_y']), 
                 ign_text, font=font, fill=PLAYER_NAME_COLOR)
        
        # Kills (Yellow)
        kills_text = str(player['kills'])
        draw.text((row_config['kills_x'], row_config['kills_y']), 
                 kills_text, font=font, fill=KILLS_COLOR)
        
        # Deaths (Yellow)
        deaths_text = str(player['deaths'])
        draw.text((row_config['deaths_x'], row_config['deaths_y']), 
                 deaths_text, font=font, fill=DEATHS_COLOR)
        
        # Assists (Yellow)
        assists_text = str(player['assists'])
        draw.text((row_config['assists_x'], row_config['assists_y']), 
                 assists_text, font=font, fill=ASSISTS_COLOR)
        
        # MVP (Yellow)
        mvp_text = str(player['mvps'])
        draw.text((row_config['mvp_x'], row_config['mvp_y']), 
                 mvp_text, font=font, fill=MVP_COLOR)
        
        # Points (Yellow)
        points_text = f"{player['points']:.1f}"
        draw.text((row_config['points_x'], row_config['points_y']), 
                 points_text, font=font, fill=POINTS_COLOR)
    
    # Save output
    output_path = BASE_DIR / 'test_player_leaderboard_output.jpg'
    img.save(output_path, format='JPEG', quality=95)
    
    print(f"\n✅ Test image saved: {output_path}")
    print(f"\n📊 Configuration Summary:")
    print(f"   • Template: Individual_Leaderboard.jpg (4000x3200px)")
    print(f"   • Font: Lato-Bold.ttf, Size: 75")
    print(f"   • Colors: Rank=#000000 (black), All other text=#ffff23 (yellow)")
    print(f"   • Fields: Rank, Name, Kills, Deaths, Assists, MVP, Points")
    print(f"   • Players: 14 rows")
    print(f"\n📝 To adjust alignment:")
    print(f"   1. Open test_player_leaderboard_output.jpg")
    print(f"   2. Check if text aligns with your template columns")
    print(f"   3. Edit the X and Y coordinates in PLAYER_CONFIG above")
    print(f"   4. Run this script again to test")
    print(f"   5. Once aligned, copy PLAYER_CONFIG to services/leaderboard_generator.py")
    print(f"\n💡 Each row has 7 fields with 14 coordinates (x, y for each field)")
    print(f"\n📋 Sample Data Values:")
    print(f"   • Rank: 1-14")
    print(f"   • Names: Various lengths (Player One, ProGamer123, etc.)")
    print(f"   • Kills: 66-245")
    print(f"   • Deaths: 55-102")
    print(f"   • Assists: 56-156")
    print(f"   • MVP: 1-12")
    print(f"   • Points: 323.3-856.5")


if __name__ == "__main__":
    print("=" * 70)
    print("🎯 Player Leaderboard Alignment Test Script")
    print("=" * 70)
    generate_test_image()
    print("=" * 70)
