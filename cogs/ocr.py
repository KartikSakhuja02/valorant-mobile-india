# cogs/ocr.py - Hybrid OCR: Gemini API for text + Local color detection for teams + Local agent detection
from __future__ import annotations

import io, json, base64, colorsys, asyncio, random, re
from typing import List, Dict, Any, Optional
from pathlib import Path
import os

# Try to load .env if present (optional)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except Exception:
    pass

# helper to read env var or fallback to config.json
_CONFIG_JSON = None
def _load_config_json():
    global _CONFIG_JSON
    if _CONFIG_JSON is not None:
        return _CONFIG_JSON
    try:
        path = Path(__file__).parent.parent / 'config.json'
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                _CONFIG_JSON = json.load(f)
                return _CONFIG_JSON
    except Exception:
        _CONFIG_JSON = {}
    _CONFIG_JSON = {}
    return _CONFIG_JSON

def cfg(key, default=None):
    val = os.environ.get(key)
    if val is not None:
        return val
    return _load_config_json().get(key, default)

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from PIL import Image, ImageOps
import numpy as np
import cv2
from services import db  # Add database import
from services.yolo_agent_detector import get_yolo_agent_detector  # YOLO for agent detection
from services.gemini_agent_detector import get_gemini_agent_detector  # Gemini Vision API
from services.hybrid_agent_detector import get_hybrid_agent_detector  # Hybrid detector (YOLO + Gemini + JSON)
# from services.template_agent_detector import TemplateAgentDetector  # Not used  # Template matching detector
from services.roboflow_agent_detector import RoboflowAgentDetector
from services.roboflow_agent_detector import get_roboflow_agent_detector  # Roboflow hosted workflow detector

# Import agent detector
import sys
sys.path.append(str(Path(__file__).parent.parent))

# Chinese to English map name translation
CHINESE_MAP_NAMES = {
    '亚海悬城': 'Ascent',
    '源工重镇': 'Bind',
    '极寒冬港': 'Icebox',
    '隐世修所': 'Haven',
    '霓虹町': 'Split',
    '微风岛屿': 'Breeze',
    '裂变峡谷': 'Fracture',
    '珍珠': 'Pearl',
    '莲华古城': 'Lotus',
    '日落之城': 'Sunset',
    '深夜迷城': 'Abyss'
}

def translate_map_name(map_text: str) -> str:
    """Translate Chinese map name to English. If already English or unknown, return as-is."""
    if not map_text:
        return 'Unknown'
    
    # Check if it's Chinese map name
    for chinese, english in CHINESE_MAP_NAMES.items():
        if chinese in map_text:
            return english
    
    # Check if it's already English (case-insensitive partial match)
    map_text_lower = map_text.lower()
    english_maps = ['ascent', 'bind', 'icebox', 'haven', 'split', 'breeze', 
                    'fracture', 'pearl', 'lotus', 'sunset', 'abyss']
    
    for eng_map in english_maps:
        if eng_map in map_text_lower:
            return eng_map.capitalize()
    
    return map_text  # Return as-is if unknown


# Agent selection view for manual verification
class AgentCorrectionView(discord.ui.View):
    def __init__(self, row_index: int, current_agent: str, callback):
        super().__init__(timeout=300)  # 5 minute timeout
        self.row_index = row_index
        self.current_agent = current_agent
        self.callback = callback
        self.selected_agent = current_agent
        
        # Load agent names dynamically from agents images folder
        self.agents = self._load_agent_names()
        if not self.agents:
            # Fallback to hardcoded list if folder not found
            self.agents = [
                "Jett", "Sage", "Phoenix", "Reyna", "Raze", "Breach",
                "Omen", "Brimstone", "Viper", "Cypher", "Sova", "Killjoy",
                "Skye", "Yoru", "Astra", "KAY/O", "Chamber", "Neon",
                "Fade", "Harbor", "Gekko", "Deadlock", "Iso", "Clove", "Vyse"
            ]
    
    async def save_agent_usage(self, discord_id: int, agent_name: str, kills: int, deaths: int, assists: int, is_mvp: bool = False):
        """Track which agents a player uses and their stats with each agent"""
        try:
            pool = await db.get_pool()
            await pool.execute("""
                INSERT INTO player_agent_stats 
                (discord_id, agent_name, matches_played, total_kills, total_deaths, total_assists, mvps)
                VALUES ($1, $2, 1, $3, $4, $5, $6)
                ON CONFLICT (discord_id, agent_name)
                DO UPDATE SET
                    matches_played = player_agent_stats.matches_played + 1,
                    total_kills = player_agent_stats.total_kills + $3,
                    total_deaths = player_agent_stats.total_deaths + $4,
                    total_assists = player_agent_stats.total_assists + $5,
                    mvps = player_agent_stats.mvps + $6,
                    updated_at = CURRENT_TIMESTAMP
            """, discord_id, agent_name, kills, deaths, assists, 1 if is_mvp else 0)
        except Exception as e:
            print(f"Error saving agent usage: {e}")


    async def save_match_to_database(self, match_data: dict, team_a_players: list, team_b_players: list):
        """Save match data, player stats, and agent usage to PostgreSQL"""
        try:
            pool = await db.get_pool()
            
            # 1. Insert match record
            match_id = await pool.fetchval("""
                INSERT INTO matches (
                    map_name, team1_score, team2_score
                )
                VALUES ($1, $2, $3)
                RETURNING id
            """, 
                match_data.get('map', 'Unknown'),
                match_data.get('team_a_rounds', 0),
                match_data.get('team_b_rounds', 0)
            )
            
            print(f"[DB] Match saved with ID: {match_id}")
            
            # 2. Process all players (both teams)
            all_players = []
            for player in team_a_players:
                player['team'] = match_data.get('team_a', 'Team A')
                all_players.append(player)
            for player in team_b_players:
                player['team'] = match_data.get('team_b', 'Team B')
                all_players.append(player)
            
            for player in all_players:
                # Look up player by IGN to get discord_id
                ign = player.get('ign', '').strip()
                if not ign:
                    continue
                
                player_db = await db.get_player_by_ign(ign)
                if not player_db:
                    print(f"[DB] Player '{ign}' not registered, skipping...")
                    continue
                
                discord_id = player_db['discord_id']
                agent = player.get('agent', 'Unknown')
                kills = int(player.get('kills', 0))
                deaths = int(player.get('deaths', 0))
                assists = int(player.get('assists', 0))
                is_mvp = player.get('mvp', False)
                team = player.get('team', '')
                
                # 3. Insert into match_players table
                await pool.execute("""
                    INSERT INTO match_players (
                        match_id, discord_id, team, kills, deaths, assists, agent, is_mvp
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, match_id, discord_id, team, kills, deaths, assists, agent, is_mvp)
                
                # 4. Update player_agent_stats
                await self.save_agent_usage(discord_id, agent, kills, deaths, assists, is_mvp)
                
                # 5. Update player_stats (uses discord_id)
                await pool.execute("""
                    INSERT INTO player_stats (discord_id, tournament_id, kills, deaths, assists, matches_played, wins, losses, mvps)
                    VALUES ($1, 1, $2, $3, $4, 1, 0, 0, $5)
                    ON CONFLICT (discord_id, tournament_id)
                    DO UPDATE SET
                        matches_played = player_stats.matches_played + 1,
                        kills = player_stats.kills + $2,
                        deaths = player_stats.deaths + $3,
                        assists = player_stats.assists + $4,
                        mvps = player_stats.mvps + $5,
                        updated_at = CURRENT_TIMESTAMP
                """, discord_id, kills, deaths, assists, 1 if is_mvp else 0)
            
            # 6. Update team stats - DISABLED for now (focus on player stats)
            # winner = match_data.get('winner', '')
            # TODO: Re-enable team stats after player stats are working
            
            print(f"[DB] Match data saved successfully! Match ID: {match_id}")
            return match_id
            
        except Exception as e:
            print(f"Error saving match to database: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _load_agent_names(self) -> List[str]:
        """Load agent names from agents images folder"""
        try:
            agents_folder = Path("agents images")
            if not agents_folder.exists():
                return []
            
            agent_names = []
            for file in agents_folder.iterdir():
                if file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                    # Extract agent name from filename
                    # Format: "1280-agentkayo.png" -> "KAY/O"
                    # Format: "1980-agentjett.png" -> "Jett"
                    # Format: "5344-valorant-skye-icon.png" -> "Skye"
                    filename = file.stem.lower()
                    
                    # Clean up filename: remove numbers, "valorant-", "-icon", etc.
                    filename = filename.replace('valorant-', '').replace('-icon', '')
                    
                    # Remove number prefix and "agent" prefix
                    if '-agent' in filename:
                        agent_name = filename.split('-agent')[1]
                    elif 'agent' in filename:
                        agent_name = filename.replace('agent', '')
                    else:
                        agent_name = filename
                    
                    # Remove any remaining numbers
                    agent_name = ''.join([c for c in agent_name if not c.isdigit()]).strip('-_')
                    
                    # Convert to proper case
                    agent_map = {
                        'jett': 'Jett', 'sage': 'Sage', 'phoenix': 'Phoenix',
                        'reyna': 'Reyna', 'raze': 'Raze', 'breach': 'Breach',
                        'omen': 'Omen', 'brimstone': 'Brimstone', 'viper': 'Viper',
                        'cypher': 'Cypher', 'sova': 'Sova', 'killjoy': 'Killjoy',
                        'skye': 'Skye', 'yoru': 'Yoru', 'astra': 'Astra',
                        'kayo': 'KAY/O', 'chamber': 'Chamber', 'neon': 'Neon',
                        'fade': 'Fade', 'harbor': 'Harbor', 'gekko': 'Gekko',
                        'deadlock': 'Deadlock', 'iso': 'Iso', 'clove': 'Clove',
                        'vyse': 'Vyse'
                    }
                    
                    proper_name = agent_map.get(agent_name)
                    if proper_name and proper_name not in agent_names:
                        agent_names.append(proper_name)
            
            return sorted(agent_names)
        except Exception as e:
            print(f"Error loading agent names: {e}")
            return []
        
        # Create select menu
        options = [discord.SelectOption(label=agent, value=agent, default=(agent==current_agent)) for agent in self.agents]
        select = discord.ui.Select(placeholder=f"Row {row_index}: {current_agent}", options=options[:25])  # Discord limit
        select.callback = self.select_callback
        self.add_item(select)
        
        # Confirm button
        confirm_btn = discord.ui.Button(label="✅ Confirm", style=discord.ButtonStyle.success)
        confirm_btn.callback = self.confirm_callback
        self.add_item(confirm_btn)
    
    async def select_callback(self, interaction: discord.Interaction):
        self.selected_agent = interaction.data['values'][0]
        await interaction.response.defer()
    
    async def confirm_callback(self, interaction: discord.Interaction):
        await self.callback(self.row_index, self.selected_agent)
        await interaction.response.send_message(f"✅ Row {self.row_index}: {self.selected_agent}", ephemeral=True)
        self.stop()

# local OCR options
try:
    import easyocr
    _HAS_EASYOCR = True
except Exception:
    _HAS_EASYOCR = False

try:
    import pytesseract
    _HAS_TESSERACT = True
except Exception:
    _HAS_TESSERACT = False

# --------------------------- Config -----------------------------------------
try:
    GUILD_ID = int(cfg('GUILD_ID') or cfg('GUILD') or 0)
except Exception:
    GUILD_ID = 0

try:
    EMBED_COLOR = int(cfg('EMBED_COLOR') or 0xFF7A00)
except Exception:
    EMBED_COLOR = 0xFF7A00

BRAND_ICON_URL = cfg('BRAND_ICON_URL')
GEMINI_API_KEY = cfg('GEMINI_API_KEY')

GUILD = discord.Object(id=GUILD_ID) if GUILD_ID else None

# --------------------------- Gemini OCR setup -------------------------------
# We'll allow multiple model candidates and endpoints; config may override model
GEMINI_MODEL = cfg('GEMINI_MODEL')
GEMINI_MODEL_CANDIDATES = [
    "gemini-2.5-flash",      # Latest stable multimodal model
    "gemini-flash-latest",   # Always points to latest flash
    "gemini-2.0-flash",      # Older but stable
    GEMINI_MODEL,
]

def _gemini_url_for(model_name: str, use_v1: bool = True) -> str:
    if not model_name:
        return ""
    version = "v1" if use_v1 else "v1beta"
    return f"https://generativelanguage.googleapis.com/{version}/models/{model_name}:generateContent"

def _load_valid_agents() -> List[str]:
    """Load all agent names from agents images folder"""
    try:
        agents_folder = Path("agents images")
        if not agents_folder.exists():
            return []
        
        agent_names = []
        agent_map = {
            'jett': 'Jett', 'sage': 'Sage', 'phoenix': 'Phoenix',
            'reyna': 'Reyna', 'raze': 'Raze', 'breach': 'Breach',
            'omen': 'Omen', 'brimstone': 'Brimstone', 'viper': 'Viper',
            'cypher': 'Cypher', 'sova': 'Sova', 'killjoy': 'Killjoy',
            'skye': 'Skye', 'yoru': 'Yoru', 'astra': 'Astra',
            'kayo': 'KAY/O', 'chamber': 'Chamber', 'neon': 'Neon',
            'fade': 'Fade', 'harbor': 'Harbor', 'gekko': 'Gekko',
            'deadlock': 'Deadlock', 'iso': 'Iso', 'clove': 'Clove',
            'vyse': 'Vyse'
        }
        
        for file in agents_folder.iterdir():
            if file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                filename = file.stem.lower()
                
                # Clean up filename: remove numbers, "valorant-", "-icon", etc.
                filename = filename.replace('valorant-', '').replace('-icon', '')
                
                # Remove number prefix and "agent" prefix
                if '-agent' in filename:
                    agent_name = filename.split('-agent')[1]
                elif 'agent' in filename:
                    agent_name = filename.replace('agent', '')
                else:
                    agent_name = filename
                
                # Remove any remaining numbers
                agent_name = ''.join([c for c in agent_name if not c.isdigit()]).strip('-_')
                
                proper_name = agent_map.get(agent_name)
                if proper_name and proper_name not in agent_names:
                    agent_names.append(proper_name)
        
        return sorted(agent_names)
    except Exception as e:
        print(f"Error loading agent names: {e}")
        return []

# Load valid agents dynamically
VALID_AGENTS = _load_valid_agents()
if not VALID_AGENTS:
    # Fallback list if folder not found
    VALID_AGENTS = [
        "Jett", "Sage", "Phoenix", "Reyna", "Raze", "Breach",
        "Omen", "Brimstone", "Viper", "Cypher", "Sova", "Killjoy",
        "Skye", "Yoru", "Astra", "KAY/O", "Chamber", "Neon",
        "Fade", "Harbor", "Gekko", "Deadlock", "Iso", "Clove", "Vyse"
    ]

# Load AI-generated agent descriptions
def _load_agent_descriptions() -> Dict[str, str]:
    """Load AI-generated descriptions from JSON file"""
    try:
        # Try multiple possible paths
        possible_paths = [
            Path(__file__).parent.parent / 'data' / 'agent_descriptions.json',
            Path(__file__).parent / 'data' / 'agent_descriptions.json',
            Path('data') / 'agent_descriptions.json',
        ]
        
        for desc_path in possible_paths:
            if desc_path.exists():
                print(f"Loading agent descriptions from: {desc_path}")
                with open(desc_path, 'r', encoding='utf-8') as f:
                    descriptions = json.load(f)
                    if descriptions:
                        print(f"Loaded {len(descriptions)} agent descriptions")
                        return descriptions
    except Exception as e:
        print(f"Could not load agent descriptions: {e}")
    return {}

AGENT_DESCRIPTIONS = _load_agent_descriptions()

# Load confusion pairs for extra clarification
def _load_confusion_pairs() -> List[Dict[str, Any]]:
    """Load agent confusion pairs from JSON file"""
    try:
        possible_paths = [
            Path(__file__).parent.parent / 'data' / 'confused_agents.json',
            Path(__file__).parent / 'data' / 'confused_agents.json',
            Path('data') / 'confused_agents.json',
        ]
        
        for conf_path in possible_paths:
            if conf_path.exists():
                print(f"Loading confusion pairs from: {conf_path}")
                with open(conf_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    pairs = data.get('confusion_pairs', [])
                    if pairs:
                        print(f"Loaded {len(pairs)} confusion pairs")
                        return pairs
    except Exception as e:
        print(f"Could not load confusion pairs: {e}")
    return []

CONFUSION_PAIRS = _load_confusion_pairs()

# Build agent guide from AI descriptions or use fallback
def _build_agent_guide() -> str:
    """Build agent identification guide from AI descriptions"""
    if AGENT_DESCRIPTIONS:
        # Use AI-generated descriptions
        guide = "AGENT IDENTIFICATION - AI-ANALYZED DESCRIPTIONS:\n\n"
        guide += "Study the small circular portrait icon on the LEFT of each player row.\n"
        guide += "Compare what you see with these AI-generated visual descriptions:\n\n"
        
        for agent in sorted(VALID_AGENTS):
            desc = AGENT_DESCRIPTIONS.get(agent, f"Visual features for {agent}")
            guide += f"- {agent}: {desc}\n"
        
        # Add confusion warnings if available
        if CONFUSION_PAIRS:
            guide += "\n⚠️ COMMON CONFUSIONS - EXTRA CARE NEEDED:\n\n"
            for pair in CONFUSION_PAIRS:
                agents = pair.get('agents', [])
                note = pair.get('note', '')
                if len(agents) >= 2 and note:
                    guide += f"❗ {agents[0]} vs {agents[1]}: {note}\n"
        
        return guide
    else:
        # Fallback to manual descriptions
        return """AGENT IDENTIFICATION - Study the small circular portrait icon on the LEFT of each player row:

🔥 DUELISTS (Aggressive attackers):
- Jett: WHITE/SILVER SHORT HAIR, Asian female, calm face, BLUE/WHITE color scheme, wind theme
- Phoenix: Black British male, BRIGHT ORANGE FLAMING HAIR (literally on fire), big smile, orange/yellow/fire colors
- Reyna: Latina female, PURPLE GLOWING EYES (most distinctive!), vampire/soul theme, DARK PURPLE/BLACK colors, fierce expression
- Raze: Brazilian female, SHORT BRIGHT ORANGE/YELLOW HAIR, GOGGLES on forehead, cheerful grin, explosive theme, tan skin
- Yoru: Japanese male, BLUE HAIR with white/light highlights, rift mask (blue), edgy look, dimensional theme
- Neon: Filipino female, ELECTRIC BLUE STREAKS in dark hair, athletic build, lightning bolts, energetic look
- Iso: Chinese male, PURPLE geometric patterns, shield symbol, modern tactical gear, serious expression

☁️ CONTROLLERS (Area denial):
- Brimstone: Older American male, COMPLETELY BALD HEAD (key!), ORANGE/BROWN TACTICAL VEST, facial hair (beard/mustache), serious
- Omen: DARK HOODED FIGURE, NO VISIBLE FACE (shadowy/ghostly), purple/black smoke effects, three eyes on hood, very dark
- Viper: Female, BRIGHT GREEN theme, GAS MASK covering face, toxic/poison aesthetic, green chemicals
- Astra: African female, COSMIC/SPACE theme, PURPLE ENERGY and stars, braided hair, mystical appearance
- Harbor: Indian male, BLUE WATER/OCEAN theme, glowing artifact on chest, water effects, calm expression
- Clove: Young Scottish, PINK/PURPLE SMOKE, butterfly motifs, vibrant colors, playful look

⚡ INITIATORS (Intel gatherers):
- Sova: Russian male, BLONDE/YELLOW HAIR, BOW AND ARROW visible, BLUE tactical gear, hunter aesthetic, serious face
- Breach: Swedish male, ROBOTIC/MECHANICAL ARMS (bionic), ORANGE/BROWN colors, very muscular, bald with tattoos
- Skye: Australian female, ANIMAL COMPANION (hawk/creatures), GREEN NATURE theme, friendly warm smile, outdoorsy
- KAY/O: FULL ROBOT (not human!), MECHANICAL HEAD with glowing blue lights, no face, suppression tech, very robotic
- Fade: Turkish female, DARK NIGHTMARE theme, BLACK/PURPLE colors, haunting scary look, fear aesthetic
- Gekko: Latino American, GREEN CREATURES/PETS (radivores), young male, colorful, friendly animals around him

🛡️ SENTINELS (Defenders):
- Sage: Chinese female, TRADITIONAL OUTFIT, ICE/FROST theme, BLACK HAIR with ice ornaments, calm healer look, composed
- Cypher: Moroccan male, FULL FACE MASK (completely covered!), SPY HAT, YELLOW/TAN colors, mysterious, can't see face at all
- Killjoy: German female, BRIGHT YELLOW CLOTHES/JACKET, GLASSES (nerdy), tech genius, turret builder, young cheerful
- Chamber: French male, FANCY GOLD SUIT, sophisticated businessman, gold accents, well-dressed, handsome smirk
- Deadlock: Norwegian female, MECHANICAL BEAR TRAP theme, tactical gear, serious military look, blonde
- Vyse: METALLIC/SILVER theme, rose/flower motifs, precise geometric patterns, elegant tech aesthetic
"""

# Build the prompt - NO AGENT DETECTION, FOCUS ON PLAYER ROWS
PROMPT_TEMPLATE = """
You are reading a VALORANT Mobile scoreboard screenshot. FOCUS CAREFULLY on identifying the agent icons.

IMPORTANT: There are exactly 10 player rows in the scoreboard. Each row shows:
- A small circular AGENT PORTRAIT ICON on the far left (THIS IS CRITICAL - LOOK CLOSELY AT THESE ICONS)
- Player IGN (in-game name)
- K/D/A stats in format "kills / deaths / assists"

AGENT IDENTIFICATION IS CRUCIAL:
- The circular portrait on the LEFT of each player's name shows their agent
- Look at the icon's colors, design, and character features carefully
- If you're unsure between similar agents, make your best educated guess
- Common similar agents: Jett vs Neon, Sage vs Skye, Omen vs Harbor

IGNORE everything else: match time, date, buttons, headers, etc.

Return RAW JSON ONLY (no markdown), exactly like:
{{
  "map": "Ascent",
  "score": {{"top": 13, "bottom": 9}},
  "players": [
    {{"ign":"Chiku.Zr","agent":"Jett","kills":16,"deaths":10,"assists":7}},
    {{"ign":"Andyyyyy","agent":"Sage","kills":13,"deaths":8,"assists":4}},
    {{"ign":"DarkWiz.Zr","agent":"Phoenix","kills":13,"deaths":8,"assists":6}},
    {{"ign":"Kan4Ki","agent":"Reyna","kills":12,"deaths":13,"assists":3}},
    {{"ign":"SPNX.kirmada","agent":"Raze","kills":12,"deaths":10,"assists":2}},
    {{"ign":"Remz.Zr","agent":"Omen","kills":9,"deaths":9,"assists":8}},
    {{"ign":"Fateh.Zr","agent":"Brimstone","kills":8,"deaths":9,"assists":4}},
    {{"ign":"Zanis7","agent":"Viper","kills":6,"deaths":13,"assists":4}},
    {{"ign":"Ir0nic","agent":"Cypher","kills":7,"deaths":13,"assists":2}},
    {{"ign":"~ZensU","agent":"Sova","kills":7,"deaths":10,"assists":1}}
  ]
}}

AVAILABLE VALORANT AGENTS (use exact spelling - case sensitive):
DUELISTS (aggressive, damage dealers):
- Jett (white/blue, wind theme, knife)
- Phoenix (orange/red, fire theme)
- Reyna (purple, soul theme)
- Raze (orange/yellow, explosives)
- Yoru (blue, rift walker)
- Neon (electric blue, lightning)
- Iso (purple/blue shield)

INITIATORS (gather intel, start fights):
- Sova (blue, bow and arrow)
- Breach (orange, mechanical arms)
- Skye (green, nature/healing)
- KAY/O (gray/blue, robotic)
- Fade (dark purple, nightmare)
- Gekko (green/yellow, creatures)

CONTROLLERS (smoke, area denial):
- Brimstone (orange, military, orbital)
- Omen (dark blue/black, ghost)
- Viper (green, poison/toxic)
- Astra (purple/cosmic, stars)
- Harbor (teal/cyan, water)
- Clove (pink/purple, Scottish)

SENTINELS (defense, support):
- Sage (white/ice blue, healing)
- Cypher (tan/brown, surveillance)
- Killjoy (yellow, tech/turrets)
- Chamber (gold/white, businessman)
- Deadlock (gray/white, Norwegian)
- Vyse (blue/silver, metallic)

AGENT IDENTIFICATION TIPS:
- Jett: Distinctive white/light blue hair, wind motif
- Sage: Long black hair with white/ice theme
- Phoenix: Bright orange/red, flame design
- Reyna: Purple eyes prominent, soul collector
- Raze: Bright orange/yellow, explosive personality
- Omen: Very dark, hooded, ghostly
- Brimstone: Military look, mustache, orange
- Viper: Green toxic theme, mask
- Cypher: Brown/tan colors, technology
- Sova: Blue with bow, recon hunter
- Breach: Orange mechanical, Swedish
- Skye: Green nature theme, Australian
- KAY/O: Robotic, gray/blue
- Fade: Dark purple, Turkish, nightmarish
- Gekko: Colorful, creatures companion
- Astra: Purple cosmic theme, African
- Harbor: Teal water theme, Indian
- Neon: Electric blue lightning theme
- Chamber: Gold/elegant, French
- Killjoy: Yellow tech, German
- Yoru: Blue rift walker, Japanese
- Deadlock: Gray/white, Norwegian
- Clove: Pink/purple, Scottish
- Iso: Purple/blue shield, Chinese
- Vyse: Blue/silver metallic

CRITICAL RULES:
1. CAREFULLY EXAMINE each circular portrait icon on the left of player names
2. Match the icon's colors and design to the agent descriptions above
3. Each row has: [Agent Portrait Icon] [Player Name] [Score] [K/D/A] [Other Stats]
4. Player names can contain: letters, numbers, dots, underscores, Chinese characters, spaces
5. K/D/A format is "number / number / number" (e.g., "16 / 10 / 7")
6. SKIP any rows that don't have a portrait icon (those are headers/time/etc)
7. Return exactly 10 players in order from top to bottom
8. Get the match score from the top (format like "10 获胜 4" or "13 — 9")
9. If IGN is unreadable, use "PLAYER_X" where X is the row number
10. If K/D/A numbers are unreadable, set to null
11. If agent is really unclear after careful examination, use "Unknown" but TRY YOUR BEST FIRST

DO NOT include:
- Match date/time (e.g., "2025/07/20 17:48")
- Headers (e.g., "个人排名", "平均战斗评分")
- Buttons or UI elements
- Anything without a circular portrait icon

FOCUS: Examine the agent portrait icons carefully - they are your PRIMARY source for agent identification!
"""

AGENT_GUIDE = ""  # Agent detection disabled
PROMPT = PROMPT_TEMPLATE  # No formatting needed

# --------------------------- Utilities --------------------------------------
def _extract_json(text: str) -> dict:
    s = (text or "").strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1]
        if s.endswith("```"):
            s = s[:-3]
    start = s.find("{")
    if start == -1:
        raise ValueError("no JSON object found")
    depth = 0
    for i, ch in enumerate(s[start:], start=start):
        if ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(s[start:i+1])
    raise ValueError("unbalanced JSON")

def _downscale_max_side(pil: Image.Image, max_side: int = 1600) -> Image.Image:
    w, h = pil.size
    side = max(w, h)
    if side <= max_side:
        return pil
    scale = max_side / float(side)
    new_size = (int(w * scale), int(h * scale))
    return pil.resize(new_size, Image.LANCZOS)

# --------------------- Color classification ---------------------------------
def _rgb_to_hsv01(arr_uint8: np.ndarray) -> np.ndarray:
    arr = arr_uint8.astype(np.float32) / 255.0
    out = np.zeros_like(arr)
    for i, (r, g, b) in enumerate(arr):
        h, s, v = colorsys.rgb_to_hsv(float(r), float(g), float(b))
        out[i] = (h, s, v)
    return out

def _mask_hsv(hsv: np.ndarray, ranges_deg, s_min: float, v_min: float):
    h = hsv[:, 0] * 360.0
    s = hsv[:, 1]
    v = hsv[:, 2]
    ok = np.zeros(len(h), dtype=bool)
    for lo, hi in ranges_deg:
        if lo <= hi:
            ok |= (h >= lo) & (h <= hi)
        else:
            ok |= (h >= lo) | (h <= hi)  # wrap
    ok &= (s >= s_min) & (v >= v_min)
    return ok

def _score_patch(patch_rgb: np.ndarray):
    """
    Score a color patch for team detection.
    Returns: (blue_score, red_score, is_gold)
    - blue_score: confidence this is Team A (blue/cyan color)
    - red_score: confidence this is Team B (red color)
    - is_gold: True if this player has gold/yellow outline (MVP/top fragger)
    """
    if patch_rgb.size == 0:
        return 0.0, 0.0, False
    flat = patch_rgb.reshape(-1, 3).astype(np.uint8)
    hsv = _rgb_to_hsv01(flat)
    
    # Expanded Blue/Cyan range for Team A (more permissive)
    blue = _mask_hsv(hsv, [(170, 230)], 0.20, 0.20)
    
    # Red for Team B (slightly expanded)
    red = _mask_hsv(hsv, [(0, 25), (335, 360)], 0.30, 0.20)
    
    # Gold/Yellow outline (more permissive to catch edge cases)
    gold = _mask_hsv(hsv, [(25, 65)], 0.30, 0.35)
    
    return float(blue.mean()), float(red.mean()), bool(gold.any())

def _row_team_from_patches(patches: List[np.ndarray], row_idx: int = None):
    """
    Determine team from color patches.
    Blue = Team A, Red = Team B
    Returns: ("A", is_gold) or ("B", is_gold)
    """
    b_list, r_list, golds = [], [], []
    for p in patches:
        b, r, gold = _score_patch(p)
        b_list.append(b)
        r_list.append(r)
        golds.append(gold)
    
    # Weight patches differently - emphasize left and center patches more
    # Left patches near IGN are most reliable for team color
    weights = np.array([2.0, 1.5, 1.0, 0.8, 0.6], dtype=np.float32)
    blue_score = float((np.array(b_list) * weights).sum())
    red_score = float((np.array(r_list) * weights).sum())
    has_gold = any(golds)
    
    # Calculate confidence - if one color is clearly dominant, use it
    total_score = blue_score + red_score
    if total_score > 0:
        blue_confidence = blue_score / total_score
        red_confidence = red_score / total_score
        
        # If one team is clearly dominant (>60%), assign to that team
        if blue_confidence > 0.60:
            return "A", has_gold
        elif red_confidence > 0.60:
            return "B", has_gold
    
    # Fallback: small bias towards blue if very close
    if abs(blue_score - red_score) < 0.15:
        blue_score += 0.05
    
    team = "A" if blue_score >= red_score else "B"
    return team, has_gold

def _sample_color_patches(img: Image.Image, row_idx: int) -> List[np.ndarray]:
    im = img.convert("RGB")
    W, H = im.size
    arr = np.asarray(im)

    top = int(0.255 * H)
    row_h = int(0.067 * H)
    cy = top + int((row_idx + 0.5) * row_h)
    y1 = max(cy - 8, 0); y2 = min(cy + 8, H)

    x_ign_left  = int(0.19 * W)
    x_ign_right = int(0.38 * W)
    x_mid       = int(0.49 * W)
    x_kda       = int(0.56 * W)
    x_like      = int(0.90 * W)

    def patch(xc: int, width: int = 16) -> np.ndarray:
        half = width // 2
        x1 = max(xc - half, 0); x2 = min(xc + half, W)
        return arr[y1:y2, x1:x2, :]

    # Sample 5 patches with strategic positioning
    # Patches near IGN are most reliable for team color
    return [
        patch(int(x_ign_left + 5), width=20),      # Left side of IGN (wider, more reliable)
        patch(int(x_ign_right - 10), width=20),    # Right side of IGN (wider)
        patch(x_mid, width=16),                     # Center
        patch(int(x_kda + 8), width=12),           # KDA area (smaller)
        patch(int(x_like - 10), width=12),         # Right side (smaller)
    ]

# --------------------------- HTTP / Gemini ----------------------------------
RETRY_STATUSES = {429, 500, 502, 503, 504}
AIO_TIMEOUT = aiohttp.ClientTimeout(total=30)

async def call_gemini_with_retry(png_bytes: bytes, api_key: str, max_attempts: int = 4) -> dict:
    # Build payload once
    payload = {
        "contents": [{
            "parts": [
                {"text": PROMPT},
                {"inline_data": {"mime_type": "image/png", "data": base64.b64encode(png_bytes).decode("utf-8")}}
            ]
        }],
        "generationConfig": {"temperature": 0}
    }
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}

    # Try multiple model names with v1beta endpoint (vision models are in v1beta)
    tried = []
    models = [m for m in GEMINI_MODEL_CANDIDATES if m]
    if not models:
        models = ["gemini-1.5-flash-002", "gemini-pro-vision"]

    async with aiohttp.ClientSession(timeout=AIO_TIMEOUT) as session:
        for model in models:
            # Only use v1beta for vision models
            url = _gemini_url_for(model, use_v1=False)
            if not url:
                continue
            tried.append(url)
            for attempt in range(1, max_attempts + 1):
                try:
                    async with session.post(url, headers=headers, params=params, json=payload) as resp:
                        status = resp.status
                        data = await resp.json(content_type=None)
                        if status == 200:
                            return data
                        if status in RETRY_STATUSES:
                            sleep_s = (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                            await asyncio.sleep(sleep_s)
                            continue
                        # If 404 try next model
                        if status == 404:
                            break
                        raise RuntimeError(f"Gemini HTTP {status}: {data}")
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    sleep_s = (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                    await asyncio.sleep(sleep_s)
        # If we get here none of the models worked
    raise RuntimeError(f"Gemini models not available (tried: {tried})")

def parse_gemini_payload(data: dict) -> dict:
    if "candidates" not in data or not data["candidates"]:
        raise RuntimeError(f"Gemini bad response: {data}")
    parts = data["candidates"][0].get("content", {}).get("parts", [])
    if not parts or "text" not in parts[0]:
        raise RuntimeError(f"Gemini missing text: {data}")
    return _extract_json(parts[0]["text"])


def _local_ocr_from_image(pil: Image.Image) -> dict:
    """Return a parsed-like dict from local OCR (best-effort). Uses EasyOCR if available, otherwise pytesseract."""
    try:
        W, H = pil.size
        text_blocks = []
        ocr_results = []
        
        if _HAS_EASYOCR:
            reader = easyocr.Reader(['en', 'ch_sim'], gpu=False)
            results = reader.readtext(np.array(pil))
            for bbox, txt, conf in results:
                text_blocks.append(txt)
                # Store position info: bbox is [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                y_avg = sum(p[1] for p in bbox) / 4
                x_avg = sum(p[0] for p in bbox) / 4
                ocr_results.append((txt, x_avg, y_avg, conf))
        elif _HAS_TESSERACT:
            txt = pytesseract.image_to_string(pil, lang='eng+chi_sim')
            for line in txt.splitlines():
                if line.strip():
                    text_blocks.append(line.strip())
        else:
            raise RuntimeError("No local OCR engine available")

        all_text = "\n".join(text_blocks)
        
        # Extract score (8 获胜 6 format or 8-6 format)
        score_top = None
        score_bottom = None
        score_match = re.search(r'(\d{1,2})\s*[获胜]{2}\s*(\d{1,2})', all_text)
        if score_match:
            score_top, score_bottom = int(score_match.group(1)), int(score_match.group(2))
        else:
            dash = re.search(r'(\d{1,2})\s*[-–]\s*(\d{1,2})', all_text)
            if dash:
                score_top, score_bottom = int(dash.group(1)), int(dash.group(2))
        
        # Extract map name (English or Chinese)
        map_name = None
        # Try English map names first
        map_patterns_en = r'(Haven|Bind|Split|Ascent|Icebox|Breeze|Fracture|Pearl|Lotus|Sunset|Abyss|District)'
        map_match = re.search(map_patterns_en, all_text, re.IGNORECASE)
        if map_match:
            map_name = map_match.group(1).capitalize()
        else:
            # Try Chinese map names
            map_patterns_cn = r'(亚海悬城|源工重镇|极寒冬港|隐世修所|霓虹町|微风岛屿|裂变峡谷|珍珠|莲华古城|日落之城|深夜迷城)'
            map_match_cn = re.search(map_patterns_cn, all_text)
            if map_match_cn:
                # Translate to English
                map_name = translate_map_name(map_match_cn.group(1))
        
        # Extract K/D/A triplets (format: "17 / 11 / 6")
        kda_pattern = r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{1,2})'
        kda_matches = list(re.finditer(kda_pattern, all_text))
        
        players = []
        # Use OCR result positions to pair IGNs with K/D/A stats if available
        if _HAS_EASYOCR and ocr_results:
            # Sort by Y position to get rows
            ocr_sorted = sorted(ocr_results, key=lambda x: x[2])
            
            # Group into rows (tolerance: within 30 pixels vertically)
            rows = []
            current_row = []
            for item in ocr_sorted:
                if not current_row:
                    current_row.append(item)
                else:
                    if abs(item[2] - current_row[0][2]) < 30:
                        current_row.append(item)
                    else:
                        rows.append(sorted(current_row, key=lambda x: x[1]))  # Sort by X
                        current_row = [item]
            if current_row:
                rows.append(sorted(current_row, key=lambda x: x[1]))
            
            # Extract players from rows with K/D/A
            for row in rows:
                row_text = " ".join([item[0] for item in row])
                kda = re.search(kda_pattern, row_text)
                if kda:
                    k, d, a = int(kda.group(1)), int(kda.group(2)), int(kda.group(3))
                    # IGN is usually the leftmost text in the row before K/D/A
                    ign = "Unknown"
                    for item in row:
                        if not re.match(r'^\d+\s*/\s*\d+\s*/\s*\d+$', item[0].strip()):
                            # Not a K/D/A, might be IGN
                            if item[1] < W * 0.4:  # Left side of screen
                                ign = item[0].strip()
                                break
                    players.append({"ign": ign, "kills": k, "deaths": d, "assists": a})
        else:
            # Fallback: just use K/D/A matches without IGNs
            for i, match in enumerate(kda_matches[:10]):
                k, d, a = int(match.group(1)), int(match.group(2)), int(match.group(3))
                players.append({"ign": f"PLAYER_{i+1}", "kills": k, "deaths": d, "assists": a})
        
        # Pad to 10 players if needed
        while len(players) < 10:
            players.append({"ign": f"PLAYER_{len(players)+1}", "kills": None, "deaths": None, "assists": None})

        return {"players": players[:10], "map": map_name, "score": {"top": score_top, "bottom": score_bottom}}
    except Exception as e:
        raise

# ------------------------------ The Cog -------------------------------------
class OCRScanner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Initialize Template Matching detector (HIGHEST PRIORITY - 100% accurate)
        self.template_detector = None
        try:
            self.template_detector = TemplateAgentDetector()
            if len(self.template_detector.templates) > 0:
                print(f"✅ Template Agent Detector initialized with {len(self.template_detector.templates)} templates")
            else:
                print("⚠️ Template Detector loaded but no templates found")
                self.template_detector = None
        except Exception as e:
            print(f"⚠️ Template Detector failed to load: {e}")
        
        # Initialize YOLO agent detector
        self.yolo_detector = None
        self.roboflow_detector = None
        try:
            self.yolo_detector = get_yolo_agent_detector()
            print("✅ YOLO Agent Detector initialized")
        except Exception as e:
            print(f"⚠️ YOLO Detector failed to load: {e}")
        
        # Initialize Gemini Vision agent detector
        self.gemini_detector = None
        try:
            self.gemini_detector = get_gemini_agent_detector(GEMINI_API_KEY)
            print("✅ Gemini Vision Agent Detector initialized")
        except Exception as e:
            print(f"⚠️ Gemini Agent Detector failed to load: {e}")
        
        # Initialize Hybrid Detector (combines YOLO + Gemini + JSON descriptions)
        self.hybrid_detector = None
        try:
            self.hybrid_detector = get_hybrid_agent_detector(
                yolo_detector=self.yolo_detector,
                gemini_detector=self.gemini_detector
            )
            print("✅ Hybrid Agent Detector initialized (YOLO + Gemini + JSON)")
        except Exception as e:
            print(f"⚠️ Hybrid Detector failed to load: {e}")

        # Initialize Roboflow hosted workflow detector if configured via env/config
        self.roboflow_detector = None
        try:
            roboflow_url = cfg('ROBOFLOW_WORKFLOW_URL', None) or os.environ.get('ROBOFLOW_WORKFLOW_URL')
            if roboflow_url:
                try:
                    self.roboflow_detector = get_roboflow_agent_detector(roboflow_url)
                    print("✅ Roboflow Agent Detector initialized")
                except Exception as e:
                    print(f"⚠️ Roboflow Detector failed to initialize: {e}")
        except Exception:
            # non-fatal
            pass

# ---- setup
async def setup(bot: commands.Bot):
    await bot.add_cog(OCRScanner(bot))
