import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import asyncio
import os
from typing import Optional
from services import db


class RegionSelectView(View):
    """View for selecting team region"""
    def __init__(self):
        super().__init__(timeout=60)
        self.selected_region = None
        
    @discord.ui.button(label="🌎 NA", style=discord.ButtonStyle.primary)
    async def na_button(self, interaction: discord.Interaction, button: Button):
        await self.select_region(interaction, "na", "North America")
    
    @discord.ui.button(label="🌍 EU", style=discord.ButtonStyle.primary)
    async def eu_button(self, interaction: discord.Interaction, button: Button):
        await self.select_region(interaction, "eu", "Europe")
    
    @discord.ui.button(label="🌏 ASIA", style=discord.ButtonStyle.primary)
    async def asia_button(self, interaction: discord.Interaction, button: Button):
        await self.select_region(interaction, "ap", "Asia")
    
    @discord.ui.button(label="🌏 SEA", style=discord.ButtonStyle.primary)
    async def sea_button(self, interaction: discord.Interaction, button: Button):
        await self.select_region(interaction, "ap", "Southeast Asia")
    
    @discord.ui.button(label="🌎 LATAM", style=discord.ButtonStyle.primary)
    async def latam_button(self, interaction: discord.Interaction, button: Button):
        await self.select_region(interaction, "latam", "Latin America")
    
    @discord.ui.button(label="🌏 OCE", style=discord.ButtonStyle.primary)
    async def oce_button(self, interaction: discord.Interaction, button: Button):
        await self.select_region(interaction, "ap", "Oceania")
    
    async def select_region(self, interaction: discord.Interaction, region_code: str, region_name: str):
        """Handle region selection"""
        self.selected_region = region_code
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"✅ Selected region: **{region_name}**", ephemeral=True)
        self.stop()


class ContinueAddingView(View):
    """View for continuing to add players or finishing"""
    def __init__(self):
        super().__init__(timeout=60)
        self.continue_adding = None
    
    @discord.ui.button(label="✅ Finish Registration", style=discord.ButtonStyle.success)
    async def finish_button(self, interaction: discord.Interaction, button: Button):
        self.continue_adding = False
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("✅ Finalizing team registration...", ephemeral=True)
        self.stop()
    
    @discord.ui.button(label="➕ Add More Players", style=discord.ButtonStyle.primary)
    async def continue_button(self, interaction: discord.Interaction, button: Button):
        self.continue_adding = True
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("✅ Continue adding players...", ephemeral=True)
        self.stop()


class AdminTeamRegister(commands.Cog):
    """Interactive team registration for admins to help users"""
    
    def __init__(self, bot):
        self.bot = bot

        # Built-in allowed role names (case-insensitive)
        self.allowed_role_names = [
            "admin", "administrator", "moderator", "mod", 
            "owner", "staff", "manager"
        ]

        # Read role and channel IDs from environment (.env)
        # Expected env keys: ROLE_APAC_ID, ROLE_EMEA_ID, ROLE_AMERICAS_ID
        # CHANNEL_PLAYER_REG_ID (normal player registration)
        # CHANNEL_PLAYER_FORCE_REG_ID (admin force player registration)
        # CHANNEL_TEAM_REG_ID (normal team registration)
        # CHANNEL_TEAM_INTERACTIVE_REG_ID (admin interactive team registration)
        def _env_int(key: str):
            v = os.getenv(key)
            try:
                return int(v) if v else None
            except:
                return None

        self.role_apac_id = _env_int('ROLE_APAC_ID')
        self.role_emea_id = _env_int('ROLE_EMEA_ID')
        self.role_americas_id = _env_int('ROLE_AMERICAS_ID')

        # Normal registration channels (for existing /register commands)
        self.player_reg_channel_id = _env_int('CHANNEL_PLAYER_REG_ID')
        self.team_reg_channel_id = _env_int('CHANNEL_TEAM_REG_ID')
        
        # Admin/force registration channels (for interactive commands)
        self.player_force_reg_channel_id = _env_int('CHANNEL_PLAYER_FORCE_REG_ID')
        self.team_interactive_reg_channel_id = _env_int('CHANNEL_TEAM_INTERACTIVE_REG_ID')

    def _get_role_id_for_region(self, region_code: str) -> Optional[int]:
        """Map region code to one of the three role IDs (APAC/EMEA/AMERICAS)"""
        rc = (region_code or '').lower()
        # APAC covers 'ap', 'asia', 'oce', 'sea'
        if rc in ('ap', 'asia', 'oce', 'sea'):
            return self.role_apac_id
        # EMEA / EU
        if rc in ('eu', 'emea'):
            return self.role_emea_id
        # Americas covers NA and LATAM
        if rc in ('na', 'americas', 'latam', 'north-america', 'south-america'):
            return self.role_americas_id
        return None

    async def _assign_region_role(self, guild: discord.Guild, discord_id: int, region_code: str):
        """Assign region role to a guild member if role ID exists in env."""
        role_id = self._get_role_id_for_region(region_code)
        if not role_id:
            return
        try:
            member = guild.get_member(discord_id)
            if not member:
                return
            role = guild.get_role(role_id)
            if not role:
                return
            if role not in member.roles:
                await member.add_roles(role, reason='Regional role assigned on registration')
        except Exception:
            # don't block registration on role errors
            return
    
    def has_admin_permissions(self, member: discord.Member) -> bool:
        """Check if user has admin permissions"""
        # Check if user has Administrator permission
        if member.guild_permissions.administrator:
            return True
        
        # Check if user has an allowed role
        for role in member.roles:
            if role.name.lower() in self.allowed_role_names:
                return True
        
        return False
    
    @app_commands.command(
        name="register-team-interactive",
        description="Register a team interactively (Admin only)"
    )
    async def register_team_interactive(self, interaction: discord.Interaction):
        """Interactive team registration command"""
        
        # Phase 0: Permission Check
        if not self.has_admin_permissions(interaction.user):
            await interaction.response.send_message(
                "❌ **Permission Denied**\n\n"
                "You need Administrator permissions or an admin role to use this command.",
                ephemeral=True
            )
            return
        
        # Enforce interactive team registration channel if configured
        if self.team_interactive_reg_channel_id and interaction.channel.id != self.team_interactive_reg_channel_id:
            await interaction.response.send_message(
                f"❌ Interactive team registrations are only allowed in the configured channel.",
                ephemeral=True
            )
            return

        # Create a thread for registration
        await interaction.response.defer(ephemeral=True)

        try:
            thread = await interaction.channel.create_thread(
                name=f"Team Registration - {interaction.user.display_name}",
                auto_archive_duration=60,
                reason=f"Interactive team registration by {interaction.user.display_name}"
            )
            
            await interaction.followup.send(
                f"✅ **Interactive Team Registration Started!**\n"
                f"Please continue in the thread: {thread.mention}\n\n"
                f"Type `cancel` at any time to cancel registration.",
                ephemeral=True
            )
            
            await thread.send(
                f"{interaction.user.mention} **Welcome to Team Registration!**\n\n"
                f"🔹 Answer each question step by step\n"
                f"🔹 Type `cancel` at any time to stop and delete this thread\n"
                f"🔹 Each step has a 60-second timeout\n\n"
                f"Let's get started! 🚀"
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Failed to create thread: {str(e)}",
                ephemeral=True
            )
            return
        
        author = interaction.user
        
        def check(m):
            return m.author == author and m.channel == thread
        
        try:
            # Phase 1: Team Name
            await thread.send(f"{author.mention} **Step 1/5: Team Name**\nPlease enter the team name:")
            
            try:
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                
                # Check for cancellation
                if msg.content.lower() == 'cancel':
                    await thread.send("❌ Registration cancelled. This thread will be deleted in 5 seconds...")
                    await asyncio.sleep(5)
                    await thread.delete()
                    return
                
                team_name = msg.content.strip()
                
                # Check if team name already exists
                existing_team = await db.get_team_by_name(team_name)
                if existing_team:
                    await thread.send(f"❌ Team name **{team_name}** already exists! Registration cancelled.\nThis thread will be deleted in 5 seconds...")
                    await asyncio.sleep(5)
                    await thread.delete()
                    return
                
                await thread.send(f"✅ Team name: **{team_name}**")
                
            except asyncio.TimeoutError:
                await thread.send("❌ Registration timed out (60s). This thread will be deleted in 5 seconds...")
                await asyncio.sleep(5)
                await thread.delete()
                return
            
            # Phase 2: Region Selection
            await thread.send(f"{author.mention} **Step 2/5: Region**\nSelect the team's region:")
            
            region_view = RegionSelectView()
            region_msg = await thread.send("Click a button to select region:", view=region_view)
            
            await region_view.wait()
            
            if region_view.selected_region is None:
                await thread.send("❌ No region selected. Registration cancelled.\nThis thread will be deleted in 5 seconds...")
                await asyncio.sleep(5)
                await thread.delete()
                return
            
            region = region_view.selected_region
            
            # Phase 3: Captain
            await thread.send(
                f"{author.mention} **Step 3/5: Captain**\n"
                f"Please mention the captain (e.g., @username):"
            )
            
            try:
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                
                # Check for cancellation
                if msg.content.lower() == 'cancel':
                    await thread.send("❌ Registration cancelled. This thread will be deleted in 5 seconds...")
                    await asyncio.sleep(5)
                    await thread.delete()
                    return
                
                if not msg.mentions:
                    await thread.send("❌ No user mentioned. Registration cancelled.\nThis thread will be deleted in 5 seconds...")
                    await asyncio.sleep(5)
                    await thread.delete()
                    return
                
                captain = msg.mentions[0]
                await thread.send(f"✅ Captain: {captain.mention}")
                
                # Get captain IGN
                await thread.send(f"What is {captain.mention}'s in-game name (IGN)?")
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                
                # Check for cancellation
                if msg.content.lower() == 'cancel':
                    await thread.send("❌ Registration cancelled. This thread will be deleted in 5 seconds...")
                    await asyncio.sleep(5)
                    await thread.delete()
                    return
                
                captain_ign = msg.content.strip()
                
                await thread.send(f"✅ Captain IGN: **{captain_ign}**")
                
            except asyncio.TimeoutError:
                await thread.send("❌ Registration timed out. This thread will be deleted in 5 seconds...")
                await asyncio.sleep(5)
                await thread.delete()
                return
            
            # Phase 4: Additional Players
            players = [
                {
                    'discord_id': captain.id,
                    'ign': captain_ign,
                    'user': captain
                }
            ]
            
            await thread.send(
                f"{author.mention} **Step 4/5: Team Roster**\n"
                f"Current roster: **{len(players)}/8** players\n\n"
                f"Add more players by mentioning them and providing their IGN.\n"
                f"You need at least 5 players total.\n\n"
                f"**Format:** @player\n(then type their IGN in the next message)\n\n"
                f"Type `done` when finished adding players, or `cancel` to cancel."
            )
            
            while len(players) < 8:
                try:
                    msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                    
                    # Check for cancellation
                    if msg.content.lower() == 'cancel':
                        await thread.send("❌ Registration cancelled. This thread will be deleted in 5 seconds...")
                        await asyncio.sleep(5)
                        await thread.delete()
                        return
                    
                    if msg.content.lower() == 'done':
                        if len(players) < 5:
                            await thread.send(
                                f"⚠️ You need at least 5 players. Currently have {len(players)}. "
                                f"Please add {5 - len(players)} more."
                            )
                            continue
                        else:
                            break
                    
                    if not msg.mentions:
                        await thread.send("⚠️ Please mention a player, type `done` to finish, or `cancel` to cancel.")
                        continue
                    
                    player = msg.mentions[0]
                    
                    # Check if player already added
                    if any(p['discord_id'] == player.id for p in players):
                        await thread.send(f"⚠️ {player.mention} is already in the roster!")
                        continue
                    
                    # Get player IGN
                    await thread.send(f"What is {player.mention}'s in-game name (IGN)?")
                    ign_msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                    
                    # Check for cancellation
                    if ign_msg.content.lower() == 'cancel':
                        await thread.send("❌ Registration cancelled. This thread will be deleted in 5 seconds...")
                        await asyncio.sleep(5)
                        await thread.delete()
                        return
                    
                    player_ign = ign_msg.content.strip()
                    
                    players.append({
                        'discord_id': player.id,
                        'ign': player_ign,
                        'user': player
                    })
                    
                    await thread.send(
                        f"✅ Added {player.mention} ({player_ign})\n"
                        f"Current roster: **{len(players)}/8** players"
                    )
                    
                    # After 5 players, offer to finish or continue
                    if len(players) >= 5 and len(players) < 8:
                        continue_view = ContinueAddingView()
                        await thread.send(
                            f"You have {len(players)} players. Do you want to:",
                            view=continue_view
                        )
                        await continue_view.wait()
                        
                        if continue_view.continue_adding is False:
                            break
                        elif continue_view.continue_adding is None:
                            await thread.send("❌ Timed out. Registration cancelled.\nThis thread will be deleted in 5 seconds...")
                            await asyncio.sleep(5)
                            await thread.delete()
                            return
                    
                except asyncio.TimeoutError:
                    await thread.send("❌ Registration timed out. This thread will be deleted in 5 seconds...")
                    await asyncio.sleep(5)
                    await thread.delete()
                    return
            
            # Phase 5: Finalization
            await thread.send(f"{author.mention} **Step 5/5: Finalizing Registration...**")
            
            # Generate team tag from first 3 letters of team name
            team_tag = team_name[:3].upper()
            
            # Create team in database
            try:
                # Create team
                team = await db.create_team(
                    name=team_name,
                    tag=team_tag,
                    region=region,
                    captain_discord_id=captain.id,
                    members=[
                        {
                            'discord_id': p['discord_id'],
                            'ign': p['ign']
                        } for p in players
                    ]
                )
                
                # Register each player in player_leaderboard
                for player_data in players:
                    # Check if player exists
                    existing_player = await db.get_player_by_discord_id(player_data['discord_id'])
                    
                    if not existing_player:
                        # Create new player
                        await db.create_player_leaderboard(
                            discord_id=player_data['discord_id'],
                            ign=player_data['ign'],
                            team_id=team['id'],
                            region=region
                        )
                    else:
                        # Update existing player
                        await db.update_player_team(
                            player_data['discord_id'],
                            team['id']
                        )
                
                # Try to set nicknames (IGN | TeamName)
                for player_data in players:
                    try:
                        member = interaction.guild.get_member(player_data['discord_id'])
                        if member:
                            new_nick = f"{player_data['ign']} | {team_name}"
                            await member.edit(nick=new_nick[:32])  # Discord nick limit is 32 chars
                    except:
                        pass  # Ignore failures
                
                # Create success embed
                embed = discord.Embed(
                    title="✅ Team Registered Successfully!",
                    description=f"**{team_name}** [{team_tag}] has been created!",
                    color=0x00ff00
                )
                
                embed.add_field(
                    name="Team ID",
                    value=f"`{team['id']}`",
                    inline=True
                )
                
                embed.add_field(
                    name="Region",
                    value=region.upper(),
                    inline=True
                )
                
                embed.add_field(
                    name="Captain",
                    value=f"{captain.mention} ({captain_ign})",
                    inline=False
                )
                
                roster_text = "\n".join([
                    f"• {p['user'].mention} - {p['ign']}"
                    for p in players
                ])
                
                embed.add_field(
                    name=f"Roster ({len(players)} players)",
                    value=roster_text,
                    inline=False
                )
                
                embed.set_footer(text=f"Registered by {author.display_name}")
                embed.timestamp = discord.utils.utcnow()
                
                await thread.send(embed=embed)
                await thread.send(f"✅ **Registration complete!** This thread will remain open for reference.")
                
            except Exception as e:
                await thread.send(
                    f"❌ **Error creating team:**\n```\n{str(e)}\n```\n"
                    f"Please contact a developer.\nThis thread will be deleted in 10 seconds..."
                )
                import traceback
                traceback.print_exc()
                await asyncio.sleep(10)
                await thread.delete()
        
        except Exception as e:
            try:
                await thread.send(
                    f"❌ **An error occurred:**\n```\n{str(e)}\n```\n"
                    f"Registration cancelled. This thread will be deleted in 10 seconds..."
                )
                await asyncio.sleep(10)
                await thread.delete()
            except:
                pass
            import traceback
            traceback.print_exc()

    @app_commands.command(
        name="force-player-reg",
        description="Force register a player interactively (Admin only)"
    )
    async def force_player_reg(self, interaction: discord.Interaction):
        """Interactive player registration forced by admin"""
        if not self.has_admin_permissions(interaction.user):
            await interaction.response.send_message("❌ Permission denied.", ephemeral=True)
            return

        # Enforce force player registration channel if configured
        if self.player_force_reg_channel_id and interaction.channel.id != self.player_force_reg_channel_id:
            await interaction.response.send_message(
                "❌ Force player registrations are only allowed in the configured channel.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            thread = await interaction.channel.create_thread(
                name=f"Player Registration - {interaction.user.display_name}",
                auto_archive_duration=60,
                reason=f"Interactive player registration by {interaction.user.display_name}"
        )

            await interaction.followup.send(
                f"✅ **Interactive Player Registration Started!**\nContinue in the thread: {thread.mention}",
                ephemeral=True
            )

            await thread.send(
                f"{interaction.user.mention} **Player Registration**\n\n"
                f"🔹 Mention the player to register (e.g. @player)\n"
                f"🔹 Type `cancel` at any time to cancel and delete this thread\n"
            )

        except Exception as e:
            await interaction.followup.send(f"❌ Failed to create thread: {e}", ephemeral=True)
            return

        author = interaction.user

        def check(m):
            return m.author == author and m.channel == thread

        try:
            # Ask for player mention
            await thread.send("Please mention the player to register:")
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            if msg.content.lower() == 'cancel':
                await thread.send("❌ Registration cancelled. Deleting thread in 5s...")
                await asyncio.sleep(5)
                await thread.delete()
                return

            if not msg.mentions:
                await thread.send("❌ No user mentioned. Cancelling.")
                await asyncio.sleep(5)
                await thread.delete()
                return

            player = msg.mentions[0]

            # Ask for IGN
            await thread.send(f"What is {player.mention}'s in-game name (IGN)?")
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            if msg.content.lower() == 'cancel':
                await thread.send("❌ Registration cancelled. Deleting thread in 5s...")
                await asyncio.sleep(5)
                await thread.delete()
                return
            player_ign = msg.content.strip()

            # Region selection
            await thread.send("Select the player's region:")
            region_view = RegionSelectView()
            await thread.send("Click a button to select region:", view=region_view)
            await region_view.wait()
            if region_view.selected_region is None:
                await thread.send("❌ No region selected. Cancelling.")
                await asyncio.sleep(5)
                await thread.delete()
                return
            region = region_view.selected_region

            # Create or update player in DB
            try:
                existing = await db.get_player_by_discord_id(player.id)
                if not existing:
                    created = await db.create_player_leaderboard(
                        discord_id=player.id,
                        ign=player_ign,
                        team_id=None,
                        region=region
                    )
                else:
                    await db.update_player_team(player.id, None)
                    # Also update IGN and region if functions exist; otherwise leave as-is
            except Exception as e:
                await thread.send(f"❌ Database error: {e}\nCancelling. Deleting thread in 10s...")
                await asyncio.sleep(10)
                await thread.delete()
                return

            # Try to set nickname and assign region role
            try:
                guild = interaction.guild
                member = guild.get_member(player.id)
                if member:
                    try:
                        await member.edit(nick=f"{player_ign}"[:32])
                    except:
                        pass
                    await self._assign_region_role(guild, player.id, region)
            except:
                pass

            # Final embed
            embed = discord.Embed(
                title="✅ Player Registered",
                description=f"{player.mention} has been registered.",
                color=0x00ff00
            )
            embed.add_field(name="IGN", value=player_ign, inline=True)
            embed.add_field(name="Region", value=region.upper(), inline=True)
            embed.set_footer(text=f"Registered by {author.display_name}")
            embed.timestamp = discord.utils.utcnow()

            await thread.send(embed=embed)
            await thread.send("✅ Registration complete. This thread will remain open for reference.")

        except asyncio.TimeoutError:
            await thread.send("❌ Timed out. Deleting thread in 5s...")
            await asyncio.sleep(5)
            await thread.delete()
            return


async def setup(bot):
    await bot.add_cog(AdminTeamRegister(bot))

