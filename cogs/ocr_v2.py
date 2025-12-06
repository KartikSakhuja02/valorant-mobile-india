"""
OCR V2 - Simple and Clean Match Result Scanner
Extracts match data from VALORANT Mobile screenshots
"""

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
import json
import base64
import os
from typing import Optional, Dict, List
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = 'gemini-2.0-flash-exp'  # Gemini 2.0 Flash model

class MatchScanner(commands.Cog):
    """Simple match result scanner using Gemini Vision API"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="scan", description="Scan a match result screenshot")
    async def scan_match(self, interaction: discord.Interaction, screenshot: discord.Attachment):
        """Scan match screenshot and extract results"""
        try:
            await interaction.response.defer()
        except Exception as e:
            print(f"Error deferring: {e}")
            return
        
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
            
            # Resize if too large (max 1600px)
            if max(image.size) > 1600:
                ratio = 1600 / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.LANCZOS)
                print(f"📐 Resized to: {new_size}")
            
            # Convert to PNG for API
            png_buffer = io.BytesIO()
            image.save(png_buffer, format='PNG')
            png_bytes = png_buffer.getvalue()
            
            print(f"📦 PNG size: {len(png_bytes)} bytes")
            
            # Extract data using Gemini
            await interaction.followup.send("🔍 Analyzing screenshot...")
            
            match_data = await self.extract_match_data(png_bytes)
            
            if not match_data:
                await interaction.followup.send("❌ Could not extract match data. Please ensure the screenshot shows the match results clearly.")
                return
            
            print(f"✅ Extracted data: {json.dumps(match_data, indent=2)}")
            
            # Display results
            await self.display_match_results(interaction, match_data)
            
        except Exception as e:
            print(f"❌ Error scanning match: {e}")
            import traceback
            traceback.print_exc()
            try:
                await interaction.followup.send(f"❌ Error scanning screenshot: {str(e)}")
            except:
                pass
    
    async def extract_match_data(self, image_bytes: bytes) -> Optional[Dict]:
        """Extract match data using Gemini Vision API"""
        
        prompt = """
You are analyzing a VALORANT Mobile match result screenshot.

Extract the following information:

1. MAP NAME (e.g., Haven, Bind, Ascent, etc.)
2. SCORE: Two numbers showing Team A vs Team B (format: "10 - 5")
3. TEAM A (Cyan/Green team) - List all players with:
   - IGN (in-game name)
   - Kills / Deaths / Assists (K/D/A format)
4. TEAM B (Red team) - List all players with:
   - IGN (in-game name)
   - Kills / Deaths / Assists (K/D/A format)

IMPORTANT:
- Team A is the CYAN/GREEN team (left side, appears first)
- Team B is the RED team (right side, appears second)
- Each team should have exactly 5 players
- Extract K/D/A in format: kills/deaths/assists

Return ONLY valid JSON in this exact format:
{
  "map": "Haven",
  "score": {
    "team_a": 10,
    "team_b": 5
  },
  "team_a": [
    {"ign": "player1", "kills": 17, "deaths": 10, "assists": 5},
    {"ign": "player2", "kills": 11, "deaths": 12, "assists": 4}
  ],
  "team_b": [
    {"ign": "player3", "kills": 10, "deaths": 11, "assists": 10},
    {"ign": "player4", "kills": 12, "deaths": 9, "assists": 0}
  ]
}

Rules:
- Return ONLY the JSON, no markdown, no explanation
- Team A = Cyan/Green color
- Team B = Red color
- If you can't read a value, use null
"""
        
        try:
            # Prepare API request
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
            headers = {"Content-Type": "application/json"}
            params = {"key": GEMINI_API_KEY}
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": base64.b64encode(image_bytes).decode("utf-8")
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0,
                    "maxOutputTokens": 2048
                }
            }
            
            # Call Gemini API
            print(f"🌐 Calling Gemini API...")
            timeout = aiohttp.ClientTimeout(total=60)  # Increased to 60 seconds
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, params=params, json=payload) as resp:
                    print(f"📡 Response status: {resp.status}")
                    
                    if resp.status != 200:
                        error_text = await resp.text()
                        print(f"❌ Gemini API error: {resp.status} - {error_text}")
                        return None
                    
                    data = await resp.json()
                    print(f"✅ Got response from Gemini")
            
            # Parse response
            if "candidates" not in data or not data["candidates"]:
                print(f"❌ No candidates in response: {data}")
                return None
            
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Extract JSON from response
            match_data = self.extract_json(text)
            
            # Validate data
            if not self.validate_match_data(match_data):
                print(f"❌ Invalid match data: {match_data}")
                return None
            
            return match_data
            
        except Exception as e:
            print(f"❌ Error calling Gemini API: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_json(self, text: str) -> Dict:
        """Extract JSON from Gemini response"""
        text = text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
        
        # Find JSON object
        start = text.find("{")
        if start == -1:
            raise ValueError("No JSON found in response")
        
        # Find matching closing brace
        depth = 0
        for i, ch in enumerate(text[start:], start=start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i+1])
        
        raise ValueError("Unbalanced JSON braces")
    
    def validate_match_data(self, data: Dict) -> bool:
        """Validate extracted match data"""
        if not data:
            return False
        
        # Check required fields
        if "map" not in data or "score" not in data:
            return False
        
        if "team_a" not in data or "team_b" not in data:
            return False
        
        team_a = data["team_a"]
        team_b = data["team_b"]
        
        # Check teams are lists
        if not isinstance(team_a, list) or not isinstance(team_b, list):
            return False
        
        # Check we have players
        if len(team_a) == 0 or len(team_b) == 0:
            return False
        
        # Validate each player has required fields
        for player in team_a + team_b:
            if "ign" not in player:
                return False
            # K/D/A can be null if unreadable
        
        return True
    
    async def display_match_results(self, interaction: discord.Interaction, data: Dict):
        """Display match results in a formatted embed with color-coded styling"""
        
        map_name = data.get("map", "Unknown")
        scores = data.get("score", {})
        team_a_score = scores.get("team_a", 0)
        team_b_score = scores.get("team_b", 0)
        team_a = data.get("team_a", [])
        team_b = data.get("team_b", [])
        
        # Determine winner and MVP
        if team_a_score > team_b_score:
            winner_text = "Team A (Cyan)"
            embed_color = discord.Color.from_rgb(0, 255, 255)  # Cyan
            winning_team = team_a
        elif team_b_score > team_a_score:
            winner_text = "Team B (Red)"
            embed_color = discord.Color.from_rgb(255, 69, 58)  # Red
            winning_team = team_b
        else:
            winner_text = "Draw"
            embed_color = discord.Color.from_rgb(255, 204, 0)  # Yellow for draw
            winning_team = team_a  # Arbitrary for MVP
        
        # Find MVP (most kills in winning team)
        mvp = None
        max_kills = -1
        if winning_team:
            for player in winning_team:
                kills = player.get("kills", 0)
                if kills and kills > max_kills:
                    max_kills = kills
                    mvp = player.get("ign", "Unknown")
        
        # Create embed
        embed = discord.Embed(
            title="📊 MATCH RESULTS",
            color=embed_color
        )
        
        # Map info
        embed.add_field(
            name="🗺️ Map",
            value=f"**{map_name}**",
            inline=True
        )
        
        # Score with color indicators
        score_text = f"```ansi\n\u001b[36m{team_a_score}\u001b[0m - \u001b[31m{team_b_score}\u001b[0m\n```"
        embed.add_field(
            name="📈 Score",
            value=score_text,
            inline=True
        )
        
        # Winner
        embed.add_field(
            name="🏆 Winner",
            value=f"**{winner_text}**",
            inline=True
        )
        
        # Team A (Cyan) - with color coding
        team_a_text = "```ansi\n"
        for player in team_a:
            ign = player.get("ign", "Unknown")
            k = player.get("kills", "?")
            d = player.get("deaths", "?")
            a = player.get("assists", "?")
            
            # Highlight MVP with yellow
            if mvp and ign == mvp:
                team_a_text += f"\u001b[33m⭐ {ign}\u001b[0m • {k}/{d}/{a}\n"
            else:
                team_a_text += f"\u001b[36m{ign}\u001b[0m • {k}/{d}/{a}\n"
        team_a_text += "```"
        
        embed.add_field(
            name=f"🟦 Team A (Cyan) - {team_a_score}",
            value=team_a_text,
            inline=False
        )
        
        # Team B (Red) - with color coding
        team_b_text = "```ansi\n"
        for player in team_b:
            ign = player.get("ign", "Unknown")
            k = player.get("kills", "?")
            d = player.get("deaths", "?")
            a = player.get("assists", "?")
            
            # Highlight MVP with yellow
            if mvp and ign == mvp:
                team_b_text += f"\u001b[33m⭐ {ign}\u001b[0m • {k}/{d}/{a}\n"
            else:
                team_b_text += f"\u001b[31m{ign}\u001b[0m • {k}/{d}/{a}\n"
        team_b_text += "```"
        
        embed.add_field(
            name=f"🟥 Team B (Red) - {team_b_score}",
            value=team_b_text,
            inline=False
        )
        
        # MVP highlight
        if mvp:
            embed.add_field(
                name="⭐ MVP",
                value=f"**{mvp}** ({max_kills} kills)",
                inline=False
            )
        
        embed.set_footer(text=f"Scanned by {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(MatchScanner(bot))
