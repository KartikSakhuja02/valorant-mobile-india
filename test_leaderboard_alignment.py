"""
Leaderboard Text Alignment Test Script
Run this to test and adjust text positioning on leaderboard images
"""

import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Discord-style UI colors
DISCORD_BG = (47, 49, 54)        # Dark background #2f3136
DISCORD_BORDER = (32, 34, 37)    # Darker border #202225
DISCORD_ACCENT = (88, 101, 242)  # Blurple accent #5865f2
BORDER_WIDTH = 20                 # Border thickness in pixels
ADD_BORDER = True                 # Set to False to disable border

# =============================================================================
# LEADERBOARD CONFIGURATION - CHANGE THESE NUMBERS TO ADJUST POSITIONS/SIZES
# =============================================================================

# --- Which template to test ---
REGION = 'apac'  # Change to: 'apac', 'global', 'emea', 'americas', 'india'

# --- HEADER ROW (# | TEAM NAME | M | W | L | POINTS) ---
HEADER_Y = 300              # Move header UP (smaller) or DOWN (bigger)
HEADER_FONT_SIZE = 28       # Size of header text
HEADER_COLOR_R = 220        # Red value (0-255)
HEADER_COLOR_G = 220        # Green value (0-255)
HEADER_COLOR_B = 220        # Blue value (0-255)

# Header column X positions
HEADER_RANK_X = 120
HEADER_TEAM_NAME_X = 240
HEADER_MATCHES_X = 680
HEADER_WINS_X = 800
HEADER_LOSSES_X = 920
HEADER_POINTS_X = 1100

# --- ROW FONT SETTINGS ---
ROW_FONT_SIZE = 75          # Size of team data text

# --- COLORS (RGB values 0-255 OR hex colors) ---
# Different colors for different elements
RANK_COLOR = "#000000"      # Black for rank numbers
TEAM_NAME_COLOR = "#ffff23" # Bright yellow for team names
WINS_COLOR = "#ffff23"      # Bright yellow for wins
LOSSES_COLOR = "#ffff23"    # Bright yellow for losses
WINRATE_COLOR = "#ffff23"   # Bright yellow for winrate
POINTS_COLOR = "#ffff23"    # Bright yellow for points

# ===== ROW 1 (RANK #1) =====
ROW_1_RANK_X = 670
ROW_1_RANK_Y = 900
ROW_1_TEAM_NAME_X = 825
ROW_1_TEAM_NAME_Y = 895
ROW_1_WINS_X = 1900
ROW_1_WINS_Y = 895
ROW_1_LOSSES_X = 2345
ROW_1_LOSSES_Y = 895
ROW_1_WINRATE_X = 2700
ROW_1_WINRATE_Y = 895
ROW_1_POINTS_X = 3110
ROW_1_POINTS_Y = 895

# ===== ROW 2 (RANK #2) =====
ROW_2_RANK_X = 670
ROW_2_RANK_Y = 1045
ROW_2_TEAM_NAME_X = 825
ROW_2_TEAM_NAME_Y = 1040
ROW_2_WINS_X = 1900
ROW_2_WINS_Y = 1040
ROW_2_LOSSES_X = 2345
ROW_2_LOSSES_Y = 1040
ROW_2_WINRATE_X = 2700
ROW_2_WINRATE_Y = 1040
ROW_2_POINTS_X = 3110
ROW_2_POINTS_Y = 1040

# ===== ROW 3 (RANK #3) =====
ROW_3_RANK_X = 670
ROW_3_RANK_Y = 1185
ROW_3_TEAM_NAME_X = 825
ROW_3_TEAM_NAME_Y = 1180
ROW_3_WINS_X = 1900
ROW_3_WINS_Y = 1180
ROW_3_LOSSES_X = 2345
ROW_3_LOSSES_Y = 1180
ROW_3_WINRATE_X = 2700
ROW_3_WINRATE_Y = 1180
ROW_3_POINTS_X = 3110
ROW_3_POINTS_Y = 1180

# ===== ROW 4 (RANK #4) =====
ROW_4_RANK_X = 670
ROW_4_RANK_Y = 1330
ROW_4_TEAM_NAME_X = 825
ROW_4_TEAM_NAME_Y = 1325
ROW_4_WINS_X = 1900
ROW_4_WINS_Y = 1325
ROW_4_LOSSES_X = 2345
ROW_4_LOSSES_Y = 1325
ROW_4_WINRATE_X = 2700
ROW_4_WINRATE_Y = 1325
ROW_4_POINTS_X = 3110
ROW_4_POINTS_Y = 1325

# ===== ROW 5 (RANK #5) =====
ROW_5_RANK_X = 670
ROW_5_RANK_Y = 1475
ROW_5_TEAM_NAME_X = 825
ROW_5_TEAM_NAME_Y = 1470
ROW_5_WINS_X = 1900
ROW_5_WINS_Y = 1470
ROW_5_LOSSES_X = 2345
ROW_5_LOSSES_Y = 1470
ROW_5_WINRATE_X = 2700
ROW_5_WINRATE_Y = 1470   
ROW_5_POINTS_X = 3110
ROW_5_POINTS_Y = 1470

# ===== ROW 6 (RANK #6) =====
ROW_6_RANK_X = 670
ROW_6_RANK_Y = 1620
ROW_6_TEAM_NAME_X = 825
ROW_6_TEAM_NAME_Y = 1615
ROW_6_WINS_X = 1900
ROW_6_WINS_Y = 1615
ROW_6_LOSSES_X = 2345
ROW_6_LOSSES_Y = 1615
ROW_6_WINRATE_X = 2700
ROW_6_WINRATE_Y = 1615
ROW_6_POINTS_X = 3110
ROW_6_POINTS_Y = 1615

# ===== ROW 7 (RANK #7) =====
ROW_7_RANK_X = 670
ROW_7_RANK_Y = 1765
ROW_7_TEAM_NAME_X = 825
ROW_7_TEAM_NAME_Y = 1760
ROW_7_WINS_X = 1900
ROW_7_WINS_Y = 1760
ROW_7_LOSSES_X = 2345
ROW_7_LOSSES_Y = 1760
ROW_7_WINRATE_X = 2700
ROW_7_WINRATE_Y = 1760
ROW_7_POINTS_X = 3110
ROW_7_POINTS_Y = 1760

# ===== ROW 8 (RANK #8) =====
ROW_8_RANK_X = 670
ROW_8_RANK_Y = 1900
ROW_8_TEAM_NAME_X = 825
ROW_8_TEAM_NAME_Y = 1895
ROW_8_WINS_X = 1900
ROW_8_WINS_Y = 1895
ROW_8_LOSSES_X = 2345
ROW_8_LOSSES_Y = 1895
ROW_8_WINRATE_X = 2700
ROW_8_WINRATE_Y = 1895
ROW_8_POINTS_X = 3110
ROW_8_POINTS_Y = 1895

# ===== ROW 9 (RANK #9) =====
ROW_9_RANK_X = 670
ROW_9_RANK_Y = 2050
ROW_9_TEAM_NAME_X = 825
ROW_9_TEAM_NAME_Y = 2045
ROW_9_WINS_X = 1900
ROW_9_WINS_Y = 2045
ROW_9_LOSSES_X = 2345
ROW_9_LOSSES_Y = 2045
ROW_9_WINRATE_X = 2700
ROW_9_WINRATE_Y = 2045
ROW_9_POINTS_X = 3110
ROW_9_POINTS_Y = 2045

# ===== ROW 10 (RANK #10) =====
ROW_10_RANK_X = 670
ROW_10_RANK_Y = 2190
ROW_10_TEAM_NAME_X = 825
ROW_10_TEAM_NAME_Y = 2185
ROW_10_WINS_X = 1900
ROW_10_WINS_Y = 2185
ROW_10_LOSSES_X = 2345
ROW_10_LOSSES_Y = 2185
ROW_10_WINRATE_X = 2700
ROW_10_WINRATE_Y = 2185
ROW_10_POINTS_X = 3110
ROW_10_POINTS_Y = 2185

# ===== ROW 11 (RANK #11) =====
ROW_11_RANK_X = 670
ROW_11_RANK_Y = 2335
ROW_11_TEAM_NAME_X = 825
ROW_11_TEAM_NAME_Y = 2330
ROW_11_WINS_X = 1900
ROW_11_WINS_Y = 2330
ROW_11_LOSSES_X = 2345
ROW_11_LOSSES_Y = 2330
ROW_11_WINRATE_X = 2700
ROW_11_WINRATE_Y = 2330
ROW_11_POINTS_X = 3110
ROW_11_POINTS_Y = 2330

# ===== ROW 12 (RANK #12) =====
ROW_12_RANK_X = 670
ROW_12_RANK_Y = 2485
ROW_12_TEAM_NAME_X = 825
ROW_12_TEAM_NAME_Y = 2480
ROW_12_WINS_X = 1900
ROW_12_WINS_Y = 2480
ROW_12_LOSSES_X = 2345
ROW_12_LOSSES_Y = 2480
ROW_12_WINRATE_X = 2700
ROW_12_WINRATE_Y = 2480
ROW_12_POINTS_X = 3110
ROW_12_POINTS_Y = 2480

# ===== ROW 13 (RANK #13) =====
ROW_13_RANK_X = 670
ROW_13_RANK_Y = 2630
ROW_13_TEAM_NAME_X = 825
ROW_13_TEAM_NAME_Y = 2625
ROW_13_WINS_X = 1900
ROW_13_WINS_Y = 2625
ROW_13_LOSSES_X = 2345
ROW_13_LOSSES_Y = 2625
ROW_13_WINRATE_X = 2700
ROW_13_WINRATE_Y = 2625
ROW_13_POINTS_X = 3110
ROW_13_POINTS_Y = 2625

# ===== ROW 14 (RANK #14) =====
ROW_14_RANK_X = 670
ROW_14_RANK_Y = 2780
ROW_14_TEAM_NAME_X = 825
ROW_14_TEAM_NAME_Y = 2775
ROW_14_WINS_X = 1900
ROW_14_WINS_Y = 2775
ROW_14_LOSSES_X = 2345
ROW_14_LOSSES_Y = 2775
ROW_14_WINRATE_X = 2700
ROW_14_WINRATE_Y = 2775
ROW_14_POINTS_X = 3110
ROW_14_POINTS_Y = 2775

# ===== ROW 15 (RANK #15) =====
ROW_15_RANK_X = 670
ROW_15_RANK_Y = 2920
ROW_15_TEAM_NAME_X = 825
ROW_15_TEAM_NAME_Y = 2915
ROW_15_WINS_X = 1900
ROW_15_WINS_Y = 2915
ROW_15_LOSSES_X = 2345
ROW_15_LOSSES_Y = 2915
ROW_15_WINRATE_X = 2700
ROW_15_WINRATE_Y = 2915
ROW_15_POINTS_X = 3110
ROW_15_POINTS_Y = 2915

# =============================================================================
# DO NOT EDIT BELOW THIS LINE (unless you know what you're doing)
# =============================================================================

# Paths
BASE_DIR = Path(__file__).parent
TEMPLATE_DIR = BASE_DIR / 'imports' / 'leaderboard'
FONT_DIR = BASE_DIR / 'imports' / 'font'
OUTPUT_DIR = BASE_DIR / 'test_alignment'

# Font settings
FONT_PATH = FONT_DIR / 'Lato-Bold.ttf'

# Build config from variables above
TEMPLATE_FILES = {
    'apac': 'APAC_Leaderboard.jpg',
    'global': 'Global_Leaderboard.jpg',
    'emea': 'EMEA_Leaderboard.jpg',
    'americas': 'Americas_Leaderboard.jpg',
    'india': 'India_Leaderboard.jpg',
}

TEST_CONFIG = {
    'region': REGION,
    'template': TEMPLATE_DIR / TEMPLATE_FILES.get(REGION, 'APAC_Leaderboard.jpg'),
    'header_y': HEADER_Y,
    'header_size': HEADER_FONT_SIZE,
    'header_color': (HEADER_COLOR_R, HEADER_COLOR_G, HEADER_COLOR_B),
    'header_rank_x': HEADER_RANK_X,
    'header_team_name_x': HEADER_TEAM_NAME_X,
    'header_matches_x': HEADER_MATCHES_X,
    'header_wins_x': HEADER_WINS_X,
    'header_losses_x': HEADER_LOSSES_X,
    'header_points_x': HEADER_POINTS_X,
    'row_size': ROW_FONT_SIZE,
    'rank_color': RANK_COLOR,
    'team_name_color': TEAM_NAME_COLOR,
    'wins_color': WINS_COLOR,
    'losses_color': LOSSES_COLOR,
    'winrate_color': WINRATE_COLOR,
    'points_color': POINTS_COLOR,
    'rows': [
        {
            'rank': 1,
            'rank_x': ROW_1_RANK_X, 'rank_y': ROW_1_RANK_Y,
            'team_name_x': ROW_1_TEAM_NAME_X, 'team_name_y': ROW_1_TEAM_NAME_Y,
            'wins_x': ROW_1_WINS_X, 'wins_y': ROW_1_WINS_Y,
            'losses_x': ROW_1_LOSSES_X, 'losses_y': ROW_1_LOSSES_Y,
            'winrate_x': ROW_1_WINRATE_X, 'winrate_y': ROW_1_WINRATE_Y,
            'points_x': ROW_1_POINTS_X, 'points_y': ROW_1_POINTS_Y,
        },
        {
            'rank': 2,
            'rank_x': ROW_2_RANK_X, 'rank_y': ROW_2_RANK_Y,
            'team_name_x': ROW_2_TEAM_NAME_X, 'team_name_y': ROW_2_TEAM_NAME_Y,
            'wins_x': ROW_2_WINS_X, 'wins_y': ROW_2_WINS_Y,
            'losses_x': ROW_2_LOSSES_X, 'losses_y': ROW_2_LOSSES_Y,
            'winrate_x': ROW_2_WINRATE_X, 'winrate_y': ROW_2_WINRATE_Y,
            'points_x': ROW_2_POINTS_X, 'points_y': ROW_2_POINTS_Y,
        },
        {
            'rank': 3,
            'rank_x': ROW_3_RANK_X, 'rank_y': ROW_3_RANK_Y,
            'team_name_x': ROW_3_TEAM_NAME_X, 'team_name_y': ROW_3_TEAM_NAME_Y,
            'wins_x': ROW_3_WINS_X, 'wins_y': ROW_3_WINS_Y,
            'losses_x': ROW_3_LOSSES_X, 'losses_y': ROW_3_LOSSES_Y,
            'winrate_x': ROW_3_WINRATE_X, 'winrate_y': ROW_3_WINRATE_Y,
            'points_x': ROW_3_POINTS_X, 'points_y': ROW_3_POINTS_Y,
        },
        {
            'rank': 4,
            'rank_x': ROW_4_RANK_X, 'rank_y': ROW_4_RANK_Y,
            'team_name_x': ROW_4_TEAM_NAME_X, 'team_name_y': ROW_4_TEAM_NAME_Y,
            'wins_x': ROW_4_WINS_X, 'wins_y': ROW_4_WINS_Y,
            'losses_x': ROW_4_LOSSES_X, 'losses_y': ROW_4_LOSSES_Y,
            'winrate_x': ROW_4_WINRATE_X, 'winrate_y': ROW_4_WINRATE_Y,
            'points_x': ROW_4_POINTS_X, 'points_y': ROW_4_POINTS_Y,
        },
        {
            'rank': 5,
            'rank_x': ROW_5_RANK_X, 'rank_y': ROW_5_RANK_Y,
            'team_name_x': ROW_5_TEAM_NAME_X, 'team_name_y': ROW_5_TEAM_NAME_Y,
            'wins_x': ROW_5_WINS_X, 'wins_y': ROW_5_WINS_Y,
            'losses_x': ROW_5_LOSSES_X, 'losses_y': ROW_5_LOSSES_Y,
            'winrate_x': ROW_5_WINRATE_X, 'winrate_y': ROW_5_WINRATE_Y,
            'points_x': ROW_5_POINTS_X, 'points_y': ROW_5_POINTS_Y,
        },
        {
            'rank': 6,
            'rank_x': ROW_6_RANK_X, 'rank_y': ROW_6_RANK_Y,
            'team_name_x': ROW_6_TEAM_NAME_X, 'team_name_y': ROW_6_TEAM_NAME_Y,
            'wins_x': ROW_6_WINS_X, 'wins_y': ROW_6_WINS_Y,
            'losses_x': ROW_6_LOSSES_X, 'losses_y': ROW_6_LOSSES_Y,
            'winrate_x': ROW_6_WINRATE_X, 'winrate_y': ROW_6_WINRATE_Y,
            'points_x': ROW_6_POINTS_X, 'points_y': ROW_6_POINTS_Y,
        },
        {
            'rank': 7,
            'rank_x': ROW_7_RANK_X, 'rank_y': ROW_7_RANK_Y,
            'team_name_x': ROW_7_TEAM_NAME_X, 'team_name_y': ROW_7_TEAM_NAME_Y,
            'wins_x': ROW_7_WINS_X, 'wins_y': ROW_7_WINS_Y,
            'losses_x': ROW_7_LOSSES_X, 'losses_y': ROW_7_LOSSES_Y,
            'winrate_x': ROW_7_WINRATE_X, 'winrate_y': ROW_7_WINRATE_Y,
            'points_x': ROW_7_POINTS_X, 'points_y': ROW_7_POINTS_Y,
        },
        {
            'rank': 8,
            'rank_x': ROW_8_RANK_X, 'rank_y': ROW_8_RANK_Y,
            'team_name_x': ROW_8_TEAM_NAME_X, 'team_name_y': ROW_8_TEAM_NAME_Y,
            'wins_x': ROW_8_WINS_X, 'wins_y': ROW_8_WINS_Y,
            'losses_x': ROW_8_LOSSES_X, 'losses_y': ROW_8_LOSSES_Y,
            'winrate_x': ROW_8_WINRATE_X, 'winrate_y': ROW_8_WINRATE_Y,
            'points_x': ROW_8_POINTS_X, 'points_y': ROW_8_POINTS_Y,
        },
        {
            'rank': 9,
            'rank_x': ROW_9_RANK_X, 'rank_y': ROW_9_RANK_Y,
            'team_name_x': ROW_9_TEAM_NAME_X, 'team_name_y': ROW_9_TEAM_NAME_Y,
            'wins_x': ROW_9_WINS_X, 'wins_y': ROW_9_WINS_Y,
            'losses_x': ROW_9_LOSSES_X, 'losses_y': ROW_9_LOSSES_Y,
            'winrate_x': ROW_9_WINRATE_X, 'winrate_y': ROW_9_WINRATE_Y,
            'points_x': ROW_9_POINTS_X, 'points_y': ROW_9_POINTS_Y,
        },
        {
            'rank': 10,
            'rank_x': ROW_10_RANK_X, 'rank_y': ROW_10_RANK_Y,
            'team_name_x': ROW_10_TEAM_NAME_X, 'team_name_y': ROW_10_TEAM_NAME_Y,
            'wins_x': ROW_10_WINS_X, 'wins_y': ROW_10_WINS_Y,
            'losses_x': ROW_10_LOSSES_X, 'losses_y': ROW_10_LOSSES_Y,
            'winrate_x': ROW_10_WINRATE_X, 'winrate_y': ROW_10_WINRATE_Y,
            'points_x': ROW_10_POINTS_X, 'points_y': ROW_10_POINTS_Y,
        },
        {
            'rank': 11,
            'rank_x': ROW_11_RANK_X, 'rank_y': ROW_11_RANK_Y,
            'team_name_x': ROW_11_TEAM_NAME_X, 'team_name_y': ROW_11_TEAM_NAME_Y,
            'wins_x': ROW_11_WINS_X, 'wins_y': ROW_11_WINS_Y,
            'losses_x': ROW_11_LOSSES_X, 'losses_y': ROW_11_LOSSES_Y,
            'winrate_x': ROW_11_WINRATE_X, 'winrate_y': ROW_11_WINRATE_Y,
            'points_x': ROW_11_POINTS_X, 'points_y': ROW_11_POINTS_Y,
        },
        {
            'rank': 12,
            'rank_x': ROW_12_RANK_X, 'rank_y': ROW_12_RANK_Y,
            'team_name_x': ROW_12_TEAM_NAME_X, 'team_name_y': ROW_12_TEAM_NAME_Y,
            'wins_x': ROW_12_WINS_X, 'wins_y': ROW_12_WINS_Y,
            'losses_x': ROW_12_LOSSES_X, 'losses_y': ROW_12_LOSSES_Y,
            'winrate_x': ROW_12_WINRATE_X, 'winrate_y': ROW_12_WINRATE_Y,
            'points_x': ROW_12_POINTS_X, 'points_y': ROW_12_POINTS_Y,
        },
        {
            'rank': 13,
            'rank_x': ROW_13_RANK_X, 'rank_y': ROW_13_RANK_Y,
            'team_name_x': ROW_13_TEAM_NAME_X, 'team_name_y': ROW_13_TEAM_NAME_Y,
            'wins_x': ROW_13_WINS_X, 'wins_y': ROW_13_WINS_Y,
            'losses_x': ROW_13_LOSSES_X, 'losses_y': ROW_13_LOSSES_Y,
            'winrate_x': ROW_13_WINRATE_X, 'winrate_y': ROW_13_WINRATE_Y,
            'points_x': ROW_13_POINTS_X, 'points_y': ROW_13_POINTS_Y,
        },
        {
            'rank': 14,
            'rank_x': ROW_14_RANK_X, 'rank_y': ROW_14_RANK_Y,
            'team_name_x': ROW_14_TEAM_NAME_X, 'team_name_y': ROW_14_TEAM_NAME_Y,
            'wins_x': ROW_14_WINS_X, 'wins_y': ROW_14_WINS_Y,
            'losses_x': ROW_14_LOSSES_X, 'losses_y': ROW_14_LOSSES_Y,
            'winrate_x': ROW_14_WINRATE_X, 'winrate_y': ROW_14_WINRATE_Y,
            'points_x': ROW_14_POINTS_X, 'points_y': ROW_14_POINTS_Y,
        },
        {
            'rank': 15,
            'rank_x': ROW_15_RANK_X, 'rank_y': ROW_15_RANK_Y,
            'team_name_x': ROW_15_TEAM_NAME_X, 'team_name_y': ROW_15_TEAM_NAME_Y,
            'wins_x': ROW_15_WINS_X, 'wins_y': ROW_15_WINS_Y,
            'losses_x': ROW_15_LOSSES_X, 'losses_y': ROW_15_LOSSES_Y,
            'winrate_x': ROW_15_WINRATE_X, 'winrate_y': ROW_15_WINRATE_Y,
            'points_x': ROW_15_POINTS_X, 'points_y': ROW_15_POINTS_Y,
        },
    ],
}

# Sample test data
SAMPLE_TEAMS = [
    {'rank': 1, 'team_tag': 'VCT', 'team_name': 'Valorant Champions', 'total_matches': 15, 'wins': 12, 'losses': 3, 'win_rate': 80.0, 'points': 36.5},
    {'rank': 2, 'team_tag': 'PRX', 'team_name': 'Paper Rex', 'total_matches': 14, 'wins': 11, 'losses': 3, 'win_rate': 78.6, 'points': 33.2},
    {'rank': 3, 'team_tag': 'DRX', 'team_name': 'DRX Esports', 'total_matches': 13, 'wins': 10, 'losses': 3, 'win_rate': 76.9, 'points': 30.8},
    {'rank': 4, 'team_tag': 'GEN', 'team_name': 'Gen.G Esports', 'total_matches': 12, 'wins': 9, 'losses': 3, 'win_rate': 75.0, 'points': 27.4},
    {'rank': 5, 'team_tag': 'RRQ', 'team_name': 'Rex Regum Qeon', 'total_matches': 11, 'wins': 8, 'losses': 3, 'win_rate': 72.7, 'points': 24.1},
    {'rank': 6, 'team_tag': 'TS', 'team_name': 'Team Secret', 'total_matches': 10, 'wins': 7, 'losses': 3, 'win_rate': 70.0, 'points': 21.7},
    {'rank': 7, 'team_tag': 'TLN', 'team_name': 'Talon Esports', 'total_matches': 9, 'wins': 6, 'losses': 3, 'win_rate': 66.7, 'points': 18.9},
    {'rank': 8, 'team_tag': 'BLD', 'team_name': 'Bleed Esports', 'total_matches': 8, 'wins': 5, 'losses': 3, 'win_rate': 62.5, 'points': 15.3},
    {'rank': 9, 'team_tag': 'GE', 'team_name': 'Global Esports', 'total_matches': 7, 'wins': 4, 'losses': 3, 'win_rate': 57.1, 'points': 12.8},
    {'rank': 10, 'team_tag': 'ZETA', 'team_name': 'ZETA DIVISION', 'total_matches': 6, 'wins': 3, 'losses': 3, 'win_rate': 50.0, 'points': 9.5},
    {'rank': 11, 'team_tag': 'T1', 'team_name': 'T1 Esports', 'total_matches': 8, 'wins': 4, 'losses': 4, 'win_rate': 50.0, 'points': 8.2},
    {'rank': 12, 'team_tag': 'DFM', 'team_name': 'DetonatioN FocusMe', 'total_matches': 9, 'wins': 4, 'losses': 5, 'win_rate': 44.4, 'points': 6.9},
    {'rank': 13, 'team_tag': 'XIA', 'team_name': 'XERXIA Esports', 'total_matches': 10, 'wins': 4, 'losses': 6, 'win_rate': 40.0, 'points': 5.1},
    {'rank': 14, 'team_tag': 'FS', 'team_name': 'Full Sense', 'total_matches': 8, 'wins': 3, 'losses': 5, 'win_rate': 37.5, 'points': 3.8},
    {'rank': 15, 'team_tag': 'OG', 'team_name': 'Orangutan Gaming', 'total_matches': 7, 'wins': 2, 'losses': 5, 'win_rate': 28.6, 'points': 2.4},
]

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

def generate_test_image():
    """Generate a test leaderboard image with sample data"""
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    config = TEST_CONFIG
    
    # Check if template exists
    if not config['template'].exists():
        print(f"❌ Template not found: {config['template']}")
        print(f"Available templates:")
        for file in TEMPLATE_DIR.glob('*.jpg'):
            print(f"  - {file.name}")
        return
    
    # Load template
    print(f"📂 Loading template: {config['template'].name}")
    img = Image.open(config['template'])
    draw = ImageDraw.Draw(img)
    
    # Get image dimensions
    width, height = img.size
    print(f"📐 Image size: {width}x{height}")
    
    # Load fonts
    try:
        row_font = ImageFont.truetype(str(FONT_PATH), config['row_size'])
        print(f"✅ Font loaded: {FONT_PATH.name}")
    except Exception as e:
        print(f"❌ Error loading font: {e}")
        return
    
    # Draw team rows with individual positions for EACH text element
    print(f"📝 Drawing {len(config['rows'])} team rows with individual positions for each element")
    for row_config in config['rows']:
        idx = row_config['rank'] - 1
        if idx >= len(SAMPLE_TEAMS):
            continue
            
        team = SAMPLE_TEAMS[idx]
        
        # Rank - has its own X, Y, and color
        rank_text = f"{team['rank']}"
        draw.text((row_config['rank_x'], row_config['rank_y']), rank_text, font=row_font, fill=config['rank_color'])
        
        # Team name - has its own X, Y, and color
        team_text = f"[{team['team_tag']}] {team['team_name']}"
        if len(team_text) > 30:
            team_text = team_text[:27] + "..."
        draw.text((row_config['team_name_x'], row_config['team_name_y']), team_text, font=row_font, fill=config['team_name_color'])
        
        # Wins - has its own X, Y, and color
        draw.text((row_config['wins_x'], row_config['wins_y']), str(team['wins']), font=row_font, fill=config['wins_color'])
        
        # Losses - has its own X, Y, and color
        draw.text((row_config['losses_x'], row_config['losses_y']), str(team['losses']), font=row_font, fill=config['losses_color'])
        
        # Winrate - has its own X, Y, and color
        winrate_text = f"{team['win_rate']:.1f}%"
        draw.text((row_config['winrate_x'], row_config['winrate_y']), winrate_text, font=row_font, fill=config['winrate_color'])
        
        # Points - has its own X, Y, and color
        points_text = f"{team['points']:.1f}"
        draw.text((row_config['points_x'], row_config['points_y']), points_text, font=row_font, fill=config['points_color'])
        
        print(f"  Row {team['rank']}: {team['team_name']}")
        print(f"    Rank at ({row_config['rank_x']}, {row_config['rank_y']})")
        print(f"    Team Name at ({row_config['team_name_x']}, {row_config['team_name_y']})")
        print(f"    Wins at ({row_config['wins_x']}, {row_config['wins_y']})")
        print(f"    Losses at ({row_config['losses_x']}, {row_config['losses_y']})")
        print(f"    Winrate at ({row_config['winrate_x']}, {row_config['winrate_y']})")
        print(f"    Points at ({row_config['points_x']}, {row_config['points_y']})")
    
    # Add Discord-style border if enabled
    if ADD_BORDER:
        print(f"\n🎨 Adding Discord-style border...")
        img = add_discord_border(img)
    
    # Save image
    output_path = OUTPUT_DIR / f'test_{config["region"]}_leaderboard.jpg'
    img.save(output_path, quality=95)
    
    print(f"\n✅ Test image generated: {output_path}")
    print(f"\n📋 Current Configuration:")
    print(f"  Region: {config['region']}")
    print(f"  Template: {config['template'].name}")
    print(f"  Row Font Size: {config['row_size']}")
    print(f"\n💡 Each text element has its own X and Y position!")
    print(f"💡 Edit values at the TOP of this file to adjust alignment.")
    
    return output_path

if __name__ == "__main__":
    print("="*70)
    print("🎨 LEADERBOARD TEXT ALIGNMENT TEST")
    print("="*70)
    print("\n📝 Instructions:")
    print("  1. Edit the values at the TOP of this script")
    print("  2. Save the file")
    print("  3. Run: python test_leaderboard_alignment.py")
    print("  4. Check output in test_alignment/ folder")
    print("  5. Repeat until perfect!")
    print("\n" + "="*70 + "\n")
    
    generate_test_image()
    
    print("\n" + "="*70)
    print("✨ Done! Check the test_alignment folder for the output.")
    print("="*70)
