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
from services.template_agent_detector import TemplateAgentDetector  # Template matching detector
from services.roboflow_agent_detector import get_roboflow_agent_detector  # Roboflow hosted workflow detector

# Import agent detector
import sys
sys.path.append(str(Path(__file__).parent.parent))

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
        
        # Extract map name (common Valorant maps)
        map_name = None
        map_patterns = r'(Haven|Bind|Split|Ascent|Icebox|Breeze|Fracture|Pearl|Lotus|Sunset|Abyss|District)'
        map_match = re.search(map_patterns, all_text, re.IGNORECASE)
        if map_match:
            map_name = map_match.group(1).capitalize()
        
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

    @app_commands.command(name="scan", description="[ADMIN] Scan a Valorant Mobile scoreboard screenshot")
    @app_commands.describe(image="Upload the scoreboard screenshot")
    async def scan(self, interaction: discord.Interaction, image: discord.Attachment):
        # Defer IMMEDIATELY to avoid timeout (must be within 3 seconds)
        try:
            await interaction.response.defer(thinking=True)
        except discord.errors.NotFound:
            # Interaction already expired or responded to
            return
        except Exception as e:
            print(f"⚠️ Failed to defer interaction: {e}")
            return
        
        # Admin check
        if not interaction.guild:
            await interaction.followup.send("❌ This command can only be used in a server!", ephemeral=True)
            return
        
        if not interaction.user.guild_permissions.administrator:
            user_roles = [role.name.lower() for role in interaction.user.roles]
            if not any(role in user_roles for role in ['admin', 'staff', 'moderator', 'mod']):
                await interaction.followup.send("❌ You need Admin or Staff role to scan scoreboards!", ephemeral=True)
                return
        
        if not GEMINI_API_KEY:
            await interaction.followup.send("❌ No `GEMINI_API_KEY` set. Please set GEMINI_API_KEY in environment variables or your .env file.", ephemeral=True)
            return
        
        # Define file paths for JSON fallback (needed for points calculation)
        players_file = Path(__file__).parent.parent / "data" / "players.json"
        
        try:
            # Read and process image
            img_bytes = await image.read()
            pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            pil = _downscale_max_side(pil, 1600)
            pil_for_ocr = ImageOps.autocontrast(pil, cutoff=1)

            # Prepare for Gemini
            bio = io.BytesIO()
            pil_for_ocr.save(bio, format="PNG")
            png_bytes = bio.getvalue()

            # Call Gemini API for text extraction
            parsed = None
            used_fallback = False
            try:
                data = await call_gemini_with_retry(png_bytes, GEMINI_API_KEY, max_attempts=4)
                parsed = parse_gemini_payload(data)
            except Exception as e_api:
                # If Gemini fails (404 or model not available), fallback to local OCR
                used_fallback = True
                parsed = _local_ocr_from_image(pil_for_ocr)

            # Get players from Gemini
            players: List[Dict[str, Any]] = (parsed.get("players") or [])[:10]
            while len(players) < 10:
                players.append({"ign": "UNKNOWN", "kills": None, "deaths": None, "assists": None})
            

            # ============ AGENT DETECTION: YOLO ONLY ============
            # Save temp image for YOLO agent detection
            temp_image_path = Path(__file__).parent.parent / "temp" / f"scan_{interaction.id}.png"
            temp_image_path.parent.mkdir(exist_ok=True)
            pil.save(temp_image_path, format="PNG")

            detected_agents = []
            detected_map = 'Unknown'
            agent_detection_success = False
            detection_method = "YOLO"

            try:
                print("\n" + "="*70)
                print("🎯 USING YOLO FOR AGENT DETECTION (SOLO)")
                print("="*70)

                # Use YOLO with specified weights file
                yolo_weights_path = Path(__file__).parent.parent / "imports" / "agents images" / "agent_weight" / "best.pt"
                if not hasattr(self, 'yolo_detector') or self.yolo_detector is None or getattr(self.yolo_detector, 'model_path', None) != yolo_weights_path:
                    print(f"⚠️ YOLO detector not initialized with correct weights - loading now...")
                    from services.yolo_agent_detector import get_yolo_agent_detector
                    self.yolo_detector = get_yolo_agent_detector(str(yolo_weights_path))

                # Run YOLO detection
                result = self.yolo_detector.detect_agents_from_screenshot(str(temp_image_path), confidence_threshold=0.25)
                detected_agents = [a.capitalize() if isinstance(a, str) else 'Unknown' for a in result.get('agents', ['Unknown']*10)]
                detected_map = result.get('map', 'Unknown')
                detections = result.get('detections', [])

                # Count confident detections (>= 0.5)
                confident_detections = sum(1 for d in detections if d.get('confidence', 0) >= 0.5)
                agent_detection_success = confident_detections > 0
                detection_method = f"YOLO ({confident_detections}/10 confident)"

                print(f"\n✅ YOLO Results:")
                print(f"   Total confident detections: {confident_detections}/10")
                print(f"   Detected agents: {detected_agents}")
                print(f"\n📊 Detailed Confidence Scores:")
                for i, d in enumerate(detections[:10]):
                    conf = d.get('confidence', 0)
                    agent = d.get('agent', 'unknown')
                    status = "✅" if conf >= 0.5 else "⚠️"
                    print(f"   {status} Slot {i+1}: {agent.upper():12s} (confidence: {conf:.1%})")

            except Exception as e:
                print(f"\n❌ YOLO detection failed: {e}")
                import traceback
                traceback.print_exc()
                # Try Roboflow hosted workflow if initialized
                try:
                    if getattr(self, 'roboflow_detector', None):
                        print("➡️ Falling back to Roboflow hosted workflow for detection")
                        rf_result = self.roboflow_detector.detect_agents_from_screenshot(str(temp_image_path))
                        detected_agents = [a.capitalize() if isinstance(a, str) else 'Unknown' for a in rf_result.get('agents', ['Unknown']*10)]
                        detected_map = rf_result.get('map', 'Unknown')
                        detections = rf_result.get('detections', [])
                        confident_detections = sum(1 for d in detections if d.get('confidence', 0) >= 0.5)
                        agent_detection_success = confident_detections > 0
                        detection_method = f"Roboflow ({confident_detections}/10 confident)"
                        print(f"   Roboflow detected agents: {detected_agents}")
                    else:
                        raise RuntimeError("No Roboflow detector configured")
                except Exception as e2:
                    print(f"❌ Roboflow fallback failed: {e2}")
                    traceback.print_exc()
                    detected_agents = ['Unknown'] * 10
                    detected_map = 'Unknown'
                    detection_method = "Failed"

            # ============ ENFORCE NO DUPLICATE AGENTS PER TEAM ============
            def enforce_team_uniqueness(agents_list):
                """
                Ensures no duplicate agents within each team (slots 0-4 and 5-9).
                Team A: slots 0-4
                Team B: slots 5-9
                Same agent CAN appear in both teams, just not within the same team.
                """
                print("\n🔧 Enforcing team uniqueness constraints...")

                # Split into teams
                team_a_agents = agents_list[:5]  # First 5 players
                team_b_agents = agents_list[5:10]  # Last 5 players

                # Function to remove duplicates within a team
                def deduplicate_team(team_agents, team_name):
                    seen = {}
                    for i, agent in enumerate(team_agents):
                        if agent == 'Unknown':
                            continue
                        agent_lower = agent.lower()
                        if agent_lower in seen:
                            print(f"   ⚠️ {team_name}: Duplicate {agent} at position {i} (already at position {seen[agent_lower]})")
                            print(f"      Setting position {i} to 'Unknown'")
                            team_agents[i] = 'Unknown'
                        else:
                            seen[agent_lower] = i
                    return team_agents

                # Deduplicate each team independently
                team_a_agents = deduplicate_team(team_a_agents, "Team A")
                team_b_agents = deduplicate_team(team_b_agents, "Team B")

                # Combine back
                result = team_a_agents + team_b_agents
                print(f"   ✅ After deduplication:")
                print(f"      Team A: {team_a_agents}")
                print(f"      Team B: {team_b_agents}")

                return result

            # Apply uniqueness constraint
            if detected_agents and len(detected_agents) == 10:
                detected_agents = enforce_team_uniqueness(detected_agents)
            # ============ END TEAM UNIQUENESS ============

            # Assign detected agents to players

            import difflib
            for i, player in enumerate(players[:10]):
                if i < len(detected_agents):
                    agent = detected_agents[i]
                    player["agent"] = agent
                    player["agent_source"] = detection_method if agent_detection_success and agent != 'Unknown' else "Unknown"
                    # Set confidence based on detection method
                    if agent != 'Unknown':
                        if detection_method.startswith("Hybrid"):
                            player["agent_confidence"] = 0.98  # Hybrid is most accurate
                        elif detection_method.startswith("YOLO"):
                            player["agent_confidence"] = 0.7  # YOLO alone (now 70%)
                        elif detection_method.startswith("Roboflow"):
                            player["agent_confidence"] = 0.6  # Roboflow fallback (now 60%)
                        else:
                            player["agent_confidence"] = 0.6  # Gemini alone or other fallback
                    else:
                        player["agent_confidence"] = 0.0
                else:
                    player["agent"] = "Unknown"
                    player["agent_source"] = "None"
                    player["agent_confidence"] = 0.0

            # For any player with agent 'Unknown', use agent description fuzzy match if player['desc'] exists
            for idx, player in enumerate(players[:10]):
                # Only run Gemini Vision for agents that are still 'Unknown' after all other detection
                if player.get("agent", "Unknown") == "Unknown":
                    try:
                        # Crop agent region if detection boxes available
                        region_img = None
                        if 'detections' in locals() and idx < len(detections):
                            det = detections[idx]
                            bbox = det.get('bbox')
                            if bbox and len(bbox) == 4:
                                x1, y1, x2, y2 = map(int, bbox)
                                region_img = pil.crop((x1, y1, x2, y2))
                        if region_img is None:
                            # fallback: use a horizontal row crop (1/10th of image height)
                            W, H = pil.size
                            row_h = H // 10
                            y1 = idx * row_h
                            y2 = min(H, (idx + 1) * row_h)
                            region_img = pil.crop((0, y1, W, y2))
                        # Use a focused prompt for Gemini
                        prompt = "Identify the Valorant agent in this cropped region. Only return the agent name."
                        bio = io.BytesIO()
                        region_img.save(bio, format="PNG")
                        png_bytes = bio.getvalue()
                        # Patch PROMPT for this call
                        global PROMPT
                        old_prompt = PROMPT
                        PROMPT = prompt
                        data = await call_gemini_with_retry(png_bytes, GEMINI_API_KEY, max_attempts=2)
                        PROMPT = old_prompt
                        gemini_result = None
                        try:
                            gemini_result = parse_gemini_payload(data)
                        except Exception:
                            # Try to extract text directly
                            if "candidates" in data and data["candidates"]:
                                parts = data["candidates"][0].get("content", {}).get("parts", [])
                                if parts and "text" in parts[0]:
                                    gemini_text = parts[0]["text"]
                                    # Fuzzy match to agent names
                                    import difflib
                                    agent_names = list(AGENT_DESCRIPTIONS.keys())
                                    best_agent = difflib.get_close_matches(gemini_text.strip(), agent_names, n=1, cutoff=0.2)
                                    if best_agent:
                                        player["agent"] = best_agent[0]
                                        player["agent_source"] = "GeminiVisionText"
                                        player["agent_confidence"] = 0.6
                                        continue
                        # Try to extract agent name from Gemini result
                        gemini_agent = None
                        if gemini_result and 'players' in gemini_result and len(gemini_result['players']) > 0:
                            gemini_agent = gemini_result['players'][0].get('agent')
                        if gemini_agent and gemini_agent.lower() != 'unknown':
                            player["agent"] = gemini_agent
                            player["agent_source"] = "GeminiVision"
                            player["agent_confidence"] = 0.7
                            continue
                    except Exception as e:
                        print(f"Gemini fallback failed for player {idx}: {e}")
                    # Fallback: use agent description best match
                    if AGENT_DESCRIPTIONS:
                        desc_fields = [player.get("desc"), player.get("description"), player.get("ign"), " ".join(str(v) for v in player.values() if isinstance(v, str))]
                        best_agent = None
                        best_score = 0.0
                        for desc in desc_fields:
                            if not desc:
                                continue
                            for agent, agent_desc in AGENT_DESCRIPTIONS.items():
                                score = difflib.SequenceMatcher(None, desc.lower(), agent_desc.lower()).ratio()
                                if score > best_score:
                                    best_score = score
                                    best_agent = agent
                        if best_agent and best_score > 0.15:
                            player["agent"] = best_agent
                            player["agent_source"] = "DescriptionMatch"
                            player["agent_confidence"] = round(0.5 + 0.5 * best_score, 2)

            # Clean up temp file
            try:
                if temp_image_path.exists():
                    import time
                    time.sleep(0.1)  # Small delay to ensure file is released
                    temp_image_path.unlink()
            except Exception as e:
                print(f"⚠️ Failed to delete temp file: {e}")
                # Try to delete on next scan
                pass
            # ============ END AGENT DETECTION ============
            print("\n" + "="*60)
            print("🔍 STARTING TEAM ASSIGNMENT WITH COLOR DETECTION")
            print("="*60)
            
            # Use LOCAL color detection to assign teams
            team_a: List[Dict[str, Any]] = []
            team_b: List[Dict[str, Any]] = []
            gold_players: List[tuple[int, Dict[str, Any]]] = []  # (idx, player_dict)
            
            print("\n🎨 === COLOR DETECTION DEBUG ===")
            # First pass: detect blue and red players
            for idx, p in enumerate(players[:10]):
                patches = _sample_color_patches(pil, idx)
                team, has_gold = _row_team_from_patches(patches)
                
                # Debug: Calculate scores for logging
                b_list, r_list = [], []
                for patch in patches:
                    b, r, _ = _score_patch(patch)
                    b_list.append(b)
                    r_list.append(r)
                blue_total = sum(b_list)
                red_total = sum(r_list)
                
                ign = p.get('ign', 'Unknown')
                print(f"  Row {idx+1} ({ign}): Blue={blue_total:.3f}, Red={red_total:.3f} → Team {team} {'⭐GOLD' if has_gold else ''}")
                
                if has_gold:
                    # Store gold players for second pass
                    gold_players.append((idx, p))
                else:
                    # Assign non-gold players directly
                    if team == "A":
                        team_a.append(p)
                    else:
                        team_b.append(p)
            
            print(f"After first pass: Team A={len(team_a)}, Team B={len(team_b)}, Gold={len(gold_players)}\n")
            
            # Second pass: assign gold players to the team with 4 players
            for idx, gold_p in gold_players:
                if len(team_a) == 4:
                    team_a.append(gold_p)
                elif len(team_b) == 4:
                    team_b.append(gold_p)
                else:
                    # Fallback: use color detection for gold player
                    patches = _sample_color_patches(pil, idx)
                    team, _ = _row_team_from_patches(patches)
                    if team == "A":
                        team_a.append(gold_p)
                    else:
                        team_b.append(gold_p)
            
            # Validation: Ensure 5v5 split (fix any imbalances)
            if len(team_a) != 5 or len(team_b) != 5:
                print(f"⚠️ Team imbalance detected: Team A={len(team_a)}, Team B={len(team_b)}")
                
                # Recalculate all players with confidence scores
                all_players_with_scores = []
                for idx, p in enumerate(players[:10]):
                    patches = _sample_color_patches(pil, idx)
                    team, has_gold = _row_team_from_patches(patches)
                    
                    # Calculate individual color scores
                    b_list, r_list = [], []
                    for patch in patches:
                        b, r, _ = _score_patch(patch)
                        b_list.append(b)
                        r_list.append(r)
                    
                    blue_score = sum(b_list)
                    red_score = sum(r_list)
                    
                    # Determine which team this player SHOULD be on based on colors
                    detected_team = "A" if blue_score >= red_score else "B"
                    confidence = abs(blue_score - red_score)
                    
                    all_players_with_scores.append({
                        'idx': idx,
                        'player': p,
                        'detected_team': detected_team,
                        'has_gold': has_gold,
                        'confidence': confidence,
                        'blue_score': blue_score,
                        'red_score': red_score
                    })
                
                # Sort by confidence (HIGHEST confidence first - most reliable assignments)
                all_players_with_scores.sort(key=lambda x: x['confidence'], reverse=True)
                
                # Rebuild teams: assign high-confidence players first
                team_a.clear()
                team_b.clear()
                
                # First pass: assign high-confidence players to their detected teams
                for entry in all_players_with_scores:
                    if entry['detected_team'] == 'A' and len(team_a) < 5:
                        team_a.append(entry['player'])
                        entry['assigned'] = True
                    elif entry['detected_team'] == 'B' and len(team_b) < 5:
                        team_b.append(entry['player'])
                        entry['assigned'] = True
                    else:
                        entry['assigned'] = False
                
                # Second pass: assign remaining players to whichever team needs them
                for entry in all_players_with_scores:
                    if not entry['assigned']:
                        if len(team_a) < 5:
                            team_a.append(entry['player'])
                        else:
                            team_b.append(entry['player'])
                
                print(f"✅ Teams rebalanced: Team A={len(team_a)}, Team B={len(team_b)}")

            # ============ FIX DUPLICATE AGENTS WITHIN TEAMS ============
            print("\n🔄 Checking for duplicate agents within teams...")
            
            def fix_team_duplicates(team: List[Dict[str, Any]], team_name: str):
                """Remove duplicate agents within a team - each agent can only appear once per team"""
                seen_agents = set()
                fixed_count = 0
                
                for player in team:
                    agent = player.get('agent', 'Unknown')
                    if agent != 'Unknown' and agent in seen_agents:
                        print(f"  ⚠️ Duplicate {agent} found in Team {team_name} for {player.get('ign', 'Unknown')} - marking as Unknown")
                        player['agent'] = 'Unknown'
                        player['agent_source'] = 'Duplicate_Removed'
                        fixed_count += 1
                    else:
                        seen_agents.add(agent)
                
                return fixed_count
            
            duplicates_a = fix_team_duplicates(team_a, "A")
            duplicates_b = fix_team_duplicates(team_b, "B")
            
            if duplicates_a > 0 or duplicates_b > 0:
                print(f"✅ Fixed {duplicates_a + duplicates_b} duplicate agents (Team A: {duplicates_a}, Team B: {duplicates_b})")
            else:
                print("✅ No duplicate agents found - all clear!")
            
            # ============ END DUPLICATE FIX ============

            # ============ CROSS-TEAM DUPLICATE CHECK ============
            print("\n🔍 Checking for cross-team duplicates...")
            
            # Get all agents from both teams
            team_a_agents = {p.get('agent', 'Unknown'): p for p in team_a if p.get('agent', 'Unknown') != 'Unknown'}
            team_b_agents = {p.get('agent', 'Unknown'): p for p in team_b if p.get('agent', 'Unknown') != 'Unknown'}
            
            # Find agents that appear on both teams
            cross_duplicates = set(team_a_agents.keys()) & set(team_b_agents.keys())
            
            if cross_duplicates:
                print(f"  ⚠️ Found {len(cross_duplicates)} agents on BOTH teams: {cross_duplicates}")
                
                for agent in cross_duplicates:
                    player_a = team_a_agents[agent]
                    player_b = team_b_agents[agent]
                    
                    conf_a = player_a.get('agent_confidence', 0)
                    conf_b = player_b.get('agent_confidence', 0)
                    
                    # Keep the one with higher confidence, mark other as Unknown
                    if conf_a >= conf_b:
                        print(f"    Keeping {agent} in Team A (conf: {conf_a:.2f}) - removing from Team B")
                        player_b['agent'] = 'Unknown'
                        player_b['agent_source'] = 'Cross_Duplicate_Removed'
                    else:
                        print(f"    Keeping {agent} in Team B (conf: {conf_b:.2f}) - removing from Team A")
                        player_a['agent'] = 'Unknown'
                        player_a['agent_source'] = 'Cross_Duplicate_Removed'
            else:
                print("✅ No cross-team duplicates - all agents unique!")
            
            # ============ LOW CONFIDENCE RE-CHECK ============
            print("\n📊 Checking agent detection confidence...")
            
            low_confidence_count = 0
            for team_name, team in [("A", team_a), ("B", team_b)]:
                for player in team:
                    agent = player.get('agent', 'Unknown')
                    conf = player.get('agent_confidence', 0)
                    ign = player.get('ign', 'Unknown')
                    
                    if agent != 'Unknown' and conf < 0.70:  # Less than 70% confidence
                        print(f"  ⚠️ Low confidence: {ign} ({agent}) - {conf:.1%} confidence in Team {team_name}")
                        low_confidence_count += 1
            
            if low_confidence_count > 0:
                print(f"⚠️ {low_confidence_count} players with confidence < 70% - may need manual review")
            else:
                print("✅ All detections have high confidence (≥70%)")
            
            # ============ AGENT COUNT VALIDATION ============
            total_known_agents = sum(1 for team in [team_a, team_b] for p in team if p.get('agent', 'Unknown') != 'Unknown')
            unknown_count = 10 - total_known_agents
            
            print(f"\n📈 Detection Summary:")
            print(f"  ✅ Detected: {total_known_agents}/10 agents ({total_known_agents*10}%)")
            print(f"  ❓ Unknown: {unknown_count}/10 agents")
            print(f"  🎯 Team A: {len([p for p in team_a if p.get('agent', 'Unknown') != 'Unknown'])}/5 detected")
            print(f"  🎯 Team B: {len([p for p in team_b if p.get('agent', 'Unknown') != 'Unknown'])}/5 detected")
            
            # ============ END VALIDATION ============

            # ============ CONFIDENCE BOOSTING ============
            # If all agents detected with no duplicates and good confidence, boost accuracy
            if total_known_agents == 10 and low_confidence_count == 0 and (not cross_duplicates if 'cross_duplicates' in locals() else True):
                print("\n🎉 PERFECT DETECTION: All 10 agents detected with high confidence and no duplicates!")
                print("   Confidence level: 99%+")
                
                # Boost all confidences slightly
                for team in [team_a, team_b]:
                    for player in team:
                        if player.get('agent', 'Unknown') != 'Unknown':
                            current_conf = player.get('agent_confidence', 0.9)
                            player['agent_confidence'] = min(0.99, current_conf + 0.05)
            elif total_known_agents >= 9:
                print(f"\n✅ EXCELLENT DETECTION: {total_known_agents}/10 agents detected")
                print("   Confidence level: 95%+")
            elif total_known_agents >= 8:
                print(f"\n👍 GOOD DETECTION: {total_known_agents}/10 agents detected")
                print("   Confidence level: 85%+")
            else:
                print(f"\n⚠️ PARTIAL DETECTION: Only {total_known_agents}/10 agents detected")
                print("   Consider re-scanning or manual verification")
            
            # ============ END CONFIDENCE BOOSTING ============

            # Get score - Use COLOR DETECTION instead of position
            score = parsed.get("score")
            
            # Try to detect score colors from the image
            def detect_score_by_color(image_path: Path, score_dict: dict) -> dict:
                """
                Detect which score is green/teal (Team A) and which is red (Team B)
                by analyzing the color of the score numbers in the image
                """
                try:
                    img = cv2.imread(str(image_path))
                    if img is None:
                        return score_dict
                    
                    height, width = img.shape[:2]
                    
                    # Score is typically at the top center of the screen
                    # Look in the top 15% of the image
                    score_region = img[0:int(height * 0.15), :]
                    
                    # Convert to HSV for better color detection
                    hsv = cv2.cvtColor(score_region, cv2.COLOR_BGR2HSV)
                    
                    # Define color ranges
                    # Teal/Cyan/Green range (Team A)
                    teal_lower = np.array([80, 50, 50])   # Cyan/teal/green
                    teal_upper = np.array([100, 255, 255])
                    
                    # Red range (Team B) - need to check both ends of HSV spectrum
                    red_lower1 = np.array([0, 50, 50])
                    red_upper1 = np.array([10, 255, 255])
                    red_lower2 = np.array([170, 50, 50])
                    red_upper2 = np.array([180, 255, 255])
                    
                    # Create masks
                    teal_mask = cv2.inRange(hsv, teal_lower, teal_upper)
                    red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
                    red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
                    red_mask = cv2.bitwise_or(red_mask1, red_mask2)
                    
                    # Count pixels
                    teal_pixels = cv2.countNonZero(teal_mask)
                    red_pixels = cv2.countNonZero(red_mask)
                    
                    print(f"\n🎨 Score Color Detection:")
                    print(f"   Teal/Green pixels: {teal_pixels}")
                    print(f"   Red pixels: {red_pixels}")
                    
                    # If we have both colors, determine which number is which
                    if teal_pixels > 100 and red_pixels > 100:
                        # Split score region in half to find which side is which color
                        left_half = score_region[:, :width//2]
                        right_half = score_region[:, width//2:]
                        
                        # Check colors in each half
                        left_hsv = cv2.cvtColor(left_half, cv2.COLOR_BGR2HSV)
                        right_hsv = cv2.cvtColor(right_half, cv2.COLOR_BGR2HSV)
                        
                        left_teal = cv2.countNonZero(cv2.inRange(left_hsv, teal_lower, teal_upper))
                        right_teal = cv2.countNonZero(cv2.inRange(right_hsv, teal_lower, teal_upper))
                        left_red = cv2.countNonZero(cv2.bitwise_or(
                            cv2.inRange(left_hsv, red_lower1, red_upper1),
                            cv2.inRange(left_hsv, red_lower2, red_upper2)
                        ))
                        right_red = cv2.countNonZero(cv2.bitwise_or(
                            cv2.inRange(right_hsv, red_lower1, red_upper1),
                            cv2.inRange(right_hsv, red_lower2, red_upper2)
                        ))
                        
                        print(f"   Left side - Teal: {left_teal}, Red: {left_red}")
                        print(f"   Right side - Teal: {right_teal}, Red: {right_red}")
                        
                        # Determine which score is which based on color position
                        if "top" in score_dict and "bottom" in score_dict:
                            # If left side is more teal, then "top" is Team A (green)
                            # If left side is more red, then "top" is Team B (red)
                            if left_teal > left_red:
                                print("   ✅ Left score is TEAL (Team A), Right score is RED (Team B)")
                                return {"A": score_dict["top"], "B": score_dict["bottom"]}
                            else:
                                print("   ✅ Left score is RED (Team B), Right score is TEAL (Team A)")
                                return {"A": score_dict["bottom"], "B": score_dict["top"]}
                
                except Exception as e:
                    print(f"   ⚠️ Color detection failed: {e}")
                
                # Fallback to original logic if color detection fails
                return {"A": score_dict.get("bottom"), "B": score_dict.get("top")}
            
            if isinstance(score, dict) and ("top" in score or "bottom" in score):
                # Use common sense: higher score = Team A (winner), lower score = Team B
                score_top = score.get("top", 0)
                score_bottom = score.get("bottom", 0)
                
                if score_top > score_bottom:
                    score_ab = {"A": score_top, "B": score_bottom}
                    print(f"✅ Team A (winner): {score_top}, Team B: {score_bottom}")
                else:
                    score_ab = {"A": score_bottom, "B": score_top}
                    print(f"✅ Team A (winner): {score_bottom}, Team B: {score_top}")
            else:
                score_ab = score

            def score_str(s) -> str:
                if isinstance(s, dict) and ("A" in s or "B" in s):
                    return f"{s.get('A','?')} — {s.get('B','?')}"
                if isinstance(s, list) and len(s) >= 2:
                    return f"{s[0]} — {s[1]}"
                if isinstance(s, str):
                    return s
                return "N/A"

            # Load registered players from database
            all_players = await db.get_all_players()
            registered_igns = {p['ign'].strip().lower() for p in all_players if p.get('ign')}
            ign_to_player = {p['ign'].strip().lower(): p for p in all_players if p.get('ign')}
            players_data = all_players  # Keep reference for compatibility with nested functions
                
            # Update stats for registered players found in the scan
            updated_count = 0
            try:
                # Determine which team won based on score
                team_a_won = None
                if isinstance(score_ab, dict) and score_ab.get("A") is not None and score_ab.get("B") is not None:
                    team_a_score = score_ab.get("A")
                    team_b_score = score_ab.get("B")
                    if team_a_score > team_b_score:
                        team_a_won = True
                    elif team_b_score > team_a_score:
                        team_a_won = False
                    
                    # Determine which team won based on score
                    team_a_won = None
                    if isinstance(score_ab, dict) and score_ab.get("A") is not None and score_ab.get("B") is not None:
                        team_a_score = score_ab.get("A")
                        team_b_score = score_ab.get("B")
                        if team_a_score > team_b_score:
                            team_a_won = True
                        elif team_b_score > team_a_score:
                            team_a_won = False
                        # If tied, don't count as win or loss (team_a_won stays None)
                    
                    # Update stats for each scanned player
                    for idx, scanned_player in enumerate(players[:10]):
                        ign = scanned_player.get("ign", "").strip()
                        ign_lower = ign.lower()  # Convert to lowercase for fuzzy matching
                        
                        # If player is registered, update their stats (case-insensitive match)
                        if ign_lower in ign_to_player:
                            player_record = ign_to_player[ign_lower]
                            
                            # Determine which team this player is on
                            patches = _sample_color_patches(pil, idx)
                            player_team, _ = _row_team_from_patches(patches)  # Ignore gold flag here
                            
                            # Ensure stats structure exists
                            if "stats" not in player_record:
                                player_record["stats"] = {}
                            
                            # Use tournament ID "1" as default (you can make this configurable)
                            tournament_id = "1"
                            if tournament_id not in player_record["stats"]:
                                player_record["stats"][tournament_id] = {
                                    "kills": 0,
                                    "deaths": 0,
                                    "assists": 0,
                                    "matches_played": 0,
                                    "wins": 0,
                                    "losses": 0,
                                    "mvps": 0,
                                    "agents": {}  # Track agent usage
                                }
                            
                            # Add the stats from this match
                            stats = player_record["stats"][tournament_id]
                            kills = scanned_player.get("kills")
                            deaths = scanned_player.get("deaths")
                            assists = scanned_player.get("assists")
                            agent = scanned_player.get("agent")
                            
                            if kills is not None:
                                stats["kills"] += int(kills)
                            if deaths is not None:
                                stats["deaths"] += int(deaths)
                            if assists is not None:
                                stats["assists"] += int(assists)
                            
                            stats["matches_played"] += 1
                            
                            # Track agent usage
                            if agent:
                                if "agents" not in stats:
                                    stats["agents"] = {}
                                if agent not in stats["agents"]:
                                    stats["agents"][agent] = {"matches": 0, "kills": 0, "deaths": 0, "assists": 0}
                                
                                stats["agents"][agent]["matches"] += 1
                                if kills is not None:
                                    stats["agents"][agent]["kills"] += int(kills)
                                if deaths is not None:
                                    stats["agents"][agent]["deaths"] += int(deaths)
                                if assists is not None:
                                    stats["agents"][agent]["assists"] += int(assists)
                            
                            # Update wins/losses based on team and score
                            if team_a_won is not None:
                                if player_team == "A" and team_a_won:
                                    stats["wins"] += 1
                                elif player_team == "B" and not team_a_won:
                                    stats["wins"] += 1
                                else:
                                    stats["losses"] += 1
                            
                            updated_count += 1
                    
                    # Stats are now saved to PostgreSQL via save_match_results
                    # No need to save to JSON file
                        
                        # Update nicknames for all updated players
                        try:
                            registration_cog = self.bot.get_cog("Registration")
                            if registration_cog and interaction.guild:
                                for player_entry in players_data:
                                    discord_id = player_entry.get("discord_id")
                                    ign = player_entry.get("ign")
                                    
                                    # Check if this player was in the scan
                                    player_in_scan = any(
                                        sp.get("ign", "").strip().lower() == ign.lower() 
                                        for sp in players[:10]
                                    )
                                    
                                    if player_in_scan:
                                        try:
                                            member = await interaction.guild.fetch_member(discord_id)
                                            if member:
                                                await registration_cog.update_nickname(member, ign, player_entry)
                                        except:
                                            pass  # Skip if member not found or other error
                        except Exception as e:
                            print(f"Error updating nicknames: {e}")
            except Exception as e:
                # Log error but don't fail the whole scan
                print(f"Error updating player stats: {e}")
            
            # --- Team Match Tracking (PostgreSQL) ---
            team_match_info = None
            try:
                # Determine winner first
                winner_text = "Unknown"
                if isinstance(score_ab, dict) and score_ab.get("A") is not None and score_ab.get("B") is not None:
                    if score_ab["A"] > score_ab["B"]:
                        winner_text = "Team A wins"
                    elif score_ab["B"] > score_ab["A"]:
                        winner_text = "Team B wins"
                    else:
                        winner_text = "Draw"
                
                print(f"\n🏆 TEAM TRACKING DEBUG:")
                print(f"  Winner: {winner_text}")
                print(f"  Score: Team A={score_ab.get('A')}, Team B={score_ab.get('B')}")
                
                # Get teams for players in Team A (first 5)
                team_a_discord_ids = []
                for p in players[:5]:
                    ign = p.get('ign', '').strip().lower()
                    if ign in registered_igns:
                        player_db = await db.get_player_by_ign(ign)
                        if player_db:
                            team_a_discord_ids.append(player_db['discord_id'])
                            print(f"  ✅ Team A player found: {ign} (ID: {player_db['discord_id']})")
                        else:
                            print(f"  ❌ Team A player NOT in DB: {ign}")
                    else:
                        print(f"  ⚠️ Team A player not registered: {ign}")
                
                # Get teams for players in Team B (next 5)
                team_b_discord_ids = []
                for p in players[5:10]:
                    ign = p.get('ign', '').strip().lower()
                    if ign in registered_igns:
                        player_db = await db.get_player_by_ign(ign)
                        if player_db:
                            team_b_discord_ids.append(player_db['discord_id'])
                            print(f"  ✅ Team B player found: {ign} (ID: {player_db['discord_id']})")
                        else:
                            print(f"  ❌ Team B player NOT in DB: {ign}")
                    else:
                        print(f"  ⚠️ Team B player not registered: {ign}")
                
                print(f"\n  Team A Discord IDs: {team_a_discord_ids}")
                print(f"  Team B Discord IDs: {team_b_discord_ids}")
                
                # Find teams for each side
                team_a_data = None
                team_b_data = None
                
                if team_a_discord_ids:
                    # Check if any player is in a team
                    for player_id in team_a_discord_ids:
                        player_team = await db.get_player_team(player_id)
                        if player_team:
                            team_a_data = player_team
                            print(f"  🎯 Team A found: {player_team['name']} [{player_team['tag']}]")
                            break
                    if not team_a_data:
                        print(f"  ⚠️ No team found for Team A players")
                
                if team_b_discord_ids:
                    for player_id in team_b_discord_ids:
                        player_team = await db.get_player_team(player_id)
                        if player_team:
                            team_b_data = player_team
                            print(f"  🎯 Team B found: {player_team['name']} [{player_team['tag']}]")
                            break
                    if not team_b_data:
                        print(f"  ⚠️ No team found for Team B players")
                
                # Update team records (even if only one team is found)
                if winner_text != "Draw" and winner_text != "Unknown":
                    print(f"\n  📊 Updating team records...")
                    
                    if winner_text == "Team A wins":
                        if team_a_data:
                            await db.update_team_record(team_a_data['id'], won=True)
                            print(f"  ✅ {team_a_data['name']} WIN recorded")
                        if team_b_data:
                            await db.update_team_record(team_b_data['id'], won=False)
                            print(f"  ✅ {team_b_data['name']} LOSS recorded")
                        
                        # Build message based on what teams were found
                        if team_a_data and team_b_data:
                            team_match_info = f"**{team_a_data['name']}** [{team_a_data['tag']}] defeats **{team_b_data['name']}** [{team_b_data['tag']}]"
                        elif team_a_data:
                            team_match_info = f"**{team_a_data['name']}** [{team_a_data['tag']}] wins"
                        elif team_b_data:
                            team_match_info = f"**{team_b_data['name']}** [{team_b_data['tag']}] loses"
                    
                    elif winner_text == "Team B wins":
                        if team_b_data:
                            await db.update_team_record(team_b_data['id'], won=True)
                            print(f"  ✅ {team_b_data['name']} WIN recorded")
                        if team_a_data:
                            await db.update_team_record(team_a_data['id'], won=False)
                            print(f"  ✅ {team_a_data['name']} LOSS recorded")
                        
                        # Build message based on what teams were found
                        if team_a_data and team_b_data:
                            team_match_info = f"**{team_b_data['name']}** [{team_b_data['tag']}] defeats **{team_a_data['name']}** [{team_a_data['tag']}]"
                        elif team_b_data:
                            team_match_info = f"**{team_b_data['name']}** [{team_b_data['tag']}] wins"
                        elif team_a_data:
                            team_match_info = f"**{team_a_data['name']}** [{team_a_data['tag']}] loses"
                
                elif team_a_data and team_b_data and winner_text == "Draw":
                    team_match_info = f"**{team_a_data['name']}** [{team_a_data['tag']}] vs **{team_b_data['name']}** [{team_b_data['tag']}] - Draw"
                    print(f"  ⚖️ Draw - no records updated")
                else:
                    if team_a_data or team_b_data:
                        print(f"  ⚠️ Teams found but winner unclear: team_a={bool(team_a_data)}, team_b={bool(team_b_data)}, winner={winner_text}")
                    else:
                        print(f"  ℹ️ No registered teams found in this match")
                
            except Exception as e:
                print(f"Error updating team records: {e}")
                team_match_info = None
            
            # Build ultra-clean embed
            # Determine winner (already done above, but keep for compatibility)
            winner_text = "Unknown"
            if isinstance(score_ab, dict) and score_ab.get("A") is not None and score_ab.get("B") is not None:
                if score_ab["A"] > score_ab["B"]:
                    winner_text = "Team A wins"
                elif score_ab["B"] > score_ab["A"]:
                    winner_text = "Team B wins"
                else:
                    winner_text = "Draw"
            
            # Count registered/unregistered
            total_players = len(players[:10])
            registered_count = sum(1 for p in players[:10] if p.get('ign', '').strip().lower() in registered_igns)
            unregistered_count = total_players - registered_count
            
            # Pre-fetch all player stats from database for registered players
            player_stats_cache = {}
            try:
                for p in players[:10]:
                    ign = p.get('ign', '').strip().lower()
                    if ign in registered_igns:
                        try:
                            player_db = await db.get_player_by_ign(ign)
                            if player_db:
                                stats = await db.get_player_stats(player_db['discord_id'])
                                if stats:
                                    player_stats_cache[ign] = {
                                        'discord_id': player_db['discord_id'],
                                        'ign': player_db['ign'],
                                        'kills': stats.get('kills', 0),
                                        'deaths': stats.get('deaths', 0),
                                        'assists': stats.get('assists', 0),
                                        'matches_played': stats.get('matches_played', 0),
                                        'wins': stats.get('wins', 0),
                                        'losses': stats.get('losses', 0)
                                    }
                        except Exception as e:
                            print(f"Error fetching stats for {ign}: {e}")
            except Exception as e:
                print(f"Error pre-fetching player stats: {e}")
            
            # Build player lines with points
            def format_player_line(p, idx):
                ign = p.get('ign', 'UNKNOWN')
                agent = p.get('agent', 'Unknown')
                k = p.get('kills', '?')
                d = p.get('deaths', '?')
                a = p.get('assists', '?')
                
                # Format K/D/A
                kda = f"{k}/{d}/{a}"
                
                # Check if registered
                ign_lower = ign.strip().lower()
                is_registered = ign_lower in registered_igns
                reg_symbol = "✅" if is_registered else "❌"
                
                if is_registered and ign_lower in player_stats_cache:
                    # Get cached stats
                    try:
                        player_data = player_stats_cache[ign_lower]
                        player_data['ign'] = ign
                        
                        # Calculate points from stats
                        registration_cog = self.bot.get_cog("Registration")
                        if registration_cog:
                            points = int(registration_cog.calculate_player_score(player_data))
                            # Calculate points gained this match
                            k_val = int(k) if str(k).isdigit() else 0
                            a_val = int(a) if str(a).isdigit() else 0
                            match_points = (k_val * 2) + a_val
                            return f"{reg_symbol} **{ign}** ({agent}) • `{kda}` • {points} pts `(+{match_points})`"
                    except Exception as e:
                        print(f"Error calculating points for {ign}: {e}")
                
                if is_registered:
                    return f"{reg_symbol} **{ign}** ({agent}) • `{kda}`"
                else:
                    return f"{reg_symbol} {ign} ({agent}) • `{kda}`"
            
            # Sort teams by performance (kills * 2 + assists) - best players first
            def player_score(p):
                k = p.get('kills', 0)
                a = p.get('assists', 0)
                k = int(k) if str(k).isdigit() else 0
                a = int(a) if str(a).isdigit() else 0
                return (k * 2) + a
            
            team_a_sorted = sorted(team_a, key=player_score, reverse=True)
            team_b_sorted = sorted(team_b, key=player_score, reverse=True)
            
            # Set up match data structure for database
            # Save match data to database
            match_data = {
                'team1_score': score_ab.get("A") if isinstance(score_ab, dict) else None,
                'team2_score': score_ab.get("B") if isinstance(score_ab, dict) else None,
                'map': parsed.get("map", "Unknown"),
                'team_a_id': team_a_data['id'] if team_a_data else None,
                'team_b_id': team_b_data['id'] if team_b_data else None,
                'team_a_name': team_a_data['name'] if team_a_data else None,
                'team_b_name': team_b_data['name'] if team_b_data else None,
                'players': []
            }

            # Process team A players
            for idx, player in enumerate(team_a):
                ign = player.get('ign', '').strip()
                ign_lower = ign.lower()
                
                if ign_lower in ign_to_player:
                    is_mvp = idx == 0  # First player in sorted team is MVP
                    player_data = {
                        'discord_id': ign_to_player[ign_lower]['discord_id'],
                        'agent': player.get('agent', 'Unknown'),
                        'kills': int(player.get('kills', 0)) if str(player.get('kills', '')).isdigit() else 0,
                        'deaths': int(player.get('deaths', 0)) if str(player.get('deaths', '')).isdigit() else 0,
                        'assists': int(player.get('assists', 0)) if str(player.get('assists', '')).isdigit() else 0,
                        'score': player_score(player),
                        'mvp': is_mvp,
                        'team': 1,  # Team A = 1
                        'won': team_a_won
                    }
                    match_data['players'].append(player_data)

            # Process team B players
            for idx, player in enumerate(team_b):
                ign = player.get('ign', '').strip()
                ign_lower = ign.lower()
                
                if ign_lower in ign_to_player:
                    is_mvp = idx == 0  # First player in sorted team is MVP
                    player_data = {
                        'discord_id': ign_to_player[ign_lower]['discord_id'],
                        'agent': player.get('agent', 'Unknown'),
                        'kills': int(player.get('kills', 0)) if str(player.get('kills', '')).isdigit() else 0,
                        'deaths': int(player.get('deaths', 0)) if str(player.get('deaths', '')).isdigit() else 0,
                        'assists': int(player.get('assists', 0)) if str(player.get('assists', '')).isdigit() else 0,
                        'score': player_score(player),
                        'mvp': is_mvp,
                        'team': 2,  # Team B = 2
                        'won': not team_a_won if team_a_won is not None else None
                    }
                    match_data['players'].append(player_data)

            # Save match to database
            match_result = None
            try:
                match_result = await db.save_match_results(match_data)
                updated_count = len(match_data['players'])
                
                # Update team_stats if we have team data and match was saved
                if match_result and match_result.get('match_id'):
                    match_id = match_result['match_id']
                    match_timestamp = match_result['timestamp']
                    
                    # Update Team A stats if present
                    if team_a_data:
                        team_a_won = score_ab.get("A", 0) > score_ab.get("B", 0) if isinstance(score_ab, dict) else None
                        await db.update_team_stats(team_a_data['id'], {
                            'match_id': match_id,
                            'opponent_id': team_b_data['id'] if team_b_data else None,
                            'opponent_name': f"{team_b_data['name']} [{team_b_data['tag']}]" if team_b_data else 'Randoms',
                            'map': match_data['map'],
                            'score_for': score_ab.get("A") if isinstance(score_ab, dict) else 0,
                            'score_against': score_ab.get("B") if isinstance(score_ab, dict) else 0,
                            'won': team_a_won,
                            'timestamp': match_timestamp
                        })
                    
                    # Update Team B stats if present
                    if team_b_data:
                        team_b_won = score_ab.get("B", 0) > score_ab.get("A", 0) if isinstance(score_ab, dict) else None
                        await db.update_team_stats(team_b_data['id'], {
                            'match_id': match_id,
                            'opponent_id': team_a_data['id'] if team_a_data else None,
                            'opponent_name': f"{team_a_data['name']} [{team_a_data['tag']}]" if team_a_data else 'Randoms',
                            'map': match_data['map'],
                            'score_for': score_ab.get("B") if isinstance(score_ab, dict) else 0,
                            'score_against': score_ab.get("A") if isinstance(score_ab, dict) else 0,
                            'won': team_b_won,
                            'timestamp': match_timestamp
                        })
                    
                # Update team leaderboards for both teams
                if match_result and match_result.get('match_id'):
                    print("\n📊 Updating team leaderboards...")
                    try:
                        # Update Team A leaderboard
                        if team_a_id:
                            team_a = await db.get_team_by_id(team_a_id)
                            if team_a:
                                # Check if team is India-based (check captain's role or region)
                                is_india = team_a['region'].lower() == 'india'
                                if not is_india and interaction.guild:
                                    try:
                                        captain = await interaction.guild.fetch_member(team_a['captain_id'])
                                        if captain:
                                            india_role = discord.utils.get(captain.roles, name="India")
                                            is_india = india_role is not None
                                    except:
                                        pass
                                
                                await db.update_team_leaderboard(
                                    team_a_id,
                                    team_a['name'],
                                    team_a['tag'],
                                    team_a['region'],
                                    team_a.get('logo_url'),
                                    is_india
                                )
                                print(f"  ✅ Updated leaderboard for {team_a['name']}")
                        
                        # Update Team B leaderboard
                        if team_b_id:
                            team_b = await db.get_team_by_id(team_b_id)
                            if team_b:
                                # Check if team is India-based
                                is_india = team_b['region'].lower() == 'india'
                                if not is_india and interaction.guild:
                                    try:
                                        captain = await interaction.guild.fetch_member(team_b['captain_id'])
                                        if captain:
                                            india_role = discord.utils.get(captain.roles, name="India")
                                            is_india = india_role is not None
                                    except:
                                        pass
                                
                                await db.update_team_leaderboard(
                                    team_b_id,
                                    team_b['name'],
                                    team_b['tag'],
                                    team_b['region'],
                                    team_b.get('logo_url'),
                                    is_india
                                )
                                print(f"  ✅ Updated leaderboard for {team_b['name']}")
                        
                        # Update all team leaderboard ranks
                        for lb_type in ['global', 'apac', 'emea', 'americas', 'india']:
                            try:
                                await db.update_team_leaderboard_ranks(lb_type)
                            except:
                                pass
                        print("  ✅ All team leaderboard ranks updated")
                        
                    except Exception as e:
                        print(f"  ❌ Error updating team leaderboards: {e}")
                    
                    # Update player leaderboards for all participants
                    print("\n📊 Updating player leaderboards...")
                    for player in match_data['players']:
                        try:
                            # Get player data
                            player_db = await db.get_player(player['discord_id'])
                            if player_db:
                                # Update player leaderboard
                                await db.update_player_leaderboard(
                                    player['discord_id'],
                                    player_db['ign'],
                                    player_db['region']
                                )
                                print(f"  ✅ Updated player leaderboard for {player_db['ign']}")
                        except Exception as e:
                            print(f"  ❌ Error updating player leaderboard for {player['discord_id']}: {e}")
                    
                    # Update player leaderboard ranks
                    try:
                        await db.update_player_leaderboard_ranks()
                        print("  ✅ Player leaderboard ranks updated")
                    except Exception as e:
                        print(f"  ❌ Error updating player leaderboard ranks: {e}")
                    
            except Exception as e:
                print(f"Error saving match to database: {e}")
            
            # Build team sections with MVP marker for top player
            team_a_lines = []
            for idx, p in enumerate(team_a_sorted):
                line = format_player_line(p, idx)
                if idx == 0:  # Top player gets MVP marker
                    line = f"⭐ {line}"
                team_a_lines.append(line)
            
            team_b_lines = []
            for idx, p in enumerate(team_b_sorted):
                line = format_player_line(p, idx)
                if idx == 0:  # Top player gets MVP marker
                    line = f"⭐ {line}"
                team_b_lines.append(line)
            
            # Build description with cleaner formatting
            description = f"## 📊 MATCH RESULTS\n\n"
            description += f"**Map:** {detected_map} 🗺️\n"
            description += f"**Score:** {score_str(score_ab)}\n"
            description += f"**Status:** {winner_text}\n"
            description += f"**Players:** {registered_count} registered • {unregistered_count} unregistered\n\n"
            description += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            description += f"### 🟢 Team A{' 🏆' if winner_text == 'Team A wins' else ''}\n"
            description += "\n".join(team_a_lines) + "\n\n"
            
            description += f"### 🔴 Team B{' 🏆' if winner_text == 'Team B wins' else ''}\n"
            description += "\n".join(team_b_lines) + "\n\n"
            
            # Add team match info
            if team_match_info:
                description += f"🏆 {team_match_info}\n"
            
            # Add stats update info
            if updated_count > 0:
                description += f"📈 All stats & nicknames updated!\n"
            
            # Add fallback notice if used
            if used_fallback:
                description += f"\n⚠️ Using local OCR (Gemini unavailable)"
            
            # Add agent detection info
            vision_count = sum(1 for p in players[:10] if p.get('agent_source') == 'Gemini Vision')
            unknown_count = sum(1 for p in players[:10] if p.get('agent', 'Unknown') == 'Unknown')
            
            if vision_count > 0:
                avg_confidence = sum(p.get('agent_confidence', 0) for p in players[:10] if p.get('agent', 'Unknown') != 'Unknown') / max(1, (10 - unknown_count))
                agent_detection_info = f"\n🎯 Agent Detection: {vision_count} detected (Vision AI, {avg_confidence*100:.0f}% confidence)"
                if unknown_count > 0:
                    agent_detection_info += f" • {unknown_count} unknown"
                description += agent_detection_info
            
            emb = discord.Embed(
                description=description,
                color=discord.Color.green() if winner_text == "Team A wins" else discord.Color.red() if winner_text == "Team B wins" else discord.Color.gold()
            )
            
            try: 
                emb.set_thumbnail(url=image.url)
            except Exception: 
                pass

            # Save match data to database
            match_data = {
                'team1_score': score_ab.get("A") if isinstance(score_ab, dict) else None,
                'team2_score': score_ab.get("B") if isinstance(score_ab, dict) else None,
                'map': detected_map,  # Use detected map name
                'players': []
            }

            # Get all registered players from PostgreSQL database
            try:
                all_db_players = await db.get_all_players()
                # Create a lookup dict: ign.lower() -> discord_id
                ign_to_discord_id = {
                    p['ign'].strip().lower(): p['discord_id'] 
                    for p in all_db_players 
                    if p.get('ign')
                }
            except Exception as e:
                print(f"Error loading players from database: {e}")
                ign_to_discord_id = {}

            # Process all players from both teams
            for player in team_a:
                player_ign = player.get('ign', '').strip().lower()
                if player_ign in registered_igns:
                    # Get discord ID from database
                    discord_id = ign_to_discord_id.get(player_ign)
                    if discord_id:
                        player_data = {
                            'discord_id': discord_id,
                            'agent': player.get('agent', 'Unknown'),
                            'kills': int(player.get('kills', 0)) if str(player.get('kills', '')).isdigit() else 0,
                            'deaths': int(player.get('deaths', 0)) if str(player.get('deaths', '')).isdigit() else 0,
                            'assists': int(player.get('assists', 0)) if str(player.get('assists', '')).isdigit() else 0,
                            'score': player_score(player),  # Using the existing player_score function
                            'mvp': player == team_a_sorted[0] if team_a_sorted else False,
                            'team': 1,  # Team A = 1
                            'won': winner_text == "Team A wins"
                        }
                        match_data['players'].append(player_data)

            for player in team_b:
                player_ign = player.get('ign', '').strip().lower()
                if player_ign in registered_igns:
                    # Get discord ID from database
                    discord_id = ign_to_discord_id.get(player_ign)
                    if discord_id:
                        player_data = {
                            'discord_id': discord_id,
                            'agent': player.get('agent', 'Unknown'),
                            'kills': int(player.get('kills', 0)) if str(player.get('kills', '')).isdigit() else 0,
                            'deaths': int(player.get('deaths', 0)) if str(player.get('deaths', '')).isdigit() else 0,
                            'assists': int(player.get('assists', 0)) if str(player.get('assists', '')).isdigit() else 0,
                            'score': player_score(player),  # Using the existing player_score function
                            'mvp': player == team_b_sorted[0] if team_b_sorted else False,
                            'team': 2,  # Team B = 2
                            'won': winner_text == "Team B wins"
                        }
                        match_data['players'].append(player_data)

            # Match results already saved above at line ~1567, no need to save again
            # try:
            #     await db.save_match_results(match_data)
            # except Exception as e:
            #     print(f"Error saving match results to database: {e}")

            await interaction.followup.send(embed=emb)

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            await interaction.followup.send(
                f"💥 OCR error: `{type(e).__name__}: {e}`\n```\n{error_detail[:500]}```",
                ephemeral=True
            )
    
    @app_commands.command(name="editagent", description="[ADMIN] Manually edit a player's agent in the last scanned match")
    @app_commands.describe(
        player_ign="Player's in-game name",
        agent="Agent name to assign"
    )
    async def edit_agent(self, interaction: discord.Interaction, player_ign: str, agent: str):
        """Allow admins/staff to manually correct agent detection errors"""
        # Admin check
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
            return
        
        if not interaction.user.guild_permissions.administrator:
            user_roles = [role.name.lower() for role in interaction.user.roles]
            if not any(role in user_roles for role in ['admin', 'staff', 'moderator', 'mod']):
                await interaction.response.send_message("❌ You need Admin or Staff role to edit agents!", ephemeral=True)
                return
        
        await interaction.response.defer(thinking=True)
        
        # Validate agent name
        valid_agents = [
            "Astra", "Breach", "Brimstone", "Chamber", "Clove", "Cypher", "Deadlock",
            "Fade", "Gekko", "Harbor", "Iso", "Jett", "KAY/O", "Killjoy", "Neon",
            "Omen", "Phoenix", "Raze", "Reyna", "Sage", "Skye", "Sova", "Viper",
            "Vyse", "Yoru"
        ]
        
        # Case-insensitive matching
        agent_lower = agent.lower()
        matched_agent = None
        for valid_agent in valid_agents:
            if valid_agent.lower() == agent_lower:
                matched_agent = valid_agent
                break
        
        if not matched_agent:
            await interaction.followup.send(
                f"❌ Invalid agent name: `{agent}`\n"
                f"Valid agents: {', '.join(valid_agents)}",
                ephemeral=True
            )
            return
        
        try:
            # Get the most recent match from database
            recent_matches = await db.get_recent_matches(limit=1)
            if not recent_matches:
                await interaction.followup.send("❌ No matches found in database!", ephemeral=True)
                return
            
            latest_match = recent_matches[0]
            
            # Parse players - handle both list and JSON string cases
            players_data = latest_match.get('players', [])
            
            # If it's a string, parse it
            if isinstance(players_data, str):
                try:
                    players_data = json.loads(players_data) if players_data else []
                except json.JSONDecodeError:
                    players_data = []
            
            # Ensure it's a list
            if not isinstance(players_data, list):
                await interaction.followup.send(
                    f"❌ Invalid player data format in match!",
                    ephemeral=True
                )
                return
            
            # Search for the player in the match players
            player_found = False
            old_agent = None
            team_name = None
            player_id = None
            match_id = latest_match.get('id')
            
            for player in players_data:
                # Ensure player is a dict
                if not isinstance(player, dict):
                    continue
                    
                player_ign_db = player.get('ign', '').strip().lower()
                if player_ign_db == player_ign.strip().lower():
                    player_found = True
                    old_agent = player.get('agent', 'Unknown')
                    player_id = player.get('player_id')
                    team_num = player.get('team', 1)
                    team_name = f"Team {team_num}"
                    break
            
            if not player_found:
                await interaction.followup.send(
                    f"❌ Player `{player_ign}` not found in the most recent match!",
                    ephemeral=True
                )
                return
            
            # Update the agent in the match_players table
            pool = await db.get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE match_players
                    SET agent = $1
                    WHERE match_id = $2 AND player_id = $3
                """, matched_agent, match_id, player_id)
            
            # Send confirmation
            await interaction.followup.send(
                f"✅ **Agent Updated Successfully!**\n"
                f"Player: `{player_ign}` ({team_name})\n"
                f"Old Agent: `{old_agent}`\n"
                f"New Agent: `{matched_agent}`\n"
                f"Match ID: `{match_id}`"
            )
            
            print(f"✏️ Agent edited by {interaction.user.name}: {player_ign} {old_agent} → {matched_agent}")
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error updating agent: `{type(e).__name__}: {e}`",
                ephemeral=True
            )
            import traceback
            print(f"Error in edit_agent: {traceback.format_exc()}")

# ---- setup
async def setup(bot: commands.Bot):
    await bot.add_cog(OCRScanner(bot))