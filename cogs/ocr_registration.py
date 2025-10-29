"""
OCR-based Registration System
Player sends profile screenshot, bot reads IGN and ID automatically
"""

import discord
from discord import app_commands
from discord.ext import commands
import json
import aiohttp
import base64
from pathlib import Path
from io import BytesIO
from PIL import Image
import os
from services import db

# load .env optionally
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except Exception:
    pass

# helper: try env then config.json
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

class OCRRegistrationView(discord.ui.View):
    """View with Approve/Decline buttons after OCR scan"""
    
    def __init__(self, user_id: int, ign: str, player_id: str, cog):
        super().__init__(timeout=300)  # 5 minute timeout
        self.user_id = user_id
        self.ign = ign
        self.player_id = player_id
        self.cog = cog
    
    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success)
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Approve the OCR results and proceed to region selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your registration!", ephemeral=True)
            return
        
        # Show region selection
        region_view = RegionSelectionView(self.user_id, self.ign, self.player_id, self.cog)
        await interaction.response.edit_message(
            content=f"✅ **Information Confirmed!**\n\n**IGN:** `{self.ign}`\n**ID:** `{self.player_id}`\n\n**Select your region:**",
            view=region_view
        )
    
    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.danger)
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Decline and ask to send screenshot again"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your registration!", ephemeral=True)
            return
        
        await interaction.response.edit_message(
            content="❌ **OCR reading was incorrect.**\n\n"
                    "Please send your profile screenshot again with:\n"
                    "✅ **IGN (In-Game Name) clearly visible**\n"
                    "✅ **Player ID visible**\n"
                    "✅ **Good image quality**\n\n"
                    "Send the screenshot now:",
            view=None
        )


class RegionSelectionView(discord.ui.View):
    """View with region selection buttons"""
    
    def __init__(self, user_id: int, ign: str, player_id: str, cog):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.ign = ign
        self.player_id = player_id
        self.cog = cog
    
    @discord.ui.button(label="� North America (NA)", style=discord.ButtonStyle.primary)
    async def na_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Select NA region"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your registration!", ephemeral=True)
            return
        await self.complete_registration(interaction, "na")

    @discord.ui.button(label="🌍 Europe (EU)", style=discord.ButtonStyle.primary)
    async def eu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Select EU region"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your registration!", ephemeral=True)
            return
        await self.complete_registration(interaction, "eu")

    @discord.ui.button(label="🌏 Asia-Pacific (AP)", style=discord.ButtonStyle.primary)
    async def ap_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Select AP region"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your registration!", ephemeral=True)
            return
        await self.complete_registration(interaction, "ap")

    @discord.ui.button(label="🇰🇷 Korea (KR)", style=discord.ButtonStyle.primary)
    async def kr_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Select KR region"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your registration!", ephemeral=True)
            return
        await self.complete_registration(interaction, "kr")

    @discord.ui.button(label="🇧🇷 Brazil (BR)", style=discord.ButtonStyle.primary)
    async def br_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Select BR region"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your registration!", ephemeral=True)
            return
        await self.complete_registration(interaction, "br")

    @discord.ui.button(label="🌎 Latin America (LATAM)", style=discord.ButtonStyle.primary)
    async def latam_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Select LATAM region"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your registration!", ephemeral=True)
            return
        await self.complete_registration(interaction, "latam")

    @discord.ui.button(label="🇯🇵 Japan (JP)", style=discord.ButtonStyle.primary)
    async def jp_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Select JP region"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your registration!", ephemeral=True)
            return
        await self.complete_registration(interaction, "jp")
    
    async def complete_registration(self, interaction: discord.Interaction, region: str):
        """Complete the registration with selected region"""
        await interaction.response.defer()
        
        # Register the player
        success, message = await self.cog.register_player_ocr(
            interaction.user.id,
            self.ign,
            self.player_id,
            region
        )
        
        if success:
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                content=f"✅ **Registration Complete!**\n\n"
                        f"**IGN:** `{self.ign}`\n"
                        f"**ID:** `{self.player_id}`\n"
                        f"**Region:** `{region.upper()}`\n\n"
                        f"You're all set! Your stats will be tracked automatically.",
                view=None
            )
        else:
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                content=f"❌ **Registration Failed**\n\n{message}",
                view=None
            )


class OCRRegistration(commands.Cog):
    """OCR-based automatic registration system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path(__file__).parent.parent / "data"
        self.players_file = self.data_dir / "players.json"
        
        # Track users waiting for screenshot
        self.pending_registrations = {}  # {user_id: True}
        
        # Load config for Gemini API
        self.gemini_api_key = cfg('GEMINI_API_KEY')
    
    @app_commands.command(name="register_ocr", description="Register for the tournament using OCR (automatic)")
    async def register_ocr(self, interaction: discord.Interaction):
        """Start OCR registration process"""
        
        # Defer response immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        # Check if already registered in database
        try:
            existing_player = await db.get_player_by_discord_id(interaction.user.id)
            if existing_player:
                await interaction.followup.send(
                    "❌ You're already registered!\n"
                    f"**IGN:** `{existing_player.get('ign', 'Unknown')}`\n"
                    f"**Region:** `{existing_player.get('region', 'Unknown')}`",
                    ephemeral=True
                )
                return
        except Exception as e:
            print(f"Error checking existing player: {e}")
        
        # Send instructions in DM
        try:
            dm_channel = await interaction.user.create_dm()
            
            instructions_embed = discord.Embed(
                title="📝 Tournament Registration",
                description="Welcome! Let's get you registered automatically using OCR.",
                color=discord.Color.blue()
            )
            
            instructions_embed.add_field(
                name="📸 Step 1: Take a Screenshot",
                value=(
                    "Open VALORANT Mobile and go to your **Profile**\n"
                    "Make sure these are visible:\n"
                    "✅ Your **IGN** (In-Game Name)\n"
                    "✅ Your **Player ID** (numbers with #)\n"
                    "✅ Clear and readable text"
                ),
                inline=False
            )
            
            instructions_embed.add_field(
                name="📤 Step 2: Send Screenshot",
                value="Send your profile screenshot **here in DM**\nI'll read it automatically!",
                inline=False
            )
            
            instructions_embed.add_field(
                name="✅ Step 3: Confirm",
                value="Check if I read it correctly, then select your region!",
                inline=False
            )
            
            instructions_embed.set_footer(text="You have 5 minutes to complete registration")
            
            await dm_channel.send(embed=instructions_embed)
            
            # Mark user as pending registration
            self.pending_registrations[interaction.user.id] = True
            
            await interaction.followup.send(
                "✅ Check your DMs! I've sent you registration instructions.",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I couldn't send you a DM! Please enable DMs from server members and try again.",
                ephemeral=True
            )
        except Exception as e:
            print(f"Error in register_ocr: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for screenshots in DMs"""
        
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Only process DMs
        if not isinstance(message.channel, discord.DMChannel):
            return
        
        # Check if user is pending registration
        if message.author.id not in self.pending_registrations:
            return
        
        # Check if message has attachments
        if not message.attachments:
            await message.channel.send(
                "❌ Please send a screenshot image!\n"
                "Attach your VALORANT Mobile profile screenshot."
            )
            return
        
        # Get the first image attachment
        attachment = message.attachments[0]
        
        # Check if it's an image
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            await message.channel.send(
                "❌ Please send an image file!\n"
                "Supported formats: PNG, JPG, JPEG"
            )
            return
        
        # Process the screenshot with OCR
        await message.channel.send("🔄 Reading your profile screenshot...")
        
        try:
            # Download image
            image_bytes = await attachment.read()
            
            # Run OCR
            ign, player_id = await self.extract_profile_info(image_bytes)
            
            if not ign or not player_id:
                await message.channel.send(
                    "❌ **Could not read your profile!**\n\n"
                    "Please make sure:\n"
                    "✅ Your IGN is clearly visible\n"
                    "✅ Your Player ID is visible\n"
                    "✅ The image is not blurry\n\n"
                    "Send another screenshot:"
                )
                return
            
            # Show what was read with approve/decline buttons
            view = OCRRegistrationView(message.author.id, ign, player_id, self)
            
            await message.channel.send(
                f"✅ **Successfully read your profile!**\n\n"
                f"**IGN:** `{ign}`\n"
                f"**Player ID:** `{player_id}`\n\n"
                f"Is this information correct?",
                view=view
            )
            
        except Exception as e:
            print(f"OCR Registration error: {e}")
            await message.channel.send(
                f"❌ **Error processing screenshot**\n\n"
                f"Error: `{str(e)}`\n\n"
                f"Please try again with a clearer screenshot."
            )
    
    async def extract_profile_info(self, image_bytes: bytes) -> tuple[str, str]:
        """Extract IGN and Player ID from profile screenshot using Gemini OCR"""
        
        if not self.gemini_api_key:
            return None, None
        
        # Convert image to base64
        img = Image.open(BytesIO(image_bytes))
        
        # Resize if too large
        max_size = 1600
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.LANCZOS)
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Gemini prompt for profile extraction
        prompt = """
You are reading a VALORANT Mobile player profile screenshot.

Extract the following information:
1. IGN (In-Game Name) - the player's username
2. Player ID - the numeric ID (format: 1234 or #1234)

Return RAW JSON ONLY (no markdown):
{
  "ign": "PlayerName",
  "id": "1234567"
}

Rules:
- Find the player's IGN (usually displayed prominently)
- Find the Player ID (numbers, may have # prefix)
- Remove # from ID if present
- If IGN not found, set to null
- If ID not found, set to null
"""
        
        # Try multiple Gemini models
        models = [
            ("v1beta", "gemini-2.0-flash-exp"),
            ("v1beta", "gemini-exp-1206"),
            ("v1beta", "gemini-1.5-pro"),
        ]
        
        for version, model in models:
            try:
                url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent"
                
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": img_b64
                                }
                            }
                        ]
                    }]
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        params={"key": self.gemini_api_key},
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as resp:
                        if resp.status != 200:
                            continue
                        
                        data = await resp.json()
                        text_response = data['candidates'][0]['content']['parts'][0]['text']
                        
                        # Parse JSON response
                        import re
                        json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
                        if json_match:
                            result = json.loads(json_match.group())
                            ign = result.get('ign')
                            player_id = result.get('id')
                            
                            # Clean up ID (remove # if present)
                            if player_id:
                                player_id = str(player_id).replace('#', '').strip()
                            
                            return ign, player_id
            
            except Exception as e:
                print(f"OCR error with {model}: {e}")
                continue
        
        return None, None
    
    async def register_player_ocr(self, discord_id: int, ign: str, player_id: str, region: str) -> tuple[bool, str]:
        """Register a player with OCR-extracted data using PostgreSQL"""
        
        try:
            from services import db

            # Reset sequences if needed
            await db.reset_sequences()

            # Check if already registered by discord_id
            existing_player = await db.get_player(discord_id)
            if existing_player:
                return False, "You are already registered!"

            # Check if IGN exists (case insensitive)
            existing_ign = await db.get_player_by_ign(ign)
            if existing_ign:
                return False, f"IGN `{ign}` is already taken!"

            # Create new player in database
            try:
                player = await db.create_player(
                    discord_id=discord_id,
                    ign=ign,
                    player_id=int(player_id) if player_id.isdigit() else 0,
                    region=region
                )

                # Initialize empty stats
                initial_stats = {
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0,
                    "matches_played": 0,
                    "wins": 0,
                    "losses": 0,
                    "mvps": 0
                }
                
                # Create initial player stats
                await db.create_player_stats(discord_id, initial_stats)

                # Send log to logs channel
                try:
                    log_channel_id = os.getenv("LOG_CHANNEL_ID")
                    if log_channel_id:
                        log_channel = self.bot.get_channel(int(log_channel_id))
                        if log_channel:
                            # Get the member object for better logging
                            member = self.bot.get_user(discord_id)
                            log_embed = discord.Embed(
                                title="🆕 New Player Registration (OCR)",
                                color=discord.Color.purple(),
                                timestamp=discord.utils.utcnow()
                            )
                            if member:
                                log_embed.add_field(name="Player", value=f"{member.mention} ({member})", inline=False)
                                log_embed.set_thumbnail(url=member.display_avatar.url)
                            else:
                                log_embed.add_field(name="Player", value=f"User ID: {discord_id}", inline=False)
                            
                            log_embed.add_field(name="IGN", value=ign, inline=True)
                            log_embed.add_field(name="Player ID", value=str(player_id), inline=True)
                            log_embed.add_field(name="Region", value=region.upper(), inline=True)
                            log_embed.add_field(name="Discord ID", value=str(discord_id), inline=True)
                            log_embed.set_footer(text=f"User ID: {discord_id} • Method: OCR")
                            
                            await log_channel.send(embed=log_embed)
                except Exception as log_error:
                    print(f"Error sending OCR registration log: {log_error}")

            except Exception as e:
                return False, f"Database error: {str(e)}"

            # Remove from pending registrations
            if discord_id in self.pending_registrations:
                del self.pending_registrations[discord_id]
            
            return True, "Registration successful!"
            
        except Exception as e:
            return False, f"Error: {str(e)}"


async def setup(bot):
    await bot.add_cog(OCRRegistration(bot))
