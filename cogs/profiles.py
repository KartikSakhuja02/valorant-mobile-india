import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os
import json
import aiohttp
import asyncio
from io import BytesIO
from datetime import datetime
from services import db

# Helper to get config values
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

# View for region selection via DM
class RegionSelectView(View):
    def __init__(self, user: discord.Member, guild: discord.Guild):
        super().__init__(timeout=300)
        self.user = user
        self.guild = guild
        self.selected_region = None
    
    @discord.ui.button(label="NA", style=discord.ButtonStyle.primary, emoji="🌎")
    async def na_button(self, interaction: discord.Interaction, button: Button):
        await self.select_region(interaction, "NA")
    
    @discord.ui.button(label="EU", style=discord.ButtonStyle.primary, emoji="🌍")
    async def eu_button(self, interaction: discord.Interaction, button: Button):
        await self.select_region(interaction, "EU")
    
    @discord.ui.button(label="AP", style=discord.ButtonStyle.primary, emoji="🌏")
    async def ap_button(self, interaction: discord.Interaction, button: Button):
        await self.select_region(interaction, "AP")
    
    @discord.ui.button(label="KR", style=discord.ButtonStyle.primary, emoji="🇰🇷")
    async def kr_button(self, interaction: discord.Interaction, button: Button):
        await self.select_region(interaction, "KR")
    
    @discord.ui.button(label="BR", style=discord.ButtonStyle.primary, emoji="🇧🇷")
    async def br_button(self, interaction: discord.Interaction, button: Button):
        await self.select_region(interaction, "BR")
    
    @discord.ui.button(label="LATAM", style=discord.ButtonStyle.primary, emoji="🌎")
    async def latam_button(self, interaction: discord.Interaction, button: Button):
        await self.select_region(interaction, "LATAM")
    
    @discord.ui.button(label="JP", style=discord.ButtonStyle.primary, emoji="🇯🇵")
    async def jp_button(self, interaction: discord.Interaction, button: Button):
        await self.select_region(interaction, "JP")
    
    async def select_region(self, interaction: discord.Interaction, region: str):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return
        
        await interaction.response.defer()
        self.selected_region = region
        
        try:
            # Get old region
            player_data = await db.get_player(self.user.id)
            old_region = player_data.get('region', 'Unknown')
            
            # Update region in database
            await db.update_player_region(self.user.id, region)
            
            # Get role IDs from config
            role_map = {
                'NA': cfg('ROLE_AMERICAS_ID'),
                'EU': cfg('ROLE_EMEA_ID'),
                'EMEA': cfg('ROLE_EMEA_ID'),
                'AP': cfg('ROLE_APAC_ID'),
                'APAC': cfg('ROLE_APAC_ID'),
                'KR': cfg('ROLE_APAC_ID'),
                'BR': cfg('ROLE_AMERICAS_ID'),
                'LATAM': cfg('ROLE_AMERICAS_ID'),
                'JP': cfg('ROLE_APAC_ID')
            }
            
            # Get member in guild
            member = self.guild.get_member(self.user.id)
            if not member:
                await interaction.followup.send(f"✅ Region updated to **{region}** in database!")
                return
            
            # Remove old region role
            old_role_id = role_map.get(old_region.upper())
            if old_role_id:
                try:
                    old_role = self.guild.get_role(int(old_role_id))
                    if old_role and old_role in member.roles:
                        await member.remove_roles(old_role)
                        print(f"Removed old region role: {old_role.name}")
                except Exception as e:
                    print(f"Error removing old role: {e}")
            
            # Add new region role
            new_role_id = role_map.get(region)
            if new_role_id:
                try:
                    new_role = self.guild.get_role(int(new_role_id))
                    if new_role:
                        await member.add_roles(new_role)
                        print(f"Added new region role: {new_role.name}")
                except Exception as e:
                    print(f"Error adding new role: {e}")
            
            # If changing FROM APAC to another region, remove India role and status
            if old_region.upper() in ['AP', 'APAC', 'KR', 'JP'] and region not in ['AP', 'KR', 'JP']:
                india_role_id = cfg('INDIA_ROLE_ID')
                if india_role_id:
                    try:
                        india_role = self.guild.get_role(int(india_role_id))
                        if india_role and india_role in member.roles:
                            await member.remove_roles(india_role)
                            await db.update_player_india_status(self.user.id, False)
                            print(f"Removed India role (left APAC region)")
                    except Exception as e:
                        print(f"Error removing India role: {e}")
            
            # If changing TO APAC, prompt for India status
            if region in ['AP', 'KR', 'JP'] and old_region.upper() not in ['AP', 'APAC', 'KR', 'JP']:
                india_view = IndiaToggleView(self.user, self.guild, False)
                await interaction.followup.send(
                    f"✅ Region updated to **{region}** and roles updated!\n\n"
                    "🇮🇳 **Are you from India?** Please select below:",
                    view=india_view
                )
            else:
                await interaction.followup.send(f"✅ Region updated to **{region}** and roles updated!")
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error updating region: {e}")

# View for India role toggle
class IndiaToggleView(View):
    def __init__(self, user: discord.Member, guild: discord.Guild, current_status: bool):
        super().__init__(timeout=300)
        self.user = user
        self.guild = guild
        self.current_status = current_status
    
    @discord.ui.button(label="✅ Yes, I'm from India", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, button: Button):
        await self.toggle_india(interaction, True)
    
    @discord.ui.button(label="❌ No, I'm not from India", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: Button):
        await self.toggle_india(interaction, False)
    
    async def toggle_india(self, interaction: discord.Interaction, is_india: bool):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ This is not for you!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Update in database
            await db.update_player_india_status(self.user.id, is_india)
            
            # Update India role
            india_role_id = cfg('INDIA_ROLE_ID')
            if india_role_id:
                member = self.guild.get_member(self.user.id)
                if member:
                    india_role = self.guild.get_role(int(india_role_id))
                    if india_role:
                        if is_india and india_role not in member.roles:
                            await member.add_roles(india_role)
                        elif not is_india and india_role in member.roles:
                            await member.remove_roles(india_role)
            
            status_text = "from India" if is_india else "not from India"
            role_action = "added" if is_india else "removed"
            await interaction.followup.send(
                f"✅ India status updated! You are now marked as **{status_text}**.\n"
                f"🇮🇳 India role {role_action}."
            )
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error updating India status: {e}")

# Main profile edit view
class ProfileEditView(View):
    def __init__(self, player_data: dict, user: discord.Member, bot, guild: discord.Guild, requester: discord.Member):
        super().__init__(timeout=300)
        self.player_data = player_data
        self.user = user  # The profile owner
        self.requester = requester  # The person who clicked the button
        self.bot = bot
        self.guild = guild
        
        # Hide India status button if not APAC region
        player_region = player_data.get('region', '').upper()
        if player_region not in ['AP', 'APAC', 'KR', 'JP']:
            # Remove the India Status button
            self.remove_item(self.india_status_button)
    
    def is_admin(self, member: discord.Member) -> bool:
        """Check if user has admin/staff/moderator role"""
        admin_role_id = cfg('ROLE_ADMIN_ID')
        staff_role_id = cfg('ROLE_STAFF_ID')
        mod_role_id = cfg('ROLE_MODERATOR_ID')
        
        member_role_ids = [role.id for role in member.roles]
        
        if admin_role_id and int(admin_role_id) in member_role_ids:
            return True
        if staff_role_id and int(staff_role_id) in member_role_ids:
            return True
        if mod_role_id and int(mod_role_id) in member_role_ids:
            return True
        
        return False
    
    @discord.ui.button(label="Edit IGN", style=discord.ButtonStyle.primary, emoji="✏️")
    async def edit_ign_button(self, interaction: discord.Interaction, button: Button):
        # Allow profile owner or admins
        if interaction.user.id != self.user.id and not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Only the profile owner or admins can edit this!", ephemeral=True)
            return
        
        is_admin_edit = interaction.user.id != self.user.id
        helper_name = interaction.user.display_name if is_admin_edit else None
        
        dm_target = "your" if not is_admin_edit else f"{self.user.mention}'s"
        await interaction.response.send_message(
            f"📩 Check {dm_target} DMs! I've sent a message to update the IGN.",
            ephemeral=True
        )
        
        try:
            dm_channel = await self.user.create_dm()
            prefix = f"🛡️ **Admin {helper_name} is helping you edit your profile**\n\n" if is_admin_edit else ""
            await dm_channel.send(
                f"{prefix}✏️ **Edit IGN**\n\n"
                f"Current IGN: **{self.player_data.get('ign', 'Unknown')}**\n\n"
                "Please reply with your new IGN (you have 5 minutes):"
            )
            
            def check(m):
                return m.author.id == self.user.id and m.channel.id == dm_channel.id
            
            msg = await self.bot.wait_for('message', timeout=300, check=check)
            new_ign = msg.content.strip()
            
            # Update IGN
            await db.update_player_ign(self.user.id, new_ign)
            await dm_channel.send(f"✅ IGN updated to **{new_ign}**!\nRun `/profile` to see the changes.")
            
        except asyncio.TimeoutError:
            try:
                await dm_channel.send("❌ Timed out. Please click the button again to retry.")
            except:
                pass
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I couldn't send you a DM! Please enable DMs from server members.",
                ephemeral=True
            )
        except Exception as e:
            try:
                await dm_channel.send(f"❌ Error updating IGN: {e}")
            except:
                pass
    
    @discord.ui.button(label="Edit Player ID", style=discord.ButtonStyle.primary, emoji="🆔")
    async def edit_id_button(self, interaction: discord.Interaction, button: Button):
        # Allow profile owner or admins
        if interaction.user.id != self.user.id and not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Only the profile owner or admins can edit this!", ephemeral=True)
            return
        
        is_admin_edit = interaction.user.id != self.user.id
        helper_name = interaction.user.display_name if is_admin_edit else None
        
        dm_target = "your" if not is_admin_edit else f"{self.user.mention}'s"
        await interaction.response.send_message(
            f"📩 Check {dm_target} DMs! I've sent a message to update the Player ID.",
            ephemeral=True
        )
        
        try:
            dm_channel = await self.user.create_dm()
            prefix = f"🛡️ **Admin {helper_name} is helping you edit your profile**\n\n" if is_admin_edit else ""
            await dm_channel.send(
                f"{prefix}🆔 **Edit Player ID**\n\n"
                f"Current Player ID: **{self.player_data.get('player_id', 'Unknown')}**\n\n"
                "Please reply with your new Player ID (numbers only, you have 5 minutes):"
            )
            
            def check(m):
                return m.author.id == self.user.id and m.channel.id == dm_channel.id
            
            msg = await self.bot.wait_for('message', timeout=300, check=check)
            
            try:
                new_id = int(msg.content.strip())
                await db.update_player_id(self.user.id, new_id)
                await dm_channel.send(f"✅ Player ID updated to **{new_id}**!\nRun `/profile` to see the changes.")
            except ValueError:
                await dm_channel.send("❌ Player ID must be a number! Please try again.")
                
        except asyncio.TimeoutError:
            try:
                await dm_channel.send("❌ Timed out. Please click the button again to retry.")
            except:
                pass
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I couldn't send you a DM! Please enable DMs from server members.",
                ephemeral=True
            )
        except Exception as e:
            try:
                await dm_channel.send(f"❌ Error updating Player ID: {e}")
            except:
                pass
    
    @discord.ui.button(label="Change Region", style=discord.ButtonStyle.primary, emoji="🌍")
    async def change_region_button(self, interaction: discord.Interaction, button: Button):
        # Allow profile owner or admins
        if interaction.user.id != self.user.id and not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Only the profile owner or admins can edit this!", ephemeral=True)
            return
        
        is_admin_edit = interaction.user.id != self.user.id
        helper_name = interaction.user.display_name if is_admin_edit else None
        
        try:
            dm_channel = await self.user.create_dm()
            view = RegionSelectView(self.user, self.guild)
            
            dm_target = "your" if not is_admin_edit else f"{self.user.mention}'s"
            await interaction.response.send_message(
                f"📩 Check {dm_target} DMs! I've sent a message to update the region.",
                ephemeral=True
            )
            
            prefix = f"🛡️ **Admin {helper_name} is helping you edit your profile**\n\n" if is_admin_edit else ""
            await dm_channel.send(
                f"{prefix}🌍 **Change Region**\n\n"
                f"Current Region: **{self.player_data.get('region', 'Unknown')}**\n\n"
                "Please select your new region:",
                view=view
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I couldn't send you a DM! Please enable DMs from server members.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error: {e}",
                ephemeral=True
            )
    
    @discord.ui.button(label="India Status", style=discord.ButtonStyle.primary, emoji="🇮🇳")
    async def india_status_button(self, interaction: discord.Interaction, button: Button):
        # Allow profile owner or admins
        if interaction.user.id != self.user.id and not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ Only the profile owner or admins can edit this!", ephemeral=True)
            return
        
        is_admin_edit = interaction.user.id != self.user.id
        helper_name = interaction.user.display_name if is_admin_edit else None
        
        try:
            dm_channel = await self.user.create_dm()
            current_status = self.player_data.get('is_india', False)
            view = IndiaToggleView(self.user, self.guild, current_status)
            
            dm_target = "your" if not is_admin_edit else f"{self.user.mention}'s"
            await interaction.response.send_message(
                f"📩 Check {dm_target} DMs! I've sent a message to update the India status.",
                ephemeral=True
            )
            
            current_text = "from India" if current_status else "not from India"
            prefix = f"🛡️ **Admin {helper_name} is helping you edit your profile**\n\n" if is_admin_edit else ""
            await dm_channel.send(
                f"{prefix}🇮🇳 **Update India Status**\n\n"
                f"You are currently marked as **{current_text}**.\n\n"
                "Please select your correct status:",
                view=view
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I couldn't send you a DM! Please enable DMs from server members.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error: {e}",
                ephemeral=True
            )

class Profiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    def calculate_kdr(self, kills: int, deaths: int) -> float:
        """Calculate K/D ratio"""
        return kills / deaths if deaths > 0 else kills

    def calculate_winrate(self, wins: int, matches: int) -> float:
        """Calculate win rate percentage"""
        return (wins / matches * 100) if matches > 0 else 0

    def calculate_points(self, stats: dict) -> int:
        """Calculate total points"""
        kill_points = stats.get('kills', 0) * 100
        death_penalty = stats.get('deaths', 0) * -50
        win_points = stats.get('wins', 0) * 500
        mvp_points = stats.get('mvps', 0) * 200
        participation = stats.get('matches_played', 0) * 100
        
        return kill_points + death_penalty + win_points + mvp_points + participation

    async def create_profile_image(self, member: discord.Member, player_data: dict, stats: dict):
        """Create and save profile image"""
        # Load template and font
        template_path = Path("imports/profile/Profile.jpg")
        font_path = Path("imports/font/Poppins-Bold.ttf")
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template image not found at {template_path}")
        if not font_path.exists():
            raise FileNotFoundError(f"Font file not found at {font_path}")
        
        # Open template image
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)
        
        # Add Discord avatar
        try:
            # Get avatar URL - fallback to default if none set
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            async with aiohttp.ClientSession() as session:
                async with session.get(str(avatar_url)) as response:
                    avatar_data = await response.read()
                    avatar = Image.open(BytesIO(avatar_data))
                    
                    # Resize avatar to desired size
                    avatar_size = (250, 250)  # Same size as in test
                    avatar = avatar.resize(avatar_size)
                    
                    # Create circular mask
                    mask = Image.new('L', avatar_size, 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse((0, 0, avatar_size[0], avatar_size[1]), fill=255)
                    
                    # Apply circular mask
                    output = Image.new('RGBA', avatar_size, (0, 0, 0, 0))
                    output.paste(avatar, (0, 0))
                    output.putalpha(mask)
                    
                    # Paste avatar onto profile image
                    avatar_pos = (819, 232)  # Same position as in test
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
        
        # Calculate derived stats
        kdr = self.calculate_kdr(stats.get('kills', 0), stats.get('deaths', 0))
        winrate = self.calculate_winrate(stats.get('wins', 0), stats.get('matches_played', 0))
        points = self.calculate_points(stats)
        
        # Prepare data
        profile_data = {
            "discord": str(member),
            "created_at": player_data.get('created_at', datetime.now()).strftime('%Y-%m-%d'),
            "discord_id": str(member.id),
            "in_game_id": str(player_data.get('ign', 'Unknown')),  # Using IGN instead of player_id
            "rank": "Unranked",  # Add rank if you have it in your database
            "region": player_data.get('region', 'Unknown'),
            "points": str(points),
            "kills": str(stats.get('kills', 0)),
            "kdr": f"{kdr:.2f}",
            "deaths": str(stats.get('deaths', 0)),
            "winrate": f"{winrate:.1f}%",
            "matches": str(stats.get('matches_played', 0)),
            "mvp": str(stats.get('mvps', 0))
        }
        
        # Position for each field (using the new template coordinates)
        positions = {
            "discord": (930, 534),
            "created_at": (988, 578),
            "discord_id": (828, 617),
            "in_game_id": (1455, 185),
            "rank": (1380, 252),
            "region": (1403, 325),
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
            text = str(profile_data[field])  # Just display the value without the field label
            # Get the appropriate font for this field
            field_size = font_sizes[field]
            current_font = fonts[field_size]
            draw.text(pos, text, fill="#ffff23", font=current_font)  # Bright yellow color
        
        # ===== ADD MATCH HISTORY SECTION =====
        try:
            from services import db
            match_history = await db.get_player_match_history(member.id, limit=10)
            
            if match_history:
                # Match history configuration (same as test script)
                MATCH_START_Y = 780
                MATCH_ROW_HEIGHT = 90
                
                # Colors
                WIN_COLOR = "#00ff00"
                LOSS_COLOR = "#ff0000"
                KDA_COLOR = "#ffff23"
                
                # Background padding
                SCORE_BG_PADDING = 3
                KDA_BG_PADDING = 3
                MAP_NAME_BG_PADDING = 3
                
                # Configuration for each match (same as test script)
                match_configs = [
                    # FIRST
                    {
                        'map_x': 300, 'map_y_offset': 49, 'map_width': 290, 'map_height': 150,
                        'agent_x': 320, 'agent_y_offset': 68, 'agent_size': 85,
                        'score_x': 475, 'score_y_offset': 150, 'score_font_size': 24,
                        'kda_x': 329, 'kda_y_offset': 165, 'kda_font_size': 20,
                        'map_name_x': 450, 'map_name_y_offset': 95, 'map_name_font_size': 30
                    },
                    # SECOND
                    {
                        'map_x': 635, 'map_y_offset': -42, 'map_width': 290, 'map_height': 150,
                        'agent_x': 655, 'agent_y_offset': -20, 'agent_size': 85,
                        'score_x': 800, 'score_y_offset': 55, 'score_font_size': 24,
                        'kda_x': 660, 'kda_y_offset': 73, 'kda_font_size': 20,
                        'map_name_x': 795, 'map_name_y_offset': 5, 'map_name_font_size': 30
                    },
                    # THIRD
                    {
                        'map_x': 970, 'map_y_offset': -131, 'map_width': 290, 'map_height': 150,
                        'agent_x': 1000, 'agent_y_offset': -110, 'agent_size': 85,
                        'score_x': 1140, 'score_y_offset': -39, 'score_font_size': 24,
                        'kda_x': 1002, 'kda_y_offset': -18, 'kda_font_size': 20,
                        'map_name_x': 1120, 'map_name_y_offset': -90, 'map_name_font_size': 30
                    },
                    # FOURTH
                    {
                        'map_x': 1310, 'map_y_offset': -219, 'map_width': 290, 'map_height': 150,
                        'agent_x': 1330, 'agent_y_offset': -200, 'agent_size': 85,
                        'score_x': 1490, 'score_y_offset': -130, 'score_font_size': 24,
                        'kda_x': 1335, 'kda_y_offset': -105, 'kda_font_size': 20,
                        'map_name_x': 1465, 'map_name_y_offset': -180, 'map_name_font_size': 30
                    },
                    # FIFTH through TENTH (using standard layout)
                    {
                        'map_x': 100, 'map_y_offset': 0, 'map_width': 100, 'map_height': 60,
                        'agent_x': 220, 'agent_y_offset': -10, 'agent_size': 80,
                        'score_x': 320, 'score_y_offset': 20, 'score_font_size': 24,
                        'kda_x': 470, 'kda_y_offset': 20, 'kda_font_size': 24,
                        'map_name_x': 650, 'map_name_y_offset': 20, 'map_name_font_size': 24
                    },
                    {
                        'map_x': 100, 'map_y_offset': 0, 'map_width': 100, 'map_height': 60,
                        'agent_x': 220, 'agent_y_offset': -10, 'agent_size': 80,
                        'score_x': 320, 'score_y_offset': 20, 'score_font_size': 24,
                        'kda_x': 470, 'kda_y_offset': 20, 'kda_font_size': 24,
                        'map_name_x': 650, 'map_name_y_offset': 20, 'map_name_font_size': 24
                    },
                    {
                        'map_x': 100, 'map_y_offset': 0, 'map_width': 100, 'map_height': 60,
                        'agent_x': 220, 'agent_y_offset': -10, 'agent_size': 80,
                        'score_x': 320, 'score_y_offset': 20, 'score_font_size': 24,
                        'kda_x': 470, 'kda_y_offset': 20, 'kda_font_size': 24,
                        'map_name_x': 650, 'map_name_y_offset': 20, 'map_name_font_size': 24
                    },
                    {
                        'map_x': 100, 'map_y_offset': 0, 'map_width': 100, 'map_height': 60,
                        'agent_x': 220, 'agent_y_offset': -10, 'agent_size': 80,
                        'score_x': 320, 'score_y_offset': 20, 'score_font_size': 24,
                        'kda_x': 470, 'kda_y_offset': 20, 'kda_font_size': 24,
                        'map_name_x': 650, 'map_name_y_offset': 20, 'map_name_font_size': 24
                    },
                    {
                        'map_x': 100, 'map_y_offset': 0, 'map_width': 100, 'map_height': 60,
                        'agent_x': 220, 'agent_y_offset': -10, 'agent_size': 80,
                        'score_x': 320, 'score_y_offset': 20, 'score_font_size': 24,
                        'kda_x': 470, 'kda_y_offset': 20, 'kda_font_size': 24,
                        'map_name_x': 650, 'map_name_y_offset': 20, 'map_name_font_size': 24
                    },
                    {
                        'map_x': 100, 'map_y_offset': 0, 'map_width': 100, 'map_height': 60,
                        'agent_x': 220, 'agent_y_offset': -10, 'agent_size': 80,
                        'score_x': 320, 'score_y_offset': 20, 'score_font_size': 24,
                        'kda_x': 470, 'kda_y_offset': 20, 'kda_font_size': 24,
                        'map_name_x': 650, 'map_name_y_offset': 20, 'map_name_font_size': 24
                    }
                ]
                
                for i, match_data in enumerate(match_history[:10]):  # Limit to 10 matches
                    if i >= len(match_configs):
                        break
                        
                    config = match_configs[i]
                    y_pos = MATCH_START_Y + (i * MATCH_ROW_HEIGHT)
                    
                    # Parse players JSON if it's a string
                    players = match_data.get('players', [])
                    if isinstance(players, str):
                        players = json.loads(players)
                    
                    # Get player's data from this match
                    player_match_data = None
                    for player in players:
                        if player.get('player_id') == member.id:
                            player_match_data = player
                            break
                    
                    if not player_match_data:
                        continue
                    
                    # Create fonts for this match
                    score_font = ImageFont.truetype(str(font_path), config['score_font_size'])
                    kda_font = ImageFont.truetype(str(font_path), config['kda_font_size'])
                    map_name_font = ImageFont.truetype(str(font_path), config['map_name_font_size'])
                    
                    # 1. Add Map Image
                    try:
                        map_name = match_data.get('map_name', 'Unknown')
                        map_img_path = Path(f"imports/maps/{map_name}.jpg")
                        if map_img_path.exists():
                            map_img = Image.open(map_img_path)
                            map_img = map_img.resize((config['map_width'], config['map_height']), Image.Resampling.LANCZOS)
                            map_y = y_pos + config['map_y_offset']
                            img.paste(map_img, (config['map_x'], map_y))
                        else:
                            # Draw placeholder if map image not found
                            map_y = y_pos + config['map_y_offset']
                            draw.rectangle([config['map_x'], map_y, 
                                          config['map_x'] + config['map_width'], 
                                          map_y + config['map_height']], 
                                         outline="white", width=2)
                    except Exception as e:
                        print(f"Error loading map image: {e}")
                    
                    # 2. Add Agent Icon
                    try:
                        agent_name = player_match_data.get('agent', 'Unknown')
                        agent_folder = Path("imports/agents images")
                        agent_file = None
                        
                        # Try to find agent file (case-insensitive search)
                        if agent_folder.exists():
                            for file in agent_folder.iterdir():
                                if agent_name.lower() in file.stem.lower():
                                    agent_file = file
                                    break
                        
                        if agent_file and agent_file.exists():
                            agent_img = Image.open(agent_file)
                            agent_size = config['agent_size']
                            agent_img = agent_img.resize((agent_size, agent_size), Image.Resampling.LANCZOS)
                            
                            # Make circular agent icon
                            mask = Image.new('L', (agent_size, agent_size), 0)
                            mask_draw = ImageDraw.Draw(mask)
                            mask_draw.ellipse((0, 0, agent_size, agent_size), fill=255)
                            
                            output = Image.new('RGBA', (agent_size, agent_size), (0, 0, 0, 0))
                            output.paste(agent_img, (0, 0))
                            output.putalpha(mask)
                            
                            agent_y = y_pos + config['agent_y_offset']
                            img.paste(output, (config['agent_x'], agent_y), output)
                    except Exception as e:
                        print(f"Error loading agent image: {e}")
                    
                    # 3. Add Team Score with black background
                    team1_score = match_data.get('team1_score', 0)
                    team2_score = match_data.get('team2_score', 0)
                    player_team = player_match_data.get('team', 'A')
                    
                    # Determine if player won
                    if player_team == 'A':
                        our_score = team1_score
                        their_score = team2_score
                    else:
                        our_score = team2_score
                        their_score = team1_score
                    
                    won = our_score > their_score
                    team_score_text = f"{our_score}-{their_score}"
                    score_color = WIN_COLOR if won else LOSS_COLOR
                    
                    score_y = y_pos + config['score_y_offset']
                    score_bbox = draw.textbbox((config['score_x'], score_y), team_score_text, font=score_font)
                    draw.rectangle([score_bbox[0] - SCORE_BG_PADDING, score_bbox[1] - SCORE_BG_PADDING,
                                   score_bbox[2] + SCORE_BG_PADDING, score_bbox[3] + SCORE_BG_PADDING],
                                  fill="black")
                    draw.text((config['score_x'], score_y), team_score_text, 
                             fill=score_color, font=score_font)
                    
                    # 4. Add Player K/D/A with black background
                    kills = player_match_data.get('kills', 0)
                    deaths = player_match_data.get('deaths', 0)
                    assists = player_match_data.get('assists', 0)
                    kda_text = f"{kills}/{deaths}/{assists}"
                    
                    kda_y = y_pos + config['kda_y_offset']
                    kda_bbox = draw.textbbox((config['kda_x'], kda_y), kda_text, font=kda_font)
                    draw.rectangle([kda_bbox[0] - KDA_BG_PADDING, kda_bbox[1] - KDA_BG_PADDING,
                                   kda_bbox[2] + KDA_BG_PADDING, kda_bbox[3] + KDA_BG_PADDING],
                                  fill="black")
                    draw.text((config['kda_x'], kda_y), kda_text, 
                             fill=KDA_COLOR, font=kda_font)
                    
                    # 5. Add Map Name with black background
                    map_name_y = y_pos + config['map_name_y_offset']
                    map_name_bbox = draw.textbbox((config['map_name_x'], map_name_y), map_name, font=map_name_font)
                    draw.rectangle([map_name_bbox[0] - MAP_NAME_BG_PADDING, map_name_bbox[1] - MAP_NAME_BG_PADDING,
                                   map_name_bbox[2] + MAP_NAME_BG_PADDING, map_name_bbox[3] + MAP_NAME_BG_PADDING],
                                  fill="black")
                    draw.text((config['map_name_x'], map_name_y), map_name, 
                             fill=score_color, font=map_name_font)
        
        except Exception as e:
            print(f"Error adding match history to profile: {e}")
            import traceback
            traceback.print_exc()
            # Continue without match history if there's an error
        
        # Convert image to bytes for Discord upload
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer

    @app_commands.command(name="profile", description="Display your tournament profile")
    @app_commands.describe(user="The player to look up (optional, defaults to yourself)")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer()
        
        from services import db
        
        target_user = user or interaction.user
        
        # Get player data from database
        player_data = await db.get_player(target_user.id)
        if not player_data:
            await interaction.followup.send(
                f"{target_user.mention} is not registered for the tournament!",
                ephemeral=True
            )
            return
        
        # Get player stats
        stats = await db.get_player_stats(target_user.id)
        if not stats:
            stats = {}  # Use empty dict if no stats found
        
        # Build a Discord embed with profile fields
        try:
            # Calculate derived stats
            kdr = self.calculate_kdr(stats.get('kills', 0), stats.get('deaths', 0))
            winrate = self.calculate_winrate(stats.get('wins', 0), stats.get('matches_played', 0))
            points = self.calculate_points(stats)

            profile_embed = discord.Embed(
                title=f"🎮 Tournament Profile for {target_user.display_name}",
                color=0x5865F2,
                timestamp=datetime.utcnow()
            )

            # Thumbnail: user's avatar
            try:
                thumb = target_user.avatar.url if target_user.avatar else target_user.default_avatar.url
                profile_embed.set_thumbnail(url=thumb)
            except Exception:
                pass

            # Add core fields
            profile_embed.add_field(name="IGN", value=player_data.get('ign', 'Unknown'), inline=True)
            profile_embed.add_field(name="Player ID", value=player_data.get('player_id', 'Unknown'), inline=True)
            profile_embed.add_field(name="Region", value=player_data.get('region', 'Unknown'), inline=True)
            profile_embed.add_field(name="Points", value=str(points), inline=True)
            profile_embed.add_field(name="K/D", value=f"{kdr:.2f}", inline=True)
            profile_embed.add_field(name="Win Rate", value=f"{winrate:.1f}%", inline=True)
            profile_embed.add_field(name="Kills / Deaths", value=f"{stats.get('kills',0)} / {stats.get('deaths',0)}", inline=True)
            profile_embed.add_field(name="Matches Played", value=str(stats.get('matches_played', 0)), inline=True)
            profile_embed.add_field(name="MVPs", value=str(stats.get('mvps', 0)), inline=True)
            
            # Show India status only for APAC regions
            player_region = player_data.get('region', '').upper()
            if player_region in ['AP', 'APAC', 'KR', 'JP']:
                is_india = player_data.get('is_india', False)
                india_status = "🇮🇳 Yes" if is_india else "❌ No"
                profile_embed.add_field(name="From India?", value=india_status, inline=True)

            # Show edit buttons if viewing own profile OR if admin viewing any profile
            is_own_profile = target_user.id == interaction.user.id
            
            # Check if user is admin
            is_admin = False
            if isinstance(interaction.user, discord.Member):
                admin_role_id = cfg('ROLE_ADMIN_ID')
                staff_role_id = cfg('ROLE_STAFF_ID')
                mod_role_id = cfg('ROLE_MODERATOR_ID')
                
                member_role_ids = [role.id for role in interaction.user.roles]
                
                if admin_role_id and int(admin_role_id) in member_role_ids:
                    is_admin = True
                elif staff_role_id and int(staff_role_id) in member_role_ids:
                    is_admin = True
                elif mod_role_id and int(mod_role_id) in member_role_ids:
                    is_admin = True
            
            if is_own_profile or is_admin:
                view = ProfileEditView(player_data, target_user, self.bot, interaction.guild, interaction.user)
                if is_admin and not is_own_profile:
                    profile_embed.set_footer(text="🛡️ Admin Mode: You can edit this profile to help the user")
                await interaction.followup.send(embed=profile_embed, view=view)
            else:
                await interaction.followup.send(embed=profile_embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error building profile: {e}", ephemeral=True)

    @app_commands.command(name="team-profile", description="Displays a team's profile")
    @app_commands.describe(name="The name or tag of the team to look up (optional, defaults to your team)")
    async def team_profile(self, interaction: discord.Interaction, name: str = None):
        """Displays a team's profile with Discord UI."""
        try:
            await interaction.response.defer()
            
            target_team = None
            
            # If no name provided, try to get user's team
            if not name:
                # Check if user is a captain
                target_team = await db.get_team_by_captain(interaction.user.id)
                
                # If not captain, check if user is a member
                if not target_team:
                    target_team = await db.get_player_team(interaction.user.id)
                
                if not target_team:
                    await interaction.followup.send(
                        "❌ You are not part of any team!\n"
                        "To view another team's profile, use `/team-profile [team name]`",
                        ephemeral=True
                    )
                    return
            else:
                # Try to get team by name first
                target_team = await db.get_team_by_name(name)
                
                # If not found by name, try searching all teams by tag
                if not target_team:
                    all_teams = await db.get_all_teams()
                    team_id_match = None
                    for team in all_teams:
                        if team.get('tag', '').lower() == name.lower():
                            team_id_match = team['id']
                            break
                    
                    # If found by tag, get the full team data with members
                    if team_id_match:
                        target_team = await db.get_team_by_id(team_id_match)
            
            if not target_team:
                if name:
                    await interaction.followup.send(f"❌ Team `{name}` not found. Try using the full team name or tag.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Could not find team.", ephemeral=True)
                return

            # Get captain info
            try:
                captain = await self.bot.fetch_user(target_team['captain_id'])
                captain_name = f"{captain.display_name} ({captain.mention})"
            except discord.NotFound:
                captain_name = "Unknown Captain"

            # Extract member data
            members_data = target_team.get('members', [])
            if isinstance(members_data, str):
                members_data = json.loads(members_data)
            
            # Build roster list with player stats
            roster_lines = []
            for member in members_data:
                if isinstance(member, dict):
                    ign = member.get('ign', 'Unknown')
                    kills = member.get('kills', 0)
                    deaths = member.get('deaths', 0)
                    kd = f"{kills / deaths:.2f}" if deaths > 0 else f"{kills}"
                    roster_lines.append(f"• **{ign}** - {kills}K / {deaths}D (KD: {kd})")
            
            roster_str = "\n".join(roster_lines) if roster_lines else "No members found."

            # Calculate stats
            wins = target_team.get('wins', 0)
            losses = target_team.get('losses', 0)
            total_matches = wins + losses
            win_rate = (wins / total_matches * 100) if total_matches > 0 else 0

            # Create main embed
            embed = discord.Embed(
                title=f"🏆 {target_team['name']}",
                description=f"**Tag:** `{target_team['tag']}`\n**Captain:** {captain_name}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )

            # Set thumbnail - use team logo or default Valorant logo
            logo_url = target_team.get("logo_url")
            if logo_url and logo_url.startswith('http'):
                embed.set_thumbnail(url=logo_url)
            else:
                # Use Valorant logo as default
                embed.set_thumbnail(url="https://i.imgur.com/dJriIOC.png")

            # Get and display staff (managers and coach)
            staff = await db.get_team_staff(target_team['id'])
            staff_lines = []
            
            if staff.get('manager_1_id'):
                try:
                    manager1 = await self.bot.fetch_user(staff['manager_1_id'])
                    staff_lines.append(f"👔 **Manager 1:** {manager1.mention}")
                except:
                    staff_lines.append(f"👔 **Manager 1:** <@{staff['manager_1_id']}>")
            
            if staff.get('manager_2_id'):
                try:
                    manager2 = await self.bot.fetch_user(staff['manager_2_id'])
                    staff_lines.append(f"👔 **Manager 2:** {manager2.mention}")
                except:
                    staff_lines.append(f"👔 **Manager 2:** <@{staff['manager_2_id']}>")
            
            if staff.get('coach_id'):
                try:
                    coach = await self.bot.fetch_user(staff['coach_id'])
                    staff_lines.append(f"🎓 **Coach:** {coach.mention}")
                except:
                    staff_lines.append(f"🎓 **Coach:** <@{staff['coach_id']}>")
            
            if staff_lines:
                embed.add_field(name="📋 Staff", value="\n".join(staff_lines), inline=False)

            # Add roster
            embed.add_field(name=f"👥 Roster ({len(roster_lines)} players)", value=roster_str[:1024], inline=False)
            
            # Add stats
            stats_text = f"**Wins:** {wins}\n**Losses:** {losses}\n**Total Matches:** {total_matches}\n**Win Rate:** {win_rate:.1f}%"
            embed.add_field(name="📊 Team Stats", value=stats_text, inline=True)
            
            # Add region
            region = target_team.get('region', 'Unknown').upper()
            embed.add_field(name="🌍 Region", value=region, inline=True)
            
            # Load and display recent matches
            recent_matches_str = "No matches played yet."
            try:
                team_stats = await db.get_team_stats(target_team['id'])
                
                if team_stats and team_stats.get('recent_matches'):
                    recent_matches = team_stats['recent_matches']
                    
                    if isinstance(recent_matches, str):
                        recent_matches = json.loads(recent_matches)
                    
                    if recent_matches and len(recent_matches) > 0:
                        match_lines = []
                        for match in recent_matches[:5]:
                            opponent_name = match.get('opponent_name', 'Unknown')
                            score_for = match.get('score_for', 0)
                            score_against = match.get('score_against', 0)
                            won = match.get('won', False)
                            
                            result_icon = "✅" if won else "❌"
                            match_lines.append(f"{result_icon} vs **{opponent_name}** - {score_for}:{score_against}")
                        
                        recent_matches_str = "\n".join(match_lines)
            except Exception as e:
                print(f"Error loading recent matches: {e}")
            
            embed.add_field(name="🎮 Recent Matches", value=recent_matches_str[:1024], inline=False)
            
            # Add footer
            created_at = target_team.get('created_at')
            if created_at:
                embed.set_footer(text=f"Team ID: {target_team['id']} • Created")
                embed.timestamp = created_at
            else:
                embed.set_footer(text=f"Team ID: {target_team['id']}")

            # Check if user is captain or manager to show management buttons
            user_id = interaction.user.id
            is_captain = user_id == target_team['captain_id']
            is_manager = user_id in [staff.get('manager_1_id'), staff.get('manager_2_id')]
            
            # Debug logging
            print(f"DEBUG: User {user_id}, Captain: {target_team['captain_id']}, is_captain: {is_captain}")
            print(f"DEBUG: Manager 1: {staff.get('manager_1_id')}, Manager 2: {staff.get('manager_2_id')}, is_manager: {is_manager}")
            
            if is_captain or is_manager:
                # Add management buttons (ephemeral so only captain/manager can see them)
                view = TeamManagementView(target_team, staff, is_captain, is_manager)
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error building team profile: {e}", ephemeral=True)
            print(f"Team profile error: {e}")
            import traceback
            traceback.print_exc()

class TeamManagementView(discord.ui.View):
    """Interactive team management view with all controls."""
    
    def __init__(self, team_data: dict, staff_data: dict, is_captain: bool, is_manager: bool):
        super().__init__(timeout=300)
        self.team_data = team_data
        self.staff_data = staff_data
        self.is_captain = is_captain
        self.is_manager = is_manager
        self.authorized_user_id = None  # Will be set on first interaction
        
        # Disable captain-only buttons for managers
        if not is_captain:
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id in ['transfer_captain', 'add_coach', 'remove_coach', 'add_manager', 'remove_manager']:
                    item.disabled = True
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user is authorized to use these buttons."""
        # Set authorized user on first interaction
        if self.authorized_user_id is None:
            self.authorized_user_id = interaction.user.id
        
        # Check if this is the authorized user (captain or manager)
        user_id = interaction.user.id
        is_captain = user_id == self.team_data['captain_id']
        is_manager = user_id in [self.staff_data.get('manager_1_id'), self.staff_data.get('manager_2_id')]
        
        if not (is_captain or is_manager):
            await interaction.response.send_message(
                "❌ Only the team captain or managers can use these controls!",
                ephemeral=True
            )
            return False
        
        return True
    
    @discord.ui.button(label="✏️ Edit Team", style=discord.ButtonStyle.primary, custom_id="edit_team", row=0)
    async def edit_team_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Edit team details (name, tag, logo)."""
        await interaction.response.send_message(
            "✏️ **Edit Team Details**\n\n"
            "What would you like to edit?\n"
            "• **Name** - Change team name\n"
            "• **Tag** - Change team tag\n"
            "• **Logo** - Change team logo\n\n"
            "Reply with: `name`, `tag`, or `logo`\n\n"
            "*Waiting for response... (30 seconds)*",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
            choice = msg.content.lower().strip()
            
            try:
                await msg.delete()
            except:
                pass
            
            if choice == "name":
                await interaction.followup.send(
                    "✏️ **Change Team Name**\n\n"
                    f"Current name: **{self.team_data['name']}**\n\n"
                    "Please type the new team name:\n\n"
                    "*Waiting for response... (60 seconds)*",
                    ephemeral=True
                )
                
                name_msg = await interaction.client.wait_for('message', timeout=60.0, check=check)
                new_name = name_msg.content.strip()
                
                try:
                    await name_msg.delete()
                except:
                    pass
                
                # Check if name is already taken
                existing = await db.get_team_by_name(new_name)
                if existing and existing['id'] != self.team_data['id']:
                    await interaction.followup.send(f"❌ Team name `{new_name}` is already taken!", ephemeral=True)
                    return
                
                # Update team name
                await db.update_team_name(self.team_data['id'], new_name)
                await interaction.followup.send(f"✅ Team name updated to **{new_name}**!", ephemeral=True)
                
            elif choice == "tag":
                await interaction.followup.send(
                    "✏️ **Change Team Tag**\n\n"
                    f"Current tag: **{self.team_data['tag']}**\n\n"
                    "Please type the new team tag (2-5 characters):\n\n"
                    "*Waiting for response... (30 seconds)*",
                    ephemeral=True
                )
                
                tag_msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
                new_tag = tag_msg.content.strip().upper()
                
                try:
                    await tag_msg.delete()
                except:
                    pass
                
                if len(new_tag) < 2 or len(new_tag) > 5:
                    await interaction.followup.send("❌ Tag must be 2-5 characters!", ephemeral=True)
                    return
                
                # Check if tag is already taken
                all_teams = await db.get_all_teams()
                tag_taken = any(t.get('tag', '').upper() == new_tag and t['id'] != self.team_data['id'] for t in all_teams)
                
                if tag_taken:
                    await interaction.followup.send(f"❌ Team tag `{new_tag}` is already taken!", ephemeral=True)
                    return
                
                # Update team tag
                await db.update_team_tag(self.team_data['id'], new_tag)
                await interaction.followup.send(f"✅ Team tag updated to **{new_tag}**!", ephemeral=True)
                
            elif choice == "logo":
                await interaction.followup.send(
                    "✏️ **Change Team Logo**\n\n"
                    "Please upload an image or provide an image URL:\n\n"
                    "*Waiting for response... (60 seconds)*",
                    ephemeral=True
                )
                
                logo_msg = await interaction.client.wait_for('message', timeout=60.0, check=check)
                
                logo_url = None
                if logo_msg.attachments:
                    attachment = logo_msg.attachments[0]
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        logo_url = attachment.url
                elif logo_msg.content.startswith(('http://', 'https://')):
                    logo_url = logo_msg.content.strip()
                
                try:
                    await logo_msg.delete()
                except:
                    pass
                
                if not logo_url:
                    await interaction.followup.send("❌ Please provide a valid image URL or attachment!", ephemeral=True)
                    return
                
                # Update team logo
                await db.update_team_logo(self.team_data['id'], logo_url)
                await interaction.followup.send(f"✅ Team logo updated!", ephemeral=True)
            else:
                await interaction.followup.send("❌ Invalid choice. Please reply with `name`, `tag`, or `logo`.", ephemeral=True)
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Request timed out. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="➕ Add Player", style=discord.ButtonStyle.success, custom_id="add_player", row=0)
    async def add_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add a player to the team."""
        await interaction.response.send_message(
            "➕ **Invite Player to Team**\n\n"
            "Please mention the user you want to invite to the team.\n"
            "*Example: @username*\n\n"
            "Waiting for your mention... (30 seconds)",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
            
            if not msg.mentions:
                await interaction.followup.send("❌ Please mention a user.", ephemeral=True)
                return
            
            user = msg.mentions[0]
            
            # Check if user is registered
            player = await db.get_player(user.id)
            if not player:
                await interaction.followup.send(f"❌ {user.mention} must be registered as a player first!", ephemeral=True)
                return
            
            # Check if user is already on a team
            existing_team = await db.get_player_team(user.id)
            if existing_team:
                await interaction.followup.send(
                    f"❌ {user.mention} is already on team **{existing_team['name']}**. "
                    f"They must leave that team first.",
                    ephemeral=True
                )
                return
            
            # Send invite to player via DM
            try:
                dm_channel = await user.create_dm()
                
                invite_view = discord.ui.View(timeout=300)
                
                accept_button = discord.ui.Button(
                    label="✅ Accept Invite",
                    style=discord.ButtonStyle.success,
                    custom_id="accept_invite"
                )
                
                decline_button = discord.ui.Button(
                    label="❌ Decline Invite",
                    style=discord.ButtonStyle.danger,
                    custom_id="decline_invite"
                )
                
                async def accept_callback(button_interaction: discord.Interaction):
                    if button_interaction.user.id != user.id:
                        await button_interaction.response.send_message("❌ This invite is not for you!", ephemeral=True)
                        return
                    
                    await button_interaction.response.defer()
                    
                    # Add player to team
                    try:
                        await db.add_team_member(self.team_data['id'], user.id)
                        
                        # Update player's team in leaderboard
                        await db.update_player_team(user.id, self.team_data['id'])
                        
                        await button_interaction.followup.send(
                            f"✅ **You've joined {self.team_data['name']}!**\n"
                            f"Team Tag: [{self.team_data['tag']}]\n"
                            f"Captain: <@{self.team_data['captain_id']}>\n\n"
                            f"Use `/team-profile` to view your team!"
                        )
                        
                        # Notify the captain/manager
                        try:
                            inviter = await interaction.client.fetch_user(interaction.user.id)
                            inviter_dm = await inviter.create_dm()
                            await inviter_dm.send(
                                f"✅ **{user.mention} ({player['ign']}) has accepted your invite!**\n"
                                f"They are now part of **{self.team_data['name']}**."
                            )
                        except:
                            pass
                        
                        # Log to admin logs
                        log_channel_id = cfg("log_channel_id")
                        if log_channel_id:
                            try:
                                log_channel = interaction.client.get_channel(int(log_channel_id))
                                if log_channel:
                                    log_embed = discord.Embed(
                                        title="👥 Player Joined Team",
                                        color=discord.Color.green(),
                                        timestamp=discord.utils.utcnow()
                                    )
                                    log_embed.add_field(name="Player", value=f"{user.mention} ({player['ign']})", inline=False)
                                    log_embed.add_field(name="Team", value=f"{self.team_data['name']} [{self.team_data['tag']}]", inline=False)
                                    log_embed.add_field(name="Invited by", value=f"{interaction.user.mention}", inline=False)
                                    log_embed.set_footer(text=f"Player ID: {user.id} | Team ID: {self.team_data['id']}")
                                    await log_channel.send(embed=log_embed)
                            except:
                                pass
                        
                        # Disable buttons
                        for item in invite_view.children:
                            item.disabled = True
                        await button_interaction.message.edit(view=invite_view)
                        
                    except Exception as e:
                        await button_interaction.followup.send(f"❌ Error joining team: {e}")
                
                async def decline_callback(button_interaction: discord.Interaction):
                    if button_interaction.user.id != user.id:
                        await button_interaction.response.send_message("❌ This invite is not for you!", ephemeral=True)
                        return
                    
                    await button_interaction.response.defer()
                    
                    await button_interaction.followup.send(
                        f"❌ You've declined the invite to **{self.team_data['name']}**."
                    )
                    
                    # Notify the captain/manager
                    try:
                        inviter = await interaction.client.fetch_user(interaction.user.id)
                        inviter_dm = await inviter.create_dm()
                        await inviter_dm.send(
                            f"❌ **{user.mention} ({player['ign']}) has declined your invite.**\n"
                            f"Team: **{self.team_data['name']}**"
                        )
                    except:
                        pass
                    
                    # Disable buttons
                    for item in invite_view.children:
                        item.disabled = True
                    await button_interaction.message.edit(view=invite_view)
                
                accept_button.callback = accept_callback
                decline_button.callback = decline_callback
                
                invite_view.add_item(accept_button)
                invite_view.add_item(decline_button)
                
                invite_embed = discord.Embed(
                    title="🎮 Team Invite",
                    description=f"**{interaction.user.display_name}** has invited you to join their team!",
                    color=discord.Color.blue()
                )
                invite_embed.add_field(name="Team Name", value=self.team_data['name'], inline=True)
                invite_embed.add_field(name="Team Tag", value=f"[{self.team_data['tag']}]", inline=True)
                invite_embed.add_field(name="Region", value=self.team_data['region'].upper(), inline=True)
                invite_embed.add_field(name="Captain", value=f"<@{self.team_data['captain_id']}>", inline=False)
                invite_embed.set_footer(text="This invite expires in 5 minutes")
                
                await dm_channel.send(embed=invite_embed, view=invite_view)
                
                await interaction.followup.send(
                    f"✅ Invite sent to {user.mention}!\n"
                    f"They will receive a DM to accept or decline.",
                    ephemeral=True
                )
                
            except discord.Forbidden:
                await interaction.followup.send(
                    f"❌ Could not send DM to {user.mention}. They may have DMs disabled.\n"
                    f"Ask them to enable DMs from server members and try again.",
                    ephemeral=True
                )
                return
            
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Request timed out. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="➖ Remove Player", style=discord.ButtonStyle.danger, custom_id="remove_player", row=0)
    async def remove_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Remove a player from the team."""
        # Get current members
        members_data = self.team_data.get('members', [])
        if isinstance(members_data, str):
            members_data = json.loads(members_data)
        
        if not members_data:
            await interaction.response.send_message("❌ No players in the team to remove.", ephemeral=True)
            return
        
        # Create member list
        member_list = ""
        for member in members_data:
            if isinstance(member, dict):
                member_list += f"• <@{member.get('discord_id')}> ({member.get('ign', 'Unknown')})\n"
        
        await interaction.response.send_message(
            "➖ **Remove Player from Team**\n\n"
            f"Current Members:\n{member_list}\n"
            "Please mention the user you want to remove from the team.\n\n"
            "*Waiting for mention... (30 seconds)*",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
            
            if not msg.mentions:
                await interaction.followup.send("❌ Please mention a user to remove.", ephemeral=True)
                return
            
            target_user = msg.mentions[0]
            
            # Check if user is on the team
            is_member = any(m.get('discord_id') == target_user.id for m in members_data if isinstance(m, dict))
            
            if not is_member:
                await interaction.followup.send(f"❌ {target_user.mention} is not on this team.", ephemeral=True)
                return
            
            # Can't remove captain
            if target_user.id == self.team_data['captain_id']:
                await interaction.followup.send("❌ Cannot remove the team captain. Transfer captainship first.", ephemeral=True)
                return
            
            # Get player info before removal
            player = await db.get_player(target_user.id)
            player_ign = player.get('ign', 'Unknown') if player else 'Unknown'
            
            # Remove player from team
            await db.remove_player_from_team(self.team_data['id'], target_user.id)
            
            # Send DM to removed player
            try:
                dm_channel = await target_user.create_dm()
                removal_embed = discord.Embed(
                    title="❌ Removed from Team",
                    description=f"You have been removed from **{self.team_data['name']}** [{self.team_data['tag']}]",
                    color=discord.Color.red()
                )
                removal_embed.add_field(name="Removed by", value=interaction.user.mention, inline=False)
                removal_embed.set_footer(text="Contact the team captain if you have questions")
                await dm_channel.send(embed=removal_embed)
            except discord.Forbidden:
                # Player has DMs disabled, skip DM
                pass
            
            # Log to admin logs
            log_channel_id = cfg("log_channel_id")
            if log_channel_id:
                try:
                    log_channel = interaction.client.get_channel(int(log_channel_id))
                    if log_channel:
                        log_embed = discord.Embed(
                            title="👥 Player Removed from Team",
                            color=discord.Color.orange(),
                            timestamp=discord.utils.utcnow()
                        )
                        log_embed.add_field(name="Player", value=f"{target_user.mention} ({player_ign})", inline=False)
                        log_embed.add_field(name="Team", value=f"{self.team_data['name']} [{self.team_data['tag']}]", inline=False)
                        log_embed.add_field(name="Removed by", value=f"{interaction.user.mention}", inline=False)
                        log_embed.set_footer(text=f"Player ID: {target_user.id} | Team ID: {self.team_data['id']}")
                        await log_channel.send(embed=log_embed)
                except:
                    pass
            
            await interaction.followup.send(f"✅ Successfully removed {target_user.mention} from the team!", ephemeral=True)
            
            # Delete user's message
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Request timed out. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="👑 Transfer Captain", style=discord.ButtonStyle.primary, custom_id="transfer_captain", row=1)
    async def transfer_captain_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Transfer captainship to another team member."""
        # Get current members (excluding captain)
        members_data = self.team_data.get('members', [])
        if isinstance(members_data, str):
            members_data = json.loads(members_data)
        
        eligible_members = [m for m in members_data if isinstance(m, dict) and m.get('discord_id') != self.team_data['captain_id']]
        
        if not eligible_members:
            await interaction.response.send_message(
                "❌ No eligible team members to transfer captainship to.\n"
                "You need at least one other player on the team.",
                ephemeral=True
            )
            return
        
        # Show list of eligible members
        member_list = ""
        for member in eligible_members:
            member_list += f"• <@{member.get('discord_id')}> ({member.get('ign', 'Unknown')})\n"
        
        await interaction.response.send_message(
            "👑 **Transfer Captainship**\n\n"
            "⚠️ **WARNING:** This action will make you a regular team member!\n\n"
            f"Eligible Members:\n{member_list}\n"
            "Please mention the user you want to make the new captain.\n\n"
            "*Waiting for mention... (30 seconds)*",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
            
            if not msg.mentions:
                await interaction.followup.send("❌ Please mention a user.", ephemeral=True)
                return
            
            new_captain = msg.mentions[0]
            
            # Check if new captain is on the team
            is_member = any(m.get('discord_id') == new_captain.id for m in members_data if isinstance(m, dict))
            
            if not is_member:
                await interaction.followup.send(
                    f"❌ **{new_captain.mention} is not in your team!**\n"
                    f"You can only transfer captainship to players who are already on **{self.team_data['name']}**.",
                    ephemeral=True
                )
                return
            
            # Transfer captainship
            await db.transfer_team_captainship(self.team_data['id'], new_captain.id)
            
            await interaction.followup.send(f"✅ Successfully transferred captainship to {new_captain.mention}!", ephemeral=True)
            
            # Delete user's message
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Request timed out. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="🎓 Add Coach", style=discord.ButtonStyle.success, custom_id="add_coach", row=1)
    async def add_coach_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add a coach to the team."""
        # Check if coach slot is taken
        if self.staff_data.get('coach_id'):
            await interaction.response.send_message("❌ Team already has a coach. Remove the current coach first.", ephemeral=True)
            return
        
        await interaction.response.send_message(
            "🎓 **Add Coach**\n\n"
            "Please mention the user you want to add as coach.\n\n"
            "*Waiting for mention... (30 seconds)*",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
            
            if not msg.mentions:
                await interaction.followup.send("❌ Please mention a user to add as coach.", ephemeral=True)
                return
            
            coach_user = msg.mentions[0]
            
            # Add coach
            await db.add_team_coach(self.team_data['id'], coach_user.id)
            
            await interaction.followup.send(f"✅ Successfully added {coach_user.mention} as team coach!", ephemeral=True)
            
            # Delete user's message
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Request timed out. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="👔 Add Manager", style=discord.ButtonStyle.success, custom_id="add_manager", row=1)
    async def add_manager_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add a manager to the team (max 2)."""
        # Check manager slots
        manager_1 = self.staff_data.get('manager_1_id')
        manager_2 = self.staff_data.get('manager_2_id')
        
        if manager_1 and manager_2:
            await interaction.response.send_message("❌ Team already has 2 managers (maximum limit).", ephemeral=True)
            return
        
        await interaction.response.send_message(
            "👔 **Add Manager**\n\n"
            f"Available slots: {2 - sum([1 for m in [manager_1, manager_2] if m])} / 2\n\n"
            "Please mention the user you want to add as manager.\n\n"
            "*Waiting for mention... (30 seconds)*",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
            
            if not msg.mentions:
                await interaction.followup.send("❌ Please mention a user to add as manager.", ephemeral=True)
                return
            
            manager_user = msg.mentions[0]
            
            # Add manager to first available slot
            if not manager_1:
                await db.add_team_manager(self.team_data['id'], manager_user.id, slot=1)
            else:
                await db.add_team_manager(self.team_data['id'], manager_user.id, slot=2)
            
            await interaction.followup.send(f"✅ Successfully added {manager_user.mention} as team manager!", ephemeral=True)
            
            # Delete user's message
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Request timed out. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="❌ Remove Coach", style=discord.ButtonStyle.danger, custom_id="remove_coach", row=2)
    async def remove_coach_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Remove the team coach."""
        if not self.staff_data.get('coach_id'):
            await interaction.response.send_message("❌ Team doesn't have a coach.", ephemeral=True)
            return
        
        coach_id = self.staff_data['coach_id']
        
        await interaction.response.send_message(
            f"❌ **Remove Coach**\n\n"
            f"Are you sure you want to remove <@{coach_id}> as coach?\n\n"
            "Reply with `yes` to confirm or `no` to cancel.\n\n"
            "*Waiting for response... (15 seconds)*",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id and m.content.lower() in ['yes', 'no']
        
        try:
            msg = await interaction.client.wait_for('message', timeout=15.0, check=check)
            
            if msg.content.lower() == 'yes':
                await db.remove_team_coach(self.team_data['id'])
                await interaction.followup.send(f"✅ Successfully removed <@{coach_id}> as team coach!", ephemeral=True)
            else:
                await interaction.followup.send("❌ Coach removal cancelled.", ephemeral=True)
            
            # Delete user's message
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Request timed out. Coach removal cancelled.", ephemeral=True)
    
    @discord.ui.button(label="❌ Remove Manager", style=discord.ButtonStyle.danger, custom_id="remove_manager", row=2)
    async def remove_manager_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Remove a team manager."""
        manager_1 = self.staff_data.get('manager_1_id')
        manager_2 = self.staff_data.get('manager_2_id')
        
        if not manager_1 and not manager_2:
            await interaction.response.send_message("❌ Team doesn't have any managers.", ephemeral=True)
            return
        
        # Show list of managers
        manager_list = ""
        if manager_1:
            manager_list += f"1. <@{manager_1}>\n"
        if manager_2:
            manager_list += f"2. <@{manager_2}>\n"
        
        await interaction.response.send_message(
            "❌ **Remove Manager**\n\n"
            f"Current Managers:\n{manager_list}\n"
            "Please mention the manager you want to remove.\n\n"
            "*Waiting for mention... (30 seconds)*",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
            
            if not msg.mentions:
                await interaction.followup.send("❌ Please mention a manager to remove.", ephemeral=True)
                return
            
            target_user = msg.mentions[0]
            
            # Check which slot
            if target_user.id == manager_1:
                await db.remove_team_manager(self.team_data['id'], slot=1)
                await interaction.followup.send(f"✅ Successfully removed {target_user.mention} as manager!", ephemeral=True)
            elif target_user.id == manager_2:
                await db.remove_team_manager(self.team_data['id'], slot=2)
                await interaction.followup.send(f"✅ Successfully removed {target_user.mention} as manager!", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ {target_user.mention} is not a manager of this team.", ephemeral=True)
            
            # Delete user's message
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Request timed out. Please try again.", ephemeral=True)

class TeamProfileEditView(discord.ui.View):
    """Edit view for team profile - Captain and Managers only."""
    
    def __init__(self, team_data: dict, staff_data: dict, is_captain: bool):
        super().__init__(timeout=300)  # 5 minute timeout
        self.team_data = team_data
        self.staff_data = staff_data
        self.is_captain = is_captain
        
        # If not captain, disable captain-only buttons
        if not is_captain:
            # Managers can't add/remove other managers or coach
            for item in self.children:
                if item.custom_id in ['add_manager', 'remove_manager', 'add_coach', 'remove_coach']:
                    item.disabled = True
    
    @discord.ui.button(label="📋 Manage Staff", style=discord.ButtonStyle.primary, custom_id="manage_staff")
    async def manage_staff_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open staff management menu."""
        if not self.is_captain:
            await interaction.response.send_message("❌ Only the captain can manage staff.", ephemeral=True)
            return
        
        # Create staff management view
        staff_view = StaffManagementView(self.team_data, self.staff_data)
        
        embed = discord.Embed(
            title=f"📋 Staff Management - {self.team_data['name']}",
            description="Select an action below:",
            color=discord.Color.blue()
        )
        
        # Show current staff
        staff_info = ""
        if self.staff_data.get('manager_1_id'):
            staff_info += f"👔 **Manager 1:** <@{self.staff_data['manager_1_id']}>\n"
        else:
            staff_info += "👔 **Manager 1:** *Empty*\n"
            
        if self.staff_data.get('manager_2_id'):
            staff_info += f"👔 **Manager 2:** <@{self.staff_data['manager_2_id']}>\n"
        else:
            staff_info += "👔 **Manager 2:** *Empty*\n"
            
        if self.staff_data.get('coach_id'):
            staff_info += f"🎓 **Coach:** <@{self.staff_data['coach_id']}>"
        else:
            staff_info += "🎓 **Coach:** *Empty*"
        
        embed.add_field(name="Current Staff", value=staff_info, inline=False)
        
        await interaction.response.send_message(embed=embed, view=staff_view, ephemeral=True)
    
    @discord.ui.button(label="� Manage Players", style=discord.ButtonStyle.primary, custom_id="manage_players")
    async def manage_players_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open player management menu."""
        # Create player management view
        player_view = PlayerManagementView(self.team_data)
        
        embed = discord.Embed(
            title=f"👥 Player Management - {self.team_data['name']}",
            description="Add or remove players from your roster:",
            color=discord.Color.blue()
        )
        
        # Show current roster
        members_data = self.team_data.get('members', [])
        if isinstance(members_data, str):
            import json
            members_data = json.loads(members_data)
        
        roster_text = ""
        if members_data:
            for member in members_data:
                if isinstance(member, dict):
                    roster_text += f"• <@{member.get('discord_id')}> ({member.get('ign', 'Unknown')})\n"
        else:
            roster_text = "*No players in roster*"
        
        embed.add_field(name="Current Roster", value=roster_text, inline=False)
        
        await interaction.response.send_message(embed=embed, view=player_view, ephemeral=True)
    
    @discord.ui.button(label="�🖼️ Change Logo", style=discord.ButtonStyle.secondary, custom_id="change_logo")
    async def change_logo_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Change team logo."""
        await interaction.response.send_message(
            "🖼️ **Change Team Logo**\n\n"
            "Please upload an image or provide an image URL in this channel.\n"
            "The logo will be updated once you send it.\n\n"
            "*Waiting for your image... (60 seconds)*",
            ephemeral=True
        )
        
        # Wait for image
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=60.0, check=check)
            
            logo_url = None
            
            # Check for attachment
            if msg.attachments:
                attachment = msg.attachments[0]
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    logo_url = attachment.url
                else:
                    await interaction.followup.send("❌ Please upload a valid image file.", ephemeral=True)
                    return
            
            # Check for URL
            elif msg.content.startswith('http://') or msg.content.startswith('https://'):
                if any(msg.content.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    logo_url = msg.content.strip()
                else:
                    await interaction.followup.send("❌ Invalid image URL format.", ephemeral=True)
                    return
            else:
                await interaction.followup.send("❌ Please provide an image attachment or URL.", ephemeral=True)
                return
            
            # Update logo
            await db.update_team_logo(self.team_data['id'], logo_url)
            
            # Update leaderboard
            await db.update_team_leaderboard(
                self.team_data['id'],
                self.team_data['name'],
                self.team_data['tag'],
                self.team_data['region'],
                logo_url
            )
            
            await interaction.followup.send(
                f"✅ Team logo updated successfully!\n*Preview: {logo_url}*",
                ephemeral=True
            )
            
            # Delete the user's message
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Logo change timed out. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="👑 Transfer Captainship", style=discord.ButtonStyle.danger, custom_id="transfer_captain", row=1)
    async def transfer_captain_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Transfer captainship to another team member."""
        if not self.is_captain:
            await interaction.response.send_message("❌ Only the captain can transfer captainship.", ephemeral=True)
            return
        
        # Get current members (excluding captain)
        members_data = self.team_data.get('members', [])
        if isinstance(members_data, str):
            import json
            members_data = json.loads(members_data)
        
        # Filter out current captain
        eligible_members = [m for m in members_data if isinstance(m, dict) and m.get('discord_id') != self.team_data['captain_id']]
        
        if not eligible_members:
            await interaction.response.send_message(
                "❌ No eligible team members to transfer captainship to.\n"
                "You need at least one other player on the team.",
                ephemeral=True
            )
            return
        
        # Show list of eligible members
        member_list = ""
        for member in eligible_members:
            member_list += f"• <@{member.get('discord_id')}> ({member.get('ign', 'Unknown')})\n"
        
        await interaction.response.send_message(
            "👑 **Transfer Captainship**\n\n"
            "⚠️ **WARNING:** This action will make you a regular team member and cannot be undone!\n\n"
            f"Eligible Members:\n{member_list}\n"
            "Please mention the user you want to make the new captain:\n\n"
            "Waiting for your response... (30 seconds)",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
            
            if not msg.mentions:
                await interaction.followup.send("❌ Please mention a user.", ephemeral=True)
                return
            
            new_captain = msg.mentions[0]
            
            # Verify the mentioned user is an eligible member
            is_eligible = any(m.get('discord_id') == new_captain.id for m in eligible_members if isinstance(m, dict))
            
            if not is_eligible:
                await interaction.followup.send(
                    f"❌ {new_captain.mention} is not an eligible team member.\n"
                    "They must be on your team and not already the captain.",
                    ephemeral=True
                )
                return
            
            # Transfer captainship
            await db.transfer_team_captain(self.team_data['id'], new_captain.id)
            
            await interaction.followup.send(
                f"✅ **Captainship Transferred!**\n\n"
                f"{new_captain.mention} is now the captain of **{self.team_data['name']}**!\n"
                f"You are now a regular team member.",
                ephemeral=True
            )
            
            # Send notification to new captain
            try:
                await new_captain.send(
                    f"👑 **You are now the captain of {self.team_data['name']}!**\n\n"
                    f"<@{interaction.user.id}> has transferred captainship to you.\n"
                    f"You now have full control over team management."
                )
            except:
                pass  # If DMs are disabled
            
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timed out. Captainship transfer cancelled.", ephemeral=True)
    
    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger, custom_id="close", row=1)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the edit menu."""
        await interaction.message.delete()

class StaffManagementView(discord.ui.View):
    """Staff management sub-menu."""
    
    def __init__(self, team_data: dict, staff_data: dict):
        super().__init__(timeout=300)
        self.team_data = team_data
        self.staff_data = staff_data
    
    @discord.ui.button(label="➕ Add Manager", style=discord.ButtonStyle.success, custom_id="add_manager")
    async def add_manager_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add a manager."""
        # Check available slots
        slot = None
        if not self.staff_data.get('manager_1_id'):
            slot = 1
        elif not self.staff_data.get('manager_2_id'):
            slot = 2
        
        if not slot:
            await interaction.response.send_message("❌ Both manager slots are full!", ephemeral=True)
            return
        
        await interaction.response.send_message(
            f"➕ **Add Manager to Slot {slot}**\n\n"
            "Please mention the user you want to add as manager.\n"
            "*Example: @username*\n\n"
            "Waiting for your response... (30 seconds)",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
            
            if not msg.mentions:
                await interaction.followup.send("❌ Please mention a user.", ephemeral=True)
                return
            
            user = msg.mentions[0]
            
            # Check if user is registered
            player = await db.get_player(user.id)
            if not player:
                await interaction.followup.send(f"❌ {user.mention} must be registered as a player first!", ephemeral=True)
                return
            
            # Check if user is captain
            if user.id == self.team_data['captain_id']:
                await interaction.followup.send("❌ The captain cannot be a manager.", ephemeral=True)
                return
            
            # Check if already manager or coach
            if user.id == self.staff_data.get('manager_1_id') or user.id == self.staff_data.get('manager_2_id'):
                await interaction.followup.send(f"❌ {user.mention} is already a manager.", ephemeral=True)
                return
            
            if user.id == self.staff_data.get('coach_id'):
                await interaction.followup.send(f"❌ {user.mention} is the coach. They cannot be both.", ephemeral=True)
                return
            
            # Add manager
            success = await db.add_team_manager(self.team_data['id'], user.id, slot)
            
            if success:
                self.staff_data[f'manager_{slot}_id'] = user.id
                await interaction.followup.send(
                    f"✅ {user.mention} has been added as Manager {slot}!",
                    ephemeral=True
                )
            else:
                await interaction.followup.send("❌ Failed to add manager.", ephemeral=True)
            
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timed out. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="➖ Remove Manager", style=discord.ButtonStyle.danger, custom_id="remove_manager")
    async def remove_manager_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Remove a manager."""
        # Check if there are any managers
        if not self.staff_data.get('manager_1_id') and not self.staff_data.get('manager_2_id'):
            await interaction.response.send_message("❌ No managers to remove.", ephemeral=True)
            return
        
        manager_list = ""
        if self.staff_data.get('manager_1_id'):
            manager_list += f"1️⃣ **Manager 1:** <@{self.staff_data['manager_1_id']}>\n"
        if self.staff_data.get('manager_2_id'):
            manager_list += f"2️⃣ **Manager 2:** <@{self.staff_data['manager_2_id']}>\n"
        
        await interaction.response.send_message(
            f"➖ **Remove Manager**\n\n"
            f"Current Managers:\n{manager_list}\n"
            "Type the slot number (1 or 2) to remove:\n\n"
            "Waiting for your response... (30 seconds)",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
            
            slot = msg.content.strip()
            if slot not in ['1', '2']:
                await interaction.followup.send("❌ Please enter 1 or 2.", ephemeral=True)
                return
            
            slot_num = int(slot)
            manager_id = self.staff_data.get(f'manager_{slot_num}_id')
            
            if not manager_id:
                await interaction.followup.send(f"❌ Manager slot {slot_num} is already empty.", ephemeral=True)
                return
            
            # Remove manager
            await db.remove_team_manager(self.team_data['id'], slot=slot_num)
            self.staff_data[f'manager_{slot_num}_id'] = None
            
            await interaction.followup.send(
                f"✅ Manager {slot_num} has been removed!",
                ephemeral=True
            )
            
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timed out. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="➕ Add Coach", style=discord.ButtonStyle.success, custom_id="add_coach")
    async def add_coach_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add a coach."""
        if self.staff_data.get('coach_id'):
            await interaction.response.send_message("❌ Coach slot is already filled!", ephemeral=True)
            return
        
        await interaction.response.send_message(
            "➕ **Add Coach**\n\n"
            "Please mention the user you want to add as coach.\n"
            "*Example: @username*\n\n"
            "Waiting for your response... (30 seconds)",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
            
            if not msg.mentions:
                await interaction.followup.send("❌ Please mention a user.", ephemeral=True)
                return
            
            user = msg.mentions[0]
            
            # Check if user is registered
            player = await db.get_player(user.id)
            if not player:
                await interaction.followup.send(f"❌ {user.mention} must be registered as a player first!", ephemeral=True)
                return
            
            # Check if user is captain
            if user.id == self.team_data['captain_id']:
                await interaction.followup.send("❌ The captain cannot be a coach.", ephemeral=True)
                return
            
            # Check if already manager
            if user.id == self.staff_data.get('manager_1_id') or user.id == self.staff_data.get('manager_2_id'):
                await interaction.followup.send(f"❌ {user.mention} is a manager. They cannot be both.", ephemeral=True)
                return
            
            # Add coach
            success = await db.add_team_coach(self.team_data['id'], user.id)
            
            if success:
                self.staff_data['coach_id'] = user.id
                await interaction.followup.send(
                    f"✅ {user.mention} has been added as Coach!",
                    ephemeral=True
                )
            else:
                await interaction.followup.send("❌ Failed to add coach.", ephemeral=True)
            
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timed out. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="➖ Remove Coach", style=discord.ButtonStyle.danger, custom_id="remove_coach")
    async def remove_coach_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Remove the coach."""
        if not self.staff_data.get('coach_id'):
            await interaction.response.send_message("❌ No coach to remove.", ephemeral=True)
            return
        
        coach_id = self.staff_data['coach_id']
        
        # Remove coach
        await db.remove_team_coach(self.team_data['id'])
        self.staff_data['coach_id'] = None
        
        await interaction.response.send_message(
            f"✅ <@{coach_id}> has been removed as coach!",
            ephemeral=True
        )

class PlayerManagementView(discord.ui.View):
    """Player management sub-menu."""
    
    def __init__(self, team_data: dict):
        super().__init__(timeout=300)
        self.team_data = team_data
    
    @discord.ui.button(label="➕ Add Player", style=discord.ButtonStyle.success, custom_id="add_player")
    async def add_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add a player to the team."""
        await interaction.response.send_message(
            "➕ **Add Player to Roster**\n\n"
            "Please mention the user you want to invite to the team.\n"
            "*Example: @username*\n\n"
            "Waiting for your response... (30 seconds)",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
            
            if not msg.mentions:
                await interaction.followup.send("❌ Please mention a user.", ephemeral=True)
                return
            
            user = msg.mentions[0]
            
            # Check if user is registered
            player = await db.get_player(user.id)
            if not player:
                await interaction.followup.send(f"❌ {user.mention} must be registered as a player first!", ephemeral=True)
                return
            
            # Check if user is already on a team
            existing_team = await db.get_player_team(user.id)
            if existing_team:
                await interaction.followup.send(
                    f"❌ {user.mention} is already on team **{existing_team['name']}**. "
                    f"They must leave that team first.",
                    ephemeral=True
                )
                return
            
            # Send invite to player via DM
            try:
                dm_channel = await user.create_dm()
                
                invite_view = discord.ui.View(timeout=300)
                
                accept_button = discord.ui.Button(
                    label="✅ Accept Invite",
                    style=discord.ButtonStyle.success,
                    custom_id="accept_invite"
                )
                
                decline_button = discord.ui.Button(
                    label="❌ Decline Invite",
                    style=discord.ButtonStyle.danger,
                    custom_id="decline_invite"
                )
                
                async def accept_callback(button_interaction: discord.Interaction):
                    if button_interaction.user.id != user.id:
                        await button_interaction.response.send_message("❌ This invite is not for you!", ephemeral=True)
                        return
                    
                    await button_interaction.response.defer()
                    
                    # Add player to team
                    try:
                        await db.add_team_member(self.team_data['id'], user.id)
                        
                        # Update player's team in leaderboard
                        await db.update_player_team(user.id, self.team_data['id'])
                        
                        await button_interaction.followup.send(
                            f"✅ **You've joined {self.team_data['name']}!**\n"
                            f"Team Tag: [{self.team_data['tag']}]\n"
                            f"Captain: <@{self.team_data['captain_id']}>\n\n"
                            f"Use `/team-profile` to view your team!"
                        )
                        
                        # Notify the captain
                        try:
                            captain = await interaction.client.fetch_user(self.team_data['captain_id'])
                            captain_dm = await captain.create_dm()
                            await captain_dm.send(
                                f"✅ **{user.mention} ({player['ign']}) has accepted your invite!**\n"
                                f"They are now part of **{self.team_data['name']}**."
                            )
                        except:
                            pass
                        
                        # Disable buttons
                        for item in invite_view.children:
                            item.disabled = True
                        await button_interaction.message.edit(view=invite_view)
                        
                    except Exception as e:
                        await button_interaction.followup.send(f"❌ Error joining team: {e}")
                
                async def decline_callback(button_interaction: discord.Interaction):
                    if button_interaction.user.id != user.id:
                        await button_interaction.response.send_message("❌ This invite is not for you!", ephemeral=True)
                        return
                    
                    await button_interaction.response.defer()
                    
                    await button_interaction.followup.send(
                        f"❌ You've declined the invite to **{self.team_data['name']}**."
                    )
                    
                    # Notify the captain
                    try:
                        captain = await interaction.client.fetch_user(self.team_data['captain_id'])
                        captain_dm = await captain.create_dm()
                        await captain_dm.send(
                            f"❌ **{user.mention} ({player['ign']}) has declined your invite.**\n"
                            f"Team: **{self.team_data['name']}**"
                        )
                    except:
                        pass
                    
                    # Disable buttons
                    for item in invite_view.children:
                        item.disabled = True
                    await button_interaction.message.edit(view=invite_view)
                
                accept_button.callback = accept_callback
                decline_button.callback = decline_callback
                
                invite_view.add_item(accept_button)
                invite_view.add_item(decline_button)
                
                invite_embed = discord.Embed(
                    title="🎮 Team Invite",
                    description=f"**{interaction.user.display_name}** has invited you to join their team!",
                    color=discord.Color.blue()
                )
                invite_embed.add_field(name="Team Name", value=self.team_data['name'], inline=True)
                invite_embed.add_field(name="Team Tag", value=f"[{self.team_data['tag']}]", inline=True)
                invite_embed.add_field(name="Region", value=self.team_data['region'].upper(), inline=True)
                invite_embed.add_field(name="Captain", value=f"<@{self.team_data['captain_id']}>", inline=False)
                invite_embed.set_footer(text="This invite expires in 5 minutes")
                
                await dm_channel.send(embed=invite_embed, view=invite_view)
                
                await interaction.followup.send(
                    f"✅ Invite sent to {user.mention}!\n"
                    f"They will receive a DM to accept or decline.",
                    ephemeral=True
                )
                
            except discord.Forbidden:
                await interaction.followup.send(
                    f"❌ Could not send DM to {user.mention}. They may have DMs disabled.\n"
                    f"Ask them to enable DMs from server members and try again.",
                    ephemeral=True
                )
                return
            
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timed out. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="➖ Remove Player", style=discord.ButtonStyle.danger, custom_id="remove_player")
    async def remove_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Remove a player from the team."""
        # Get current members
        members_data = self.team_data.get('members', [])
        if isinstance(members_data, str):
            import json
            members_data = json.loads(members_data)
        
        # Filter out captain from removable players
        removable_players = [m for m in members_data if isinstance(m, dict) and m.get('discord_id') != self.team_data['captain_id']]
        
        if not removable_players:
            await interaction.response.send_message("❌ No players to remove (captain cannot be removed this way).", ephemeral=True)
            return
        
        player_list = ""
        for member in removable_players:
            player_list += f"• <@{member.get('discord_id')}> ({member.get('ign', 'Unknown')})\n"
        
        await interaction.response.send_message(
            f"➖ **Remove Player**\n\n"
            f"Current Players:\n{player_list}\n"
            "Please mention the user you want to remove:\n\n"
            "Waiting for your response... (30 seconds)",
            ephemeral=True
        )
        
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id
        
        try:
            msg = await interaction.client.wait_for('message', timeout=30.0, check=check)
            
            if not msg.mentions:
                await interaction.followup.send("❌ Please mention a user.", ephemeral=True)
                return
            
            user = msg.mentions[0]
            
            # Check if user is captain
            if user.id == self.team_data['captain_id']:
                await interaction.followup.send("❌ Cannot remove the captain. Use `/disband` to disband the team.", ephemeral=True)
                return
            
            # Check if user is actually on the team
            is_member = any(m.get('discord_id') == user.id for m in members_data if isinstance(m, dict))
            if not is_member:
                await interaction.followup.send(f"❌ {user.mention} is not on this team.", ephemeral=True)
                return
            
            # Remove player from team
            await db.remove_team_member(self.team_data['id'], user.id)
            
            # Update player's team in leaderboard (set to None)
            await db.update_player_team(user.id, None)
            
            await interaction.followup.send(
                f"✅ {user.mention} has been removed from **{self.team_data['name']}**!",
                ephemeral=True
            )
            
            try:
                await msg.delete()
            except:
                pass
                
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timed out. Please try again.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Profiles(bot))