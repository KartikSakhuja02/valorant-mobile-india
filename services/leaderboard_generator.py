"""
Production Leaderboard Image Generator
Generates leaderboard images with pagination support
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import List, Dict
import io

# Paths
BASE_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = BASE_DIR / 'imports' / 'leaderboard'
FONT_DIR = BASE_DIR / 'imports' / 'font'

# Font settings
FONT_PATH = FONT_DIR / 'Lato-Bold.ttf'
ROW_FONT_SIZE = 75

# Cache for loaded fonts to avoid reloading
_FONT_CACHE = {}

# Text Colors - Different colors for different elements
RANK_COLOR = "#000000"      # Black for rank numbers
TEAM_NAME_COLOR = "#ffff23" # Bright yellow for team names
WINS_COLOR = "#ffff23"      # Bright yellow for wins
LOSSES_COLOR = "#ffff23"    # Bright yellow for losses
WINRATE_COLOR = "#ffff23"   # Bright yellow for winrate
POINTS_COLOR = "#ffff23"    # Bright yellow for points
KILLS_COLOR = "#ffff23"     # Bright yellow for kills
DEATHS_COLOR = "#ffff23"    # Bright yellow for deaths
ASSISTS_COLOR = "#ffff23"   # Bright yellow for assists

# Discord-style UI colors
DISCORD_BG = (47, 49, 54)        # Dark background #2f3136
DISCORD_BORDER = (32, 34, 37)    # Darker border #202225
DISCORD_ACCENT = (88, 101, 242)  # Blurple accent #5865f2
BORDER_WIDTH = 20                 # Border thickness in pixels
BORDER_RADIUS = 8                 # Rounded corners radius

# Template paths
TEMPLATES = {
    'apac': TEMPLATE_DIR / 'APAC_Leaderboard.jpg',
    'global': TEMPLATE_DIR / 'Global_Leaderboard.jpg',
    'emea': TEMPLATE_DIR / 'EMEA_Leaderboard.jpg',
    'americas': TEMPLATE_DIR / 'Americas_Leaderboard.jpg',
    'india': TEMPLATE_DIR / 'India_Leaderboard.jpg',
    'players': TEMPLATE_DIR / 'Individual_Leaderboard.jpg',
}

# APAC Configuration - Position data for all 15 rows
APAC_CONFIG = {
    'rows': [
        # Row 1
        {'rank': 1, 'rank_x': 670, 'rank_y': 900, 'team_name_x': 825, 'team_name_y': 895,
         'wins_x': 1900, 'wins_y': 895, 'losses_x': 2345, 'losses_y': 895,
         'winrate_x': 2700, 'winrate_y': 895, 'points_x': 3110, 'points_y': 895},
        # Row 2
        {'rank': 2, 'rank_x': 670, 'rank_y': 1045, 'team_name_x': 825, 'team_name_y': 1040,
         'wins_x': 1900, 'wins_y': 1040, 'losses_x': 2345, 'losses_y': 1040,
         'winrate_x': 2700, 'winrate_y': 1040, 'points_x': 3110, 'points_y': 1040},
        # Row 3
        {'rank': 3, 'rank_x': 670, 'rank_y': 1185, 'team_name_x': 825, 'team_name_y': 1180,
         'wins_x': 1900, 'wins_y': 1180, 'losses_x': 2345, 'losses_y': 1180,
         'winrate_x': 2700, 'winrate_y': 1180, 'points_x': 3110, 'points_y': 1180},
        # Row 4
        {'rank': 4, 'rank_x': 670, 'rank_y': 1330, 'team_name_x': 825, 'team_name_y': 1325,
         'wins_x': 1900, 'wins_y': 1325, 'losses_x': 2345, 'losses_y': 1325,
         'winrate_x': 2700, 'winrate_y': 1325, 'points_x': 3110, 'points_y': 1325},
        # Row 5
        {'rank': 5, 'rank_x': 670, 'rank_y': 1475, 'team_name_x': 825, 'team_name_y': 1470,
         'wins_x': 1900, 'wins_y': 1470, 'losses_x': 2345, 'losses_y': 1470,
         'winrate_x': 2700, 'winrate_y': 1470, 'points_x': 3110, 'points_y': 1470},
        # Row 6
        {'rank': 6, 'rank_x': 670, 'rank_y': 1620, 'team_name_x': 825, 'team_name_y': 1615,
         'wins_x': 1900, 'wins_y': 1615, 'losses_x': 2345, 'losses_y': 1615,
         'winrate_x': 2700, 'winrate_y': 1615, 'points_x': 3110, 'points_y': 1615},
        # Row 7
        {'rank': 7, 'rank_x': 670, 'rank_y': 1765, 'team_name_x': 825, 'team_name_y': 1760,
         'wins_x': 1900, 'wins_y': 1760, 'losses_x': 2345, 'losses_y': 1760,
         'winrate_x': 2700, 'winrate_y': 1760, 'points_x': 3110, 'points_y': 1760},
        # Row 8
        {'rank': 8, 'rank_x': 670, 'rank_y': 1900, 'team_name_x': 825, 'team_name_y': 1895,
         'wins_x': 1900, 'wins_y': 1895, 'losses_x': 2345, 'losses_y': 1895,
         'winrate_x': 2700, 'winrate_y': 1895, 'points_x': 3110, 'points_y': 1895},
        # Row 9
        {'rank': 9, 'rank_x': 670, 'rank_y': 2050, 'team_name_x': 825, 'team_name_y': 2045,
         'wins_x': 1900, 'wins_y': 2045, 'losses_x': 2345, 'losses_y': 2045,
         'winrate_x': 2700, 'winrate_y': 2045, 'points_x': 3110, 'points_y': 2045},
        # Row 10
        {'rank': 10, 'rank_x': 670, 'rank_y': 2190, 'team_name_x': 825, 'team_name_y': 2185,
         'wins_x': 1900, 'wins_y': 2185, 'losses_x': 2345, 'losses_y': 2185,
         'winrate_x': 2700, 'winrate_y': 2185, 'points_x': 3110, 'points_y': 2185},
        # Row 11
        {'rank': 11, 'rank_x': 670, 'rank_y': 2335, 'team_name_x': 825, 'team_name_y': 2330,
         'wins_x': 1900, 'wins_y': 2330, 'losses_x': 2345, 'losses_y': 2330,
         'winrate_x': 2700, 'winrate_y': 2330, 'points_x': 3110, 'points_y': 2330},
        # Row 12
        {'rank': 12, 'rank_x': 670, 'rank_y': 2485, 'team_name_x': 825, 'team_name_y': 2480,
         'wins_x': 1900, 'wins_y': 2480, 'losses_x': 2345, 'losses_y': 2480,
         'winrate_x': 2700, 'winrate_y': 2480, 'points_x': 3110, 'points_y': 2480},
        # Row 13
        {'rank': 13, 'rank_x': 670, 'rank_y': 2630, 'team_name_x': 825, 'team_name_y': 2625,
         'wins_x': 1900, 'wins_y': 2625, 'losses_x': 2345, 'losses_y': 2625,
         'winrate_x': 2700, 'winrate_y': 2625, 'points_x': 3110, 'points_y': 2625},
        # Row 14
        {'rank': 14, 'rank_x': 670, 'rank_y': 2780, 'team_name_x': 825, 'team_name_y': 2775,
         'wins_x': 1900, 'wins_y': 2775, 'losses_x': 2345, 'losses_y': 2775,
         'winrate_x': 2700, 'winrate_y': 2775, 'points_x': 3110, 'points_y': 2775},
        # Row 15
        {'rank': 15, 'rank_x': 670, 'rank_y': 2920, 'team_name_x': 825, 'team_name_y': 2915,
         'wins_x': 1900, 'wins_y': 2915, 'losses_x': 2345, 'losses_y': 2915,
         'winrate_x': 2700, 'winrate_y': 2915, 'points_x': 3110, 'points_y': 2915},
    ]
}

# Global Configuration - Same positions as APAC
GLOBAL_CONFIG = {
    'rows': [
        # Row 1
        {'rank': 1, 'rank_x': 670, 'rank_y': 900, 'team_name_x': 825, 'team_name_y': 895,
         'wins_x': 1900, 'wins_y': 895, 'losses_x': 2345, 'losses_y': 895,
         'winrate_x': 2700, 'winrate_y': 895, 'points_x': 3110, 'points_y': 895},
        # Row 2
        {'rank': 2, 'rank_x': 670, 'rank_y': 1045, 'team_name_x': 825, 'team_name_y': 1040,
         'wins_x': 1900, 'wins_y': 1040, 'losses_x': 2345, 'losses_y': 1040,
         'winrate_x': 2700, 'winrate_y': 1040, 'points_x': 3110, 'points_y': 1040},
        # Row 3
        {'rank': 3, 'rank_x': 670, 'rank_y': 1185, 'team_name_x': 825, 'team_name_y': 1180,
         'wins_x': 1900, 'wins_y': 1180, 'losses_x': 2345, 'losses_y': 1180,
         'winrate_x': 2700, 'winrate_y': 1180, 'points_x': 3110, 'points_y': 1180},
        # Row 4
        {'rank': 4, 'rank_x': 670, 'rank_y': 1330, 'team_name_x': 825, 'team_name_y': 1325,
         'wins_x': 1900, 'wins_y': 1325, 'losses_x': 2345, 'losses_y': 1325,
         'winrate_x': 2700, 'winrate_y': 1325, 'points_x': 3110, 'points_y': 1325},
        # Row 5
        {'rank': 5, 'rank_x': 670, 'rank_y': 1475, 'team_name_x': 825, 'team_name_y': 1470,
         'wins_x': 1900, 'wins_y': 1470, 'losses_x': 2345, 'losses_y': 1470,
         'winrate_x': 2700, 'winrate_y': 1470, 'points_x': 3110, 'points_y': 1470},
        # Row 6
        {'rank': 6, 'rank_x': 670, 'rank_y': 1620, 'team_name_x': 825, 'team_name_y': 1615,
         'wins_x': 1900, 'wins_y': 1615, 'losses_x': 2345, 'losses_y': 1615,
         'winrate_x': 2700, 'winrate_y': 1615, 'points_x': 3110, 'points_y': 1615},
        # Row 7
        {'rank': 7, 'rank_x': 670, 'rank_y': 1765, 'team_name_x': 825, 'team_name_y': 1760,
         'wins_x': 1900, 'wins_y': 1760, 'losses_x': 2345, 'losses_y': 1760,
         'winrate_x': 2700, 'winrate_y': 1760, 'points_x': 3110, 'points_y': 1760},
        # Row 8
        {'rank': 8, 'rank_x': 670, 'rank_y': 1900, 'team_name_x': 825, 'team_name_y': 1895,
         'wins_x': 1900, 'wins_y': 1895, 'losses_x': 2345, 'losses_y': 1895,
         'winrate_x': 2700, 'winrate_y': 1895, 'points_x': 3110, 'points_y': 1895},
        # Row 9
        {'rank': 9, 'rank_x': 670, 'rank_y': 2050, 'team_name_x': 825, 'team_name_y': 2045,
         'wins_x': 1900, 'wins_y': 2045, 'losses_x': 2345, 'losses_y': 2045,
         'winrate_x': 2700, 'winrate_y': 2045, 'points_x': 3110, 'points_y': 2045},
        # Row 10
        {'rank': 10, 'rank_x': 670, 'rank_y': 2190, 'team_name_x': 825, 'team_name_y': 2185,
         'wins_x': 1900, 'wins_y': 2185, 'losses_x': 2345, 'losses_y': 2185,
         'winrate_x': 2700, 'winrate_y': 2185, 'points_x': 3110, 'points_y': 2185},
        # Row 11
        {'rank': 11, 'rank_x': 670, 'rank_y': 2335, 'team_name_x': 825, 'team_name_y': 2330,
         'wins_x': 1900, 'wins_y': 2330, 'losses_x': 2345, 'losses_y': 2330,
         'winrate_x': 2700, 'winrate_y': 2330, 'points_x': 3110, 'points_y': 2330},
        # Row 12
        {'rank': 12, 'rank_x': 670, 'rank_y': 2485, 'team_name_x': 825, 'team_name_y': 2480,
         'wins_x': 1900, 'wins_y': 2480, 'losses_x': 2345, 'losses_y': 2480,
         'winrate_x': 2700, 'winrate_y': 2480, 'points_x': 3110, 'points_y': 2480},
        # Row 13
        {'rank': 13, 'rank_x': 670, 'rank_y': 2630, 'team_name_x': 825, 'team_name_y': 2625,
         'wins_x': 1900, 'wins_y': 2625, 'losses_x': 2345, 'losses_y': 2625,
         'winrate_x': 2700, 'winrate_y': 2625, 'points_x': 3110, 'points_y': 2625},
        # Row 14
        {'rank': 14, 'rank_x': 670, 'rank_y': 2780, 'team_name_x': 825, 'team_name_y': 2775,
         'wins_x': 1900, 'wins_y': 2775, 'losses_x': 2345, 'losses_y': 2775,
         'winrate_x': 2700, 'winrate_y': 2775, 'points_x': 3110, 'points_y': 2775},
        # Row 15
        {'rank': 15, 'rank_x': 670, 'rank_y': 2920, 'team_name_x': 825, 'team_name_y': 2915,
         'wins_x': 1900, 'wins_y': 2915, 'losses_x': 2345, 'losses_y': 2915,
         'winrate_x': 2700, 'winrate_y': 2915, 'points_x': 3110, 'points_y': 2915},
    ]
}

# EMEA Configuration - Same positions as APAC and Global
EMEA_CONFIG = {
    'rows': [
        # Row 1
        {'rank': 1, 'rank_x': 670, 'rank_y': 900, 'team_name_x': 825, 'team_name_y': 895,
         'wins_x': 1900, 'wins_y': 895, 'losses_x': 2345, 'losses_y': 895,
         'winrate_x': 2700, 'winrate_y': 895, 'points_x': 3110, 'points_y': 895},
        # Row 2
        {'rank': 2, 'rank_x': 670, 'rank_y': 1045, 'team_name_x': 825, 'team_name_y': 1040,
         'wins_x': 1900, 'wins_y': 1040, 'losses_x': 2345, 'losses_y': 1040,
         'winrate_x': 2700, 'winrate_y': 1040, 'points_x': 3110, 'points_y': 1040},
        # Row 3
        {'rank': 3, 'rank_x': 670, 'rank_y': 1185, 'team_name_x': 825, 'team_name_y': 1180,
         'wins_x': 1900, 'wins_y': 1180, 'losses_x': 2345, 'losses_y': 1180,
         'winrate_x': 2700, 'winrate_y': 1180, 'points_x': 3110, 'points_y': 1180},
        # Row 4
        {'rank': 4, 'rank_x': 670, 'rank_y': 1330, 'team_name_x': 825, 'team_name_y': 1325,
         'wins_x': 1900, 'wins_y': 1325, 'losses_x': 2345, 'losses_y': 1325,
         'winrate_x': 2700, 'winrate_y': 1325, 'points_x': 3110, 'points_y': 1325},
        # Row 5
        {'rank': 5, 'rank_x': 670, 'rank_y': 1475, 'team_name_x': 825, 'team_name_y': 1470,
         'wins_x': 1900, 'wins_y': 1470, 'losses_x': 2345, 'losses_y': 1470,
         'winrate_x': 2700, 'winrate_y': 1470, 'points_x': 3110, 'points_y': 1470},
        # Row 6
        {'rank': 6, 'rank_x': 670, 'rank_y': 1620, 'team_name_x': 825, 'team_name_y': 1615,
         'wins_x': 1900, 'wins_y': 1615, 'losses_x': 2345, 'losses_y': 1615,
         'winrate_x': 2700, 'winrate_y': 1615, 'points_x': 3110, 'points_y': 1615},
        # Row 7
        {'rank': 7, 'rank_x': 670, 'rank_y': 1765, 'team_name_x': 825, 'team_name_y': 1760,
         'wins_x': 1900, 'wins_y': 1760, 'losses_x': 2345, 'losses_y': 1760,
         'winrate_x': 2700, 'winrate_y': 1760, 'points_x': 3110, 'points_y': 1760},
        # Row 8
        {'rank': 8, 'rank_x': 670, 'rank_y': 1900, 'team_name_x': 825, 'team_name_y': 1895,
         'wins_x': 1900, 'wins_y': 1895, 'losses_x': 2345, 'losses_y': 1895,
         'winrate_x': 2700, 'winrate_y': 1895, 'points_x': 3110, 'points_y': 1895},
        # Row 9
        {'rank': 9, 'rank_x': 670, 'rank_y': 2050, 'team_name_x': 825, 'team_name_y': 2045,
         'wins_x': 1900, 'wins_y': 2045, 'losses_x': 2345, 'losses_y': 2045,
         'winrate_x': 2700, 'winrate_y': 2045, 'points_x': 3110, 'points_y': 2045},
        # Row 10
        {'rank': 10, 'rank_x': 670, 'rank_y': 2190, 'team_name_x': 825, 'team_name_y': 2185,
         'wins_x': 1900, 'wins_y': 2185, 'losses_x': 2345, 'losses_y': 2185,
         'winrate_x': 2700, 'winrate_y': 2185, 'points_x': 3110, 'points_y': 2185},
        # Row 11
        {'rank': 11, 'rank_x': 670, 'rank_y': 2335, 'team_name_x': 825, 'team_name_y': 2330,
         'wins_x': 1900, 'wins_y': 2330, 'losses_x': 2345, 'losses_y': 2330,
         'winrate_x': 2700, 'winrate_y': 2330, 'points_x': 3110, 'points_y': 2330},
        # Row 12
        {'rank': 12, 'rank_x': 670, 'rank_y': 2485, 'team_name_x': 825, 'team_name_y': 2480,
         'wins_x': 1900, 'wins_y': 2480, 'losses_x': 2345, 'losses_y': 2480,
         'winrate_x': 2700, 'winrate_y': 2480, 'points_x': 3110, 'points_y': 2480},
        # Row 13
        {'rank': 13, 'rank_x': 670, 'rank_y': 2630, 'team_name_x': 825, 'team_name_y': 2625,
         'wins_x': 1900, 'wins_y': 2625, 'losses_x': 2345, 'losses_y': 2625,
         'winrate_x': 2700, 'winrate_y': 2625, 'points_x': 3110, 'points_y': 2625},
        # Row 14
        {'rank': 14, 'rank_x': 670, 'rank_y': 2780, 'team_name_x': 825, 'team_name_y': 2775,
         'wins_x': 1900, 'wins_y': 2775, 'losses_x': 2345, 'losses_y': 2775,
         'winrate_x': 2700, 'winrate_y': 2775, 'points_x': 3110, 'points_y': 2775},
        # Row 15
        {'rank': 15, 'rank_x': 670, 'rank_y': 2920, 'team_name_x': 825, 'team_name_y': 2915,
         'wins_x': 1900, 'wins_y': 2915, 'losses_x': 2345, 'losses_y': 2915,
         'winrate_x': 2700, 'winrate_y': 2915, 'points_x': 3110, 'points_y': 2915},
    ]
}

# Americas Configuration - Same positions as APAC, Global, and EMEA
AMERICAS_CONFIG = {
    'rows': [
        # Row 1
        {'rank': 1, 'rank_x': 670, 'rank_y': 900, 'team_name_x': 825, 'team_name_y': 895,
         'wins_x': 1900, 'wins_y': 895, 'losses_x': 2345, 'losses_y': 895,
         'winrate_x': 2700, 'winrate_y': 895, 'points_x': 3110, 'points_y': 895},
        # Row 2
        {'rank': 2, 'rank_x': 670, 'rank_y': 1045, 'team_name_x': 825, 'team_name_y': 1040,
         'wins_x': 1900, 'wins_y': 1040, 'losses_x': 2345, 'losses_y': 1040,
         'winrate_x': 2700, 'winrate_y': 1040, 'points_x': 3110, 'points_y': 1040},
        # Row 3
        {'rank': 3, 'rank_x': 670, 'rank_y': 1185, 'team_name_x': 825, 'team_name_y': 1180,
         'wins_x': 1900, 'wins_y': 1180, 'losses_x': 2345, 'losses_y': 1180,
         'winrate_x': 2700, 'winrate_y': 1180, 'points_x': 3110, 'points_y': 1180},
        # Row 4
        {'rank': 4, 'rank_x': 670, 'rank_y': 1330, 'team_name_x': 825, 'team_name_y': 1325,
         'wins_x': 1900, 'wins_y': 1325, 'losses_x': 2345, 'losses_y': 1325,
         'winrate_x': 2700, 'winrate_y': 1325, 'points_x': 3110, 'points_y': 1325},
        # Row 5
        {'rank': 5, 'rank_x': 670, 'rank_y': 1475, 'team_name_x': 825, 'team_name_y': 1470,
         'wins_x': 1900, 'wins_y': 1470, 'losses_x': 2345, 'losses_y': 1470,
         'winrate_x': 2700, 'winrate_y': 1470, 'points_x': 3110, 'points_y': 1470},
        # Row 6
        {'rank': 6, 'rank_x': 670, 'rank_y': 1620, 'team_name_x': 825, 'team_name_y': 1615,
         'wins_x': 1900, 'wins_y': 1615, 'losses_x': 2345, 'losses_y': 1615,
         'winrate_x': 2700, 'winrate_y': 1615, 'points_x': 3110, 'points_y': 1615},
        # Row 7
        {'rank': 7, 'rank_x': 670, 'rank_y': 1765, 'team_name_x': 825, 'team_name_y': 1760,
         'wins_x': 1900, 'wins_y': 1760, 'losses_x': 2345, 'losses_y': 1760,
         'winrate_x': 2700, 'winrate_y': 1760, 'points_x': 3110, 'points_y': 1760},
        # Row 8
        {'rank': 8, 'rank_x': 670, 'rank_y': 1900, 'team_name_x': 825, 'team_name_y': 1895,
         'wins_x': 1900, 'wins_y': 1895, 'losses_x': 2345, 'losses_y': 1895,
         'winrate_x': 2700, 'winrate_y': 1895, 'points_x': 3110, 'points_y': 1895},
        # Row 9
        {'rank': 9, 'rank_x': 670, 'rank_y': 2050, 'team_name_x': 825, 'team_name_y': 2045,
         'wins_x': 1900, 'wins_y': 2045, 'losses_x': 2345, 'losses_y': 2045,
         'winrate_x': 2700, 'winrate_y': 2045, 'points_x': 3110, 'points_y': 2045},
        # Row 10
        {'rank': 10, 'rank_x': 670, 'rank_y': 2190, 'team_name_x': 825, 'team_name_y': 2185,
         'wins_x': 1900, 'wins_y': 2185, 'losses_x': 2345, 'losses_y': 2185,
         'winrate_x': 2700, 'winrate_y': 2185, 'points_x': 3110, 'points_y': 2185},
        # Row 11
        {'rank': 11, 'rank_x': 670, 'rank_y': 2335, 'team_name_x': 825, 'team_name_y': 2330,
         'wins_x': 1900, 'wins_y': 2330, 'losses_x': 2345, 'losses_y': 2330,
         'winrate_x': 2700, 'winrate_y': 2330, 'points_x': 3110, 'points_y': 2330},
        # Row 12
        {'rank': 12, 'rank_x': 670, 'rank_y': 2485, 'team_name_x': 825, 'team_name_y': 2480,
         'wins_x': 1900, 'wins_y': 2480, 'losses_x': 2345, 'losses_y': 2480,
         'winrate_x': 2700, 'winrate_y': 2480, 'points_x': 3110, 'points_y': 2480},
        # Row 13
        {'rank': 13, 'rank_x': 670, 'rank_y': 2630, 'team_name_x': 825, 'team_name_y': 2625,
         'wins_x': 1900, 'wins_y': 2625, 'losses_x': 2345, 'losses_y': 2625,
         'winrate_x': 2700, 'winrate_y': 2625, 'points_x': 3110, 'points_y': 2625},
        # Row 14
        {'rank': 14, 'rank_x': 670, 'rank_y': 2780, 'team_name_x': 825, 'team_name_y': 2775,
         'wins_x': 1900, 'wins_y': 2775, 'losses_x': 2345, 'losses_y': 2775,
         'winrate_x': 2700, 'winrate_y': 2775, 'points_x': 3110, 'points_y': 2775},
        # Row 15
        {'rank': 15, 'rank_x': 670, 'rank_y': 2920, 'team_name_x': 825, 'team_name_y': 2915,
         'wins_x': 1900, 'wins_y': 2915, 'losses_x': 2345, 'losses_y': 2915,
         'winrate_x': 2700, 'winrate_y': 2915, 'points_x': 3110, 'points_y': 2915},
    ]
}

# India Configuration - Same positions as APAC, Global, EMEA, and Americas
INDIA_CONFIG = {
    'rows': [
        # Row 1
        {'rank': 1, 'rank_x': 670, 'rank_y': 900, 'team_name_x': 825, 'team_name_y': 895,
         'wins_x': 1900, 'wins_y': 895, 'losses_x': 2345, 'losses_y': 895,
         'winrate_x': 2700, 'winrate_y': 895, 'points_x': 3110, 'points_y': 895},
        # Row 2
        {'rank': 2, 'rank_x': 670, 'rank_y': 1045, 'team_name_x': 825, 'team_name_y': 1040,
         'wins_x': 1900, 'wins_y': 1040, 'losses_x': 2345, 'losses_y': 1040,
         'winrate_x': 2700, 'winrate_y': 1040, 'points_x': 3110, 'points_y': 1040},
        # Row 3
        {'rank': 3, 'rank_x': 670, 'rank_y': 1185, 'team_name_x': 825, 'team_name_y': 1180,
         'wins_x': 1900, 'wins_y': 1180, 'losses_x': 2345, 'losses_y': 1180,
         'winrate_x': 2700, 'winrate_y': 1180, 'points_x': 3110, 'points_y': 1180},
        # Row 4
        {'rank': 4, 'rank_x': 670, 'rank_y': 1330, 'team_name_x': 825, 'team_name_y': 1325,
         'wins_x': 1900, 'wins_y': 1325, 'losses_x': 2345, 'losses_y': 1325,
         'winrate_x': 2700, 'winrate_y': 1325, 'points_x': 3110, 'points_y': 1325},
        # Row 5
        {'rank': 5, 'rank_x': 670, 'rank_y': 1475, 'team_name_x': 825, 'team_name_y': 1470,
         'wins_x': 1900, 'wins_y': 1470, 'losses_x': 2345, 'losses_y': 1470,
         'winrate_x': 2700, 'winrate_y': 1470, 'points_x': 3110, 'points_y': 1470},
        # Row 6
        {'rank': 6, 'rank_x': 670, 'rank_y': 1620, 'team_name_x': 825, 'team_name_y': 1615,
         'wins_x': 1900, 'wins_y': 1615, 'losses_x': 2345, 'losses_y': 1615,
         'winrate_x': 2700, 'winrate_y': 1615, 'points_x': 3110, 'points_y': 1615},
        # Row 7
        {'rank': 7, 'rank_x': 670, 'rank_y': 1765, 'team_name_x': 825, 'team_name_y': 1760,
         'wins_x': 1900, 'wins_y': 1760, 'losses_x': 2345, 'losses_y': 1760,
         'winrate_x': 2700, 'winrate_y': 1760, 'points_x': 3110, 'points_y': 1760},
        # Row 8
        {'rank': 8, 'rank_x': 670, 'rank_y': 1900, 'team_name_x': 825, 'team_name_y': 1895,
         'wins_x': 1900, 'wins_y': 1895, 'losses_x': 2345, 'losses_y': 1895,
         'winrate_x': 2700, 'winrate_y': 1895, 'points_x': 3110, 'points_y': 1895},
        # Row 9
        {'rank': 9, 'rank_x': 670, 'rank_y': 2050, 'team_name_x': 825, 'team_name_y': 2045,
         'wins_x': 1900, 'wins_y': 2045, 'losses_x': 2345, 'losses_y': 2045,
         'winrate_x': 2700, 'winrate_y': 2045, 'points_x': 3110, 'points_y': 2045},
        # Row 10
        {'rank': 10, 'rank_x': 670, 'rank_y': 2190, 'team_name_x': 825, 'team_name_y': 2185,
         'wins_x': 1900, 'wins_y': 2185, 'losses_x': 2345, 'losses_y': 2185,
         'winrate_x': 2700, 'winrate_y': 2185, 'points_x': 3110, 'points_y': 2185},
        # Row 11
        {'rank': 11, 'rank_x': 670, 'rank_y': 2335, 'team_name_x': 825, 'team_name_y': 2330,
         'wins_x': 1900, 'wins_y': 2330, 'losses_x': 2345, 'losses_y': 2330,
         'winrate_x': 2700, 'winrate_y': 2330, 'points_x': 3110, 'points_y': 2330},
        # Row 12
        {'rank': 12, 'rank_x': 670, 'rank_y': 2485, 'team_name_x': 825, 'team_name_y': 2480,
         'wins_x': 1900, 'wins_y': 2480, 'losses_x': 2345, 'losses_y': 2480,
         'winrate_x': 2700, 'winrate_y': 2480, 'points_x': 3110, 'points_y': 2480},
        # Row 13
        {'rank': 13, 'rank_x': 670, 'rank_y': 2630, 'team_name_x': 825, 'team_name_y': 2625,
         'wins_x': 1900, 'wins_y': 2625, 'losses_x': 2345, 'losses_y': 2625,
         'winrate_x': 2700, 'winrate_y': 2625, 'points_x': 3110, 'points_y': 2625},
        # Row 14
        {'rank': 14, 'rank_x': 670, 'rank_y': 2780, 'team_name_x': 825, 'team_name_y': 2775,
         'wins_x': 1900, 'wins_y': 2775, 'losses_x': 2345, 'losses_y': 2775,
         'winrate_x': 2700, 'winrate_y': 2775, 'points_x': 3110, 'points_y': 2775},
        # Row 15
        {'rank': 15, 'rank_x': 670, 'rank_y': 2920, 'team_name_x': 825, 'team_name_y': 2915,
         'wins_x': 1900, 'wins_y': 2915, 'losses_x': 2345, 'losses_y': 2915,
         'winrate_x': 2700, 'winrate_y': 2915, 'points_x': 3110, 'points_y': 2915},
    ]
}

# Regional configurations
REGION_CONFIGS = {
    'apac': APAC_CONFIG,
    'global': GLOBAL_CONFIG,
    'emea': EMEA_CONFIG,
    'americas': AMERICAS_CONFIG,
    'india': INDIA_CONFIG,
}

# Player Configuration - Same positions as team leaderboards
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


def add_discord_border(img: Image.Image) -> Image.Image:
    """
    Add a Discord-style UI border around the image
    
    Args:
        img: PIL Image to add border to
        
    Returns:
        New PIL Image with Discord-style border
    """
    # Calculate new size with border
    new_width = img.width + (BORDER_WIDTH * 2)
    new_height = img.height + (BORDER_WIDTH * 2)
    
    # Create new image with Discord background color
    bordered_img = Image.new('RGB', (new_width, new_height), DISCORD_BG)
    
    # Draw border with rounded corners effect
    draw = ImageDraw.Draw(bordered_img)
    
    # Draw outer border (darker)
    draw.rectangle(
        [(0, 0), (new_width-1, new_height-1)],
        outline=DISCORD_BORDER,
        width=2
    )
    
    # Draw inner accent line (blurple)
    accent_thickness = 3
    draw.rectangle(
        [(BORDER_WIDTH - accent_thickness, BORDER_WIDTH - accent_thickness),
         (new_width - BORDER_WIDTH + accent_thickness - 1, 
          new_height - BORDER_WIDTH + accent_thickness - 1)],
        outline=DISCORD_ACCENT,
        width=accent_thickness
    )
    
    # Paste the original image in the center
    bordered_img.paste(img, (BORDER_WIDTH, BORDER_WIDTH))
    
    return bordered_img


def generate_leaderboard_image(teams: List[Dict], region: str, page: int = 0) -> io.BytesIO:
    """
    Generate a leaderboard image for the given teams and region
    
    Args:
        teams: List of team dictionaries with rank, team_name, team_tag, wins, losses, win_rate, points
        region: Region name (apac, global, emea, americas, india)
        page: Page number (0-indexed) - each page shows 15 teams
        
    Returns:
        BytesIO object containing the generated PNG image
    """
    # Get template path
    template_path = TEMPLATES.get(region.lower())
    if not template_path or not template_path.exists():
        raise FileNotFoundError(f"Template not found for region: {region}")
    
    # Get config for this region
    config = REGION_CONFIGS.get(region.lower())
    if not config:
        raise ValueError(f"No configuration found for region: {region}")
    
    # Calculate which teams to show (15 per page)
    teams_per_page = 15
    start_idx = page * teams_per_page
    end_idx = start_idx + teams_per_page
    page_teams = teams[start_idx:end_idx]
    
    # Load template
    img = Image.open(template_path)
    
    # Convert to RGB immediately if needed (faster than converting at the end)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    
    # Load font (with caching to avoid reloading)
    font_key = (str(FONT_PATH), ROW_FONT_SIZE)
    if font_key not in _FONT_CACHE:
        try:
            _FONT_CACHE[font_key] = ImageFont.truetype(str(FONT_PATH), ROW_FONT_SIZE)
        except Exception as e:
            print(f"Warning: Could not load font {FONT_PATH}: {e}")
            _FONT_CACHE[font_key] = ImageFont.load_default()
    font = _FONT_CACHE[font_key]
    
    # Draw each team
    for idx, team in enumerate(page_teams):
        if idx >= len(config['rows']):
            break
            
        row_config = config['rows'][idx]
        
        # Rank (Black)
        rank_text = str(team['rank'])
        draw.text((row_config['rank_x'], row_config['rank_y']), 
                 rank_text, font=font, fill=RANK_COLOR)
        
        # Team Name (Yellow)
        team_name = f"[{team['team_tag']}] {team['team_name']}"
        draw.text((row_config['team_name_x'], row_config['team_name_y']), 
                 team_name, font=font, fill=TEAM_NAME_COLOR)
        
        # Wins (Yellow)
        wins_text = str(team['wins'])
        draw.text((row_config['wins_x'], row_config['wins_y']), 
                 wins_text, font=font, fill=WINS_COLOR)
        
        # Losses (Yellow)
        losses_text = str(team['losses'])
        draw.text((row_config['losses_x'], row_config['losses_y']), 
                 losses_text, font=font, fill=LOSSES_COLOR)
        
        # Win Rate (Yellow)
        winrate_text = f"{team['win_rate']:.1f}%"
        draw.text((row_config['winrate_x'], row_config['winrate_y']), 
                 winrate_text, font=font, fill=WINRATE_COLOR)
        
        # Points (Yellow)
        points_text = f"{team['points']:.1f}"
        draw.text((row_config['points_x'], row_config['points_y']), 
                 points_text, font=font, fill=POINTS_COLOR)
    
    # Save to BytesIO with optimized compression
    output = io.BytesIO()
    # Save as JPEG with good quality and fast compression (optimize=False is faster)
    img.save(output, format='JPEG', quality=90, optimize=False)
    output.seek(0)
    
    return output


def calculate_total_pages(total_teams: int, items_per_page: int = 15) -> int:
    """Calculate total number of pages needed"""
    return (total_teams + items_per_page - 1) // items_per_page  # Ceiling division


def calculate_player_pages(total_players: int) -> int:
    """Calculate total number of pages needed for player leaderboard (14 per page)"""
    return (total_players + 13) // 14  # Ceiling division for 14 players per page


def generate_player_leaderboard_image(players: List[Dict], page: int = 0) -> io.BytesIO:
    """
    Generate a player leaderboard image
    
    Args:
        players: List of player dictionaries with rank, ign, region, kills, deaths, assists, mvps, points
        page: Page number (0-indexed) - each page shows 14 players
        
    Returns:
        BytesIO object containing the generated JPEG image
    """
    # Get template path
    template_path = TEMPLATES.get('players')
    if not template_path or not template_path.exists():
        raise FileNotFoundError(f"Template not found: Individual-Leaderboard.jpg")
    
    # Get config for player leaderboard
    config = PLAYER_CONFIG
    
    # Calculate which players to show (14 per page)
    players_per_page = 14
    start_idx = page * players_per_page
    end_idx = start_idx + players_per_page
    page_players = players[start_idx:end_idx]
    
    # Load template
    img = Image.open(template_path)
    
    # Convert to RGB immediately if needed (faster than converting at the end)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    
    # Load font (with caching to avoid reloading)
    font_key = (str(FONT_PATH), ROW_FONT_SIZE)
    if font_key not in _FONT_CACHE:
        try:
            _FONT_CACHE[font_key] = ImageFont.truetype(str(FONT_PATH), ROW_FONT_SIZE)
        except Exception as e:
            print(f"Warning: Could not load font {FONT_PATH}: {e}")
            _FONT_CACHE[font_key] = ImageFont.load_default()
    font = _FONT_CACHE[font_key]
    
    # Draw each player
    for idx, player in enumerate(page_players):
        if idx >= len(config['rows']):
            break
            
        row_config = config['rows'][idx]
        
        # Rank (Black)
        rank_text = str(player['rank'])
        draw.text((row_config['rank_x'], row_config['rank_y']), 
                 rank_text, font=font, fill=RANK_COLOR)
        
        # Player IGN (Yellow)
        ign_text = player['ign']
        draw.text((row_config['player_name_x'], row_config['player_name_y']), 
                 ign_text, font=font, fill=TEAM_NAME_COLOR)
        
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
        mvp_text = str(player.get('mvps', 0))
        draw.text((row_config['mvp_x'], row_config['mvp_y']), 
                 mvp_text, font=font, fill=WINS_COLOR)
        
        # Points (Yellow)
        points_text = f"{player['points']:.1f}"
        draw.text((row_config['points_x'], row_config['points_y']), 
                 points_text, font=font, fill=POINTS_COLOR)
    
    # Save to BytesIO with optimized compression
    output = io.BytesIO()
    # Save as JPEG with good quality and fast compression (optimize=False is faster)
    img.save(output, format='JPEG', quality=90, optimize=False)
    output.seek(0)
    
    return output
