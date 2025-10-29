"""
Leaderboard Image Generator
Generates leaderboard images with team data overlaid on template backgrounds
"""

import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import asyncio
from services import db

# Paths
BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / 'imports' / 'leaderboard'
FONT_DIR = BASE_DIR / 'imports' / 'font'
OUTPUT_DIR = BASE_DIR / 'generated_leaderboards'

# Font settings
FONT_PATH = FONT_DIR / 'Lato-Bold.ttf'

# Leaderboard templates
LEADERBOARD_TEMPLATES = {
    'global': TEMPLATE_DIR / 'Global_Leaderboard.jpg',
    'apac': TEMPLATE_DIR / 'APAC_Leaderboard.jpg',
    'emea': TEMPLATE_DIR / 'EMEA_Leaderboard.jpg',
    'americas': TEMPLATE_DIR / 'General_Leaderboard.jpg',  # Using General for Americas
    'india': TEMPLATE_DIR / 'India_Leaderboard.jpg',
}

# Text positioning and styling (customize these based on your template)
# These are sample coordinates - you'll adjust them in the alignment test script
LEADERBOARD_CONFIG = {
    'apac': {
        'title_pos': (640, 100),  # Center top
        'title_size': 60,
        'title_color': (255, 255, 255),
        
        'header_y': 250,
        'header_size': 28,
        'header_color': (220, 220, 220),
        
        'rank_x': 120,
        'team_name_x': 240,
        'matches_x': 680,
        'wins_x': 800,
        'losses_x': 920,
        'points_x': 1100,
        
        'row_start_y': 320,
        'row_height': 65,
        'row_size': 32,
        'row_color': (255, 255, 255),
        
        'max_rows': 10,
    },
    'global': {
        'title_pos': (640, 100),
        'title_size': 60,
        'title_color': (255, 255, 255),
        
        'header_y': 250,
        'header_size': 28,
        'header_color': (220, 220, 220),
        
        'rank_x': 120,
        'team_name_x': 240,
        'matches_x': 680,
        'wins_x': 800,
        'losses_x': 920,
        'points_x': 1100,
        
        'row_start_y': 320,
        'row_height': 65,
        'row_size': 32,
        'row_color': (255, 255, 255),
        
        'max_rows': 10,
    },
    'emea': {
        'title_pos': (640, 100),
        'title_size': 60,
        'title_color': (255, 255, 255),
        
        'header_y': 250,
        'header_size': 28,
        'header_color': (220, 220, 220),
        
        'rank_x': 120,
        'team_name_x': 240,
        'matches_x': 680,
        'wins_x': 800,
        'losses_x': 920,
        'points_x': 1100,
        
        'row_start_y': 320,
        'row_height': 65,
        'row_size': 32,
        'row_color': (255, 255, 255),
        
        'max_rows': 10,
    },
    'americas': {
        'title_pos': (640, 100),
        'title_size': 60,
        'title_color': (255, 255, 255),
        
        'header_y': 250,
        'header_size': 28,
        'header_color': (220, 220, 220),
        
        'rank_x': 120,
        'team_name_x': 240,
        'matches_x': 680,
        'wins_x': 800,
        'losses_x': 920,
        'points_x': 1100,
        
        'row_start_y': 320,
        'row_height': 65,
        'row_size': 32,
        'row_color': (255, 255, 255),
        
        'max_rows': 10,
    },
    'india': {
        'title_pos': (640, 100),
        'title_size': 60,
        'title_color': (255, 255, 255),
        
        'header_y': 250,
        'header_size': 28,
        'header_color': (220, 220, 220),
        
        'rank_x': 120,
        'team_name_x': 240,
        'matches_x': 680,
        'wins_x': 800,
        'losses_x': 920,
        'points_x': 1100,
        
        'row_start_y': 320,
        'row_height': 65,
        'row_size': 32,
        'row_color': (255, 255, 255),
        
        'max_rows': 10,
    },
}

async def generate_leaderboard_image(region: str = 'apac', limit: int = 10) -> str:
    """
    Generate a leaderboard image for the specified region
    
    Args:
        region: One of 'global', 'apac', 'emea', 'americas', 'india'
        limit: Number of teams to display (max 10)
    
    Returns:
        Path to the generated image
    """
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Get template and config
    template_path = LEADERBOARD_TEMPLATES.get(region)
    if not template_path or not template_path.exists():
        raise FileNotFoundError(f"Template for {region} not found: {template_path}")
    
    config = LEADERBOARD_CONFIG.get(region)
    if not config:
        raise ValueError(f"Config for {region} not found")
    
    # Load template image
    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype(str(FONT_PATH), config['title_size'])
        header_font = ImageFont.truetype(str(FONT_PATH), config['header_size'])
        row_font = ImageFont.truetype(str(FONT_PATH), config['row_size'])
    except Exception as e:
        print(f"Error loading font: {e}")
        # Fallback to default font
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        row_font = ImageFont.load_default()
    
    # Get leaderboard data from database
    leaderboard_data = await db.get_team_leaderboard(region, limit=min(limit, config['max_rows']))
    
    # Draw header
    draw.text((config['rank_x'], config['header_y']), "#", font=header_font, fill=config['header_color'])
    draw.text((config['team_name_x'], config['header_y']), "TEAM NAME", font=header_font, fill=config['header_color'])
    draw.text((config['matches_x'], config['header_y']), "M", font=header_font, fill=config['header_color'])
    draw.text((config['wins_x'], config['header_y']), "W", font=header_font, fill=config['header_color'])
    draw.text((config['losses_x'], config['header_y']), "L", font=header_font, fill=config['header_color'])
    draw.text((config['points_x'], config['header_y']), "POINTS", font=header_font, fill=config['header_color'])
    
    # Draw team rows
    for idx, team in enumerate(leaderboard_data):
        y_pos = config['row_start_y'] + (idx * config['row_height'])
        
        # Rank
        rank_text = f"#{team['rank']}"
        draw.text((config['rank_x'], y_pos), rank_text, font=row_font, fill=config['row_color'])
        
        # Team name (with tag)
        team_text = f"[{team['team_tag']}] {team['team_name']}"
        if len(team_text) > 30:
            team_text = team_text[:27] + "..."
        draw.text((config['team_name_x'], y_pos), team_text, font=row_font, fill=config['row_color'])
        
        # Matches
        draw.text((config['matches_x'], y_pos), str(team['total_matches']), font=row_font, fill=config['row_color'])
        
        # Wins
        draw.text((config['wins_x'], y_pos), str(team['wins']), font=row_font, fill=config['row_color'])
        
        # Losses
        draw.text((config['losses_x'], y_pos), str(team['losses']), font=row_font, fill=config['row_color'])
        
        # Points
        points_text = f"{team['points']:.1f}"
        draw.text((config['points_x'], y_pos), points_text, font=row_font, fill=config['row_color'])
    
    # Save image
    output_path = OUTPUT_DIR / f'{region}_leaderboard.jpg'
    img.save(output_path, quality=95)
    
    print(f"✅ Generated {region} leaderboard: {output_path}")
    return str(output_path)

async def generate_all_leaderboards():
    """Generate leaderboard images for all regions"""
    regions = ['global', 'apac', 'emea', 'americas', 'india']
    
    for region in regions:
        try:
            path = await generate_leaderboard_image(region, limit=10)
            print(f"  {region.upper()}: {path}")
        except Exception as e:
            print(f"  ❌ Error generating {region} leaderboard: {e}")

if __name__ == "__main__":
    print("🎨 Generating leaderboard images...")
    asyncio.run(generate_all_leaderboards())
