import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from pathlib import Path
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

# --- Views for Interactions ---
class TeamInviteView(discord.ui.View):
    def __init__(self, captain: discord.Member, invited_player: discord.Member, team: dict):
        super().__init__(timeout=300)  # 5-minute timeout
        self.captain = captain
        self.invited_player = invited_player
        self.team = team
        self.message = None

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(content="This invitation has expired.", view=self)

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.invited_player.id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return

        # Add member to team in database
        try:
            await db.add_team_member(self.team['id'], self.invited_player.id)
        except Exception as e:
            print(f"Error adding team member: {e}")
            await interaction.response.send_message("Failed to join the team. Please try again.", ephemeral=True)
            return

        # Disable buttons and update message
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(content=f"Invitation to join `{self.team['name']}` approved.", view=self)
        
        # Notify captain
        await self.captain.send(f"`{self.invited_player.display_name}` has accepted your invitation to join `{self.team['name']}`.")
        await interaction.response.send_message(f"You have successfully joined `{self.team['name']}`!", ephemeral=True)

        # Send log to logs channel
        try:
            log_channel_id = cfg('LOG_CHANNEL_ID')
            if log_channel_id:
                bot = interaction.client
                log_channel = bot.get_channel(int(log_channel_id))
                if log_channel:
                    # Extract member count
                    members_data = self.team.get('members', [])
                    if isinstance(members_data, str):
                        import json
                        members_data = json.loads(members_data)
                    member_count = len(members_data) if isinstance(members_data, list) else 0
                    
                    log_embed = discord.Embed(
                        title="👥 Player Joined Team",
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow()
                    )
                    log_embed.add_field(name="Team", value=f"**{self.team['name']}** [{self.team.get('tag', 'N/A')}]", inline=False)
                    log_embed.add_field(name="New Member", value=f"{self.invited_player.mention} ({self.invited_player})", inline=False)
                    log_embed.add_field(name="Captain", value=f"{self.captain.mention} ({self.captain})", inline=False)
                    log_embed.add_field(name="Total Members", value=str(member_count + 1), inline=True)
                    log_embed.set_thumbnail(url=self.invited_player.display_avatar.url)
                    log_embed.set_footer(text=f"Player ID: {self.invited_player.id}")
                    
                    await log_channel.send(embed=log_embed)
        except Exception as log_error:
            print(f"Error sending team join log: {log_error}")


    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.invited_player.id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return

        # Disable buttons and update message
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(content=f"Invitation to join `{self.team['name']}` declined.", view=self)

        # Notify captain
        await self.captain.send(f"`{self.invited_player.display_name}` has declined your invitation to join `{self.team['name']}`.")
        await interaction.response.send_message("You have declined the invitation.", ephemeral=True)


class Teams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="register-team", description="Register a new team")
    @app_commands.describe(name="The name of your team", tag="Your team's tag (e.g., VA)", region="The region your team will play in")
    @app_commands.choices(region=[
        app_commands.Choice(name="North America (NA)", value="na"),
        app_commands.Choice(name="Europe (EU)", value="eu"),
        app_commands.Choice(name="Asia-Pacific (AP)", value="ap"),
        app_commands.Choice(name="Korea (KR)", value="kr"),
        app_commands.Choice(name="Brazil (BR)", value="br"),
        app_commands.Choice(name="Latin America (LATAM)", value="latam"),
        app_commands.Choice(name="Japan (JP)", value="jp"),
    ])
    async def register_team(self, interaction: discord.Interaction, name: str, tag: str, region: app_commands.Choice[str]):
        """Register a new team."""
        # Defer response immediately to avoid timeout
        await interaction.response.defer(ephemeral=True)

        # --- Player Registration and Region Check (using PostgreSQL) ---
        try:
            from services import db
            captain_player_data = await db.get_player(interaction.user.id)
        except Exception as e:
            print(f"Error getting player from database: {e}")
            captain_player_data = None

        if not captain_player_data:
            await interaction.followup.send("You must be a registered player to create a team. Use `/register` first.", ephemeral=True)
            return

        if captain_player_data.get('region') != region.value:
            await interaction.followup.send(f"You can only register a team in your own region (`{captain_player_data.get('region')}`).", ephemeral=True)
            return

        # --- Validation Checks (using PostgreSQL) ---
        # Check if player is already in a team
        existing_team = await db.get_player_team(interaction.user.id)
        if existing_team:
            await interaction.followup.send(f"You are already part of a team (`{existing_team['name']}`). You cannot register a new one.", ephemeral=True)
            return

        # Check if team name already exists
        existing_by_name = await db.get_team_by_name(name)
        if existing_by_name:
            await interaction.followup.send(f"A team with the name `{name}` already exists.", ephemeral=True)
            return

        # Check if tag already exists (manual check since we don't have get_team_by_tag)
        try:
            all_teams = await db.get_all_teams()
            for team in all_teams:
                if team['tag'].lower() == tag.lower():
                    await interaction.followup.send(f"A team with the tag `{tag}` already exists.", ephemeral=True)
                    return
        except Exception as e:
            print(f"Error checking existing tags: {e}")

        # --- Create New Team in Database ---
        try:
            new_team = await db.create_team(
                name=name,
                tag=tag,
                captain_id=interaction.user.id,
                region=region.value,
                logo_url=None
            )
            print(f"✅ Created team: {new_team}")
            
            # Add team to leaderboards with initial stats
            if isinstance(new_team, dict):
                team_id = new_team.get('id')
            else:
                # If new_team is not a dict, try to get the team by name
                team_data = await db.get_team_by_name(name)
                team_id = team_data.get('id') if team_data else None
            
            if team_id:
                # Check if captain has India role
                is_india = region.value.lower() == 'india'
                if not is_india and interaction.guild:
                    try:
                        member = interaction.user
                        india_role = discord.utils.get(member.roles, name="India")
                        is_india = india_role is not None
                    except:
                        pass
                
                # Add to leaderboards
                await db.update_team_leaderboard(
                    team_id,
                    name,
                    tag,
                    region.value,
                    None,  # No logo yet
                    is_india
                )
                
                # Update ranks for all leaderboards
                for lb_type in ['global', 'apac', 'emea', 'americas', 'india']:
                    try:
                        await db.update_team_leaderboard_ranks(lb_type)
                    except:
                        pass
                
                print(f"✅ Added team to leaderboards")
            else:
                print(f"⚠️ Could not get team_id, skipping leaderboard update")
                
        except Exception as e:
            print(f"Error creating team: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"Failed to create team: {e}", ephemeral=True)
            return

        await interaction.followup.send(f"Team `{name}` with tag `[{tag}]` has been successfully registered in the {region.name} region! You are the captain.", ephemeral=True)

        # Send log to logs channel
        try:
            log_channel_id = cfg('LOG_CHANNEL_ID')
            if log_channel_id:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    log_embed = discord.Embed(
                        title="🏆 New Team Registration",
                        color=discord.Color.gold(),
                        timestamp=discord.utils.utcnow()
                    )
                    log_embed.add_field(name="Team Name", value=name, inline=True)
                    log_embed.add_field(name="Team Tag", value=f"[{tag}]", inline=True)
                    log_embed.add_field(name="Region", value=region.name, inline=True)
                    log_embed.add_field(name="Captain", value=f"{interaction.user.mention} ({interaction.user})", inline=False)
                    log_embed.add_field(name="Captain IGN", value=captain_player_data.get('ign', 'Unknown'), inline=True)
                    log_embed.add_field(name="Discord ID", value=str(interaction.user.id), inline=True)
                    log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                    log_embed.set_footer(text=f"Team Captain ID: {interaction.user.id}")
                    
                    await log_channel.send(embed=log_embed)
        except Exception as log_error:
            print(f"Error sending team registration log: {log_error}")

    @app_commands.command(name="set-logo", description="Set your team's logo (Captain only)")
    @app_commands.describe(logo="The logo image file")
    async def set_logo(self, interaction: discord.Interaction, logo: discord.Attachment):
        """Sets the team's logo from an uploaded file."""
        captain_id = interaction.user.id

        # Image validation
        if not logo.content_type or not logo.content_type.startswith('image/'):
            await interaction.response.send_message("The uploaded file must be an image.", ephemeral=True)
            return

        # Get captain's team from database
        captain_team = await db.get_team_by_captain(captain_id)

        if not captain_team:
            await interaction.response.send_message("You are not the captain of any team.", ephemeral=True)
            return

        # Update logo URL with the attachment's URL
        await db.update_team_logo(captain_team['id'], logo.url)
        
        # Update team in leaderboards with new logo
        try:
            # Check if captain has India role
            is_india = captain_team['region'].lower() == 'india'
            if not is_india and interaction.guild:
                try:
                    member = interaction.user
                    india_role = discord.utils.get(member.roles, name="India")
                    is_india = india_role is not None
                except:
                    pass
            
            await db.update_team_leaderboard(
                captain_team['id'],
                captain_team['name'],
                captain_team['tag'],
                captain_team['region'],
                logo.url,  # New logo
                is_india
            )
            print(f"✅ Updated team logo in leaderboards")
        except Exception as e:
            print(f"Error updating team logo in leaderboards: {e}")

        await interaction.response.send_message(f"Team logo has been updated! You can see it by using the `/team-profile` command.", ephemeral=True)

    @app_commands.command(name="invite-player", description="Invite a player to your team")
    @app_commands.describe(player="The player to invite")
    async def invite_player(self, interaction: discord.Interaction, player: discord.Member):
        """Invites a player to the captain's team."""
        # Defer response immediately to avoid timeout
        await interaction.response.defer(ephemeral=True)
        
        captain_id = interaction.user.id

        # Get captain's team from database
        captain_team = await db.get_team_by_captain(captain_id)
        
        if not captain_team:
            await interaction.followup.send("You are not the captain of any team.", ephemeral=True)
            return

        # Check if player is registered (using PostgreSQL)
        player_data = await db.get_player(player.id)
        if not player_data:
            await interaction.followup.send(f"`{player.display_name}` is not a registered player. They must use `/register` first.", ephemeral=True)
            return
            
        if player.id == captain_id:
            await interaction.followup.send("You cannot invite yourself to your own team.", ephemeral=True)
            return

        # Check if player is already in a team
        player_team = await db.get_player_team(player.id)
        if player_team:
            await interaction.followup.send(f"`{player.display_name}` is already in a team (`{player_team['name']}`).", ephemeral=True)
            return

        try:
            view = TeamInviteView(interaction.user, player, captain_team)
            invite_message = await player.send(f"You have been invited to join `{captain_team['name']}` by `{interaction.user.display_name}`.", view=view)
            view.message = invite_message
            await interaction.followup.send(f"An invitation has been sent to `{player.display_name}`.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send(f"I could not send a DM to `{player.display_name}`. They may have DMs disabled.", ephemeral=True)

    @app_commands.command(name="leave-team", description="Leave your current team")
    async def leave_team(self, interaction: discord.Interaction):
        """Allows a player to leave their team."""
        user_id = interaction.user.id

        # Get player's team from database
        player_team = await db.get_player_team(user_id)
        
        if not player_team:
            await interaction.response.send_message("You are not in any team.", ephemeral=True)
            return

        # Check if player is the captain
        if user_id == player_team['captain_id']:
            await interaction.response.send_message("You are the captain. You cannot leave; you must disband the team.", ephemeral=True)
            return

        # Remove player from team
        await db.remove_team_member(player_team['id'], user_id)

        # Notify captain
        try:
            captain = await self.bot.fetch_user(player_team['captain_id'])
            await captain.send(f"`{interaction.user.display_name}` has left your team, `{player_team['name']}`.")
        except discord.Forbidden:
            pass # Can't send DM

        await interaction.response.send_message(f"You have successfully left `{player_team['name']}`.", ephemeral=True)


    @app_commands.command(name="kick-player", description="Kick a player from your team (Captain only)")
    @app_commands.describe(player="The player to kick")
    async def kick_player(self, interaction: discord.Interaction, player: discord.Member):
        """Allows a captain to kick a player from their team."""
        captain_id = interaction.user.id
        player_to_kick_id = player.id

        # Get captain's team from database
        captain_team = await db.get_team_by_captain(captain_id)

        if not captain_team:
            await interaction.response.send_message("You are not the captain of any team.", ephemeral=True)
            return
            
        if captain_id == player_to_kick_id:
            await interaction.response.send_message("You cannot kick yourself.", ephemeral=True)
            return

        # Extract member IDs from member objects
        members_data = captain_team.get('members', [])
        if isinstance(members_data, str):
            import json
            members_data = json.loads(members_data)
        
        team_member_ids = [member['discord_id'] for member in members_data if isinstance(member, dict)]
        
        # Check if player is in the team
        if player_to_kick_id not in team_member_ids:
            await interaction.response.send_message(f"`{player.display_name}` is not in your team.", ephemeral=True)
            return

        # Kick player from team
        await db.remove_team_member(captain_team['id'], player_to_kick_id)

        # Notify kicked player
        try:
            await player.send(f"You have been kicked from `{captain_team['name']}` by the captain.")
        except discord.Forbidden:
            pass # Can't send DM

        await interaction.response.send_message(f"You have successfully kicked `{player.display_name}` from the team.", ephemeral=True)

    @app_commands.command(name="disband", description="Disband your team (Captain only)")
    async def disband_team(self, interaction: discord.Interaction):
        """Allows a captain to completely disband their team."""
        # Defer response to avoid timeout
        await interaction.response.defer(ephemeral=True)
        
        captain_id = interaction.user.id

        # Get captain's team from database
        captain_team = await db.get_team_by_captain(captain_id)

        if not captain_team:
            await interaction.followup.send("You are not the captain of any team.", ephemeral=True)
            return

        # Store team info before deletion for notifications
        team_name = captain_team['name']
        team_tag = captain_team['tag']
        team_region = captain_team.get('region', 'Unknown')
        team_wins = captain_team.get('wins', 0)
        team_losses = captain_team.get('losses', 0)
        
        # Extract member IDs from member objects
        members_data = captain_team.get('members', [])
        if isinstance(members_data, str):
            import json
            members_data = json.loads(members_data)
        
        team_member_ids = [member['discord_id'] for member in members_data if isinstance(member, dict)]
        
        # Delete the team (cascade will remove team_members entries)
        await db.delete_team(captain_team['id'])

        # Notify all team members (except captain)
        for member_id in team_member_ids:
            if member_id != captain_id:
                try:
                    member = await self.bot.fetch_user(member_id)
                    await member.send(f"The team `{team_name}` [{team_tag}] has been disbanded by the captain.")
                except (discord.Forbidden, discord.NotFound):
                    pass  # Can't send DM or user not found

        await interaction.followup.send(f"Your team `{team_name}` [{team_tag}] has been successfully disbanded.", ephemeral=True)

        # Send log to logs channel
        try:
            log_channel_id = cfg('LOG_CHANNEL_ID')
            if log_channel_id:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    log_embed = discord.Embed(
                        title="💔 Team Disbanded",
                        color=discord.Color.red(),
                        timestamp=discord.utils.utcnow()
                    )
                    log_embed.add_field(name="Team Name", value=team_name, inline=True)
                    log_embed.add_field(name="Team Tag", value=f"[{team_tag}]", inline=True)
                    log_embed.add_field(name="Region", value=team_region, inline=True)
                    log_embed.add_field(name="Captain", value=f"{interaction.user.mention} ({interaction.user})", inline=False)
                    log_embed.add_field(name="Members at Disbandment", value=str(len(team_member_ids)), inline=True)
                    log_embed.add_field(name="Record", value=f"{team_wins}W - {team_losses}L", inline=True)
                    log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                    log_embed.set_footer(text=f"Captain ID: {captain_id}")
                    
                    await log_channel.send(embed=log_embed)
        except Exception as log_error:
            print(f"Error sending team disbandment log: {log_error}")

async def setup(bot):
    await bot.add_cog(Teams(bot))
