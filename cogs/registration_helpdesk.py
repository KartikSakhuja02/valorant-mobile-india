import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import asyncio
from pathlib import Path
from services import db
from services.ocr_service import ocr_service

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

class HelpdeskView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Help", style=discord.ButtonStyle.primary, custom_id="helpdesk_help")
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Create a help thread and notify staff"""
        print(f"🔧 Help button clicked by {interaction.user.name}")
        
        # Defer the interaction first to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        # Check if user is already registered
        try:
            existing_player = await db.get_player(interaction.user.id)
            if existing_player:
                await interaction.followup.send(
                    "You are already registered! You don't need help with registration.",
                    ephemeral=True
                )
                print(f"⚠️ User {interaction.user.name} is already registered")
                return
        except Exception as e:
            print(f"❌ Error checking registration: {e}")
        
        print(f"✓ User is not registered, creating thread...")
        
        # Create private thread
        try:
            thread = await interaction.channel.create_thread(
                name=f"Help-{interaction.user.name}",
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
        
        # Get staff role IDs
        admin_role_id = int(cfg('ROLE_ADMINISTRATOR_ID', 0)) if cfg('ROLE_ADMINISTRATOR_ID') else None
        staff_role_id = int(cfg('ROLE_STAFF_ID', 0)) if cfg('ROLE_STAFF_ID') else None
        mod_role_id = int(cfg('ROLE_MODERATOR_ID', 0)) if cfg('ROLE_MODERATOR_ID') else None
        
        print(f"🔍 Looking for staff with role IDs: Admin={admin_role_id}, Staff={staff_role_id}, Mod={mod_role_id}")
        
        # Add all staff members to thread
        staff_added = 0
        for member in interaction.guild.members:
            # Skip the user who created the thread (already added)
            if member.id == interaction.user.id:
                continue
                
            should_add = False
            
            # Check if member has admin permission
            if member.guild_permissions.administrator:
                should_add = True
                print(f"  👑 Found admin by permission: {member.name}")
            
            # Check if member has any of the staff role IDs
            for role in member.roles:
                if role.id == admin_role_id:
                    should_add = True
                    print(f"  👑 Found admin by role: {member.name}")
                elif role.id == staff_role_id:
                    should_add = True
                    print(f"  👮 Found staff: {member.name}")
                elif role.id == mod_role_id:
                    should_add = True
                    print(f"  👮 Found moderator: {member.name}")
            
            if should_add:
                try:
                    await thread.add_user(member)
                    staff_added += 1
                    print(f"  ✅ Added {member.name} to thread")
                except Exception as e:
                    print(f"  ❌ Failed to add {member.name}: {e}")
        
        print(f"✓ Added {staff_added} staff members to thread")
                
                # Check if member is online
        if member.status != discord.Status.offline:
                    online_staff.append(member)
        
        # Build role mention string for ghost ping (staff only)
        role_mentions = []
        if staff_role:
            role_mentions.append(staff_role.mention)
        
        print(f"✓ Staff added to thread, preparing to send messages...")
        
        await interaction.followup.send(f"Help request created in {thread.mention}", ephemeral=True)
        
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
                f"{interaction.user.mention} needs help with registration!\n\n"
                f"A staff member will assist you shortly."
            )
            print(f"✓ Initial message sent (ID: {msg1.id})")
            
            # Create staff action view with clear instructions
            staff_view = StaffActionView(interaction.user.id, thread, online_staff, role_mentions)
            
            # Create embed for staff instructions
            print(f"✓ Creating staff embed...")
            staff_embed = discord.Embed(
                title="Staff: Choose Registration Method",
                description="Select which registration method you would like to use to help this user:",
                color=0x5865F2
            )
            staff_embed.add_field(
                name="Screenshot Registration",
                value="User will upload their profile screenshot for automatic OCR extraction",
                inline=False
            )
            staff_embed.add_field(
                name="Manual Registration",
                value="User will manually provide their IGN, Player ID, and Region",
                inline=False
            )
            
            print(f"✓ Sending staff embed with buttons...")
            msg2 = await thread.send(embed=staff_embed, view=staff_view)
            print(f"✓ Staff embed sent (ID: {msg2.id})")
            
            print(f"✅ Helpdesk thread created successfully for {interaction.user.name}")
            
        except Exception as e:
            print(f"❌ Error sending messages to helpdesk thread: {e}")
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
        
        # Ghost ping every 10 minutes for 12 hours (72 times)
        for i in range(72):
            await asyncio.sleep(600)  # Wait 10 minutes
            
            # Check if thread still exists
            try:
                # Try to send a message to check if thread exists
                ping_msg = await thread.send(" ".join(role_mentions))
                await ping_msg.delete()
            except:
                # Thread was deleted or we don't have permission
                return
    
    async def delete_thread_after_delay(self, thread, hours):
        """Delete thread after specified hours"""
        await asyncio.sleep(hours * 3600)
        try:
            await thread.delete()
        except:
            pass

class StaffActionView(discord.ui.View):
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
    
    @discord.ui.button(label="Screenshot Registration", style=discord.ButtonStyle.primary)
    async def screenshot_registration(self, interaction: discord.Interaction, button: discord.ui.Button):
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
            content=f"**Registration Method Selected: Screenshot Registration**\n\n{interaction.user.mention} is now handling this registration.",
            view=self
        )
        
        # Ask STAFF to send screenshot
        await self.thread.send(
            f"{interaction.user.mention} Please send <@{self.user_id}>'s profile screenshot here.\n"
            "Make sure:\n"
            "- IGN (In-Game Name) is clearly visible\n"
            "- Player ID is visible\n"
            "- Image has good quality"
        )
        
        def check(message):
            return message.author.id == interaction.user.id and \
                   message.channel.id == self.thread.id and \
                   message.attachments
        
        try:
            # Wait for screenshot
            message = await interaction.client.wait_for('message', timeout=3600, check=check)
            
            # Process OCR
            success, ign, player_id = await ocr_service.process_screenshot(message.attachments[0])
            
            if not success:
                await self.thread.send(f"❌ OCR Failed: {ign}\nPlease try again with a clearer screenshot.")
                self.processing = False
                for item in self.children:
                    item.disabled = False
                await interaction.message.edit(view=self)
                return
            
            # Show OCR results
            embed = discord.Embed(
                title="Profile Information Detected",
                description="Please verify if this information is correct:",
                color=discord.Color.blue()
            )
            embed.add_field(name="IGN", value=f"`{ign}`", inline=True)
            embed.add_field(name="ID", value=f"`{player_id}`", inline=True)
            
            confirm_view = StaffConfirmView(self.user_id, self.staff_id, ign, player_id, self.thread)
            await self.thread.send(embed=embed, view=confirm_view)
            
        except asyncio.TimeoutError:
            await self.thread.send("⏰ Timeout waiting for screenshot. Please click the button again to retry.")
            self.processing = False
            for item in self.children:
                item.disabled = False
            await interaction.message.edit(view=self)
    
    @discord.ui.button(label="Manual Registration", style=discord.ButtonStyle.secondary)
    async def manual_registration(self, interaction: discord.Interaction, button: discord.ui.Button):
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
            content=f"**Registration Method Selected: Manual Registration**\n\n{interaction.user.mention} is now handling this registration.",
            view=self
        )
        
        # Ask STAFF for information
        await self.thread.send(
            f"{interaction.user.mention} Please provide <@{self.user_id}>'s information:\n"
            "1. IGN (In-Game Name)\n"
            "2. In-game ID\n"
            "3. Region (NA/EU/AP/KR/BR/LATAM/JP)"
        )
        
        try:
            registration_data = {}
            
            # Get IGN from STAFF
            await self.thread.send("**What is their IGN?**")
            msg = await interaction.client.wait_for(
                'message',
                timeout=300,
                check=lambda m: m.author.id == interaction.user.id and m.channel.id == self.thread.id
            )
            registration_data['ign'] = msg.content
            
            # Get ID from STAFF
            await self.thread.send("**What is their In-game ID?**")
            msg = await interaction.client.wait_for(
                'message',
                timeout=300,
                check=lambda m: m.author.id == interaction.user.id and m.channel.id == self.thread.id
            )
            try:
                registration_data['id'] = int(msg.content)
            except ValueError:
                await self.thread.send("❌ Invalid ID format. Registration cancelled.")
                await asyncio.sleep(5)
                await self.thread.delete()
                return
            
            # Get Region from STAFF
            valid_regions = ['na', 'eu', 'ap', 'kr', 'br', 'latam', 'jp']
            await self.thread.send(
                "**What is their Region?**\n"
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
                    registration_data['region'] = region
                    break
                await self.thread.send("Invalid region. Please choose from: NA, EU, AP, KR, BR, LATAM, JP")
            
            # Process registration
            try:
                member = interaction.guild.get_member(self.user_id)
                
                # Create new player in database
                await db.create_player(
                    discord_id=self.user_id,
                    ign=registration_data['ign'],
                    player_id=registration_data['id'],
                    region=registration_data['region']
                )
                
                # Initialize empty stats
                initial_stats = {
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0,
                    "matches_played": 0,
                    "wins": 0,
                    "losses": 0,
                    "mvps": 0
                }
                
                await db.create_player_stats(self.user_id, initial_stats)
                await db.update_player_leaderboard(
                    self.user_id,
                    registration_data['ign'],
                    registration_data['region']
                )
                await db.update_player_leaderboard_ranks()
                
                # Assign region role
                cog = interaction.client.get_cog('Registration')
                if cog and member:
                    role_assigned = await cog.assign_region_role(member, registration_data['region'])
                    role_msg = "✅ Region role assigned!" if role_assigned else "⚠️ Could not assign region role."
                else:
                    role_msg = ""
                
                # Send log to logs channel
                try:
                    log_channel_id = cfg('LOG_CHANNEL_ID')
                    if log_channel_id:
                        log_channel = interaction.client.get_channel(int(log_channel_id))
                        if log_channel:
                            log_embed = discord.Embed(
                                title="🆕 New Player Registration (Helpdesk - Manual)",
                                color=discord.Color.blue(),
                                timestamp=discord.utils.utcnow()
                            )
                            log_embed.add_field(name="Player", value=f"<@{self.user_id}>", inline=False)
                            log_embed.add_field(name="IGN", value=registration_data['ign'], inline=True)
                            log_embed.add_field(name="Player ID", value=str(registration_data['id']), inline=True)
                            log_embed.add_field(name="Region", value=registration_data['region'].upper(), inline=True)
                            log_embed.add_field(name="Staff Helper", value=interaction.user.mention, inline=False)
                            log_embed.set_thumbnail(url=member.display_avatar.url if member else None)
                            log_embed.set_footer(text=f"User ID: {self.user_id} • Method: Helpdesk Manual")
                            
                            await log_channel.send(embed=log_embed)
                except Exception as log_error:
                    print(f"Error sending registration log: {log_error}")
                
                await self.thread.send(f"✅ Registration successful! {role_msg}\nThis thread will be deleted in 10 seconds.")
                await asyncio.sleep(10)
                await self.thread.delete()
                
            except Exception as e:
                await self.thread.send(f"❌ Registration failed: {str(e)}\nPlease try again or contact an administrator.")
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

class StaffConfirmView(discord.ui.View):
    def __init__(self, user_id, staff_id, ign, player_id, thread):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.staff_id = staff_id
        self.ign = ign
        self.player_id = player_id
        self.thread = thread
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.staff_id:
            await interaction.response.send_message("Only the handling staff can use this!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Show region selection
        regions = [
            ("North America (NA)", "na"),
            ("Europe (EU)", "eu"),
            ("Asia-Pacific (AP)", "ap"),
            ("Korea (KR)", "kr"),
            ("Brazil (BR)", "br"),
            ("Latin America (LATAM)", "latam"),
            ("Japan (JP)", "jp")
        ]
        
        region_view = discord.ui.View(timeout=300)
        for region_name, region_code in regions:
            button = discord.ui.Button(
                label=region_name,
                custom_id=f"hd_region_{region_code}",
                style=discord.ButtonStyle.primary
            )
            
            async def region_callback(i: discord.Interaction, r_code=region_code):
                if i.user.id != self.staff_id:
                    await i.response.send_message("Only the handling staff can use this!", ephemeral=True)
                    return
                
                await i.response.defer()
                
                try:
                    member = i.guild.get_member(self.user_id)
                    
                    # Create new player in database
                    await db.create_player(
                        discord_id=self.user_id,
                        ign=self.ign,
                        player_id=int(self.player_id),
                        region=r_code
                    )
                    
                    # Initialize empty stats
                    initial_stats = {
                        "kills": 0,
                        "deaths": 0,
                        "assists": 0,
                        "matches_played": 0,
                        "wins": 0,
                        "losses": 0,
                        "mvps": 0
                    }
                    
                    await db.create_player_stats(self.user_id, initial_stats)
                    await db.update_player_leaderboard(
                        self.user_id,
                        self.ign,
                        r_code
                    )
                    await db.update_player_leaderboard_ranks()
                    
                    # Assign region role
                    cog = i.client.get_cog('Registration')
                    if cog and member:
                        role_assigned = await cog.assign_region_role(member, r_code)
                        role_msg = "✅ Region role assigned!" if role_assigned else "⚠️ Could not assign region role."
                    else:
                        role_msg = ""
                    
                    # Send log to logs channel
                    try:
                        log_channel_id = cfg('LOG_CHANNEL_ID')
                        if log_channel_id:
                            log_channel = i.client.get_channel(int(log_channel_id))
                            if log_channel:
                                log_embed = discord.Embed(
                                    title="🆕 New Player Registration (Helpdesk - Screenshot)",
                                    color=discord.Color.blue(),
                                    timestamp=discord.utils.utcnow()
                                )
                                log_embed.add_field(name="Player", value=f"<@{self.user_id}>", inline=False)
                                log_embed.add_field(name="IGN", value=self.ign, inline=True)
                                log_embed.add_field(name="Player ID", value=str(self.player_id), inline=True)
                                log_embed.add_field(name="Region", value=r_code.upper(), inline=True)
                                log_embed.add_field(name="Staff Helper", value=f"<@{self.staff_id}>", inline=False)
                                log_embed.set_thumbnail(url=member.display_avatar.url if member else None)
                                log_embed.set_footer(text=f"User ID: {self.user_id} • Method: Helpdesk Screenshot")
                                
                                await log_channel.send(embed=log_embed)
                    except Exception as log_error:
                        print(f"Error sending registration log: {log_error}")
                    
                    await self.thread.send(f"✅ Registration successful! {role_msg}\nThis thread will be deleted in 10 seconds.")
                    await asyncio.sleep(10)
                    await self.thread.delete()
                    
                except Exception as e:
                    await self.thread.send(f"❌ Registration failed: {str(e)}")
            
            button.callback = region_callback
            region_view.add_item(button)
        
        await interaction.message.edit(
            content="**Please select the user's region:**",
            embed=None,
            view=region_view
        )
    
    @discord.ui.button(label="Retry", style=discord.ButtonStyle.danger)
    async def retry(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.staff_id:
            await interaction.response.send_message("Only the handling staff can use this!", ephemeral=True)
            return
        
        await interaction.response.defer()
        await self.thread.send(
            f"<@{self.user_id}> Please send your profile screenshot again with a clearer image."
        )
        await interaction.message.delete()

class RegistrationHelpdesk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.helpdesk_channel_id = int(cfg('CHANNEL_PLAYER_FORCE_REG_ID', 0)) if cfg('CHANNEL_PLAYER_FORCE_REG_ID') else None
        self._instructions_sent = False
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Send helpdesk UI when bot starts"""
        if self._instructions_sent:
            return
        
        if not self.helpdesk_channel_id:
            print("⚠️  CHANNEL_PLAYER_FORCE_REG_ID not set in .env file. Skipping helpdesk UI.")
            return
        
        try:
            channel = self.bot.get_channel(self.helpdesk_channel_id)
            if not channel:
                print(f"❌ Helpdesk channel not found with ID: {self.helpdesk_channel_id}")
                return
            
            # Purge all messages in the channel
            print(f"🧹 Purging all messages in {channel.name}...")
            deleted = await channel.purge(limit=100)
            print(f"🗑️ Deleted {len(deleted)} messages from {channel.name}")
            
            # Create helpdesk UI embed
            embed = discord.Embed(
                title="Registration Helpdesk",
                description="Need help with player registration? Click the button below to get assistance from our staff team.",
                color=0xFF4654
            )
            
            embed.add_field(
                name="How It Works",
                value=(
                    "1. Click the Help button below\n"
                    "2. A private thread will be created for you\n"
                    "3. Staff members will be notified and will assist you\n"
                    "4. Staff will help you complete your registration\n"
                    "5. The thread will be automatically deleted after completion"
                ),
                inline=False
            )
            
            embed.add_field(
                name="What You'll Need",
                value=(
                    "- Your in-game profile screenshot (for OCR), OR\n"
                    "- Your IGN, Player ID, and Region (for manual entry)"
                ),
                inline=False
            )
            
            # Add persistent view
            view = HelpdeskView()
            await channel.send(embed=embed, view=view)
            
            self._instructions_sent = True
            print(f"✅ Helpdesk UI posted in {channel.name}")
            
        except Exception as e:
            print(f"❌ Error sending helpdesk UI: {e}")

async def setup(bot):
    await bot.add_cog(RegistrationHelpdesk(bot))
