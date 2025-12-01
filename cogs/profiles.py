import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os
import json
import aiohttp
import asyncio
from io import BytesIO
from datetime import datetime
from services import db

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
        
        # Build a Discord embed with profile fields instead of sending an image
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
            profile_embed.add_field(name="Points", value=str(points), inline=True)
            profile_embed.add_field(name="K/D", value=f"{kdr:.2f}", inline=True)
            profile_embed.add_field(name="Win Rate", value=f"{winrate:.1f}%", inline=True)
            profile_embed.add_field(name="Kills / Deaths", value=f"{stats.get('kills',0)} / {stats.get('deaths',0)}", inline=True)
            profile_embed.add_field(name="Matches Played", value=str(stats.get('matches_played', 0)), inline=True)
            profile_embed.add_field(name="MVPs", value=str(stats.get('mvps', 0)), inline=True)
            profile_embed.add_field(name="Discord ID", value=str(target_user.id), inline=True)

            # Footer and timestamp already set; send embed
            await interaction.followup.send(embed=profile_embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error building profile: {e}", ephemeral=True)

    @app_commands.command(name="team-profile", description="Displays a team's profile")
    @app_commands.describe(name="The name or tag of the team to look up")
    async def team_profile(self, interaction: discord.Interaction, name: str):
        """Displays a team's profile with Discord UI."""
        try:
            await interaction.response.defer()
            
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
                await interaction.followup.send(f"❌ Team `{name}` not found. Try using the full team name or tag.", ephemeral=True)
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

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error building team profile: {e}", ephemeral=True)
            print(f"Team profile error: {e}")
            import traceback
            traceback.print_exc()

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
            
            # Add player to team
            await db.add_team_member(self.team_data['id'], user.id)
            
            # Update player's team in leaderboard
            await db.update_player_team(user.id, self.team_data['id'])
            
            await interaction.followup.send(
                f"✅ {user.mention} has been added to the team!\n"
                f"They are now part of **{self.team_data['name']}** [{self.team_data['tag']}]",
                ephemeral=True
            )
            
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