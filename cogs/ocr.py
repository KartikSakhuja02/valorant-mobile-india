# cogs/ocr.py - Tesseract OCR for VALORANT Mobile match scanning
"""
Tesseract OCR Scanner:
- Uses Tesseract OCR (no API costs, works offline)
- Detects cyan (Team A) and red (Team B) players via color detection
- Handles yellow/gold MVP players (assigns to team with 4 players)
- Reads Win (获胜) or Defeat (败北) text for cyan team
- Extracts player names, K/D/A, and scores
- NO AGENT DETECTION
"""

import io
import re
import colorsys
from typing import List, Dict, Optional
import os

import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image
import numpy as np

try:
    import pytesseract
except ImportError:
    pytesseract = None
    print("⚠️ pytesseract not installed. Run: pip install pytesseract")

# Chinese to English map translation
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
    """Translate Chinese map name to English"""
    if not map_text:
        return 'Unknown'
    
    for chinese, english in CHINESE_MAP_NAMES.items():
        if chinese in map_text:
            return english
    
    map_text_lower = map_text.lower()
    english_maps = ['ascent', 'bind', 'icebox', 'haven', 'split', 'breeze', 
                    'fracture', 'pearl', 'lotus', 'sunset', 'abyss']
    
    for eng_map in english_maps:
        if eng_map in map_text_lower:
            return eng_map.capitalize()
    
    return map_text

# ======================== COLOR DETECTION ========================

def _rgb_to_hsv01(arr_uint8: np.ndarray) -> np.ndarray:
    """Convert RGB (0-255) to HSV (0-1 range)"""
    arr = arr_uint8.astype(np.float32) / 255.0
    out = np.zeros_like(arr)
    for i, (r, g, b) in enumerate(arr):
        h, s, v = colorsys.rgb_to_hsv(float(r), float(g), float(b))
        out[i] = (h, s, v)
    return out

def _mask_hsv(hsv: np.ndarray, ranges_deg, s_min: float, v_min: float):
    """Filter HSV by hue ranges, saturation, and value"""
    h = hsv[:, 0] * 360.0
    s = hsv[:, 1]
    v = hsv[:, 2]
    ok = np.zeros(len(h), dtype=bool)
    for lo, hi in ranges_deg:
        if lo <= hi:
            ok |= (h >= lo) & (h <= hi)
        else:
            ok |= (h >= lo) | (h <= hi)
    ok &= (s >= s_min) & (v >= v_min)
    return ok

def _score_patch(patch_rgb: np.ndarray):
    """Score a color patch for team detection"""
    if patch_rgb.size == 0:
        return 0.0, 0.0, 0.0
    
    flat = patch_rgb.reshape(-1, 3).astype(np.uint8)
    hsv = _rgb_to_hsv01(flat)
    
    # Cyan/Blue for Team A
    blue_mask = _mask_hsv(hsv, [(170, 230)], 0.20, 0.20)
    blue_score = float(blue_mask.mean())
    
    # Red for Team B
    red_mask = _mask_hsv(hsv, [(0, 25), (335, 360)], 0.30, 0.20)
    red_score = float(red_mask.mean())
    
    # Yellow/Gold for MVP
    gold_mask = _mask_hsv(hsv, [(25, 65)], 0.30, 0.35)
    gold_score = float(gold_mask.mean())
    
    return blue_score, red_score, gold_score

def _sample_color_patches(img: Image.Image, row_idx: int) -> List[np.ndarray]:
    """Sample 5 color patches from a player row"""
    im = img.convert("RGB")
    W, H = im.size
    arr = np.asarray(im)
    
    # Calculate row position (assumes standard VALORANT Mobile layout)
    top = int(0.255 * H)
    row_h = int(0.067 * H)
    cy = top + int((row_idx + 0.5) * row_h)
    y1 = max(cy - 8, 0)
    y2 = min(cy + 8, H)
    
    # Sample positions across the row
    x_ign_left = int(0.19 * W)
    x_ign_right = int(0.38 * W)
    x_mid = int(0.49 * W)
    x_kda = int(0.56 * W)
    x_right = int(0.90 * W)
    
    def patch(xc: int, width: int = 16) -> np.ndarray:
        half = width // 2
        x1 = max(xc - half, 0)
        x2 = min(xc + half, W)
        return arr[y1:y2, x1:x2, :]
    
    return [
        patch(int(x_ign_left + 5), width=20),
        patch(int(x_ign_right - 10), width=20),
        patch(x_mid, width=16),
        patch(int(x_kda + 8), width=12),
        patch(int(x_right - 10), width=12),
    ]

def detect_player_team(img: Image.Image, row_idx: int) -> str:
    """
    Detect which team a player belongs to based on background color
    Returns: "CYAN", "RED", or "GOLD"
    """
    patches = _sample_color_patches(img, row_idx)
    
    # Weight patches: left patches (near name) are more reliable
    weights = np.array([2.0, 1.5, 1.0, 0.8, 0.6])
    
    blue_scores = []
    red_scores = []
    gold_scores = []
    
    for patch in patches:
        b, r, g = _score_patch(patch)
        blue_scores.append(b)
        red_scores.append(r)
        gold_scores.append(g)
    
    blue_total = float((np.array(blue_scores) * weights).sum())
    red_total = float((np.array(red_scores) * weights).sum())
    gold_total = float((np.array(gold_scores) * weights).sum())
    
    # Check for gold first (MVP player)
    if gold_total > 0.8:
        return "GOLD"
    
    # Otherwise check cyan vs red
    if blue_total > red_total and blue_total > 0.5:
        return "CYAN"
    elif red_total > blue_total and red_total > 0.5:
        return "RED"
    
    # Fallback: use position (first 5 = cyan, last 5 = red)
    return "CYAN" if row_idx < 5 else "RED"

# ======================== TESSERACT OCR ========================

def extract_text_from_image(image: Image.Image) -> str:
    """Extract all text from image using Tesseract OCR"""
    if pytesseract is None:
        raise RuntimeError("pytesseract not installed")
    
    # Configure for English + Chinese
    custom_config = r'--oem 3 --psm 6 -l eng+chi_sim'
    text = pytesseract.image_to_string(image, config=custom_config)
    return text

def extract_match_data(image: Image.Image) -> Optional[Dict]:
    """Extract match data from screenshot using Tesseract OCR"""
    try:
        # Get all text from image
        text = extract_text_from_image(image)
        print(f"📄 Extracted text:\n{text}\n")
        
        # Extract map name
        map_name = "Unknown"
        for chinese, english in CHINESE_MAP_NAMES.items():
            if chinese in text:
                map_name = english
                break
        
        # Check for English map names if Chinese not found
        if map_name == "Unknown":
            text_lower = text.lower()
            english_maps = ['ascent', 'bind', 'icebox', 'haven', 'split', 'breeze', 
                          'fracture', 'pearl', 'lotus', 'sunset', 'abyss']
            for eng_map in english_maps:
                if eng_map in text_lower:
                    map_name = eng_map.capitalize()
                    break
        
        # Extract Win/Defeat text
        result_text = ""
        if "获胜" in text:
            result_text = "获胜"
            print("🏆 Found: 获胜 (Win)")
        elif "败北" in text:
            result_text = "败北"
            print("💔 Found: 败北 (Defeat)")
        
        # Extract scores (look for patterns like "10 - 5" or "10  5")
        score_patterns = [
            r'(\d{1,2})\s*[-–—]\s*(\d{1,2})',  # 10 - 5
            r'(\d{1,2})\s+(\d{1,2})',           # 10  5
        ]
        
        score_left = 0
        score_right = 0
        
        for pattern in score_patterns:
            match = re.search(pattern, text)
            if match:
                score_left = int(match.group(1))
                score_right = int(match.group(2))
                print(f"📊 Scores: {score_left} - {score_right}")
                break
        
        # Extract player data (K/D/A patterns)
        # Look for patterns like: "17 / 10 / 5" or "17/10/5"
        kda_pattern = r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{1,2})'
        kda_matches = re.findall(kda_pattern, text)
        
        print(f"🎮 Found {len(kda_matches)} K/D/A entries")
        
        # Extract player names (complex, will use lines before K/D/A)
        lines = text.split('\n')
        players = []
        
        for i, line in enumerate(lines):
            # Check if this line has K/D/A
            kda_match = re.search(kda_pattern, line)
            if kda_match:
                kills = int(kda_match.group(1))
                deaths = int(kda_match.group(2))
                assists = int(kda_match.group(3))
                
                # Try to find player name in same line or previous lines
                # Remove K/D/A from line to get name
                name_part = re.sub(kda_pattern, '', line).strip()
                
                # Clean up common OCR artifacts
                name_part = re.sub(r'[|\\\/]', '', name_part)
                name_part = name_part.strip()
                
                # If name is too short or empty, try previous line
                if len(name_part) < 2 and i > 0:
                    name_part = lines[i-1].strip()
                
                # Use fallback if still empty
                if not name_part or len(name_part) < 2:
                    name_part = f"Player{len(players)+1}"
                
                players.append({
                    "ign": name_part,
                    "kills": kills,
                    "deaths": deaths,
                    "assists": assists
                })
        
        print(f"✅ Extracted {len(players)} players")
        
        # Validate we have 10 players
        if len(players) < 8:
            print(f"⚠️ Only found {len(players)} players, need at least 8")
            return None
        
        # Take first 10 players
        players = players[:10]
        
        return {
            "map": map_name,
            "result_text": result_text,
            "score_left": score_left,
            "score_right": score_right,
            "players": players
        }
    
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        import traceback
        traceback.print_exc()
        return None

# ======================== MAIN COG ========================

class SimpleOCRScanner(commands.Cog):
    """Simplified OCR scanner for VALORANT Mobile matches"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="scan", description="Scan a match screenshot")
    async def scan_match(self, interaction: discord.Interaction, screenshot: discord.Attachment):
        """Scan match screenshot and extract results using Tesseract OCR"""
        await interaction.response.defer()
        
        try:
            # Validate image
            if not screenshot.content_type or not screenshot.content_type.startswith('image/'):
                await interaction.followup.send("❌ Please upload a valid image file!")
                return
            
            print(f"📸 Processing screenshot: {screenshot.filename}")
            
            # Download and process image
            image_bytes = await screenshot.read()
            image = Image.open(io.BytesIO(image_bytes))
            
            print(f"📐 Image size: {image.size}")
            
            # Resize if needed
            if max(image.size) > 1600:
                ratio = 1600 / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.LANCZOS)
                print(f"📐 Resized to: {new_size}")
            
            # Extract data using Tesseract
            await interaction.followup.send("🔍 Analyzing screenshot with Tesseract OCR...")
            
            tesseract_data = extract_match_data(image)
            
            if not tesseract_data:
                await interaction.followup.send("❌ Could not extract match data. Please ensure the screenshot shows the scoreboard clearly.")
                return
            
            print(f"✅ Tesseract data extracted")
            
            # Detect team colors for all 10 players
            print("\n🎨 Detecting player team colors...")
            color_assignments = []
            for i in range(10):
                team_color = detect_player_team(image, i)
                color_assignments.append(team_color)
                print(f"  Row {i}: {team_color}")
            
            # Count cyan, red, and gold players
            cyan_count = color_assignments.count("CYAN")
            red_count = color_assignments.count("RED")
            gold_count = color_assignments.count("GOLD")
            
            print(f"\n📊 Color counts: Cyan={cyan_count}, Red={red_count}, Gold={gold_count}")
            
            # Assign gold players to the team with 4 players
            final_assignments = color_assignments.copy()
            if gold_count > 0:
                for i, color in enumerate(final_assignments):
                    if color == "GOLD":
                        if cyan_count == 4 and red_count == 5:
                            final_assignments[i] = "CYAN"
                            cyan_count += 1
                            red_count -= 1
                            print(f"🟡 Assigned gold player (row {i}) to CYAN (was 4v5)")
                        elif red_count == 4 and cyan_count == 5:
                            final_assignments[i] = "RED"
                            red_count += 1
                            cyan_count -= 1
                            print(f"🟡 Assigned gold player (row {i}) to RED (was 5v4)")
                        else:
                            # Default: assign to smaller team or cyan if equal
                            if cyan_count <= red_count:
                                final_assignments[i] = "CYAN"
                                cyan_count += 1
                                print(f"🟡 Assigned gold player (row {i}) to CYAN (default)")
                            else:
                                final_assignments[i] = "RED"
                                red_count += 1
                                print(f"🟡 Assigned gold player (row {i}) to RED (default)")
            
            # Build teams
            players = tesseract_data.get("players", [])
            team_cyan = []
            team_red = []
            
            for i, player in enumerate(players[:10]):
                if final_assignments[i] == "CYAN":
                    team_cyan.append(player)
                else:
                    team_red.append(player)
            
            print(f"\n✅ Final teams: Cyan={len(team_cyan)}, Red={len(team_red)}")
            
            # Determine scores and winner
            score_left = tesseract_data.get("score_left", 0)
            score_right = tesseract_data.get("score_right", 0)
            result_text = tesseract_data.get("result_text", "")
            
            # "获胜" = Win, "败北" = Defeat (for CYAN team)
            if "获胜" in result_text:
                # Cyan won
                cyan_score = max(score_left, score_right)
                red_score = min(score_left, score_right)
                winner = "Team A (Cyan)"
            elif "败北" in result_text:
                # Cyan lost
                cyan_score = min(score_left, score_right)
                red_score = max(score_left, score_right)
                winner = "Team B (Red)"
            else:
                # Fallback: higher score wins
                if score_left > score_right:
                    cyan_score = score_left
                    red_score = score_right
                    winner = "Team A (Cyan)"
                else:
                    cyan_score = score_right
                    red_score = score_left
                    winner = "Team B (Red)"
            
            # Map name
            map_name = translate_map_name(tesseract_data.get("map", "Unknown"))
            
            # Display results
            await self.display_results(interaction, map_name, cyan_score, red_score, 
                                     team_cyan, team_red, winner)
            
        except Exception as e:
            print(f"❌ Error scanning match: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ Error: {str(e)}")
    
    async def display_results(self, interaction, map_name, cyan_score, red_score, 
                            team_cyan, team_red, winner):
        """Display match results in an embed"""
        
        # Determine embed color based on winner
        if "Cyan" in winner:
            embed_color = discord.Color.from_rgb(0, 255, 255)  # Cyan
        else:
            embed_color = discord.Color.from_rgb(255, 69, 58)  # Red
        
        # Find MVP (most kills from winning team)
        winning_team = team_cyan if "Cyan" in winner else team_red
        mvp = None
        max_kills = -1
        for player in winning_team:
            kills = player.get("kills", 0) or 0
            if kills > max_kills:
                max_kills = kills
                mvp = player.get("ign", "Unknown")
        
        # Create embed
        embed = discord.Embed(
            title="📊 MATCH RESULTS",
            color=embed_color
        )
        
        embed.add_field(name="🗺️ Map", value=f"**{map_name}**", inline=True)
        embed.add_field(name="📈 Score", value=f"**{cyan_score} - {red_score}**", inline=True)
        embed.add_field(name="🏆 Winner", value=f"**{winner}**", inline=True)
        
        # Team A (Cyan)
        cyan_text = ""
        for player in team_cyan:
            ign = player.get("ign", "Unknown")
            k = player.get("kills", "?") or "?"
            d = player.get("deaths", "?") or "?"
            a = player.get("assists", "?") or "?"
            
            if mvp and ign == mvp:
                cyan_text += f"⭐ **{ign}** • {k}/{d}/{a}\n"
            else:
                cyan_text += f"{ign} • {k}/{d}/{a}\n"
        
        embed.add_field(
            name=f"🟦 Team A (Cyan) - {cyan_score}",
            value=cyan_text or "No players",
            inline=False
        )
        
        # Team B (Red)
        red_text = ""
        for player in team_red:
            ign = player.get("ign", "Unknown")
            k = player.get("kills", "?") or "?"
            d = player.get("deaths", "?") or "?"
            a = player.get("assists", "?") or "?"
            
            if mvp and ign == mvp:
                red_text += f"⭐ **{ign}** • {k}/{d}/{a}\n"
            else:
                red_text += f"{ign} • {k}/{d}/{a}\n"
        
        embed.add_field(
            name=f"🟥 Team B (Red) - {red_score}",
            value=red_text or "No players",
            inline=False
        )
        
        if mvp:
            embed.add_field(
                name="⭐ MVP",
                value=f"**{mvp}** ({max_kills} kills)",
                inline=False
            )
        
        embed.set_footer(text=f"Scanned by {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(SimpleOCRScanner(bot))
