import discord
from discord.ext import commands
import os
import json
import asyncio
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

async def wait_for_message_with_timeout(bot, check, thread, user, timeout_duration=300):
    """
    Wait for a message with inactivity timeout system for team registration.
    - After 5 minutes of inactivity, ping the user
    - After another 5 minutes, delete thread and DM user
    Returns: (message, timed_out)
    """
    try:
        # First wait - 5 minutes
        message = await bot.wait_for('message', timeout=timeout_duration, check=check)
        return message, False
    except asyncio.TimeoutError:
        # First timeout - ping user
        try:
            await thread.send(
                f"⏰ {user.mention} **Inactivity Warning**\n\n"
                "You haven't responded for 5 minutes. Please send your message to continue.\n"
                "⚠️ **If you don't respond in the next 5 minutes, this team registration will be cancelled.**"
            )
        except:
            pass
        
        try:
            # Second wait - another 5 minutes
            message = await bot.wait_for('message', timeout=timeout_duration, check=check)
            return message, False
        except asyncio.TimeoutError:
            # Second timeout - cancel registration
            try:
                await thread.send(
                    f"❌ {user.mention} **Team Registration Cancelled**\n\n"
                    "You didn't respond for 10 minutes total.\n"
                    "This thread will be deleted in 10 seconds."
                )
            except:
                pass
            
            # Send DM
            try:
                await user.send(
                    "❌ **Team Registration Cancelled Due to Inactivity**\n\n"
                    "Your team registration thread was deleted because you didn't respond for 10 minutes.\n\n"
                    "**To register your team again:**\n"
                    "• Use the team registration button\n"
                    "• Make sure to respond promptly when asked for information\n\n"
                    "If you need help, please contact a staff member."
                )
            except:
                pass
            
            # Delete thread after delay
            await asyncio.sleep(10)
            try:
                await thread.delete()
            except:
                pass
            
            return None, True

class TeamRegistrationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view, no timeout
    
    @discord.ui.button(label="Register Team", style=discord.ButtonStyle.primary, custom_id="team_register")
    async def register_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        # Check if user is registered as a player
        try:
            player = await db.get_player(interaction.user.id)
            if not player:
                await interaction.followup.send(
                    "You must be registered as a player first! Please register in the player registration channel.",
                    ephemeral=True
                )
                return
        except Exception as e:
            print(f"❌ Error checking player registration: {e}")
            await interaction.followup.send(
                "Failed to check your registration status. Please try again.",
                ephemeral=True
            )
            return
        
        # Check if user already has a team as captain
        try:
            teams = await db.get_all_teams()
            user_team = None
            for team in teams:
                if team.get('captain_id') == interaction.user.id:
                    user_team = team
                    break
            
            if user_team:
                await interaction.followup.send(
                    f"You already have a team registered: **{user_team['name']}** [{user_team.get('tag', 'N/A')}]\n"
                    "You can only be the captain of one team.",
                    ephemeral=True
                )
                return
        except Exception as e:
            print(f"❌ Error checking team registration: {e}")

        # Create public thread so users can send messages
        try:
            thread = await interaction.channel.create_thread(
                name=f"Team-Registration-{interaction.user.name}",
                auto_archive_duration=1440,
                type=discord.ChannelType.public_thread,
                invitable=True
            )
            # Unarchive and unlock the thread
            if thread.archived:
                await thread.edit(archived=False, locked=False)
            print(f"✓ Thread created: {thread.name} (ID: {thread.id})")
        except Exception as e:
            print(f"❌ Error creating thread: {e}")
            await interaction.followup.send(
                "Failed to create registration thread. Please contact an administrator.",
                ephemeral=True
            )
            return
        
        # Add user to thread
        try:
            await thread.add_user(interaction.user)
            print(f"✓ Added {interaction.user.name} to thread")
        except Exception as e:
            print(f"❌ Error adding user to thread: {e}")
        
        # Add admins/staff to thread
        for member in interaction.guild.members:
            if any(role.name.lower() in ['admin', 'staff', 'moderator', 'mod'] for role in member.roles) or \
               member.guild_permissions.administrator:
                try:
                    await thread.add_user(member)
                except:
                    pass

        await interaction.followup.send(f"Team registration started in {thread.mention}", ephemeral=True)
        
        # Send instructions in thread
        await thread.send(
            f"{interaction.user.mention} Please provide the following information:\n"
            "1. Team Name\n"
            "2. Team Tag (2-4 characters)\n"
            "3. Region (NA/EU/AP/KR/BR/LATAM/JP)\n"
            "4. Team Logo (image upload or URL)"
        )

        # Start collecting information
        asyncio.create_task(self.collect_team_info(interaction, thread))
    
    async def collect_team_info(self, interaction: discord.Interaction, thread):
        """Collect team information from user"""
        try:
            team_data = {}
            
            # Get Team Name
            await thread.send("**What is your Team Name?**")
            msg, timed_out = await wait_for_message_with_timeout(
                interaction.client,
                lambda m: m.author.id == interaction.user.id and m.channel.id == thread.id,
                thread,
                interaction.user
            )
            if timed_out or not msg:
                return None
            team_data['name'] = msg.content.strip()
            
            # Get Team Tag
            await thread.send("**What is your Team Tag? (2-4 characters)**")
            while True:
                msg, timed_out = await wait_for_message_with_timeout(
                    interaction.client,
                    lambda m: m.author.id == interaction.user.id and m.channel.id == thread.id,
                    thread,
                    interaction.user
                )
                if timed_out or not msg:
                    return None
                tag = msg.content.strip()
                if 2 <= len(tag) <= 4:
                    team_data['tag'] = tag
                    break
                await thread.send("Tag must be 2-4 characters. Please try again.")
            
            # Get Region
            valid_regions = ['na', 'eu', 'ap', 'kr', 'br', 'latam', 'jp']
            await thread.send(
                "**What is your Region?**\n"
                "Valid options: NA, EU, AP, KR, BR, LATAM, JP"
            )
            
            while True:
                msg, timed_out = await wait_for_message_with_timeout(
                    interaction.client,
                    lambda m: m.author.id == interaction.user.id and m.channel.id == thread.id,
                    thread,
                    interaction.user
                )
                if timed_out or not msg:
                    return None
                region = msg.content.lower()
                if region in valid_regions:
                    team_data['region'] = region
                    break
                await thread.send("Invalid region. Please choose from: NA, EU, AP, KR, BR, LATAM, JP")
            
            # Get Team Logo
            await thread.send(
                "**Upload your Team Logo (image)**\n"
                "You can send an image directly or provide an image URL.\n"
                "Type `skip` if you want to add it later."
            )
            
            logo_url = None
            while True:
                msg, timed_out = await wait_for_message_with_timeout(
                    interaction.client,
                    lambda m: m.author.id == interaction.user.id and m.channel.id == thread.id,
                    thread,
                    interaction.user
                )
                if timed_out or not msg:
                    return None
                
                # Check if user wants to skip
                if msg.content.lower() == 'skip':
                    await thread.send("⏭️ Team logo skipped. You can add it later using the **Edit** button on your team profile.")
                    logo_url = None
                    break
                
                # Check if message has attachment
                if msg.attachments:
                    attachment = msg.attachments[0]
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        logo_url = attachment.url
                        await thread.send(f"✅ Logo uploaded successfully!\n*URL: {logo_url}*")
                        break
                    else:
                        await thread.send("❌ Please upload a valid image file.")
                        continue
                
                # Check if it's a URL
                elif msg.content.startswith('http://') or msg.content.startswith('https://'):
                    # Basic URL validation for image
                    if any(msg.content.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                        logo_url = msg.content.strip()
                        await thread.send(f"✅ Logo URL saved successfully!\n*URL: {logo_url}*")
                        break
                    else:
                        await thread.send("❌ URL doesn't appear to be an image. Please provide a valid image URL ending with .png, .jpg, .jpeg, .gif, or .webp")
                        continue
                else:
                    await thread.send("❌ Please upload an image or provide an image URL, or type `skip`.")
                    continue
            
            team_data['logo_url'] = logo_url
            
            # Check if team name or tag already exists
            try:
                existing_teams = await db.get_all_teams()
                for team in existing_teams:
                    if team['name'].lower() == team_data['name'].lower():
                        await thread.send(f"A team with the name '{team_data['name']}' already exists!\nPlease choose a different name.")
                        await asyncio.sleep(10)
                        await thread.delete()
                        return
                    
                    if team.get('tag', '').lower() == team_data['tag'].lower():
                        await thread.send(f"A team with the tag '{team_data['tag']}' already exists!\nPlease choose a different tag.")
                        await asyncio.sleep(10)
                        await thread.delete()
                        return
            except Exception as e:
                print(f"Error checking existing teams: {e}")
            
            # Register the team
            try:
                # Create team in database (this also initializes team stats and adds captain as member)
                team = await db.create_team(
                    name=team_data['name'],
                    tag=team_data['tag'],
                    captain_id=interaction.user.id,
                    region=team_data['region'],
                    logo_url=team_data.get('logo_url')
                )
                
                # Update team leaderboard
                await db.update_team_leaderboard(
                    team['id'], 
                    team_data['name'], 
                    team_data['tag'], 
                    team_data['region'],
                    team_data.get('logo_url')
                )
                await db.update_team_leaderboard_ranks()
                
                # Send log to logs channel
                try:
                    log_channel_id = cfg('LOG_CHANNEL_ID')
                    if log_channel_id:
                        log_channel = interaction.client.get_channel(int(log_channel_id))
                        if log_channel:
                            log_embed = discord.Embed(
                                title="🎮 New Team Registered (Thread)",
                                color=discord.Color.blue(),
                                timestamp=discord.utils.utcnow()
                            )
                            log_embed.add_field(name="Team Name", value=team_data['name'], inline=True)
                            log_embed.add_field(name="Tag", value=f"[{team_data['tag']}]", inline=True)
                            log_embed.add_field(name="Region", value=team_data['region'].upper(), inline=True)
                            log_embed.add_field(name="Captain", value=f"{interaction.user.mention} ({interaction.user})", inline=False)
                            
                            # Set team logo as thumbnail if available
                            logo = team_data.get('logo_url')
                            if logo:
                                try:
                                    log_embed.set_thumbnail(url=logo)
                                    log_embed.add_field(name="Logo", value=f"[View Logo]({logo})", inline=False)
                                except Exception as logo_error:
                                    print(f"Failed to set logo thumbnail: {logo_error}")
                                    log_embed.add_field(name="Logo", value="Failed to load", inline=False)
                            else:
                                log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                            
                            log_embed.set_footer(text=f"Team ID: {team['id']} | Captain ID: {interaction.user.id} • Method: Thread")
                            
                            await log_channel.send(embed=log_embed)
                except Exception as log_error:
                    print(f"Error sending team registration log: {log_error}")
                
                await thread.send(
                    f"Registration successful!\n\n"
                    f"**Team Name:** {team_data['name']}\n"
                    f"**Team Tag:** [{team_data['tag']}]\n"
                    f"**Region:** {team_data['region'].upper()}\n"
                    f"**Captain:** {interaction.user.mention}\n\n"
                    f"This thread will be deleted in 10 seconds."
                )
                
                await asyncio.sleep(10)
                await thread.delete()
                
            except Exception as e:
                await thread.send(f"Registration failed: {str(e)}\nPlease try again or contact an administrator.")
                await asyncio.sleep(10)
                await thread.delete()
        
        except asyncio.TimeoutError:
            await thread.send("Registration timed out. Thread will be deleted in 10 seconds.")
            await asyncio.sleep(10)
            await thread.delete()
        except Exception as e:
            print(f"Error in team registration: {e}")
            await thread.send("An error occurred during registration. Please try again.")
            await asyncio.sleep(10)
            await thread.delete()

class TeamRegistrationUI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.team_reg_channel_id = None
        
        # Load channel ID from env
        channel_id = cfg('CHANNEL_TEAM_REG_ID')
        if channel_id:
            self.team_reg_channel_id = int(channel_id)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Post team registration UI on bot startup"""
        if not self.team_reg_channel_id:
            print("⚠️ CHANNEL_TEAM_REG_ID not configured, skipping team registration UI")
            return
        
        channel = self.bot.get_channel(self.team_reg_channel_id)
        if not channel:
            print(f"❌ Could not find team registration channel: {self.team_reg_channel_id}")
            return
        
        print(f"🧹 Purging all messages in {channel.name}...")
        
        # Purge all messages
        deleted_count = 0
        async for message in channel.history(limit=100):
            try:
                await message.delete()
                deleted_count += 1
            except:
                pass
        
        print(f"🗑️ Deleted {deleted_count} messages from {channel.name}")
        
        # Post new team registration UI
        embed = discord.Embed(
            title="Team Registration",
            description="Register your team for the Valorant Mobile tournament.",
            color=0x5865F2
        )
        embed.add_field(
            name="Requirements",
            value="You must be registered as a player first\nYou can only be captain of one team\nTeam names and tags must be unique",
            inline=False
        )
        embed.add_field(
            name="What You'll Need",
            value="Team Name\nTeam Tag (2-4 characters)\nRegion (NA/EU/AP/KR/BR/LATAM/JP)",
            inline=False
        )
        
        view = TeamRegistrationView()
        await channel.send(embed=embed, view=view)
        print(f"✅ Team Registration UI posted in {channel.name}")

async def setup(bot):
    # Register persistent view
    bot.add_view(TeamRegistrationView())
    await bot.add_cog(TeamRegistrationUI(bot))
