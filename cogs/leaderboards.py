import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path
import io
from PIL import Image, ImageDraw, ImageFont
from services import db
import os


# Font settings
FONT_PATH = Path('imports/font/Lato-Bold.ttf')
ROW_FONT_SIZE = 28

# Text Colors
RANK_COLOR = "#000000"
TEAM_NAME_COLOR = "#fafafa"
WINS_COLOR = "#ffffff"
LOSSES_COLOR = "#ffffff"
WINRATE_COLOR = "#ffffff"
POINTS_COLOR = "#ffffff"

# India leaderboard configuration
INDIA_CONFIG = {
    'rows': [
        {'rank': 1, 'rank_x': 190, 'rank_y': 240, 'team_name_x': 240, 'team_name_y': 236,
         'wins_x': 540, 'wins_y': 236, 'losses_x': 667, 'losses_y': 236,
         'winrate_x': 760, 'winrate_y': 236, 'points_x': 875, 'points_y': 236},
        {'rank': 2, 'rank_x': 190, 'rank_y': 280, 'team_name_x': 240, 'team_name_y': 278,
         'wins_x': 540, 'wins_y': 278, 'losses_x': 667, 'losses_y': 278,
         'winrate_x': 760, 'winrate_y': 278, 'points_x': 875, 'points_y': 278},
        {'rank': 3, 'rank_x': 190, 'rank_y': 320, 'team_name_x': 240, 'team_name_y': 318,
         'wins_x': 540, 'wins_y': 318, 'losses_x': 667, 'losses_y': 318,
         'winrate_x': 760, 'winrate_y': 318, 'points_x': 875, 'points_y': 318},
        {'rank': 4, 'rank_x': 190, 'rank_y': 365, 'team_name_x': 240, 'team_name_y': 364,
         'wins_x': 540, 'wins_y': 364, 'losses_x': 667, 'losses_y': 364,
         'winrate_x': 760, 'winrate_y': 364, 'points_x': 875, 'points_y': 364},
        {'rank': 5, 'rank_x': 190, 'rank_y': 405, 'team_name_x': 240, 'team_name_y': 404,
         'wins_x': 540, 'wins_y': 404, 'losses_x': 667, 'losses_y': 404,
         'winrate_x': 760, 'winrate_y': 404, 'points_x': 875, 'points_y': 404},
        {'rank': 6, 'rank_x': 190, 'rank_y': 450, 'team_name_x': 240, 'team_name_y': 448,
         'wins_x': 540, 'wins_y': 448, 'losses_x': 667, 'losses_y': 448,
         'winrate_x': 760, 'winrate_y': 448, 'points_x': 875, 'points_y': 448},
        {'rank': 7, 'rank_x': 190, 'rank_y': 490, 'team_name_x': 240, 'team_name_y': 488,
         'wins_x': 540, 'wins_y': 488, 'losses_x': 667, 'losses_y': 488,
         'winrate_x': 760, 'winrate_y': 488, 'points_x': 875, 'points_y': 488},
        {'rank': 8, 'rank_x': 190, 'rank_y': 530, 'team_name_x': 240, 'team_name_y': 528,
         'wins_x': 540, 'wins_y': 528, 'losses_x': 667, 'losses_y': 528,
         'winrate_x': 760, 'winrate_y': 528, 'points_x': 875, 'points_y': 528},
        {'rank': 9, 'rank_x': 190, 'rank_y': 570, 'team_name_x': 240, 'team_name_y': 570,
         'wins_x': 540, 'wins_y': 570, 'losses_x': 667, 'losses_y': 570,
         'winrate_x': 760, 'winrate_y': 570, 'points_x': 875, 'points_y': 570},
        {'rank': 10, 'rank_x': 190, 'rank_y': 615, 'team_name_x': 240, 'team_name_y': 615,
         'wins_x': 540, 'wins_y': 615, 'losses_x': 667, 'losses_y': 615,
         'winrate_x': 760, 'winrate_y': 615, 'points_x': 875, 'points_y': 615},
        {'rank': 11, 'rank_x': 190, 'rank_y': 655, 'team_name_x': 240, 'team_name_y': 655,
         'wins_x': 540, 'wins_y': 655, 'losses_x': 667, 'losses_y': 655,
         'winrate_x': 760, 'winrate_y': 655, 'points_x': 875, 'points_y': 655},
        {'rank': 12, 'rank_x': 190, 'rank_y': 700, 'team_name_x': 240, 'team_name_y': 700,
         'wins_x': 540, 'wins_y': 700, 'losses_x': 667, 'losses_y': 700,
         'winrate_x': 760, 'winrate_y': 700, 'points_x': 875, 'points_y': 700},
        {'rank': 13, 'rank_x': 190, 'rank_y': 740, 'team_name_x': 240, 'team_name_y': 740,
         'wins_x': 540, 'wins_y': 740, 'losses_x': 667, 'losses_y': 740,
         'winrate_x': 760, 'winrate_y': 740, 'points_x': 875, 'points_y': 740},
        {'rank': 14, 'rank_x': 190, 'rank_y': 780, 'team_name_x': 240, 'team_name_y': 780,
         'wins_x': 540, 'wins_y': 780, 'losses_x': 667, 'losses_y': 780,
         'winrate_x': 760, 'winrate_y': 780, 'points_x': 875, 'points_y': 780},
        {'rank': 15, 'rank_x': 190, 'rank_y': 820, 'team_name_x': 240, 'team_name_y': 820,
         'wins_x': 540, 'wins_y': 820, 'losses_x': 667, 'losses_y': 820,
         'winrate_x': 760, 'winrate_y': 820, 'points_x': 875, 'points_y': 820},
    ]
}


def generate_leaderboard_image(teams: list, page: int = 0) -> io.BytesIO:
    """Generate leaderboard image with team data."""
    # Get template path
    template_path = Path('imports/leaderboard/valm-india-lb.png')
    
    # Calculate which teams to show (15 per page)
    start_idx = page * 15
    end_idx = start_idx + 15
    page_teams = teams[start_idx:end_idx]
    
    # Load template
    img = Image.open(template_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    
    # Load font
    try:
        font = ImageFont.truetype(str(FONT_PATH), ROW_FONT_SIZE)
    except:
        font = ImageFont.load_default()
    
    # Draw each team
    for idx, team in enumerate(page_teams):
        if idx >= len(INDIA_CONFIG['rows']):
            break
        
        row_config = INDIA_CONFIG['rows'][idx]
        
        # Rank
        draw.text((row_config['rank_x'], row_config['rank_y']), 
                 str(team['rank']), font=font, fill=RANK_COLOR)
        
        # Team Name
        team_name = f"[{team['team_tag']}] {team['team_name']}"
        draw.text((row_config['team_name_x'], row_config['team_name_y']), 
                 team_name, font=font, fill=TEAM_NAME_COLOR)
        
        # Wins
        draw.text((row_config['wins_x'], row_config['wins_y']), 
                 str(team['wins']), font=font, fill=WINS_COLOR)
        
        # Losses
        draw.text((row_config['losses_x'], row_config['losses_y']), 
                 str(team['losses']), font=font, fill=LOSSES_COLOR)
        
        # Win Rate
        winrate_text = f"{team['win_rate']:.1f}%"
        draw.text((row_config['winrate_x'], row_config['winrate_y']), 
                 winrate_text, font=font, fill=WINRATE_COLOR)
        
        # Points
        points_text = f"{team['points']:.1f}"
        draw.text((row_config['points_x'], row_config['points_y']), 
                 points_text, font=font, fill=POINTS_COLOR)
    
    # Upscale to 1.5x
    new_width = int(img.width * 1.5)
    new_height = int(img.height * 1.5)
    img = img.resize((new_width, new_height), Image.LANCZOS)
    
    # Save to BytesIO
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=90)
    output.seek(0)
    
    return output


class LeaderboardPagination(discord.ui.View):
    """Pagination view for leaderboards with multiple pages."""
    
    def __init__(self, teams: list, current_page: int = 0):
        super().__init__(timeout=300)
        self.teams = teams
        self.current_page = current_page
        self.total_pages = (len(teams) + 14) // 15
        
        self.update_buttons()
    
    def update_buttons(self):
        """Enable/disable buttons based on current page."""
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1
        self.page_indicator.label = f"Page {self.current_page + 1}/{self.total_pages}"
    
    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.primary, custom_id="prev_page")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page."""
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await self.send_page(interaction)
    
    @discord.ui.button(label="Page 1/1", style=discord.ButtonStyle.secondary, custom_id="page_indicator", disabled=True)
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Page indicator."""
        pass
    
    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.primary, custom_id="next_page")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page."""
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        self.update_buttons()
        await self.send_page(interaction)
    
    async def send_page(self, interaction: discord.Interaction):
        """Generate and send the current page."""
        # Generate image for current page
        image_bytes = generate_leaderboard_image(self.teams, page=self.current_page)
        
        # Create file
        file = discord.File(fp=image_bytes, filename=f'india_lb_page_{self.current_page + 1}.jpg')
        
        # Create embed
        embed = discord.Embed(
            title="🇮🇳 VALM India Leaderboard",
            description=f"Displaying top teams competing in India region",
            color=0xFF9933  # India flag orange color
        )
        embed.set_image(url=f"attachment://india_lb_page_{self.current_page + 1}.jpg")
        
        start_team = self.current_page * 15 + 1
        end_team = min((self.current_page + 1) * 15, len(self.teams))
        embed.set_footer(text=f"📊 Showing teams {start_team}-{end_team} of {len(self.teams)} | Page {self.current_page + 1}/{self.total_pages}")
        
        await interaction.response.edit_message(embed=embed, attachments=[file], view=self)


class Leaderboards(commands.Cog):
    """Leaderboard command to display team leaderboards with pagination."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lb", description="Show the VALM India leaderboard")
    async def lb(self, interaction: discord.Interaction):
        """Display India region leaderboard with pagination if needed."""
        await interaction.response.defer()

        try:
            # Get India leaderboard data from database (fetch ALL teams, no limit)
            teams = await db.get_team_leaderboard('india', limit=None)
            
            # If leaderboard is empty, fetch teams from teams table directly
            if not teams:
                all_teams = await db.get_all_teams(region='india')
                if not all_teams:
                    await interaction.followup.send("❌ No teams registered in India region.", ephemeral=True)
                    return
                
                # Convert teams table format to leaderboard format
                teams = []
                for idx, team in enumerate(all_teams, start=1):
                    teams.append({
                        'rank': idx,
                        'team_name': team['team_name'],
                        'team_tag': team['team_tag'],
                        'region': team['region'],
                        'total_matches': 0,
                        'wins': 0,
                        'losses': 0,
                        'win_rate': 0.0,
                        'total_rounds_won': 0,
                        'total_rounds_lost': 0,
                        'round_diff': 0,
                        'points': 0.0,
                        'logo_url': team.get('logo_url')
                    })
            
            # Generate first page
            image_bytes = generate_leaderboard_image(teams, page=0)
            
            # Create file
            file = discord.File(fp=image_bytes, filename='india_lb.jpg')
            
            # Create embed
            embed = discord.Embed(
                title="🇮🇳 VALM India Leaderboard",
                description=f"Displaying top teams competing in India region",
                color=0xFF9933  # India flag orange color
            )
            embed.set_image(url="attachment://india_lb.jpg")
            
            # If more than 15 teams, add pagination
            if len(teams) > 15:
                view = LeaderboardPagination(teams, current_page=0)
                embed.set_footer(text=f"📊 Showing teams 1-{min(15, len(teams))} of {len(teams)} | Page 1/{(len(teams) + 14) // 15}")
                await interaction.followup.send(embed=embed, file=file, view=view)
            else:
                embed.set_footer(text=f"📊 Showing all {len(teams)} team{'s' if len(teams) != 1 else ''}")
                await interaction.followup.send(embed=embed, file=file)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating leaderboard: {e}", ephemeral=True)
            print(f"Leaderboard error: {e}")
            import traceback
            traceback.print_exc()

    @app_commands.command(name="sync_teams_lb", description="[Admin] Sync all existing teams to the leaderboard")
    @app_commands.guild_only()
    async def sync_teams_lb(self, interaction: discord.Interaction):
        """Sync all existing teams to the leaderboard tables."""
        # Check if user is admin
        admin_role_id = int(os.getenv('ADMIN_ROLE_ID', 0))
        if not admin_role_id or admin_role_id not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Get all teams
            all_teams = await db.get_all_teams()
            
            synced_count = 0
            error_count = 0
            
            for team in all_teams:
                team_id = team['id']  # teams table uses 'id' not 'team_id'
                team_name = team['team_name']
                team_tag = team['team_tag']
                region = team['region']
                logo_url = team.get('logo_url')
                
                # Check if team is from India region
                is_india = region and region.lower() == 'india'
                
                try:
                    # Update team leaderboard (this will create entry if it doesn't exist)
                    await db.update_team_leaderboard(
                        team_id=team_id,
                        team_name=team_name,
                        team_tag=team_tag,
                        region=region,
                        logo_url=logo_url,
                        is_india=is_india
                    )
                    synced_count += 1
                except Exception as e:
                    print(f"Error syncing team {team_tag}: {e}")
                    error_count += 1
            
            embed = discord.Embed(
                title="✅ Teams Synced to Leaderboard",
                description=f"Successfully synced teams to the leaderboard tables.",
                color=discord.Color.green()
            )
            embed.add_field(name="Total Teams", value=str(len(all_teams)))
            embed.add_field(name="Synced", value=str(synced_count))
            if error_count > 0:
                embed.add_field(name="Errors", value=str(error_count))
                embed.color = discord.Color.orange()
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error syncing teams: {str(e)}", ephemeral=True)
            traceback.print_exc()


async def setup(bot):
    await bot.add_cog(Leaderboards(bot))
