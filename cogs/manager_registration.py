"""
Manager Registration System
Allows users to register as managers for teams
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

class ManagerRegistrationView(discord.ui.View):
    """Main manager registration view with Register button"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Register as Manager", style=discord.ButtonStyle.primary, custom_id="register_manager_button")
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle manager registration button click"""
        # Create private thread for registration
        thread = await interaction.channel.create_thread(
            name=f"Manager Registration - {interaction.user.name}",
            type=discord.ChannelType.private_thread,
            invitable=False
        )
        
        await interaction.response.send_message(
            f"Created private thread: {thread.mention}\n"
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
                "**No teams found**\n"
                "There are no registered teams available. Please try again later."
            )
            return
        
        # Create team selection dropdown
        team_select = TeamSelectView(interaction.user, teams, thread)
        
        await thread.send(
            f"{interaction.user.mention}\n\n"
            f"**Manager Registration**\n\n"
            f"Please select the team you want to manage from the dropdown below.\n"
            f"The team captain or existing manager will need to approve your request.",
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
            await interaction.response.send_message("This is not your registration.", ephemeral=True)
            return
        
        team_id = int(self.team_dropdown.values[0])
        
        # Get full team data
        team = await db.get_team_by_id(team_id)
        
        if not team:
            await interaction.response.send_message("Team not found.", ephemeral=True)
            return
        
        # Check if team already has 2 managers
        staff = await db.get_team_staff(team_id)
        manager_1_id = staff.get('manager_1_id') if staff else None
        manager_2_id = staff.get('manager_2_id') if staff else None
        
        if manager_1_id and manager_2_id:
            await interaction.response.send_message(
                f"**{team['name']}** already has 2 managers.\n"
                f"Teams can only have a maximum of 2 managers.",
                ephemeral=True
            )
            return
        
        # Disable dropdown
        self.team_dropdown.disabled = True
        await interaction.response.edit_message(view=self)
        
        # Send approval request to captain and existing managers
        captain_id = team['captain_id']
        
        # Get player info for better display
        player = await db.get_player(self.user.id)
        player_ign = player.get('ign', 'Unknown') if player else 'Unknown'
        
        await self.thread.send(
            f"**Waiting for approval**\n\n"
            f"A request has been sent to the captain and managers of **{team['name']}**.\n"
            f"They need to approve before you can join as manager."
        )
        
        # Create approval view
        approval_view = ManagerApprovalView(
            manager_user=self.user,
            manager_ign=player_ign,
            team=team,
            thread=self.thread
        )
        
        # Send DM to captain
        try:
            captain = await interaction.client.fetch_user(captain_id)
            captain_dm = await captain.create_dm()
            
            approval_embed = discord.Embed(
                title="Manager Registration Request",
                description=f"{self.user.mention} wants to be a manager for your team!",
                color=discord.Color.blue()
            )
            approval_embed.add_field(name="Manager", value=f"{self.user.mention} ({player_ign})", inline=False)
            approval_embed.add_field(name="Team", value=f"{team['name']} [{team['tag']}]", inline=False)
            approval_embed.set_footer(text="Accept or Decline below")
            
            await captain_dm.send(embed=approval_embed, view=approval_view)
        except discord.Forbidden:
            pass  # Captain has DMs disabled
        
        # Send DM to existing managers if they exist
        for manager_id in [manager_1_id, manager_2_id]:
            if manager_id:
                try:
                    manager = await interaction.client.fetch_user(manager_id)
                    manager_dm = await manager.create_dm()
                    
                    approval_embed = discord.Embed(
                        title="Manager Registration Request",
                        description=f"{self.user.mention} wants to be a manager for your team!",
                        color=discord.Color.blue()
                    )
                    approval_embed.add_field(name="Manager", value=f"{self.user.mention} ({player_ign})", inline=False)
                    approval_embed.add_field(name="Team", value=f"{team['name']} [{team['tag']}]", inline=False)
                    approval_embed.set_footer(text="Accept or Decline below")
                    
                    await manager_dm.send(embed=approval_embed, view=approval_view)
                except discord.Forbidden:
                    pass  # Manager has DMs disabled
    
    async def on_timeout(self):
        """Handle timeout"""
        try:
            await self.thread.send("Registration timed out. Please try again.")
        except:
            pass


class ManagerApprovalView(discord.ui.View):
    """View for captain/manager to approve or decline manager request"""
    
    def __init__(self, manager_user: discord.User, manager_ign: str, team: dict, thread: discord.Thread):
        super().__init__(timeout=600)  # 10 minutes
        self.manager_user = manager_user
        self.manager_ign = manager_ign
        self.team = team
        self.thread = thread
        self.approved = False
    
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, custom_id="approve_manager")
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Accept the manager request"""
        # Check if user is captain or manager
        staff = await db.get_team_staff(self.team['id'])
        is_captain = interaction.user.id == self.team['captain_id']
        is_manager = interaction.user.id in [staff.get('manager_1_id'), staff.get('manager_2_id')] if staff else False
        
        if not (is_captain or is_manager):
            await interaction.response.send_message("Only the captain or existing managers can approve.", ephemeral=True)
            return
        
        if self.approved:
            await interaction.response.send_message("This request has already been processed.", ephemeral=True)
            return
        
        self.approved = True
        
        # Check which slot is available and add manager
        manager_1_id = staff.get('manager_1_id') if staff else None
        manager_2_id = staff.get('manager_2_id') if staff else None
        
        if not manager_1_id:
            await db.add_team_manager(self.team['id'], self.manager_user.id, slot=1)
            slot_number = 1
        elif not manager_2_id:
            await db.add_team_manager(self.team['id'], self.manager_user.id, slot=2)
            slot_number = 2
        else:
            await interaction.response.send_message("Team already has 2 managers.", ephemeral=True)
            return
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        
        # Notify in DM
        await interaction.followup.send(
            f"You've accepted **{self.manager_user.mention}** as manager for **{self.team['name']}**.",
            ephemeral=True
        )
        
        # Notify in thread
        await self.thread.send(
            f"**Manager Registration Approved**\n\n"
            f"{self.manager_user.mention}, you are now manager {slot_number} of **{self.team['name']}** [{self.team['tag']}].\n"
            f"Approved by: {interaction.user.mention}"
        )
        
        # Log to admin logs
        log_channel_id = cfg("log_channel_id")
        if log_channel_id:
            try:
                log_channel = interaction.client.get_channel(int(log_channel_id))
                if log_channel:
                    log_embed = discord.Embed(
                        title="Manager Registered",
                        color=discord.Color.blue(),
                        timestamp=discord.utils.utcnow()
                    )
                    log_embed.add_field(name="Manager", value=f"{self.manager_user.mention} ({self.manager_ign})", inline=False)
                    log_embed.add_field(name="Team", value=f"{self.team['name']} [{self.team['tag']}]", inline=False)
                    log_embed.add_field(name="Slot", value=f"Manager {slot_number}", inline=False)
                    log_embed.add_field(name="Approved by", value=interaction.user.mention, inline=False)
                    log_embed.set_footer(text=f"Manager ID: {self.manager_user.id} | Team ID: {self.team['id']}")
                    await log_channel.send(embed=log_embed)
            except:
                pass
        
        # Close thread after 5 seconds
        await asyncio.sleep(5)
        try:
            await self.thread.edit(archived=True, locked=True)
        except:
            pass
    
    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger, custom_id="decline_manager")
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Decline the manager request"""
        # Check if user is captain or manager
        staff = await db.get_team_staff(self.team['id'])
        is_captain = interaction.user.id == self.team['captain_id']
        is_manager = interaction.user.id in [staff.get('manager_1_id'), staff.get('manager_2_id')] if staff else False
        
        if not (is_captain or is_manager):
            await interaction.response.send_message("Only the captain or existing managers can decline.", ephemeral=True)
            return
        
        if self.approved:
            await interaction.response.send_message("This request has already been processed.", ephemeral=True)
            return
        
        self.approved = True
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)
        
        # Notify in DM
        await interaction.followup.send(
            f"You've declined **{self.manager_user.mention}** as manager for **{self.team['name']}**.",
            ephemeral=True
        )
        
        # Notify in thread
        await self.thread.send(
            f"**Manager Registration Declined**\n\n"
            f"{self.manager_user.mention}, your request to manage **{self.team['name']}** was declined by {interaction.user.mention}."
        )
        
        # Close thread after 5 seconds
        await asyncio.sleep(5)
        try:
            await self.thread.edit(archived=True, locked=True)
        except:
            pass


class ManagerRegistration(commands.Cog):
    """Cog for manager registration system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.ui_sent = False
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Setup persistent view and send UI on bot ready"""
        self.bot.add_view(ManagerRegistrationView())
        
        # Auto-send UI to manager registration channel
        if not self.ui_sent:
            manager_channel_id = cfg("channel_manager_reg_id")
            if manager_channel_id:
                try:
                    channel = self.bot.get_channel(int(manager_channel_id))
                    if channel:
                        # Purge all messages in the channel
                        await channel.purge(limit=100)
                        
                        # Send the registration UI
                        embed = discord.Embed(
                            title="Manager Registration",
                            description=(
                                "Want to become a manager for a team? Click the button below to get started.\n\n"
                                "**Requirements:**\n"
                                "• The team must have less than 2 managers\n"
                                "• Team captain or existing manager must approve your request\n\n"
                                "**Process:**\n"
                                "1. Click the Register button\n"
                                "2. Select the team you want to manage\n"
                                "3. Wait for captain/manager approval\n"
                                "4. Get notified once approved"
                            ),
                            color=discord.Color.blue()
                        )
                        embed.set_footer(text="Managers help organize and lead their teams!")
                        
                        view = ManagerRegistrationView()
                        await channel.send(embed=embed, view=view)
                        
                        self.ui_sent = True
                        print(f"Manager registration UI sent to channel {manager_channel_id}")
                except Exception as e:
                    print(f"Error setting up manager registration UI: {e}")
        
        print("Manager Registration cog loaded")
    
    @app_commands.command(name="setup-manager-registration", description="[ADMIN] Setup manager registration UI in this channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_manager_registration(self, interaction: discord.Interaction):
        """Setup the manager registration message with button"""
        
        embed = discord.Embed(
            title="Manager Registration",
            description=(
                "Want to become a manager for a team? Click the button below to get started.\n\n"
                "**Requirements:**\n"
                "• The team must have less than 2 managers\n"
                "• Team captain or existing manager must approve your request\n\n"
                "**Process:**\n"
                "1. Click the Register button\n"
                "2. Select the team you want to manage\n"
                "3. Wait for captain/manager approval\n"
                "4. Get notified once approved"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Managers help organize and lead their teams!")
        
        view = ManagerRegistrationView()
        
        await interaction.response.send_message(
            "Manager registration UI has been set up.",
            ephemeral=True
        )
        
        await interaction.channel.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(ManagerRegistration(bot))
