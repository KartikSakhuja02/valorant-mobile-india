from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os
from io import BytesIO
import requests  # For downloading test avatar

# =============================================================================
# MATCH HISTORY CONFIGURATION - CHANGE THESE NUMBERS TO ADJUST POSITIONS/SIZES
# =============================================================================

# --- Where to start the match history section ---
MATCH_START_Y = 780        # Move ALL matches UP (smaller) or DOWN (bigger)
MATCH_ROW_HEIGHT = 90      # Space between each match row

# ===== MATCH 1 (FIRST) =====
# Map Image
FIRST_MAP_X = 300
FIRST_MAP_Y_OFFSET = 49
FIRST_MAP_WIDTH = 290
FIRST_MAP_HEIGHT = 150
# Agent Icon
FIRST_AGENT_X = 320
FIRST_AGENT_Y_OFFSET = 68
FIRST_AGENT_SIZE = 85
# Score, K/D/A, Map Name
FIRST_SCORE_X = 475
FIRST_SCORE_Y_OFFSET = 150
FIRST_SCORE_FONT_SIZE = 24
FIRST_KDA_X = 329
FIRST_KDA_Y_OFFSET = 165
FIRST_KDA_FONT_SIZE = 20
FIRST_MAP_NAME_X = 450
FIRST_MAP_NAME_Y_OFFSET = 95
FIRST_MAP_NAME_FONT_SIZE = 30

# ===== MATCH 2 (SECOND) =====
# Map Image
SECOND_MAP_X = 635
SECOND_MAP_Y_OFFSET = -42
SECOND_MAP_WIDTH = 290
SECOND_MAP_HEIGHT = 150
# Agent Icon
SECOND_AGENT_X = 655
SECOND_AGENT_Y_OFFSET = -20
SECOND_AGENT_SIZE = 85
# Score, K/D/A, Map Name
SECOND_SCORE_X = 800
SECOND_SCORE_Y_OFFSET = 55
SECOND_SCORE_FONT_SIZE = 24
SECOND_KDA_X = 660
SECOND_KDA_Y_OFFSET = 73
SECOND_KDA_FONT_SIZE = 20
SECOND_MAP_NAME_X = 795
SECOND_MAP_NAME_Y_OFFSET = 5
SECOND_MAP_NAME_FONT_SIZE = 30

# ===== MATCH 3 (THIRD) =====
# Map Image
THIRD_MAP_X = 970
THIRD_MAP_Y_OFFSET = -131
THIRD_MAP_WIDTH = 290
THIRD_MAP_HEIGHT = 150
# Agent Icon
THIRD_AGENT_X = 1000
THIRD_AGENT_Y_OFFSET = -110
THIRD_AGENT_SIZE = 85
# Score, K/D/A, Map Name
THIRD_SCORE_X = 1140
THIRD_SCORE_Y_OFFSET = -39
THIRD_SCORE_FONT_SIZE = 24
THIRD_KDA_X = 1002
THIRD_KDA_Y_OFFSET = -18
THIRD_KDA_FONT_SIZE = 20
THIRD_MAP_NAME_X = 1120
THIRD_MAP_NAME_Y_OFFSET = -90
THIRD_MAP_NAME_FONT_SIZE = 30

# ===== MATCH 4 (FOURTH) =====
# Map Image
FOURTH_MAP_X = 1310
FOURTH_MAP_Y_OFFSET = -219
FOURTH_MAP_WIDTH = 290
FOURTH_MAP_HEIGHT = 150
# Agent Icon
FOURTH_AGENT_X = 1330
FOURTH_AGENT_Y_OFFSET = -200
FOURTH_AGENT_SIZE = 85
# Score, K/D/A, Map Name
FOURTH_SCORE_X = 1490
FOURTH_SCORE_Y_OFFSET = -130
FOURTH_SCORE_FONT_SIZE = 24
FOURTH_KDA_X = 1335
FOURTH_KDA_Y_OFFSET = -105
FOURTH_KDA_FONT_SIZE = 20
FOURTH_MAP_NAME_X = 1465
FOURTH_MAP_NAME_Y_OFFSET = -180
FOURTH_MAP_NAME_FONT_SIZE = 30

# ===== MATCH 5 (FIFTH) =====
# Map Image
FIFTH_MAP_X = 100
FIFTH_MAP_Y_OFFSET = 0
FIFTH_MAP_WIDTH = 100
FIFTH_MAP_HEIGHT = 60
# Agent Icon
FIFTH_AGENT_X = 220
FIFTH_AGENT_Y_OFFSET = -10
FIFTH_AGENT_SIZE = 80
# Score, K/D/A, Map Name
FIFTH_SCORE_X = 320
FIFTH_SCORE_Y_OFFSET = 20
FIFTH_SCORE_FONT_SIZE = 24
FIFTH_KDA_X = 470
FIFTH_KDA_Y_OFFSET = 20
FIFTH_KDA_FONT_SIZE = 24
FIFTH_MAP_NAME_X = 650
FIFTH_MAP_NAME_Y_OFFSET = 20
FIFTH_MAP_NAME_FONT_SIZE = 24

# ===== MATCH 6 (SIXTH) =====
# Map Image
SIXTH_MAP_X = 100
SIXTH_MAP_Y_OFFSET = 0
SIXTH_MAP_WIDTH = 100
SIXTH_MAP_HEIGHT = 60
# Agent Icon
SIXTH_AGENT_X = 220
SIXTH_AGENT_Y_OFFSET = -10
SIXTH_AGENT_SIZE = 80
# Score, K/D/A, Map Name
SIXTH_SCORE_X = 320
SIXTH_SCORE_Y_OFFSET = 20
SIXTH_SCORE_FONT_SIZE = 24
SIXTH_KDA_X = 470
SIXTH_KDA_Y_OFFSET = 20
SIXTH_KDA_FONT_SIZE = 24
SIXTH_MAP_NAME_X = 650
SIXTH_MAP_NAME_Y_OFFSET = 20
SIXTH_MAP_NAME_FONT_SIZE = 24

# ===== MATCH 7 (SEVENTH) =====
# Map Image
SEVENTH_MAP_X = 100
SEVENTH_MAP_Y_OFFSET = 0
SEVENTH_MAP_WIDTH = 100
SEVENTH_MAP_HEIGHT = 60
# Agent Icon
SEVENTH_AGENT_X = 220
SEVENTH_AGENT_Y_OFFSET = -10
SEVENTH_AGENT_SIZE = 80
# Score, K/D/A, Map Name
SEVENTH_SCORE_X = 320
SEVENTH_SCORE_Y_OFFSET = 20
SEVENTH_SCORE_FONT_SIZE = 24
SEVENTH_KDA_X = 470
SEVENTH_KDA_Y_OFFSET = 20
SEVENTH_KDA_FONT_SIZE = 24
SEVENTH_MAP_NAME_X = 650
SEVENTH_MAP_NAME_Y_OFFSET = 20
SEVENTH_MAP_NAME_FONT_SIZE = 24

# ===== MATCH 8 (EIGHTH) =====
# Map Image
EIGHTH_MAP_X = 100
EIGHTH_MAP_Y_OFFSET = 0
EIGHTH_MAP_WIDTH = 100
EIGHTH_MAP_HEIGHT = 60
# Agent Icon
EIGHTH_AGENT_X = 220
EIGHTH_AGENT_Y_OFFSET = -10
EIGHTH_AGENT_SIZE = 80
# Score, K/D/A, Map Name
EIGHTH_SCORE_X = 320
EIGHTH_SCORE_Y_OFFSET = 20
EIGHTH_SCORE_FONT_SIZE = 24
EIGHTH_KDA_X = 470
EIGHTH_KDA_Y_OFFSET = 20
EIGHTH_KDA_FONT_SIZE = 24
EIGHTH_MAP_NAME_X = 650
EIGHTH_MAP_NAME_Y_OFFSET = 20
EIGHTH_MAP_NAME_FONT_SIZE = 24

# ===== MATCH 9 (NINTH) =====
# Map Image
NINTH_MAP_X = 100
NINTH_MAP_Y_OFFSET = 0
NINTH_MAP_WIDTH = 100
NINTH_MAP_HEIGHT = 60
# Agent Icon
NINTH_AGENT_X = 220
NINTH_AGENT_Y_OFFSET = -10
NINTH_AGENT_SIZE = 80
# Score, K/D/A, Map Name
NINTH_SCORE_X = 320
NINTH_SCORE_Y_OFFSET = 20
NINTH_SCORE_FONT_SIZE = 24
NINTH_KDA_X = 470
NINTH_KDA_Y_OFFSET = 20
NINTH_KDA_FONT_SIZE = 24
NINTH_MAP_NAME_X = 650
NINTH_MAP_NAME_Y_OFFSET = 20
NINTH_MAP_NAME_FONT_SIZE = 24

# ===== MATCH 10 (TENTH) =====
# Map Image
TENTH_MAP_X = 100
TENTH_MAP_Y_OFFSET = 0
TENTH_MAP_WIDTH = 100
TENTH_MAP_HEIGHT = 60
# Agent Icon
TENTH_AGENT_X = 220
TENTH_AGENT_Y_OFFSET = -10
TENTH_AGENT_SIZE = 80
# Score, K/D/A, Map Name
TENTH_SCORE_X = 320
TENTH_SCORE_Y_OFFSET = 20
TENTH_SCORE_FONT_SIZE = 24
TENTH_KDA_X = 470
TENTH_KDA_Y_OFFSET = 20
TENTH_KDA_FONT_SIZE = 24
TENTH_MAP_NAME_X = 650
TENTH_MAP_NAME_Y_OFFSET = 20
TENTH_MAP_NAME_FONT_SIZE = 24

# --- Colors ---
WIN_COLOR = "#00ff00"      # Green for wins
LOSS_COLOR = "#ff0000"     # Red for losses
KDA_COLOR = "#ffff23"      # Yellow for K/D/A

# --- Black Background Padding (Thickness) ---
SCORE_BG_PADDING = 3       # Padding around score text (bigger = thicker background)
KDA_BG_PADDING = 3       # Padding around K/D/A text (bigger = thicker background)
MAP_NAME_BG_PADDING = 3    # Padding around map name text (bigger = thicker background)

# =============================================================================

def create_test_profile():
    # Create output directory if it doesn't exist
    output_dir = Path("test")
    output_dir.mkdir(exist_ok=True)
    
    # Load the template image
    template_path = Path("imports/profile/Profile.jpg")
    font_path = Path("imports/font/Poppins-Bold.ttf")
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template image not found at {template_path}")
    if not font_path.exists():
        raise FileNotFoundError(f"Font file not found at {font_path}")
    
    # Open template image
    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)
    
    # Add avatar (using a sample Discord avatar or local test image)
    try:
        # You can either use a local test image:
        # avatar = Image.open("test/test_avatar.png")
        # Or download a sample avatar (replace with any image URL for testing)
        avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"
        response = requests.get(avatar_url)
        avatar = Image.open(BytesIO(response.content))
        
        # Resize avatar to desired size
        avatar_size = (250, 250)  # Adjust size as needed
        avatar = avatar.resize(avatar_size, Image.Resampling.LANCZOS)
        
        # Create circular mask
        mask = Image.new('L', avatar_size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size[0], avatar_size[1]), fill=255)
        
        # Apply circular mask
        output = Image.new('RGBA', avatar_size, (0, 0, 0, 0))
        output.paste(avatar, (0, 0))
        output.putalpha(mask)
        
        # Paste avatar onto profile image (adjust position as needed)
        avatar_pos = (819, 232)  # Adjust these coordinates to position the avatar
        img.paste(output, avatar_pos, output)
        
    except Exception as e:
        print(f"Error adding avatar: {e}")
        # Continue without avatar if there's an error
    
    # Define font sizes for each field
    font_sizes = {
        "discord": 26,        # Largest - Main identifier
        "in_game_id": 28,    # Primary game identity
        "rank": 28,          # Important status
        "region": 28,        # Important status
        "points": 28,        # Primary stats
        "kdr": 28,           # Primary stats
        "winrate": 28,       # Primary stats
        "kills": 28,         # Secondary stats
        "deaths": 28,        # Secondary stats
        "matches": 28,       # Secondary stats
        "mvp": 28,           # Secondary stats
        "created_at": 26,    # Additional info
        "discord_id": 28,    # Additional info
    }
    
    # Create font objects for each size
    fonts = {size: ImageFont.truetype(str(font_path), size) for size in set(font_sizes.values())}
    
    # Test data
    test_data = {
        "discord": "TestUser#1234",
        "created_at": "2025-10-18",
        "discord_id": "123456789",
        "in_game_id": "VALM#1234",
        "rank": "Diamond",
        "region": "Asia",
        "points": "1500",
        "kills": "150",
        "kdr": "1.5",
        "deaths": "100",
        "winrate": "65%",
        "matches": "50",
        "mvp": "10"
    }
    
    # Position for each field (adjust these coordinates to match your template)
    positions = {
        "discord": (930, 534),
        "created_at": (988, 578),
        "discord_id": (828, 617),
        "in_game_id": (1455, 185),
        "rank": (1403, 325),
        "region": (1380, 252),
        "points": (1670, 252),
        "kills": (1370, 505),
        "kdr": (1635, 505),
        "deaths": (1410, 575),
        "winrate": (1685, 575),
        "matches": (1430, 645),
        "mvp": (1640, 645)
    }
    
    # Draw each field with its specific font size
    for field, pos in positions.items():
        text = str(test_data[field])  # Just display the value without the field label
        # Get the appropriate font for this field
        field_size = font_sizes[field]
        current_font = fonts[field_size]
        draw.text(pos, text, fill="#ffff23", font=current_font)  # Bright yellow color
    
    # ===== ADD MATCH HISTORY SECTION =====
    print("Adding match history...")
    print(f"\nCurrent Configuration:")
    print(f"  Match Start Y: {MATCH_START_Y}")
    print(f"  Row Height: {MATCH_ROW_HEIGHT}")
    
    # Configuration for each match (ALL settings per match)
    match_configs = [
        # FIRST Match
        {"map_x": FIRST_MAP_X, "map_y_offset": FIRST_MAP_Y_OFFSET, "map_width": FIRST_MAP_WIDTH, "map_height": FIRST_MAP_HEIGHT,
         "agent_x": FIRST_AGENT_X, "agent_y_offset": FIRST_AGENT_Y_OFFSET, "agent_size": FIRST_AGENT_SIZE,
         "score_x": FIRST_SCORE_X, "score_y_offset": FIRST_SCORE_Y_OFFSET, "score_font_size": FIRST_SCORE_FONT_SIZE,
         "kda_x": FIRST_KDA_X, "kda_y_offset": FIRST_KDA_Y_OFFSET, "kda_font_size": FIRST_KDA_FONT_SIZE,
         "map_name_x": FIRST_MAP_NAME_X, "map_name_y_offset": FIRST_MAP_NAME_Y_OFFSET, "map_name_font_size": FIRST_MAP_NAME_FONT_SIZE},
        # SECOND Match
        {"map_x": SECOND_MAP_X, "map_y_offset": SECOND_MAP_Y_OFFSET, "map_width": SECOND_MAP_WIDTH, "map_height": SECOND_MAP_HEIGHT,
         "agent_x": SECOND_AGENT_X, "agent_y_offset": SECOND_AGENT_Y_OFFSET, "agent_size": SECOND_AGENT_SIZE,
         "score_x": SECOND_SCORE_X, "score_y_offset": SECOND_SCORE_Y_OFFSET, "score_font_size": SECOND_SCORE_FONT_SIZE,
         "kda_x": SECOND_KDA_X, "kda_y_offset": SECOND_KDA_Y_OFFSET, "kda_font_size": SECOND_KDA_FONT_SIZE,
         "map_name_x": SECOND_MAP_NAME_X, "map_name_y_offset": SECOND_MAP_NAME_Y_OFFSET, "map_name_font_size": SECOND_MAP_NAME_FONT_SIZE},
        # THIRD Match
        {"map_x": THIRD_MAP_X, "map_y_offset": THIRD_MAP_Y_OFFSET, "map_width": THIRD_MAP_WIDTH, "map_height": THIRD_MAP_HEIGHT,
         "agent_x": THIRD_AGENT_X, "agent_y_offset": THIRD_AGENT_Y_OFFSET, "agent_size": THIRD_AGENT_SIZE,
         "score_x": THIRD_SCORE_X, "score_y_offset": THIRD_SCORE_Y_OFFSET, "score_font_size": THIRD_SCORE_FONT_SIZE,
         "kda_x": THIRD_KDA_X, "kda_y_offset": THIRD_KDA_Y_OFFSET, "kda_font_size": THIRD_KDA_FONT_SIZE,
         "map_name_x": THIRD_MAP_NAME_X, "map_name_y_offset": THIRD_MAP_NAME_Y_OFFSET, "map_name_font_size": THIRD_MAP_NAME_FONT_SIZE},
        # FOURTH Match
        {"map_x": FOURTH_MAP_X, "map_y_offset": FOURTH_MAP_Y_OFFSET, "map_width": FOURTH_MAP_WIDTH, "map_height": FOURTH_MAP_HEIGHT,
         "agent_x": FOURTH_AGENT_X, "agent_y_offset": FOURTH_AGENT_Y_OFFSET, "agent_size": FOURTH_AGENT_SIZE,
         "score_x": FOURTH_SCORE_X, "score_y_offset": FOURTH_SCORE_Y_OFFSET, "score_font_size": FOURTH_SCORE_FONT_SIZE,
         "kda_x": FOURTH_KDA_X, "kda_y_offset": FOURTH_KDA_Y_OFFSET, "kda_font_size": FOURTH_KDA_FONT_SIZE,
         "map_name_x": FOURTH_MAP_NAME_X, "map_name_y_offset": FOURTH_MAP_NAME_Y_OFFSET, "map_name_font_size": FOURTH_MAP_NAME_FONT_SIZE},
        # FIFTH Match
        {"map_x": FIFTH_MAP_X, "map_y_offset": FIFTH_MAP_Y_OFFSET, "map_width": FIFTH_MAP_WIDTH, "map_height": FIFTH_MAP_HEIGHT,
         "agent_x": FIFTH_AGENT_X, "agent_y_offset": FIFTH_AGENT_Y_OFFSET, "agent_size": FIFTH_AGENT_SIZE,
         "score_x": FIFTH_SCORE_X, "score_y_offset": FIFTH_SCORE_Y_OFFSET, "score_font_size": FIFTH_SCORE_FONT_SIZE,
         "kda_x": FIFTH_KDA_X, "kda_y_offset": FIFTH_KDA_Y_OFFSET, "kda_font_size": FIFTH_KDA_FONT_SIZE,
         "map_name_x": FIFTH_MAP_NAME_X, "map_name_y_offset": FIFTH_MAP_NAME_Y_OFFSET, "map_name_font_size": FIFTH_MAP_NAME_FONT_SIZE},
        # SIXTH Match
        {"map_x": SIXTH_MAP_X, "map_y_offset": SIXTH_MAP_Y_OFFSET, "map_width": SIXTH_MAP_WIDTH, "map_height": SIXTH_MAP_HEIGHT,
         "agent_x": SIXTH_AGENT_X, "agent_y_offset": SIXTH_AGENT_Y_OFFSET, "agent_size": SIXTH_AGENT_SIZE,
         "score_x": SIXTH_SCORE_X, "score_y_offset": SIXTH_SCORE_Y_OFFSET, "score_font_size": SIXTH_SCORE_FONT_SIZE,
         "kda_x": SIXTH_KDA_X, "kda_y_offset": SIXTH_KDA_Y_OFFSET, "kda_font_size": SIXTH_KDA_FONT_SIZE,
         "map_name_x": SIXTH_MAP_NAME_X, "map_name_y_offset": SIXTH_MAP_NAME_Y_OFFSET, "map_name_font_size": SIXTH_MAP_NAME_FONT_SIZE},
        # SEVENTH Match
        {"map_x": SEVENTH_MAP_X, "map_y_offset": SEVENTH_MAP_Y_OFFSET, "map_width": SEVENTH_MAP_WIDTH, "map_height": SEVENTH_MAP_HEIGHT,
         "agent_x": SEVENTH_AGENT_X, "agent_y_offset": SEVENTH_AGENT_Y_OFFSET, "agent_size": SEVENTH_AGENT_SIZE,
         "score_x": SEVENTH_SCORE_X, "score_y_offset": SEVENTH_SCORE_Y_OFFSET, "score_font_size": SEVENTH_SCORE_FONT_SIZE,
         "kda_x": SEVENTH_KDA_X, "kda_y_offset": SEVENTH_KDA_Y_OFFSET, "kda_font_size": SEVENTH_KDA_FONT_SIZE,
         "map_name_x": SEVENTH_MAP_NAME_X, "map_name_y_offset": SEVENTH_MAP_NAME_Y_OFFSET, "map_name_font_size": SEVENTH_MAP_NAME_FONT_SIZE},
        # EIGHTH Match
        {"map_x": EIGHTH_MAP_X, "map_y_offset": EIGHTH_MAP_Y_OFFSET, "map_width": EIGHTH_MAP_WIDTH, "map_height": EIGHTH_MAP_HEIGHT,
         "agent_x": EIGHTH_AGENT_X, "agent_y_offset": EIGHTH_AGENT_Y_OFFSET, "agent_size": EIGHTH_AGENT_SIZE,
         "score_x": EIGHTH_SCORE_X, "score_y_offset": EIGHTH_SCORE_Y_OFFSET, "score_font_size": EIGHTH_SCORE_FONT_SIZE,
         "kda_x": EIGHTH_KDA_X, "kda_y_offset": EIGHTH_KDA_Y_OFFSET, "kda_font_size": EIGHTH_KDA_FONT_SIZE,
         "map_name_x": EIGHTH_MAP_NAME_X, "map_name_y_offset": EIGHTH_MAP_NAME_Y_OFFSET, "map_name_font_size": EIGHTH_MAP_NAME_FONT_SIZE},
        # NINTH Match
        {"map_x": NINTH_MAP_X, "map_y_offset": NINTH_MAP_Y_OFFSET, "map_width": NINTH_MAP_WIDTH, "map_height": NINTH_MAP_HEIGHT,
         "agent_x": NINTH_AGENT_X, "agent_y_offset": NINTH_AGENT_Y_OFFSET, "agent_size": NINTH_AGENT_SIZE,
         "score_x": NINTH_SCORE_X, "score_y_offset": NINTH_SCORE_Y_OFFSET, "score_font_size": NINTH_SCORE_FONT_SIZE,
         "kda_x": NINTH_KDA_X, "kda_y_offset": NINTH_KDA_Y_OFFSET, "kda_font_size": NINTH_KDA_FONT_SIZE,
         "map_name_x": NINTH_MAP_NAME_X, "map_name_y_offset": NINTH_MAP_NAME_Y_OFFSET, "map_name_font_size": NINTH_MAP_NAME_FONT_SIZE},
        # TENTH Match
        {"map_x": TENTH_MAP_X, "map_y_offset": TENTH_MAP_Y_OFFSET, "map_width": TENTH_MAP_WIDTH, "map_height": TENTH_MAP_HEIGHT,
         "agent_x": TENTH_AGENT_X, "agent_y_offset": TENTH_AGENT_Y_OFFSET, "agent_size": TENTH_AGENT_SIZE,
         "score_x": TENTH_SCORE_X, "score_y_offset": TENTH_SCORE_Y_OFFSET, "score_font_size": TENTH_SCORE_FONT_SIZE,
         "kda_x": TENTH_KDA_X, "kda_y_offset": TENTH_KDA_Y_OFFSET, "kda_font_size": TENTH_KDA_FONT_SIZE,
         "map_name_x": TENTH_MAP_NAME_X, "map_name_y_offset": TENTH_MAP_NAME_Y_OFFSET, "map_name_font_size": TENTH_MAP_NAME_FONT_SIZE},
    ]
    
    # Test match history data (last 10 matches)
    match_history = [
        {"map": "Ascent", "agent": "Jett", "team_score": "13-11", "player_score": "25/15/5", "won": True},
        {"map": "Bind", "agent": "Sage", "team_score": "10-13", "player_score": "18/20/8", "won": False},
        {"map": "Haven", "agent": "Phoenix", "team_score": "13-9", "player_score": "22/14/6", "won": True},
        {"map": "Icebox", "agent": "Reyna", "team_score": "11-13", "player_score": "20/18/4", "won": False},
        {"map": "Split", "agent": "Jett", "team_score": "13-7", "player_score": "28/12/7", "won": True},
        {"map": "Ascent", "agent": "Omen", "team_score": "13-10", "player_score": "21/16/9", "won": True},
        {"map": "Bind", "agent": "Cypher", "team_score": "9-13", "player_score": "15/19/6", "won": False},
        {"map": "Haven", "agent": "Jett", "team_score": "13-8", "player_score": "30/10/4", "won": True},
        {"map": "Icebox", "agent": "Killjoy", "team_score": "12-13", "player_score": "19/20/7", "won": False},
        {"map": "Split", "agent": "Raze", "team_score": "13-6", "player_score": "26/11/8", "won": True},
    ]
    
    for i, match in enumerate(match_history):
        y_pos = MATCH_START_Y + (i * MATCH_ROW_HEIGHT)
        config = match_configs[i]
        
        print(f"\nMatch {i+1} at Y={y_pos}:")
        
        # 1. Add Map Image
        try:
            map_img_path = Path(f"imports/maps/{match['map']}.jpg")
            map_y = y_pos + config["map_y_offset"]
            
            if map_img_path.exists():
                map_img = Image.open(map_img_path)
                map_img = map_img.resize((config["map_width"], config["map_height"]), Image.Resampling.LANCZOS)
                img.paste(map_img, (config["map_x"], map_y))
                print(f"  Map '{match['map']}': Position=({config['map_x']}, {map_y}), Size=({config['map_width']}, {config['map_height']})")
            else:
                # Draw placeholder if map image not found
                draw.rectangle([config["map_x"], map_y, config["map_x"] + config["map_width"], map_y + config["map_height"]], 
                             outline="white", width=2)
                # Use score font for placeholder text
                score_font = ImageFont.truetype(str(font_path), config["score_font_size"])
                draw.text((config["map_x"] + 5, map_y + 20), match['map'], 
                         fill="white", font=score_font)
                print(f"  Map '{match['map']}': NOT FOUND - Placeholder drawn")
        except Exception as e:
            print(f"  Error loading map image for {match['map']}: {e}")
        
        # 2. Add Agent Icon
        try:
            # Look for agent image in agents images folder
            agent_folder = Path("imports/agents images")
            agent_file = None
            agent_y = y_pos + config["agent_y_offset"]
            agent_size = config["agent_size"]
            
            # Try to find agent file (case-insensitive search)
            if agent_folder.exists():
                for file in agent_folder.iterdir():
                    if match['agent'].lower() in file.stem.lower():
                        agent_file = file
                        break
            
            if agent_file and agent_file.exists():
                agent_img = Image.open(agent_file)
                agent_img = agent_img.resize((agent_size, agent_size), Image.Resampling.LANCZOS)
                
                # Make circular agent icon
                mask = Image.new('L', (agent_size, agent_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, agent_size, agent_size), fill=255)
                
                output = Image.new('RGBA', (agent_size, agent_size), (0, 0, 0, 0))
                output.paste(agent_img, (0, 0))
                output.putalpha(mask)
                
                img.paste(output, (config["agent_x"], agent_y), output)
                print(f"  Agent '{match['agent']}': Position=({config['agent_x']}, {agent_y}), Size={agent_size}")
            else:
                # Draw placeholder if agent image not found
                score_font = ImageFont.truetype(str(font_path), config["score_font_size"])
                draw.ellipse([config["agent_x"], agent_y, config["agent_x"] + agent_size, agent_y + agent_size], 
                           outline="white", width=2)
                draw.text((config["agent_x"] + 10, agent_y + 30), match['agent'][:3], 
                         fill="white", font=score_font)
                print(f"  Agent '{match['agent']}': NOT FOUND - Placeholder drawn")
        except Exception as e:
            print(f"  Error loading agent image for {match['agent']}: {e}")
        
        # 3. Add Team Score (with black background)
        score_color = WIN_COLOR if match['won'] else LOSS_COLOR
        score_y = y_pos + config["score_y_offset"]
        score_font = ImageFont.truetype(str(font_path), config["score_font_size"])
        
        # Get text bounding box for background
        score_bbox = draw.textbbox((config["score_x"], score_y), match['team_score'], font=score_font)
        # Add padding around text (use configurable thickness)
        draw.rectangle([score_bbox[0] - SCORE_BG_PADDING, score_bbox[1] - SCORE_BG_PADDING, 
                       score_bbox[2] + SCORE_BG_PADDING, score_bbox[3] + SCORE_BG_PADDING], 
                      fill="black")
        # Draw text on top of black background
        draw.text((config["score_x"], score_y), match['team_score'], 
                 fill=score_color, font=score_font)
        print(f"  Team Score '{match['team_score']}': Position=({config['score_x']}, {score_y}), Color={score_color}")
        
        # 4. Add Player K/D/A (with black background)
        kda_y = y_pos + config["kda_y_offset"]
        kda_font = ImageFont.truetype(str(font_path), config["kda_font_size"])
        
        # Get text bounding box for background
        kda_bbox = draw.textbbox((config["kda_x"], kda_y), match['player_score'], font=kda_font)
        # Add padding around text (use configurable thickness)
        draw.rectangle([kda_bbox[0] - KDA_BG_PADDING, kda_bbox[1] - KDA_BG_PADDING, 
                       kda_bbox[2] + KDA_BG_PADDING, kda_bbox[3] + KDA_BG_PADDING], 
                      fill="black")
        # Draw text on top of black background
        draw.text((config["kda_x"], kda_y), match['player_score'], 
                 fill=KDA_COLOR, font=kda_font)
        print(f"  K/D/A '{match['player_score']}': Position=({config['kda_x']}, {kda_y}), Color={KDA_COLOR}")
        
        # 5. Add Map Name (with black background, colored based on win/loss)
        map_name_color = WIN_COLOR if match['won'] else LOSS_COLOR
        map_name_y = y_pos + config["map_name_y_offset"]
        map_name_font = ImageFont.truetype(str(font_path), config["map_name_font_size"])
        
        # Get text bounding box for background
        map_name_bbox = draw.textbbox((config["map_name_x"], map_name_y), match['map'], font=map_name_font)
        # Add padding around text (use configurable thickness)
        draw.rectangle([map_name_bbox[0] - MAP_NAME_BG_PADDING, map_name_bbox[1] - MAP_NAME_BG_PADDING, 
                       map_name_bbox[2] + MAP_NAME_BG_PADDING, map_name_bbox[3] + MAP_NAME_BG_PADDING], 
                      fill="black")
        # Draw text on top of black background
        draw.text((config["map_name_x"], map_name_y), match['map'], 
                 fill=map_name_color, font=map_name_font)
        print(f"  Map Name '{match['map']}': Position=({config['map_name_x']}, {map_name_y}), Color={map_name_color}")
    
    print("\nMatch history added successfully!")
    print(f"\n{'='*60}")
    print("To adjust alignment, edit values at the top of this file")
    print(f"{'='*60}\n")
    
    # Save the result
    output_path = output_dir / "test_profile.jpg"
    img.save(output_path)
    print(f"Test profile saved to {output_path}")

if __name__ == "__main__":
    create_test_profile()
