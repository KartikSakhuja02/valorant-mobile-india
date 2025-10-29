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

class TeamHelpdeskView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Help", style=discord.ButtonStyle.primary, custom_id="team_helpdesk_help")
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Create a help thread for team registration"""
        print(f"🔧 Team helpdesk Help button clicked by {interaction.user.name}")
        
        # Defer the interaction first to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        # Check if user already has a team as captain
        try:
            # Check if user is a team captain
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
                print(f"⚠️ User {interaction.user.name} already has a team")
                return
        except Exception as e:
            print(f"❌ Error checking team registration: {e}")
        
        print(f"✓ User doesn't have a team, creating thread...")
        
        # Create private thread
        try:
            thread = await interaction.channel.create_thread(
                name=f"Team-Help-{interaction.user.name}",
                type=discord.ChannelType.private_thread
            )
            print(f"✓ Thread created: {thread.name} (ID: {thread.id})")
        except Exception as e:
            print(f"❌ Error creating thread: {e}")
            await interaction.followup.send(
                "Failed to create help thread. Please contact an administrator.",
                ephemeral=True
            )
            return
        
        # Add user to thread
        try:
            await thread.add_user(interaction.user)
            print(f"✓ Added {interaction.user.name} to thread")
        except Exception as e:
            print(f"❌ Error adding user to thread: {e}")
        
        # Get staff role ID
        staff_role_id = int(cfg('ROLE_STAFF_ID', 0)) if cfg('ROLE_STAFF_ID') else None
        
        # Collect online staff members
        online_staff = []
        staff_role = interaction.guild.get_role(staff_role_id) if staff_role_id else None
        
        # Add all staff members to thread
        for member in interaction.guild.members:
            is_staff = False
            
            # Check if member has staff role or admin permissions
            if member.guild_permissions.administrator:
                is_staff = True
            elif staff_role_id and any(role.id == staff_role_id for role in member.roles):
                is_staff = True
            
            if is_staff:
                try:
                    await thread.add_user(member)
                except:
                    pass
                
                # Check if member is online
                if member.status != discord.Status.offline:
                    online_staff.append(member)
        
        # Build role mention string for ghost ping
        role_mentions = []
        if staff_role:
            role_mentions.append(staff_role.mention)
        
        print(f"✓ Staff added to thread, preparing to send messages...")
        
        await interaction.followup.send(f"Team registration help request created in {thread.mention}", ephemeral=True)
        
        print(f"✓ Interaction responded, now sending thread messages...")
        
        try:
            # Ghost ping: Send mentions then immediately delete
            if role_mentions:
                print(f"✓ Sending ghost ping with {len(role_mentions)} role mentions...")
                ping_msg = await thread.send(" ".join(role_mentions))
                await ping_msg.delete()
                print(f"✓ Ghost ping sent and deleted")
            
            # Send initial message in thread (no mentions)
            print(f"✓ Sending initial message...")
            msg1 = await thread.send(
                f"{interaction.user.mention} needs help with team registration!\n\n"
                f"A staff member will assist you shortly."
            )
            print(f"✓ Initial message sent (ID: {msg1.id})")
            
            # Create staff action view
            staff_view = TeamStaffActionView(interaction.user.id, thread, online_staff, role_mentions)
            
            # Create embed for staff instructions
            print(f"✓ Creating staff embed...")
            staff_embed = discord.Embed(
                title="Staff: Help with Team Registration",
                description="Please collect the following information from the user:",
                color=0x5865F2
            )
            staff_embed.add_field(
                name="Required Information",
                value="• Team Name\n• Team Tag (2-4 characters)\n• Region (NA/EU/AP/KR/BR/LATAM/JP)",
                inline=False
            )
            staff_embed.add_field(
                name="Note",
                value="The user who clicked Help will automatically become the team captain.",
                inline=False
            )
            
            print(f"✓ Sending staff embed with button...")
            msg2 = await thread.send(embed=staff_embed, view=staff_view)
            print(f"✓ Staff embed sent (ID: {msg2.id})")
            
            print(f"✅ Team helpdesk thread created successfully for {interaction.user.name}")
            
        except Exception as e:
            print(f"❌ Error sending messages to team helpdesk thread: {e}")
            await interaction.followup.send(
                f"There was an error setting up the help thread. Please contact an administrator.",
                ephemeral=True
            )
            return
        
        # Start ghost ping reminder task (every 10 minutes)
        asyncio.create_task(self.ghost_ping_task(thread, role_mentions, interaction.user))
        
        # Schedule thread deletion after 12 hours
        asyncio.create_task(self.delete_thread_after_delay(thread, 12))
    
    async def ghost_ping_task(self, thread, role_mentions, user):
        """Ghost ping staff every 10 minutes"""
        if not role_mentions:
            return
        
        # Wait 10 minutes before first ghost ping
        await asyncio.sleep(600)
        
        # Keep pinging for up to 12 hours
        for _ in range(72):  # 72 * 10 minutes = 12 hours
            try:
                # Check if thread still exists
                if thread.archived or not thread:
                    break
                
                # Send and delete ghost ping
                ping_msg = await thread.send(" ".join(role_mentions))
                await ping_msg.delete()
                
                # Wait 10 minutes
                await asyncio.sleep(600)
            except:
                break
    
    async def delete_thread_after_delay(self, thread, hours):
        """Delete thread after specified hours"""
        await asyncio.sleep(hours * 3600)
        try:
            await thread.delete()
        except:
            pass

class TeamStaffActionView(discord.ui.View):
    def __init__(self, user_id, thread, staff_members, role_mentions):
        super().__init__(timeout=43200)  # 12 hours
        self.user_id = user_id
        self.thread = thread
        self.staff_members = staff_members
        self.role_mentions = role_mentions
        self.staff_id = None
        self.processing = False
    
    def is_staff(self, interaction: discord.Interaction) -> bool:
        """Check if user is staff (staff role only, not the user who created the thread)"""
        # Prevent the user who clicked Help from using these buttons
        if interaction.user.id == self.user_id:
            return False
        
        # Check for admin permissions
        if interaction.user.guild_permissions.administrator:
            return True
        
        # Check for staff role ID
        staff_role_id = int(cfg('ROLE_STAFF_ID', 0)) if cfg('ROLE_STAFF_ID') else None
        if staff_role_id and any(role.id == staff_role_id for role in interaction.user.roles):
            return True
        
        return False
    
    @discord.ui.button(label="Register Team", style=discord.ButtonStyle.primary)
    async def register_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_staff(interaction):
            await interaction.response.send_message("Only staff can use this!", ephemeral=True)
            return
        
        if self.processing:
            await interaction.response.send_message("Already being handled by another staff member!", ephemeral=True)
            return
        
        # Lock to first staff member
        if self.staff_id is None:
            self.staff_id = interaction.user.id
        elif self.staff_id != interaction.user.id:
            await interaction.response.send_message("Another staff member is already handling this!", ephemeral=True)
            return
        
        self.processing = True
        
        # Disable buttons and send visible message
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(
            content=f"**Team Registration Started**\n\n{interaction.user.mention} is now handling this registration.",
            view=self
        )
        
        # Ask STAFF for team information
        await self.thread.send(
            f"{interaction.user.mention} Please provide the following information for <@{self.user_id}>'s team:\n"
            "1. Team Name\n"
            "2. Team Tag (2-4 characters)\n"
            "3. Region (NA/EU/AP/KR/BR/LATAM/JP)\n"
            "4. Team Logo (image upload or URL, or type `skip`)"
        )
        
        try:
            team_data = {}
            
            # Get Team Name from STAFF
            await self.thread.send("**What is the Team Name?**")
            msg = await interaction.client.wait_for(
                'message',
                timeout=300,
                check=lambda m: m.author.id == interaction.user.id and m.channel.id == self.thread.id
            )
            team_data['name'] = msg.content.strip()
            
            # Get Team Tag from STAFF
            await self.thread.send("**What is the Team Tag? (2-4 characters)**")
            while True:
                msg = await interaction.client.wait_for(
                    'message',
                    timeout=300,
                    check=lambda m: m.author.id == interaction.user.id and m.channel.id == self.thread.id
                )
                tag = msg.content.strip()
                if 2 <= len(tag) <= 4:
                    team_data['tag'] = tag
                    break
                await self.thread.send("❌ Tag must be 2-4 characters. Please try again.")
            
            # Get Region from STAFF
            valid_regions = ['na', 'eu', 'ap', 'kr', 'br', 'latam', 'jp']
            await self.thread.send(
                "**What is the Region?**\n"
                "Valid options: NA, EU, AP, KR, BR, LATAM, JP"
            )
            
            while True:
                msg = await interaction.client.wait_for(
                    'message',
                    timeout=300,
                    check=lambda m: m.author.id == interaction.user.id and m.channel.id == self.thread.id
                )
                region = msg.content.lower()
                if region in valid_regions:
                    team_data['region'] = region
                    break
                await self.thread.send("❌ Invalid region. Please choose from: NA, EU, AP, KR, BR, LATAM, JP")
            
            # Get Team Logo from STAFF
            await self.thread.send(
                "**Team Logo:**\n"
                "Upload an image or provide an image URL for <@{self.user_id}>'s team logo.\n"
                "Type `skip` to add it later."
            )
            
            logo_url = None
            while True:
                msg = await interaction.client.wait_for(
                    'message',
                    timeout=300,
                    check=lambda m: m.author.id == interaction.user.id and m.channel.id == self.thread.id
                )
                
                # Check if staff wants to skip
                if msg.content.lower() == 'skip':
                    await self.thread.send("⏭️ Team logo skipped. Captain can add it later using the **Edit** button on team profile.")
                    logo_url = None
                    break
                
                # Check if message has attachment
                if msg.attachments:
                    attachment = msg.attachments[0]
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        logo_url = attachment.url
                        await self.thread.send(f"✅ Logo uploaded successfully!\n*URL: {logo_url}*")
                        break
                    else:
                        await self.thread.send("❌ Please upload a valid image file.")
                        continue
                
                # Check if it's a URL
                elif msg.content.startswith('http://') or msg.content.startswith('https://'):
                    # Basic URL validation for image
                    if any(msg.content.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                        logo_url = msg.content.strip()
                        await self.thread.send(f"✅ Logo URL saved successfully!\n*URL: {logo_url}*")
                        break
                    else:
                        await self.thread.send("❌ URL doesn't appear to be an image. Please provide a valid image URL ending with .png, .jpg, .jpeg, .gif, or .webp")
                        continue
                else:
                    await self.thread.send("❌ Please upload an image or provide an image URL, or type `skip`.")
                    continue
            
            team_data['logo_url'] = logo_url
            
            # Check if team name or tag already exists
            try:
                existing_teams = await db.get_all_teams()
                for team in existing_teams:
                    if team['name'].lower() == team_data['name'].lower():
                        await self.thread.send(f"❌ A team with the name '{team_data['name']}' already exists!")
                        self.processing = False
                        for item in self.children:
                            item.disabled = False
                        await interaction.message.edit(view=self)
                        return
                    
                    if team.get('tag', '').lower() == team_data['tag'].lower():
                        await self.thread.send(f"❌ A team with the tag '{team_data['tag']}' already exists!")
                        self.processing = False
                        for item in self.children:
                            item.disabled = False
                        await interaction.message.edit(view=self)
                        return
            except Exception as e:
                print(f"Error checking existing teams: {e}")
            
            # Register the team
            try:
                captain = interaction.guild.get_member(self.user_id)
                
                # Check if user is registered as a player
                player = await db.get_player(self.user_id)
                if not player:
                    await self.thread.send(
                        f"❌ <@{self.user_id}> must be registered as a player first!\n"
                        f"Please register in the player registration channel before creating a team."
                    )
                    self.processing = False
                    for item in self.children:
                        item.disabled = False
                        await interaction.message.edit(view=self)
                    return
                
                # Create team in database (this also initializes team stats and adds captain as member)
                team = await db.create_team(
                    name=team_data['name'],
                    tag=team_data['tag'],
                    captain_id=self.user_id,
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
                
                await self.thread.send(
                    f"✅ Team registration successful!\n\n"
                    f"**Team Name:** {team_data['name']}\n"
                    f"**Team Tag:** [{team_data['tag']}]\n"
                    f"**Region:** {team_data['region'].upper()}\n"
                    f"**Captain:** <@{self.user_id}>\n\n"
                    f"This thread will be deleted in 10 seconds."
                )
                
                # Send log
                try:
                    log_channel_id = cfg('LOG_CHANNEL_ID')
                    if log_channel_id:
                        log_channel = interaction.client.get_channel(int(log_channel_id))
                        if log_channel:
                            log_embed = discord.Embed(
                                title="🎮 New Team Registered (Helpdesk)",
                                color=discord.Color.blue(),
                                timestamp=discord.utils.utcnow()
                            )
                            log_embed.add_field(name="Team Name", value=team_data['name'], inline=True)
                            log_embed.add_field(name="Tag", value=f"[{team_data['tag']}]", inline=True)
                            log_embed.add_field(name="Region", value=team_data['region'].upper(), inline=True)
                            log_embed.add_field(name="Captain", value=f"<@{self.user_id}>", inline=False)
                            log_embed.add_field(name="Staff Helper", value=interaction.user.mention, inline=False)
                            
                            # Add logo if provided
                            logo = team_data.get('logo_url')
                            if logo:
                                try:
                                    log_embed.set_thumbnail(url=logo)
                                    log_embed.add_field(name="Logo", value=f"[View Logo]({logo})", inline=False)
                                except Exception as logo_error:
                                    print(f"Failed to set logo thumbnail: {logo_error}")
                                    log_embed.add_field(name="Logo", value="Failed to load", inline=False)
                            
                            log_embed.set_footer(text=f"Team ID: {team['id']} | Captain ID: {self.user_id}")
                            
                            await log_channel.send(embed=log_embed)
                except Exception as log_error:
                    print(f"Error sending team registration log: {log_error}")
                
                await asyncio.sleep(10)
                await self.thread.delete()
                
            except Exception as e:
                await self.thread.send(f"❌ Team registration failed: {str(e)}\nPlease try again or contact an administrator.")
                self.processing = False
                for item in self.children:
                    item.disabled = False
                await interaction.message.edit(view=self)
        
        except asyncio.TimeoutError:
            await self.thread.send("⏰ Timeout waiting for information. Please click the button again to retry.")
            self.processing = False
            for item in self.children:
                item.disabled = False
            await interaction.message.edit(view=self)

class TeamRegistrationHelpdesk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.team_helpdesk_channel_id = None
        
        # Load channel ID from env
        channel_id = cfg('CHANNEL_TEAM_INTERACTIVE_REG_ID')
        if channel_id:
            self.team_helpdesk_channel_id = int(channel_id)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Post team helpdesk UI on bot startup"""
        if not self.team_helpdesk_channel_id:
            print("⚠️ CHANNEL_TEAM_INTERACTIVE_REG_ID not configured, skipping team helpdesk UI")
            return
        
        channel = self.bot.get_channel(self.team_helpdesk_channel_id)
        if not channel:
            print(f"❌ Could not find team helpdesk channel: {self.team_helpdesk_channel_id}")
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
        
        # Post new helpdesk UI
        embed = discord.Embed(
            title="Team Registration Help",
            description="Need help registering a team? Click the button below and a staff member will assist you.",
            color=0x5865F2
        )
        embed.add_field(
            name="Requirements",
            value="• You must be registered as a player first\n• You can only be captain of one team\n• Team names and tags must be unique",
            inline=False
        )
        embed.add_field(
            name="What You'll Need",
            value="• Team Name\n• Team Tag (2-4 characters)\n• Region",
            inline=False
        )
        
        view = TeamHelpdeskView()
        await channel.send(embed=embed, view=view)
        print(f"✅ Team Helpdesk UI posted in {channel.name}")

async def setup(bot):
    # Register persistent view
    bot.add_view(TeamHelpdeskView())
    await bot.add_cog(TeamRegistrationHelpdesk(bot))
