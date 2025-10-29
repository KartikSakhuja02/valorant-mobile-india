import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import View, Button, Select
import json
import os
from pathlib import Path
from datetime import datetime
from services import db
from services.leaderboard_generator import generate_leaderboard_image, calculate_total_pages, generate_player_leaderboard_image, calculate_player_pages


class ImageLeaderboardView(View):
    """Interactive view for image-based leaderboard with pagination"""
    def __init__(self, teams_data: list, region: str, page: int, total_pages: int):
        super().__init__(timeout=300)  # 5 minute timeout
        self.teams_data = teams_data
        self.region = region
        self.page = page
        self.total_pages = total_pages
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page"""
        self.clear_items()
        
        # Add region selector dropdown
        region_select = Select(
            placeholder=f"Current: {self.region.upper()}",
            options=[
                discord.SelectOption(label="Global", value="global", emoji="🌍"),
                discord.SelectOption(label="APAC", value="apac", emoji="🌏"),
                discord.SelectOption(label="EMEA", value="emea", emoji="🌍"),
                discord.SelectOption(label="Americas", value="americas", emoji="🌎"),
                discord.SelectOption(label="India", value="india", emoji="🇮🇳"),
            ]
        )
        region_select.callback = self.change_region
        self.add_item(region_select)
        
        # ⏮ First Page button (double left arrow)
        first_button = Button(
            emoji="⏮",
            style=discord.ButtonStyle.secondary,
            disabled=(self.page == 0)
        )
        first_button.callback = self.first_page
        self.add_item(first_button)
        
        # ◀ Previous button (left arrow)
        prev_button = Button(
            emoji="◀",
            style=discord.ButtonStyle.secondary,
            disabled=(self.page == 0)
        )
        prev_button.callback = self.previous_page
        self.add_item(prev_button)
        
        # 🔄 Refresh button (center)
        refresh_button = Button(
            emoji="🔄",
            style=discord.ButtonStyle.success,
            disabled=False
        )
        refresh_button.callback = self.refresh_leaderboard
        self.add_item(refresh_button)
        
        # ▶ Next button (right arrow)
        next_button = Button(
            emoji="▶",
            style=discord.ButtonStyle.secondary,
            disabled=(self.page >= self.total_pages - 1)
        )
        next_button.callback = self.next_page
        self.add_item(next_button)
        
        # ⏭ Last Page button (double right arrow)
        last_button = Button(
            emoji="⏭",
            style=discord.ButtonStyle.secondary,
            disabled=(self.page >= self.total_pages - 1)
        )
        last_button.callback = self.last_page
        self.add_item(last_button)
    
    async def first_page(self, interaction: discord.Interaction):
        """Go to first page"""
        self.page = 0
        await self.update_image(interaction)
    
    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        if self.page > 0:
            self.page -= 1
            await self.update_image(interaction)
    
    async def next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        if self.page < self.total_pages - 1:
            self.page += 1
            await self.update_image(interaction)
    
    async def last_page(self, interaction: discord.Interaction):
        """Go to last page"""
        self.page = self.total_pages - 1
        await self.update_image(interaction)
    
    async def change_region(self, interaction: discord.Interaction):
        """Change the leaderboard region"""
        await interaction.response.defer()
        
        try:
            # Get selected region from dropdown
            selected_region = interaction.data['values'][0]
            self.region = selected_region
            self.page = 0  # Reset to first page
            
            # Fetch data for new region
            from services import db
            self.teams_data = await db.get_team_leaderboard(self.region, limit=None)
            
            # Recalculate total pages
            from services.leaderboard_generator import calculate_total_pages
            self.total_pages = calculate_total_pages(len(self.teams_data))
            
            # Generate image for new region
            image_bytes = generate_leaderboard_image(self.teams_data, self.region, self.page)
            
            # Create file (using .jpg for better compression)
            filename = f"{self.region}_leaderboard_page{self.page+1}.jpg"
            file = discord.File(fp=image_bytes, filename=filename)
            
            # Region names for embed title
            region_titles = {
                'global': 'VEGA ASSASSINS Global Leaderboard',
                'apac': 'VEGA ASSASSINS APAC Leaderboard',
                'emea': 'VEGA ASSASSINS EMEA Leaderboard',
                'americas': 'VEGA ASSASSINS Americas Leaderboard',
                'india': 'VEGA ASSASSINS India Leaderboard'
            }
            
            region_display = region_titles.get(self.region, f"VEGA ASSASSINS {self.region.upper()} Leaderboard")
            
            # Create Discord embed with image
            embed = discord.Embed(
                title=region_display,
                color=0x5865F2,
                timestamp=datetime.utcnow()
            )
            
            # Attach the image to the embed
            embed.set_image(url=f"attachment://{filename}")
            
            # Simple footer
            embed.set_footer(text=f"Page {self.page+1}")
            
            # Update buttons
            self.update_buttons()
            
            # Edit message with new embed, image and buttons
            await interaction.edit_original_response(embed=embed, attachments=[file], view=self)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error changing region: {str(e)}", 
                ephemeral=True
            )
    
    async def refresh_leaderboard(self, interaction: discord.Interaction):
        """Refresh leaderboard data from database"""
        await interaction.response.defer()
        
        try:
            # Re-fetch data from database
            from services import db
            self.teams_data = await db.get_team_leaderboard(self.region, limit=None)
            
            # Recalculate total pages
            from services.leaderboard_generator import calculate_total_pages
            self.total_pages = calculate_total_pages(len(self.teams_data))
            
            # Make sure current page is still valid
            if self.page >= self.total_pages:
                self.page = max(0, self.total_pages - 1)
            
            # Generate new image with refreshed data
            image_bytes = generate_leaderboard_image(self.teams_data, self.region, self.page)
            
            # Create file (using .jpg for better compression)
            filename = f"{self.region}_leaderboard_page{self.page+1}.jpg"
            file = discord.File(fp=image_bytes, filename=filename)
            
            # Region names for embed title
            region_titles = {
                'global': 'VEGA ASSASSINS Global Leaderboard',
                'apac': 'VEGA ASSASSINS APAC Leaderboard',
                'emea': 'VEGA ASSASSINS EMEA Leaderboard',
                'americas': 'VEGA ASSASSINS Americas Leaderboard',
                'india': 'VEGA ASSASSINS India Leaderboard'
            }
            
            region_display = region_titles.get(self.region, f"VEGA ASSASSINS {self.region.upper()} Leaderboard")
            
            # Create Discord embed with image
            embed = discord.Embed(
                title=region_display,
                color=0x5865F2,
                timestamp=datetime.utcnow()
            )
            
            # Attach the image to the embed
            embed.set_image(url=f"attachment://{filename}")
            
            # Simple footer with page number
            embed.set_footer(text=f"Page {self.page+1} • Refreshed")
            
            # Update buttons
            self.update_buttons()
            
            # Edit message with new embed, image and buttons
            await interaction.edit_original_response(embed=embed, attachments=[file], view=self)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error refreshing leaderboard: {str(e)}", 
                ephemeral=True
            )
    
    async def update_image(self, interaction: discord.Interaction):
        """Generate and display the new page"""
        await interaction.response.defer()
        
        try:
            # Generate new image
            image_bytes = generate_leaderboard_image(self.teams_data, self.region, self.page)
            
            # Create file (using .jpg for better compression)
            filename = f"{self.region}_leaderboard_page{self.page+1}.jpg"
            file = discord.File(fp=image_bytes, filename=filename)
            
            # Region names for embed title
            region_titles = {
                'global': 'VEGA ASSASSINS Global Leaderboard',
                'apac': 'VEGA ASSASSINS APAC Leaderboard',
                'emea': 'VEGA ASSASSINS EMEA Leaderboard',
                'americas': 'VEGA ASSASSINS Americas Leaderboard',
                'india': 'VEGA ASSASSINS India Leaderboard'
            }
            
            region_display = region_titles.get(self.region, f"VEGA ASSASSINS {self.region.upper()} Leaderboard")
            
            # Create Discord embed with image - cleaner look
            embed = discord.Embed(
                title=region_display,
                color=0x5865F2,  # Discord blurple
                timestamp=datetime.utcnow()
            )
            
            # Attach the image to the embed
            embed.set_image(url=f"attachment://{filename}")
            
            # Simple footer with page number
            embed.set_footer(text=f"Page {self.page+1}")
            
            # Update buttons
            self.update_buttons()
            
            # Edit message with new embed, image and buttons
            await interaction.edit_original_response(embed=embed, attachments=[file], view=self)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error generating leaderboard image: {str(e)}", 
                ephemeral=True
            )


class PlayerImageLeaderboardView(View):
    """Interactive view for player leaderboard with pagination"""
    def __init__(self, players_data: list, page: int, total_pages: int):
        super().__init__(timeout=300)  # 5 minute timeout
        self.players_data = players_data
        self.page = page
        self.total_pages = total_pages
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page"""
        self.clear_items()
        
        # ⏮ First Page button (double left arrow)
        first_button = Button(
            emoji="⏮",
            style=discord.ButtonStyle.secondary,
            disabled=(self.page == 0)
        )
        first_button.callback = self.first_page
        self.add_item(first_button)
        
        # ◀ Previous button (left arrow)
        prev_button = Button(
            emoji="◀",
            style=discord.ButtonStyle.secondary,
            disabled=(self.page == 0)
        )
        prev_button.callback = self.previous_page
        self.add_item(prev_button)
        
        # 🔄 Refresh button (always enabled, green)
        refresh_button = Button(
            emoji="🔄",
            style=discord.ButtonStyle.success
        )
        refresh_button.callback = self.refresh_leaderboard
        self.add_item(refresh_button)
        
        # ▶ Next button (right arrow)
        next_button = Button(
            emoji="▶",
            style=discord.ButtonStyle.secondary,
            disabled=(self.page >= self.total_pages - 1)
        )
        next_button.callback = self.next_page
        self.add_item(next_button)
        
        # ⏭ Last Page button (double right arrow)
        last_button = Button(
            emoji="⏭",
            style=discord.ButtonStyle.secondary,
            disabled=(self.page >= self.total_pages - 1)
        )
        last_button.callback = self.last_page
        self.add_item(last_button)
    
    async def first_page(self, interaction: discord.Interaction):
        """Go to first page"""
        self.page = 0
        await self.update_image(interaction)
    
    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        self.page = max(0, self.page - 1)
        await self.update_image(interaction)
    
    async def next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        self.page = min(self.total_pages - 1, self.page + 1)
        await self.update_image(interaction)
    
    async def last_page(self, interaction: discord.Interaction):
        """Go to last page"""
        self.page = self.total_pages - 1
        await self.update_image(interaction)
    
    async def refresh_leaderboard(self, interaction: discord.Interaction):
        """Refresh the leaderboard data"""
        await interaction.response.defer()
        
        try:
            # Re-fetch player leaderboard from database
            from services import db
            from services.leaderboard_generator import generate_player_leaderboard_image, calculate_player_pages
            
            self.players_data = await db.get_player_leaderboard(limit=None)
            
            # Recalculate total pages (14 players per page)
            self.total_pages = calculate_player_pages(len(self.players_data))
            
            # If current page is beyond new total, go to last page
            if self.page >= self.total_pages:
                self.page = max(0, self.total_pages - 1)
            
            # Generate new image
            image_bytes = generate_player_leaderboard_image(self.players_data, self.page)
            
            # Create file (using .jpg for better compression)
            filename = f"player_leaderboard_page{self.page+1}.jpg"
            file = discord.File(fp=image_bytes, filename=filename)
            
            # Create Discord embed with image
            embed = discord.Embed(
                title="VEGA ASSASSINS Individual Player Leaderboard",
                color=0x5865F2,  # Discord blurple
                timestamp=datetime.utcnow()
            )
            
            # Attach the image to the embed
            embed.set_image(url=f"attachment://{filename}")
            
            # Footer with page number and refresh indicator
            embed.set_footer(text=f"Page {self.page+1} • Refreshed")
            
            # Update buttons
            self.update_buttons()
            
            # Edit message with new embed, image and buttons
            await interaction.edit_original_response(embed=embed, attachments=[file], view=self)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error refreshing leaderboard: {str(e)}", 
                ephemeral=True
            )
    
    async def update_image(self, interaction: discord.Interaction):
        """Generate and display the new page"""
        await interaction.response.defer()
        
        try:
            from services.leaderboard_generator import generate_player_leaderboard_image
            
            # Generate new image
            image_bytes = generate_player_leaderboard_image(self.players_data, self.page)
            
            # Create file (using .jpg for better compression)
            filename = f"player_leaderboard_page{self.page+1}.jpg"
            file = discord.File(fp=image_bytes, filename=filename)
            
            # Create Discord embed with image
            embed = discord.Embed(
                title="VEGA ASSASSINS Individual Player Leaderboard",
                color=0x5865F2,  # Discord blurple
                timestamp=datetime.utcnow()
            )
            
            # Attach the image to the embed
            embed.set_image(url=f"attachment://{filename}")
            
            # Simple footer with page number
            embed.set_footer(text=f"Page {self.page+1}")
            
            # Update buttons
            self.update_buttons()
            
            # Edit message with new embed, image and buttons
            await interaction.edit_original_response(embed=embed, attachments=[file], view=self)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error generating leaderboard image: {str(e)}", 
                ephemeral=True
            )


class LeaderboardView(View):
    """Interactive view for leaderboard pagination"""
    def __init__(self, cog, leaderboard_data, region, page, total_pages, is_team=False):
        super().__init__(timeout=300)  # 5 minute timeout
        self.cog = cog
        self.leaderboard_data = leaderboard_data
        self.region = region
        self.page = page
        self.total_pages = total_pages
        self.is_team = is_team
        
        # Update button states
        self.update_buttons()
    
    def update_buttons(self):
        """Enable/disable buttons based on current page"""
        # Clear existing buttons
        self.clear_items()
        
        # Previous button
        prev_button = Button(
            label="◀ Previous",
            style=discord.ButtonStyle.primary,
            disabled=(self.page == 0)
        )
        prev_button.callback = self.previous_page
        self.add_item(prev_button)
        
        # Refresh button
        refresh_button = Button(
            label="🔄 Refresh",
            style=discord.ButtonStyle.success
        )
        refresh_button.callback = self.refresh_data
        self.add_item(refresh_button)
        
        # Next button
        next_button = Button(
            label="Next ▶",
            style=discord.ButtonStyle.primary,
            disabled=(self.page >= self.total_pages - 1)
        )
        next_button.callback = self.next_page
        self.add_item(next_button)
    
    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        if self.page > 0:
            self.page -= 1
            await self.update_message(interaction)
    
    async def next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        if self.page < self.total_pages - 1:
            self.page += 1
            await self.update_message(interaction)
    
    async def refresh_data(self, interaction: discord.Interaction):
        """Refresh leaderboard data"""
        await interaction.response.defer()
        
        # Reload leaderboard data
        region_filter = None if self.region.lower() == "global" else self.region
        
        if self.is_team:
            self.leaderboard_data = await self.cog.get_team_leaderboard_async(region=region_filter)
        else:
            self.leaderboard_data = await self.cog.get_player_leaderboard_async(region=region_filter)
        
        # Recalculate total pages
        per_page = 10
        self.total_pages = (len(self.leaderboard_data) + per_page - 1) // per_page
        
        # Make sure current page is still valid
        if self.page >= self.total_pages:
            self.page = max(0, self.total_pages - 1)
        
        await self.update_message(interaction)
    
    async def update_message(self, interaction: discord.Interaction):
        """Update the message with new page"""
        if self.is_team:
            embed, _ = self.cog.create_team_leaderboard_embed(
                self.leaderboard_data, self.region, self.page
            )
        else:
            embed, _ = self.cog.create_player_leaderboard_embed(
                self.leaderboard_data, self.region, self.page
            )
        
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

class Leaderboards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path(__file__).parent.parent / "data"
        self.config_file = self.data_dir / "scoring_config.json"
        self.players_file = self.data_dir / "players.json"
        self.teams_file = self.data_dir / "teams.json"
        self.leaderboard_channels_file = self.data_dir / "leaderboard_channels.json"
        self.admins_file = self.data_dir / "admins.json"
        
        # Auto-update task (disabled by default, enable with /setup-leaderboard)
        # self.auto_update_leaderboards.start()
    
    def has_permission(self, interaction: discord.Interaction) -> bool:
        """Check if user has Admin or Staff role"""
        if not interaction.guild:
            return False
        
        # Check for Administrator permission
        if interaction.user.guild_permissions.administrator:
            return True
        
        # Check for Admin or Staff role (case-insensitive)
        user_roles = [role.name.lower() for role in interaction.user.roles]
        return any(role in user_roles for role in ['admin', 'staff', 'moderator', 'mod'])
    
    def load_scoring_config(self):
        """Load scoring configuration"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return self._default_scoring_config()
    
    def _default_scoring_config(self):
        """Return default scoring if config doesn't exist"""
        return {
            "player_scoring": {
                "weights": {
                    "kill_points": 2.0,
                    "assist_points": 1.0,
                    "death_penalty": 0.5,
                    "win_points": 10.0,
                    "participation_points": 1.0
                }
            },
            "team_scoring": {
                "weights": {
                    "win_points": 25.0,
                    "loss_penalty": 5.0,
                    "participation_points": 2.0
                }
            },
            "leaderboard_settings": {
                "max_display_entries": 15,
                "min_matches_for_ranking": 3
            }
        }
    
    def calculate_player_score(self, player_data, tournament_id="1"):
        """Calculate player leaderboard score based on config"""
        config = self.load_scoring_config()
        weights = config["player_scoring"]["weights"]
        bonuses = config["player_scoring"].get("bonus_multipliers", {})
        settings = config["leaderboard_settings"]
        
        stats = player_data.get("stats", {}).get(tournament_id, {})
        
        # Check minimum matches requirement
        matches = stats.get("matches_played", 0)
        if matches < settings.get("min_matches_for_ranking", 3):
            return None  # Not eligible for ranking
        
        kills = stats.get("kills", 0)
        deaths = stats.get("deaths", 0)
        assists = stats.get("assists", 0)
        wins = stats.get("wins", 0)
        
        # Base score calculation
        score = (
            kills * weights["kill_points"] +
            assists * weights["assist_points"] -
            deaths * weights["death_penalty"] +
            wins * weights["win_points"] +
            matches * weights["participation_points"]
        )
        
        # Apply bonuses
        kd_ratio = kills / deaths if deaths > 0 else kills
        win_rate = (wins / matches * 100) if matches > 0 else 0
        
        multiplier = 1.0
        
        # K/D bonuses
        if kd_ratio >= 2.0 and bonuses.get("kd_ratio_above_2.0"):
            multiplier *= bonuses["kd_ratio_above_2.0"]
        elif kd_ratio >= 1.5 and bonuses.get("kd_ratio_above_1.5"):
            multiplier *= bonuses["kd_ratio_above_1.5"]
        
        # Win rate bonuses
        if win_rate >= 75 and bonuses.get("win_rate_above_75"):
            multiplier *= bonuses["win_rate_above_75"]
        elif win_rate >= 60 and bonuses.get("win_rate_above_60"):
            multiplier *= bonuses["win_rate_above_60"]
        
        return round(score * multiplier, 2)
    
    def calculate_team_score(self, team_data):
        """Calculate team leaderboard score based on config"""
        config = self.load_scoring_config()
        weights = config["team_scoring"]["weights"]
        bonuses = config["team_scoring"].get("bonus_multipliers", {})
        settings = config["leaderboard_settings"]
        
        # Support both old JSON format (record.wins) and new database format (wins directly)
        if "record" in team_data:
            # Old JSON format
            record = team_data.get("record", {})
            wins = record.get("wins", 0)
            losses = record.get("losses", 0)
        else:
            # New database format
            wins = team_data.get("wins", 0)
            losses = team_data.get("losses", 0)
        
        total_matches = wins + losses
        
        # Check minimum matches requirement
        if total_matches < settings.get("min_matches_for_ranking", 3):
            return None  # Not eligible for ranking
        
        # Base score calculation
        score = (
            wins * weights["win_points"] -
            losses * weights["loss_penalty"] +
            total_matches * weights["participation_points"]
        )
        
        # Apply win rate bonuses
        win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
        multiplier = 1.0
        
        if win_rate >= 85 and bonuses.get("win_rate_above_85"):
            multiplier *= bonuses["win_rate_above_85"]
        elif win_rate >= 75 and bonuses.get("win_rate_above_75"):
            multiplier *= bonuses["win_rate_above_75"]
        elif win_rate >= 60 and bonuses.get("win_rate_above_60"):
            multiplier *= bonuses["win_rate_above_60"]
        
        return round(score * multiplier, 2)
    
    def get_player_leaderboard(self, region=None, tournament_id="1"):
        """Get ranked player leaderboard - DEPRECATED: Use async version"""
        # This is kept for compatibility but should use async version
        return []
    
    async def get_player_leaderboard_async(self, region=None, tournament_id="1", limit=100):
        """Get ranked player leaderboard from database"""
        from services import db
        
        try:
            # Get all players with stats from database
            pool = await db.get_pool()
            async with pool.acquire() as conn:
                query = """
                    SELECT 
                        p.discord_id,
                        p.ign,
                        p.region,
                        ps.kills,
                        ps.deaths,
                        ps.assists,
                        ps.matches_played,
                        ps.wins,
                        ps.losses,
                        ps.mvps,
                        CASE 
                            WHEN ps.matches_played >= 1 THEN
                                ps.kills * 100 + 
                                ps.assists * 50 + 
                                ps.deaths * -50 + 
                                ps.wins * 500 + 
                                ps.mvps * 200 +
                                ps.matches_played * 100
                            ELSE 0
                        END as score
                    FROM players p
                    JOIN player_stats ps ON p.discord_id = ps.player_id
                    WHERE ps.tournament_id = $1
                """
                
                params = [int(tournament_id)]
                
                # Add region filter if specified
                if region:
                    query += " AND LOWER(p.region) = LOWER($2)"
                    params.append(region)
                
                query += " ORDER BY score DESC LIMIT $" + str(len(params) + 1)
                params.append(limit)
                
                rows = await conn.fetch(query, *params)
                
                ranked_players = []
                for row in rows:
                    ranked_players.append({
                        "ign": row['ign'],
                        "region": row['region'],
                        "score": row['score'],
                        "kills": row['kills'],
                        "deaths": row['deaths'],
                        "assists": row['assists'],
                        "matches": row['matches_played'],
                        "wins": row['wins'],
                        "losses": row['losses'],
                        "mvps": row['mvps']
                    })
                
                return ranked_players
                
        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            return []
    
    def get_team_leaderboard(self, region=None):
        """Get ranked team leaderboard"""
        import asyncio
        
        # Run async function in sync context
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an event loop, we need to use create_task
            return []  # Will be replaced with async version
        else:
            return loop.run_until_complete(self.get_team_leaderboard_async(region))
    
    async def get_team_leaderboard_async(self, region=None):
        """Get ranked team leaderboard (async version)"""
        try:
            # Get all teams from database
            teams = await db.get_all_teams(region=region)
        except Exception as e:
            print(f"Error getting teams from database: {e}")
            return []
        
        ranked_teams = []
        for team in teams:
            # Skip banned teams (if we add a banned field later)
            if team.get("banned", False):
                continue
            
            score = self.calculate_team_score(team)
            if score is not None:  # Only include eligible teams
                wins = team.get("wins", 0)
                losses = team.get("losses", 0)
                total_matches = wins + losses
                win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
                
                ranked_teams.append({
                    "name": team.get("name", "Unknown"),
                    "tag": team.get("tag", ""),
                    "region": team.get("region", "Unknown"),
                    "score": score,
                    "wins": wins,
                    "losses": losses,
                    "win_rate": win_rate,
                    "matches": total_matches,
                    "logo_url": team.get("logo_url", None)  # Include logo URL
                })
        
        # Sort by score (descending)
        ranked_teams.sort(key=lambda x: x["score"], reverse=True)
        return ranked_teams
    
    def create_player_leaderboard_embed(self, leaderboard, region, page=0, per_page=10):
        """Create player leaderboard embed for a specific page"""
        config = self.load_scoring_config()
        
        # Calculate pagination
        total_pages = (len(leaderboard) + per_page - 1) // per_page
        start_idx = page * per_page
        end_idx = min(start_idx + per_page, len(leaderboard))
        page_data = leaderboard[start_idx:end_idx]
        
        # Build embed with gradient colors
        region_colors = {
            "global": discord.Color.gold(),
            "europe": discord.Color.blue(),
            "americas": discord.Color.red(),
            "asia": discord.Color.green()
        }
        embed_color = region_colors.get(region.lower(), discord.Color.gold())
        
        # Build embed
        title = f"🏆 PLAYER LEADERBOARD - {region.upper()}"
        embed = discord.Embed(title=title, color=embed_color, timestamp=datetime.now())
        
        # Build the table (Design 4: Fixed-Width Monospace)
        table_lines = []
        table_lines.append("```")
        table_lines.append("RANK  PLAYER        PTS   K/D   WIN%  MVP  MTCH")
        table_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Add players to table
        for i, player in enumerate(page_data, start_idx + 1):
            kd_ratio = player["kills"] / player["deaths"] if player["deaths"] > 0 else player["kills"]
            win_rate = (player["wins"] / player["matches"] * 100) if player["matches"] > 0 else 0
            mvps = player.get("mvps", 0)
            
            # Format fields with fixed widths
            rank = f"{i:2d}".rjust(2)
            ign = player['ign'][:13].ljust(13)
            pts = f"{int(player['score']):3d}".rjust(5)
            kd = f"{kd_ratio:.2f}".rjust(5)
            wr = f"{int(win_rate):3d}%".rjust(5)
            mvp = f"{mvps:2d}".rjust(3)
            matches = f"{player['matches']:2d}".rjust(3)
            
            table_lines.append(f" {rank}  {ign}  {pts} {kd} {wr} {mvp}  {matches}")
        
        table_lines.append("```")
        
        embed.description = "\n".join(table_lines)
        
        # Add medals and scoring info
        medals_text = "🥇🥈🥉 Top 3 shown"
        weights = config["player_scoring"]["weights"]
        scoring_info = f"{medals_text} • Kill×{weights['kill_points']} | Assist×{weights['assist_points']} | Death×-{weights['death_penalty']} | Win×{weights['win_points']}"
        
        embed.set_footer(text=f"{scoring_info} • Page {page + 1}/{total_pages} • {len(leaderboard)} total players")
        
        return embed, total_pages
    
    def create_team_leaderboard_embed(self, leaderboard, region, page=0, per_page=10):
        """Create team leaderboard embed for a specific page"""
        config = self.load_scoring_config()
        
        # Calculate pagination
        total_pages = (len(leaderboard) + per_page - 1) // per_page
        start_idx = page * per_page
        end_idx = min(start_idx + per_page, len(leaderboard))
        page_data = leaderboard[start_idx:end_idx]
        
        # Build embed with gradient colors
        region_colors = {
            "global": discord.Color.gold(),
            "europe": discord.Color.blue(),
            "americas": discord.Color.red(),
            "asia": discord.Color.green()
        }
        embed_color = region_colors.get(region.lower(), discord.Color.gold())
        
        # Build embed
        title = f"🏆 TEAM LEADERBOARD - {region.upper()}"
        embed = discord.Embed(title=title, color=embed_color, timestamp=datetime.now())
        
        # Build the table (Design 4: Fixed-Width Monospace - same as players)
        table_lines = []
        table_lines.append("```")
        table_lines.append("RANK  TEAM           PTS   W-L   WIN%  MATCHES")
        table_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Add teams to table
        for i, team in enumerate(page_data, start_idx + 1):
            # Format fields - aligned with header
            rank = f"{i:2d}"
            team_name = f"{team['name']}"[:15].ljust(15)  # 15 chars for team name
            pts = f"{int(team['score']):3d}".rjust(3)     # 3 chars for PTS
            record = f"{team['wins']:2d}-{team['losses']:1d}".ljust(5)
            wr = f"{int(team['win_rate']):3d}%".rjust(5)
            matches = f"{team['matches']:2d}".rjust(7)
            
            table_lines.append(f" {rank}  {team_name} {pts}  {record} {wr} {matches}")
        
        table_lines.append("```")
        
        embed.description = "\n".join(table_lines)
        
        # Add medals and scoring info (same format as players)
        medals_text = "🥇🥈🥉 Top 3 shown"
        weights = config["team_scoring"]["weights"]
        scoring_info = f"{medals_text} • Win×{weights['win_points']} | Loss×-{weights['loss_penalty']} | Match×{weights['participation_points']}"
        
        embed.set_footer(text=f"{scoring_info} • Page {page + 1}/{total_pages} • {len(leaderboard)} total teams")
        
        return embed, total_pages

    @app_commands.command(name="leaderboard-players", description="View global player leaderboard")
    async def player_leaderboard(self, interaction: discord.Interaction):
        """Show global player leaderboard with image and pagination"""
        await interaction.response.defer()
        
        try:
            # Get all player leaderboard data from database
            players_data = await db.get_player_leaderboard(limit=None)
            
            if not players_data:
                embed = discord.Embed(
                    title="📊 Global Player Leaderboard",
                    description="No players found yet. Play matches to appear on the leaderboard!",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Calculate total pages (14 players per page)
            total_pages = calculate_player_pages(len(players_data))
            
            # Generate first page image
            image_bytes = generate_player_leaderboard_image(players_data, page=0)
            
            # Create file (using .jpg for better compression)
            filename = "player_leaderboard_page1.jpg"
            file = discord.File(fp=image_bytes, filename=filename)
            
            # Create Discord embed with image
            embed = discord.Embed(
                title="VEGA ASSASSINS Individual Player Leaderboard",
                color=0x5865F2,  # Discord blurple
                timestamp=datetime.utcnow()
            )
            
            # Attach the image to the embed
            embed.set_image(url=f"attachment://{filename}")
            
            # Simple footer with page number
            embed.set_footer(text="Page 1")
            
            # Create view with pagination buttons
            view = PlayerImageLeaderboardView(players_data, page=0, total_pages=total_pages)
            
            # Send message with embed, image and buttons
            await interaction.followup.send(embed=embed, file=file, view=view)
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error generating player leaderboard: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="leaderboard-teams", description="View team leaderboard")
    @app_commands.choices(region=[
        app_commands.Choice(name="Global", value="global"),
        app_commands.Choice(name="North America (NA)", value="na"),
        app_commands.Choice(name="Europe (EU)", value="eu"),
        app_commands.Choice(name="Asia-Pacific (AP)", value="ap"),
        app_commands.Choice(name="Korea (KR)", value="kr"),
        app_commands.Choice(name="Brazil (BR)", value="br"),
        app_commands.Choice(name="Latin America (LATAM)", value="latam"),
        app_commands.Choice(name="Japan (JP)", value="jp")
    ])
    async def team_leaderboard(self, interaction: discord.Interaction, region: str = "global"):
        """Show team leaderboard"""
        await interaction.response.defer()
        
        # Get leaderboard data
        region_filter = None if region.lower() == "global" else region
        leaderboard = await self.get_team_leaderboard_async(region=region_filter)
        
        if not leaderboard:
            embed = discord.Embed(
                title="❌ No Teams Found",
                description=f"No teams meet the ranking requirements in **{region.title()}**.\n\n"
                           f"Teams need to complete at least **{self.load_scoring_config()['leaderboard_settings']['min_matches_for_ranking']} match(es)** to appear on the leaderboard.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Create initial embed and view
        embed, total_pages = self.create_team_leaderboard_embed(leaderboard, region, page=0)
        
        # Create pagination view
        view = LeaderboardView(self, leaderboard, region, page=0, total_pages=total_pages, is_team=True)
        
        await interaction.followup.send(embed=embed, view=view)
    
    @app_commands.command(name="edit-scoring", description="[ADMIN] Edit scoring configuration")
    @app_commands.describe(
        category="Which scoring to edit (player or team)",
        setting="Which setting to change (e.g., kill_points, win_points)",
        value="New value for the setting"
    )
    async def edit_scoring(self, interaction: discord.Interaction, category: str, setting: str, value: float):
        """Edit scoring configuration (admin only)"""
        # Check admin permission
        if not self.has_permission(interaction):
            await interaction.response.send_message(
                "❌ You need Admin or Staff role to edit scoring!",
                ephemeral=True
            )
            return
        
        config = self.load_scoring_config()
        
        # Validate category
        if category not in ["player", "team"]:
            await interaction.response.send_message("❌ Category must be 'player' or 'team'!", ephemeral=True)
            return
        
        # Update the setting
        scoring_key = f"{category}_scoring"
        if scoring_key not in config:
            await interaction.response.send_message(f"❌ Invalid category: {category}!", ephemeral=True)
            return
        
        if setting not in config[scoring_key]["weights"]:
            await interaction.response.send_message(
                f"❌ Invalid setting! Available settings:\n" +
                ", ".join(config[scoring_key]["weights"].keys()),
                ephemeral=True
            )
            return
        
        # Save old value
        old_value = config[scoring_key]["weights"][setting]
        
        # Update
        config[scoring_key]["weights"][setting] = value
        
        # Save to file
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        await interaction.response.send_message(
            f"✅ Updated **{category}** scoring:\n"
            f"`{setting}`: {old_value} → **{value}**\n\n"
            f"Leaderboards will reflect this change immediately!",
            ephemeral=True
        )
    
    @app_commands.command(name="view-scoring", description="View current scoring configuration")
    async def view_scoring(self, interaction: discord.Interaction):
        """View scoring configuration"""
        config = self.load_scoring_config()
        
        embed = discord.Embed(
            title="📊 Scoring Configuration", 
            description="Current point values for leaderboard calculations",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        
        # Player scoring with emojis
        player_weights = config["player_scoring"]["weights"]
        player_text = (
            f"🎯 **Kills:** `+{player_weights['kill_points']}` pts\n"
            f"🤝 **Assists:** `+{player_weights['assist_points']}` pts\n"
            f"💀 **Deaths:** `-{player_weights['death_penalty']}` pts\n"
            f"🏆 **Wins:** `+{player_weights['win_points']}` pts\n"
            f"🎮 **Match Played:** `+{player_weights['participation_points']}` pts"
        )
        embed.add_field(name="👤 Player Scoring", value=player_text, inline=True)
        
        # Team scoring with emojis
        team_weights = config["team_scoring"]["weights"]
        team_text = (
            f"✅ **Win:** `+{team_weights['win_points']}` pts\n"
            f"❌ **Loss:** `-{team_weights['loss_penalty']}` pts\n"
            f"🎮 **Match Played:** `+{team_weights['participation_points']}` pts"
        )
        embed.add_field(name="👥 Team Scoring", value=team_text, inline=True)
        
        # Bonuses
        player_bonuses = config["player_scoring"].get("bonus_multipliers", {})
        team_bonuses = config["team_scoring"].get("bonus_multipliers", {})
        
        bonus_text = (
            f"**Player Bonuses:**\n"
            f"⚡ K/D ≥ 2.0: `×{player_bonuses.get('kd_ratio_above_2.0', 1.0)}`\n"
            f"⚡ K/D ≥ 1.5: `×{player_bonuses.get('kd_ratio_above_1.5', 1.0)}`\n"
            f"⚡ WR ≥ 75%: `×{player_bonuses.get('win_rate_above_75', 1.0)}`\n"
            f"⚡ WR ≥ 60%: `×{player_bonuses.get('win_rate_above_60', 1.0)}`\n\n"
            f"**Team Bonuses:**\n"
            f"⚡ WR ≥ 85%: `×{team_bonuses.get('win_rate_above_85', 1.0)}`\n"
            f"⚡ WR ≥ 75%: `×{team_bonuses.get('win_rate_above_75', 1.0)}`\n"
            f"⚡ WR ≥ 60%: `×{team_bonuses.get('win_rate_above_60', 1.0)}`"
        )
        embed.add_field(name="✨ Bonus Multipliers", value=bonus_text, inline=False)
        
        # Settings
        settings = config["leaderboard_settings"]
        settings_text = (
            f"📋 **Max Display Entries:** `{settings['max_display_entries']}`\n"
            f"🎯 **Min Matches Required:** `{settings['min_matches_for_ranking']}`\n"
            f"📊 **Show Stats:** `{settings.get('show_stats_in_leaderboard', True)}`"
        )
        embed.add_field(name="⚙️ Leaderboard Settings", value=settings_text, inline=False)
        
        embed.set_footer(text="💡 Admins can use /edit-scoring to modify point values")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="lb", description="View regional team leaderboards")
    @app_commands.describe(region="Select the leaderboard region")
    @app_commands.choices(region=[
        app_commands.Choice(name="🌍 Global", value="global"),
        app_commands.Choice(name="🌏 APAC (AP, KR, JP)", value="apac"),
        app_commands.Choice(name="🌍 EMEA (EU)", value="emea"),
        app_commands.Choice(name="🌎 Americas (NA, BR, LATAM)", value="americas"),
        app_commands.Choice(name="🇮🇳 India", value="india")
    ])
    async def leaderboard_regional(self, interaction: discord.Interaction, region: str = "apac"):
        """Display regional team leaderboard as an image with pagination"""
        await interaction.response.defer()
        
        try:
            # Get ALL team leaderboard data from database (no limit for pagination)
            lb_data = await db.get_team_leaderboard(region, limit=None)
            
            if not lb_data:
                await interaction.followup.send(
                    f"📊 No teams found in the **{region.upper()}** leaderboard yet.\n"
                    "Teams will appear here after playing matches!"
                )
                return
            
            # Create embed
            region_names = {
                'global': '🌍 Global Team Leaderboard',
                'apac': '🌏 APAC Team Leaderboard (AP, KR, JP)',
                'emea': '🌍 EMEA Team Leaderboard (EU)',
                'americas': '🌎 Americas Team Leaderboard (NA, BR, LATAM)',
                'india': '🇮🇳 India Team Leaderboard'
            }
            
            embed = discord.Embed(
                title=region_names.get(region, f"{region.upper()} Team Leaderboard"),
                description=f"Top {len(lb_data)} teams ranked by points",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            # Build leaderboard table
            lb_text = "```\n"
            lb_text += "# │ Team                │ M  │ W-L   │  WR%  │ RD   │ Points\n"
            lb_text += "─"*68 + "\n"
            
            for team in lb_data:
                rank = team['rank']
                team_name = f"[{team['team_tag']}] {team['team_name']}"[:18].ljust(18)
                matches = str(team['total_matches']).rjust(2)
                w_l = f"{team['wins']}-{team['losses']}".rjust(5)
                wr = f"{team['win_rate']:.1f}".rjust(5)
                rd = str(team['round_diff']).rjust(4) if team['round_diff'] >= 0 else str(team['round_diff']).rjust(4)
                points = f"{team['points']:.1f}".rjust(6)
                
                # Medal emojis for top 3
                medal = ""
                if rank == 1:
                    medal = "🥇"
                elif rank == 2:
                    medal = "🥈"
                elif rank == 3:
                    medal = "🥉"
                
                rank_str = f"{rank}".rjust(2)
                lb_text += f"{rank_str}{medal} │ {team_name} │ {matches} │ {w_l} │ {wr} │ {rd} │ {points}\n"
            
            lb_text += "```"
            
            embed.add_field(name="📊 Team Rankings", value=lb_text, inline=False)
            
            # Add stats footer for top team
            if lb_data:
                top_team = lb_data[0]
                embed.add_field(
                    name="👑 Top Team",
                    value=f"**[{top_team['team_tag']}] {top_team['team_name']}** ({top_team['region'].upper()})\n"
                          f"Matches: `{top_team['total_matches']}` | W/L: `{top_team['wins']}-{top_team['losses']}` | "
                          f"Win Rate: `{top_team['win_rate']:.1f}%` | Round Diff: `{top_team['round_diff']:+d}`",
                    inline=False
                )
            
            embed.add_field(
                name="� Scoring System",
                value="• **3 points** per match win\n"
                      "• **0.1 points** per round differential\n"
                      "• Ranked by: Points → Win Rate → Matches",
                inline=False
            )
            
            # Calculate pagination
            total_pages = calculate_total_pages(len(lb_data))
            current_page = 0
            
            # Generate first page image
            image_bytes = generate_leaderboard_image(lb_data, region, current_page)
            
            # Create file (using .jpg for better compression)
            filename = f"{region}_leaderboard_page{current_page+1}.jpg"
            file = discord.File(fp=image_bytes, filename=filename)
            
            # Region names for embed title
            region_titles = {
                'global': 'VEGA ASSASSINS Global Leaderboard',
                'apac': 'VEGA ASSASSINS APAC Leaderboard',
                'emea': 'VEGA ASSASSINS EMEA Leaderboard',
                'americas': 'VEGA ASSASSINS Americas Leaderboard',
                'india': 'VEGA ASSASSINS India Leaderboard'
            }
            
            region_display = region_titles.get(region, f"VEGA ASSASSINS {region.upper()} Leaderboard")
            
            # Create Discord embed with image - cleaner look
            embed = discord.Embed(
                title=region_display,
                color=0x5865F2,  # Discord blurple
                timestamp=datetime.utcnow()
            )
            
            # Attach the image to the embed
            embed.set_image(url=f"attachment://{filename}")
            
            # Simple footer with timestamp
            embed.set_footer(text=f"Page {current_page+1}")
            
            # Create view with pagination buttons
            view = ImageLeaderboardView(lb_data, region, current_page, total_pages)
            
            # Send embed with image and buttons
            await interaction.followup.send(
                embed=embed,
                file=file,
                view=view
            )
            
        except FileNotFoundError as e:
            await interaction.followup.send(
                f"❌ Template not found for **{region.upper()}** region.\n"
                f"Please make sure the template file exists."
            )
        except Exception as e:
            print(f"Error generating leaderboard image: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(
                f"❌ Error generating leaderboard image: {str(e)}\n"
                "Please try again or contact an admin."
            )

async def setup(bot):
    await bot.add_cog(Leaderboards(bot))
