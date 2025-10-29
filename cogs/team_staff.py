import discord
from discord import app_commands
from discord.ext import commands
import services.db as db

class TeamStaff(commands.Cog):
    """Team staff management - add/remove managers and coach."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="add-manager", description="Add a manager to your team (Captain only)")
    @app_commands.describe(user="The user to add as manager")
    async def add_manager(self, interaction: discord.Interaction, user: discord.Member):
        """Add a manager to the team."""
        # Check if user has a team and is captain
        team = await db.get_team_by_captain(interaction.user.id)
        
        if not team:
            await interaction.response.send_message(
                "❌ You must be a team captain to add managers.",
                ephemeral=True
            )
            return
        
        # Check if target user is registered
        player = await db.get_player(user.id)
        if not player:
            await interaction.response.send_message(
                f"❌ {user.mention} must be registered as a player first!",
                ephemeral=True
            )
            return
        
        # Check if user is already captain
        if user.id == team['captain_id']:
            await interaction.response.send_message(
                "❌ The captain cannot be added as a manager.",
                ephemeral=True
            )
            return
        
        # Get current staff to check slots
        staff = await db.get_team_staff(team['id'])
        
        # Check if user is already a manager
        if user.id == staff.get('manager_1_id') or user.id == staff.get('manager_2_id'):
            await interaction.response.send_message(
                f"❌ {user.mention} is already a manager on this team.",
                ephemeral=True
            )
            return
        
        # Check if user is already coach
        if user.id == staff.get('coach_id'):
            await interaction.response.send_message(
                f"❌ {user.mention} is already the coach. They cannot be both coach and manager.",
                ephemeral=True
            )
            return
        
        # Try to add to slot 1 first, then slot 2
        slot = 1 if not staff.get('manager_1_id') else 2 if not staff.get('manager_2_id') else None
        
        if not slot:
            await interaction.response.send_message(
                "❌ Both manager slots are full! Remove a manager first using `/remove-manager`.",
                ephemeral=True
            )
            return
        
        # Add manager
        success = await db.add_team_manager(team['id'], user.id, slot)
        
        if success:
            await interaction.response.send_message(
                f"✅ {user.mention} has been added as Manager {slot} for **{team['name']}**!",
                ephemeral=False
            )
        else:
            await interaction.response.send_message(
                f"❌ Failed to add manager. Manager slot {slot} might already be taken.",
                ephemeral=True
            )
    
    @app_commands.command(name="remove-manager", description="Remove a manager from your team (Captain only)")
    @app_commands.describe(user="The manager to remove")
    async def remove_manager(self, interaction: discord.Interaction, user: discord.Member):
        """Remove a manager from the team."""
        # Check if user has a team and is captain
        team = await db.get_team_by_captain(interaction.user.id)
        
        if not team:
            await interaction.response.send_message(
                "❌ You must be a team captain to remove managers.",
                ephemeral=True
            )
            return
        
        # Get current staff
        staff = await db.get_team_staff(team['id'])
        
        # Check if user is actually a manager
        if user.id != staff.get('manager_1_id') and user.id != staff.get('manager_2_id'):
            await interaction.response.send_message(
                f"❌ {user.mention} is not a manager on this team.",
                ephemeral=True
            )
            return
        
        # Remove manager
        await db.remove_team_manager(team['id'], manager_id=user.id)
        
        await interaction.response.send_message(
            f"✅ {user.mention} has been removed as manager from **{team['name']}**.",
            ephemeral=False
        )
    
    @app_commands.command(name="add-coach", description="Add a coach to your team (Captain only)")
    @app_commands.describe(user="The user to add as coach")
    async def add_coach(self, interaction: discord.Interaction, user: discord.Member):
        """Add a coach to the team."""
        # Check if user has a team and is captain
        team = await db.get_team_by_captain(interaction.user.id)
        
        if not team:
            await interaction.response.send_message(
                "❌ You must be a team captain to add a coach.",
                ephemeral=True
            )
            return
        
        # Check if target user is registered
        player = await db.get_player(user.id)
        if not player:
            await interaction.response.send_message(
                f"❌ {user.mention} must be registered as a player first!",
                ephemeral=True
            )
            return
        
        # Check if user is already captain
        if user.id == team['captain_id']:
            await interaction.response.send_message(
                "❌ The captain cannot be added as a coach.",
                ephemeral=True
            )
            return
        
        # Get current staff
        staff = await db.get_team_staff(team['id'])
        
        # Check if user is already a manager
        if user.id == staff.get('manager_1_id') or user.id == staff.get('manager_2_id'):
            await interaction.response.send_message(
                f"❌ {user.mention} is already a manager. They cannot be both coach and manager.",
                ephemeral=True
            )
            return
        
        # Check if coach slot is already taken
        if staff.get('coach_id'):
            await interaction.response.send_message(
                "❌ Coach slot is already filled! Remove the current coach first using `/remove-coach`.",
                ephemeral=True
            )
            return
        
        # Add coach
        success = await db.add_team_coach(team['id'], user.id)
        
        if success:
            await interaction.response.send_message(
                f"✅ {user.mention} has been added as Coach for **{team['name']}**!",
                ephemeral=False
            )
        else:
            await interaction.response.send_message(
                "❌ Failed to add coach. The coach slot might already be taken.",
                ephemeral=True
            )
    
    @app_commands.command(name="remove-coach", description="Remove the coach from your team (Captain only)")
    async def remove_coach(self, interaction: discord.Interaction):
        """Remove the coach from the team."""
        # Check if user has a team and is captain
        team = await db.get_team_by_captain(interaction.user.id)
        
        if not team:
            await interaction.response.send_message(
                "❌ You must be a team captain to remove the coach.",
                ephemeral=True
            )
            return
        
        # Get current staff
        staff = await db.get_team_staff(team['id'])
        
        if not staff.get('coach_id'):
            await interaction.response.send_message(
                "❌ Your team doesn't have a coach.",
                ephemeral=True
            )
            return
        
        coach_id = staff['coach_id']
        coach_mention = f"<@{coach_id}>"
        
        # Remove coach
        await db.remove_team_coach(team['id'])
        
        await interaction.response.send_message(
            f"✅ {coach_mention} has been removed as coach from **{team['name']}**.",
            ephemeral=False
        )
    
    @app_commands.command(name="view-staff", description="View your team's staff (managers and coach)")
    async def view_staff(self, interaction: discord.Interaction):
        """View team staff."""
        # Get user's team
        team = await db.get_player_team(interaction.user.id)
        
        if not team:
            await interaction.response.send_message(
                "❌ You are not part of any team.",
                ephemeral=True
            )
            return
        
        # Get staff
        staff = await db.get_team_staff(team['id'])
        
        embed = discord.Embed(
            title=f"📋 {team['name']} [{team['tag']}] - Staff",
            color=discord.Color.blue()
        )
        
        # Add captain
        embed.add_field(
            name="👑 Captain",
            value=f"<@{team['captain_id']}>",
            inline=False
        )
        
        # Add managers
        manager_1 = staff.get('manager_1_id')
        manager_2 = staff.get('manager_2_id')
        
        manager_text = ""
        if manager_1:
            manager_text += f"**Manager 1:** <@{manager_1}> ({staff.get('manager_1_ign', 'Unknown')})\n"
        else:
            manager_text += "**Manager 1:** *Empty slot*\n"
        
        if manager_2:
            manager_text += f"**Manager 2:** <@{manager_2}> ({staff.get('manager_2_ign', 'Unknown')})"
        else:
            manager_text += "**Manager 2:** *Empty slot*"
        
        embed.add_field(
            name="👔 Managers",
            value=manager_text,
            inline=False
        )
        
        # Add coach
        coach = staff.get('coach_id')
        if coach:
            embed.add_field(
                name="🎓 Coach",
                value=f"<@{coach}> ({staff.get('coach_ign', 'Unknown')})",
                inline=False
            )
        else:
            embed.add_field(
                name="🎓 Coach",
                value="*Empty slot*",
                inline=False
            )
        
        # Add logo if available
        if team.get('logo_url'):
            embed.set_thumbnail(url=team['logo_url'])
        
        await interaction.response.send_message(embed=embed, ephemeral=False)

async def setup(bot):
    await bot.add_cog(TeamStaff(bot))
