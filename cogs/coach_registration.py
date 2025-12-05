"""
Coach Registration System
Allows users to register as coaches for teams
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import database functions
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services import db

def cfg(key: str) -> str:
    """Get config value from environment"""
    return os.getenv(key.upper())

class CoachRegistrationView(discord.ui.View):
    """Main coach registration view with Register button"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🎓 Register as Coach", style=discord.ButtonStyle.primary, custom_id="register_coach_button")
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle coach registration button click"""
        # Create private thread for registration
        thread = await interaction.channel.create_thread(
            name=f"Coach Registration - {interaction.user.name}",
            type=discord.ChannelType.private_thread,
            invitable=False
        )
        
        await interaction.response.send_message(
            f"✅ Created private thread: {thread.mention}\n"
            f"Please complete your registration there.",
            ephemeral=True
        )
        
        # Add user to thread
        await thread.add_user(interaction.user)
        
        # Get all teams
        teams = await db.get_all_teams()
        
        if not teams:
            await thread.send(
                f"{interaction.user.mention}\n\n"
                "❌ **No teams found!**\n"
                "There are no registered teams available. Please try again later."
            )
            return
        
        # Create team selection dropdown
        team_select = TeamSelectView(interaction.user, teams, thread)
        
        await thread.send(
            f"{interaction.user.mention}\n\n"
            f"🎓 **Coach Registration**\n\n"
            f"Please select the team you want to coach from the dropdown below.\n"
            f"The team captain or manager will need to approve your request.",
            view=team_select
        )


class TeamSelectView(discord.ui.View):
    """View with dropdown to select a team"""
    
    def __init__(self, user: discord.User, teams: list, thread: discord.Thread):
        super().__init__(timeout=300)
        self.user = user
        self.teams = teams
        self.thread = thread
        
        # Create dropdown options
        options = []
        for team in teams[:25]:  # Discord limit is 25 options
            options.append(
                discord.SelectOption(
                    label=team['name'][:100],  # Truncate if too long
                    description=f"Tag: [{team.get('tag', 'N/A')}] | Region: {team.get('region', 'N/A').upper()}",
                    value=str(team['id'])
                )
            )
        
        # Add the dropdown
        self.team_dropdown = discord.ui.Select(
            placeholder="Select a team...",
            options=options,
            custom_id="team_select"
        )
        self.team_dropdown.callback = self.team_selected
        self.add_item(self.team_dropdown)
    
    async def team_selected(self, interaction: discord.Interaction):
        """Handle team selection"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ This is not your registration!", ephemeral=True)
            return
        
        team_id = int(self.team_dropdown.values[0])
        
        # Get full team data
        team = await db.get_team_by_id(team_id)
        
        if not team:
            await interaction.response.send_message("❌ Team not found!", ephemeral=True)
            return
        
        # Check if team already has a coach
        staff = await db.get_team_staff(team_id)
        if staff and staff.get('coach_id'):
            await interaction.response.send_message(
                f"❌ **{team['name']}** already has a coach!\n"
                f"Teams can only have one coach at a time.",
                ephemeral=True
            )
            return
        
        # Disable dropdown
        self.team_dropdown.disabled = True
        await interaction.response.edit_message(view=self)
        
        # Send approval request to captain and managers
        captain_id = team['captain_id']
        manager_1_id = staff.get('manager_1_id') if staff else None
        manager_2_id = staff.get('manager_2_id') if staff else None
        
        # Get player info for better display
        player = await db.get_player(self.user.id)
        player_ign = player.get('ign', 'Unknown') if player else 'Unknown'
        
        await self.thread.send(
            f"⏳ **Waiting for approval...**\n\n"
            f"A request has been sent to the captain and managers of **{team['name']}**.\n"
            f"They need to approve before you can join as coach."
        )
        
        # Create approval view
        approval_view = CoachApprovalView(
            coach_user=self.user,
            coach_ign=player_ign,
            team=team,
            thread=self.thread
        )
        
        # Send DM to captain
        try:
            captain = await interaction.client.fetch_user(captain_id)
            captain_dm = await captain.create_dm()
            
            approval_embed = discord.Embed(
                title="🎓 Coach Registration Request",
                description=f"{self.user.mention} wants to be the coach for your team!",
                color=discord.Color.blue()
            )
            approval_embed.add_field(name="Coach", value=f"{self.user.mention} ({player_ign})", inline=False)
            approval_embed.add_field(name="Team", value=f"{team['name']} [{team['tag']}]", inline=False)
            approval_embed.set_footer(text="Accept or Decline below")
            
            await captain_dm.send(embed=approval_embed, view=approval_view)
        except discord.Forbidden:
            pass  # Captain has DMs disabled
        
        # Send DM to managers if they exist
        for manager_id in [manager_1_id, manager_2_id]:
            if manager_id:
                try:
                    manager = await interaction.client.fetch_user(manager_id)
                    manager_dm = await manager.create_dm()
                    
                    approval_embed = discord.Embed(
                        title="🎓 Coach Registration Request",
                        description=f"{self.user.mention} wants to be the coach for your team!",
                        color=discord.Color.blue()
                    )
                    approval_embed.add_field(name="Coach", value=f"{self.user.mention} ({player_ign})", inline=False)
                    approval_embed.add_field(name="Team", value=f"{team['name']} [{team['tag']}]", inline=False)
                    approval_embed.set_footer(text="Accept or Decline below")
                    
                    await manager_dm.send(embed=approval_embed, view=approval_view)
                except discord.Forbidden:
                    pass  # Manager has DMs disabled
    
    async def on_timeout(self):
        """Handle timeout"""
        try:
            await self.thread.send("⏰ Registration timed out. Please try again.")
        except:
            pass


class CoachApprovalView(discord.ui.View):
    """View for captain/manager to approve or decline coach request"""
    
    def __init__(self, coach_user: discord.User, coach_ign: str, team: dict, thread: discord.Thread):
        super().__init__(timeout=600)  # 10 minutes
        self.coach_user = coach_user
        self.coach_ign = coach_ign
        self.team = team
        self.thread = thread
        self.approved = False
    
    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.success, custom_id="approve_coach")
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Accept the coach request"""
        # Check if user is captain or manager
        staff = await db.get_team_staff(self.team['id'])
        is_captain = interaction.user.id == self.team['captain_id']
        is_manager = interaction.user.id in [staff.get('manager_1_id'), staff.get('manager_2_id')] if staff else False
        
        if not (is_captain or is_manager):
            await interaction.response.send_message("❌ Only the captain or managers can approve!", ephemeral=True)
            return
        
        if self.approved:
            await interaction.response.send_message("✅ This request has already been processed.", ephemeral=True)
            return
        
        self.approved = True
        
        # Add coach to team
        await db.add_team_coach(self.team['id'], self.coach_user.id)
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        
        # Notify in DM
        await interaction.followup.send(
            f"✅ You've accepted **{self.coach_user.mention}** as coach for **{self.team['name']}**!",
            ephemeral=True
        )
        
        # Notify in thread
        await self.thread.send(
            f"✅ **Coach Registration Approved!**\n\n"
            f"{self.coach_user.mention}, you are now the coach of **{self.team['name']}** [{self.team['tag']}]!\n"
            f"Approved by: {interaction.user.mention}"
        )
        
        # Log to admin logs
        log_channel_id = cfg("log_channel_id")
        if log_channel_id:
            try:
                log_channel = interaction.client.get_channel(int(log_channel_id))
                if log_channel:
                    log_embed = discord.Embed(
                        title="🎓 Coach Registered",
                        color=discord.Color.blue(),
                        timestamp=discord.utils.utcnow()
                    )
                    log_embed.add_field(name="Coach", value=f"{self.coach_user.mention} ({self.coach_ign})", inline=False)
                    log_embed.add_field(name="Team", value=f"{self.team['name']} [{self.team['tag']}]", inline=False)
                    log_embed.add_field(name="Approved by", value=interaction.user.mention, inline=False)
                    log_embed.set_footer(text=f"Coach ID: {self.coach_user.id} | Team ID: {self.team['id']}")
                    await log_channel.send(embed=log_embed)
            except:
                pass
        
        # Close thread after 5 seconds
        await asyncio.sleep(5)
        try:
            await self.thread.edit(archived=True, locked=True)
        except:
            pass
    
    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.danger, custom_id="decline_coach")
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Decline the coach request"""
        # Check if user is captain or manager
        staff = await db.get_team_staff(self.team['id'])
        is_captain = interaction.user.id == self.team['captain_id']
        is_manager = interaction.user.id in [staff.get('manager_1_id'), staff.get('manager_2_id')] if staff else False
        
        if not (is_captain or is_manager):
            await interaction.response.send_message("❌ Only the captain or managers can decline!", ephemeral=True)
            return
        
        if self.approved:
            await interaction.response.send_message("✅ This request has already been processed.", ephemeral=True)
            return
        
        self.approved = True
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        
        # Notify in DM
        await interaction.followup.send(
            f"❌ You've declined **{self.coach_user.mention}** as coach for **{self.team['name']}**.",
            ephemeral=True
        )
        
        # Notify in thread
        await self.thread.send(
            f"❌ **Coach Registration Declined**\n\n"
            f"{self.coach_user.mention}, your request to coach **{self.team['name']}** was declined by {interaction.user.mention}."
        )
        
        # Close thread after 5 seconds
        await asyncio.sleep(5)
        try:
            await self.thread.edit(archived=True, locked=True)
        except:
            pass


class CoachRegistration(commands.Cog):
    """Cog for coach registration system"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Setup persistent view on bot ready"""
        self.bot.add_view(CoachRegistrationView())
        print("✅ Coach Registration cog loaded")
    
    @app_commands.command(name="setup-coach-registration", description="[ADMIN] Setup coach registration UI in this channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_coach_registration(self, interaction: discord.Interaction):
        """Setup the coach registration message with button"""
        
        embed = discord.Embed(
            title="🎓 Coach Registration",
            description=(
                "Want to become a coach for a team? Click the button below to get started!\n\n"
                "**Requirements:**\n"
                "• The team must not already have a coach\n"
                "• Team captain or manager must approve your request\n\n"
                "**Process:**\n"
                "1️⃣ Click the Register button\n"
                "2️⃣ Select the team you want to coach\n"
                "3️⃣ Wait for captain/manager approval\n"
                "4️⃣ Get notified once approved!"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Coaches help guide their teams to victory!")
        
        view = CoachRegistrationView()
        
        await interaction.response.send_message(
            "✅ Coach registration UI has been set up!",
            ephemeral=True
        )
        
        await interaction.channel.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(CoachRegistration(bot))
