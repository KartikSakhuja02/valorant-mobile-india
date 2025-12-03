import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import asyncio
from pathlib import Path
from services import db

# Helper to get config values (env preferred, fallback to config.json if present)
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
    Wait for a message with inactivity timeout system.
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
                "⚠️ **If you don't respond in the next 5 minutes, this registration will be cancelled.**"
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
                    f"❌ {user.mention} **Registration Cancelled**\n\n"
                    "You didn't respond for 10 minutes total.\n"
                    "This thread will be deleted in 10 seconds."
                )
            except:
                pass
            
            # Send DM
            try:
                await user.send(
                    "❌ **Registration Cancelled Due to Inactivity**\n\n"
                    "Your registration thread was deleted because you didn't respond for 10 minutes.\n\n"
                    "**To register again:**\n"
                    "• Use the `/register` command\n"
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

class RegistrationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view, no timeout
    
    @discord.ui.button(label="Screenshot Registration", style=discord.ButtonStyle.primary, custom_id="reg_screenshot")
    async def screenshot_registration(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(f"🔧 Screenshot Registration button clicked by {interaction.user.name}")
        
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        print(f"✓ Interaction deferred")
        
        # Check if already registered
        try:
            existing_player = await db.get_player(interaction.user.id)
            if existing_player:
                await interaction.followup.send("You are already registered!", ephemeral=True)
                print(f"⚠️ User {interaction.user.name} is already registered")
                return
        except Exception as e:
            print(f"❌ Error checking registration: {e}")

        try:
            print(f"✓ Creating thread...")
            # Create private thread
            thread = await interaction.channel.create_thread(
                name=f"Registration-{interaction.user.name}",
                auto_archive_duration=1440
            )
            print(f"✓ Thread created: {thread.name} (ID: {thread.id})")
            
            # Add user to thread
            # Add user to thread
            await thread.add_user(interaction.user)
            print(f"✓ Added {interaction.user.name} to thread")
            
            # Add staff members to thread
            admin_role_id = int(cfg('ROLE_ADMINISTRATOR_ID', 0)) if cfg('ROLE_ADMINISTRATOR_ID') else None
            staff_role_id = int(cfg('ROLE_STAFF_ID', 0)) if cfg('ROLE_STAFF_ID') else None
            mod_role_id = int(cfg('ROLE_MODERATOR_ID', 0)) if cfg('ROLE_MODERATOR_ID') else None
            
            print(f"🔍 Looking for staff with role IDs: Admin={admin_role_id}, Staff={staff_role_id}, Mod={mod_role_id}")
            
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
            
            await interaction.followup.send(f"Registration started in {thread.mention}", ephemeral=True)
            print(f"✅ Registration thread created successfully for {interaction.user.name}")
        except Exception as e:
            print(f"❌ Error creating registration thread: {e}")
            await interaction.followup.send(f"❌ Error creating thread: {str(e)}", ephemeral=True)
            return
        
        # Send instructions in thread
        await thread.send(
            f"{interaction.user.mention} Please send your profile screenshot here.\n"
            "Make sure:\n"
            "- IGN (In-Game Name) is clearly visible\n"
            "- Player ID is visible\n"
            "- Image has good quality"
        )

        def check(message):
            return message.author.id == interaction.user.id and \
                   message.channel.id == thread.id and \
                   message.attachments

        try:
            # Wait for screenshot with inactivity timeout
            message, timed_out = await wait_for_message_with_timeout(
                interaction.client, check, thread, interaction.user
            )
            
            if timed_out or not message:
                return
            
            # Process OCR
            from services.ocr_service import ocr_service
            success, ign, player_id = await ocr_service.process_screenshot(message.attachments[0])
            
            if not success:
                await thread.send(f"❌ OCR Failed: {ign}\nPlease try again with a clearer screenshot.")
                asyncio.create_task(self.delete_thread_after_delay(thread, 12))
                return
            
            # Show OCR results and ask for confirmation
            embed = discord.Embed(
                title="Profile Information Detected",
                description="Please verify if this information is correct:",
                color=discord.Color.blue()
            )
            embed.add_field(name="IGN", value=f"`{ign}`", inline=True)
            embed.add_field(name="ID", value=f"`{player_id}`", inline=True)
            
            confirm_view = discord.ui.View(timeout=300)
            
            async def confirm_callback(interaction: discord.Interaction):
                if interaction.user.id != message.author.id:
                    await interaction.response.send_message("This is not your registration!", ephemeral=True)
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
                cog = interaction.client.get_cog('Registration')
                
                for region_name, region_code in regions:
                    button = discord.ui.Button(
                        label=region_name,
                        custom_id=f"region_{region_code}",
                        style=discord.ButtonStyle.primary
                    )
                    
                    async def region_callback(i: discord.Interaction, r_code=region_code):
                        if i.user.id != message.author.id:
                            await i.response.send_message("This is not your registration!", ephemeral=True)
                            return
                        
                        # If APAC region, ask if they're Indian
                        if r_code == "ap":
                            await i.response.send_message("Are you from India?", ephemeral=False)
                            
                            india_view = discord.ui.View(timeout=300)
                            
                            yes_button = discord.ui.Button(label="Yes, I'm Indian", style=discord.ButtonStyle.success)
                            no_button = discord.ui.Button(label="No", style=discord.ButtonStyle.secondary)
                            
                            async def india_yes_callback(india_i: discord.Interaction):
                                if india_i.user.id != message.author.id:
                                    await india_i.response.send_message("This is not your registration!", ephemeral=True)
                                    return
                                    
                                await india_i.response.defer()
                                
                                try:
                                    # Create player with APAC region
                                    await db.create_player(
                                        discord_id=message.author.id,
                                        ign=ign,
                                        player_id=int(player_id),
                                        region="ap"
                                    )
                                    
                                    initial_stats = {
                                        "kills": 0,
                                        "deaths": 0,
                                        "assists": 0,
                                        "matches_played": 0,
                                        "wins": 0,
                                        "losses": 0,
                                        "mvps": 0
                                    }
                                    
                                    await db.create_player_stats(message.author.id, initial_stats)
                                    await db.update_player_leaderboard(message.author.id, ign, "ap")
                                    await db.update_player_leaderboard_ranks()
                                    
                                    # Assign both APAC and India roles
                                    role_msg = ""
                                    if cog and isinstance(india_i.user, discord.Member):
                                        ap_assigned = await cog.assign_region_role(india_i.user, "ap")
                                        india_assigned = await cog.assign_region_role(india_i.user, "india")
                                        if ap_assigned and india_assigned:
                                            role_msg = "✅ APAC and India roles assigned!"
                                        elif ap_assigned:
                                            role_msg = "✅ APAC role assigned! ⚠️ Could not assign India role."
                                        else:
                                            role_msg = "⚠️ Could not assign region roles."
                                    
                                    # Send log
                                    try:
                                        log_channel_id = cfg('LOG_CHANNEL_ID')
                                        if log_channel_id:
                                            log_channel = interaction.client.get_channel(int(log_channel_id))
                                            if log_channel:
                                                log_embed = discord.Embed(
                                                    title="🆕 New Player Registration (Thread - Screenshot)",
                                                    color=discord.Color.blue(),
                                                    timestamp=discord.utils.utcnow()
                                                )
                                                log_embed.add_field(name="Player", value=f"{message.author.mention} ({message.author})", inline=False)
                                                log_embed.add_field(name="IGN", value=ign, inline=True)
                                                log_embed.add_field(name="Player ID", value=str(player_id), inline=True)
                                                log_embed.add_field(name="Region", value="AP (India)", inline=True)
                                                log_embed.set_thumbnail(url=message.author.display_avatar.url)
                                                log_embed.set_footer(text=f"User ID: {message.author.id} • Method: Thread Screenshot")
                                                await log_channel.send(embed=log_embed)
                                    except Exception as log_error:
                                        print(f"Error sending registration log: {log_error}")
                                    
                                    await thread.send(f"✅ Registration successful! {role_msg}\nThis thread will be deleted in 10 seconds.")
                                    await asyncio.sleep(10)
                                    await thread.delete()
                                    
                                except Exception as e:
                                    await thread.send(f"❌ Registration failed: {str(e)}")
                                    asyncio.create_task(cog.delete_thread_after_delay(thread, 12))
                            
                            async def india_no_callback(india_i: discord.Interaction):
                                if india_i.user.id != message.author.id:
                                    await india_i.response.send_message("This is not your registration!", ephemeral=True)
                                    return
                                    
                                await india_i.response.defer()
                                
                                try:
                                    # Create player with APAC region only
                                    await db.create_player(
                                        discord_id=message.author.id,
                                        ign=ign,
                                        player_id=int(player_id),
                                        region="ap"
                                    )
                                    
                                    initial_stats = {
                                        "kills": 0,
                                        "deaths": 0,
                                        "assists": 0,
                                        "matches_played": 0,
                                        "wins": 0,
                                        "losses": 0,
                                        "mvps": 0
                                    }
                                    
                                    await db.create_player_stats(message.author.id, initial_stats)
                                    await db.update_player_leaderboard(message.author.id, ign, "ap")
                                    await db.update_player_leaderboard_ranks()
                                    
                                    # Assign only APAC role
                                    role_msg = ""
                                    if cog and isinstance(india_i.user, discord.Member):
                                        ap_assigned = await cog.assign_region_role(india_i.user, "ap")
                                        role_msg = "✅ APAC role assigned!" if ap_assigned else "⚠️ Could not assign region role."
                                    
                                    # Send log
                                    try:
                                        log_channel_id = cfg('LOG_CHANNEL_ID')
                                        if log_channel_id:
                                            log_channel = interaction.client.get_channel(int(log_channel_id))
                                            if log_channel:
                                                log_embed = discord.Embed(
                                                    title="🆕 New Player Registration (Thread - Screenshot)",
                                                    color=discord.Color.blue(),
                                                    timestamp=discord.utils.utcnow()
                                                )
                                                log_embed.add_field(name="Player", value=f"{message.author.mention} ({message.author})", inline=False)
                                                log_embed.add_field(name="IGN", value=ign, inline=True)
                                                log_embed.add_field(name="Player ID", value=str(player_id), inline=True)
                                                log_embed.add_field(name="Region", value="AP", inline=True)
                                                log_embed.set_thumbnail(url=message.author.display_avatar.url)
                                                log_embed.set_footer(text=f"User ID: {message.author.id} • Method: Thread Screenshot")
                                                await log_channel.send(embed=log_embed)
                                    except Exception as log_error:
                                        print(f"Error sending registration log: {log_error}")
                                    
                                    await thread.send(f"✅ Registration successful! {role_msg}\nThis thread will be deleted in 10 seconds.")
                                    await asyncio.sleep(10)
                                    await thread.delete()
                                    
                                except Exception as e:
                                    await thread.send(f"❌ Registration failed: {str(e)}")
                                    asyncio.create_task(cog.delete_thread_after_delay(thread, 12))
                            
                            yes_button.callback = india_yes_callback
                            no_button.callback = india_no_callback
                            india_view.add_item(yes_button)
                            india_view.add_item(no_button)
                            
                            await i.edit_original_response(view=india_view)
                            return
                        
                        # For non-APAC regions, proceed normally
                        await i.response.defer()
                        
                        try:
                            # Create new player in database
                            await db.create_player(
                                discord_id=message.author.id,
                                ign=ign,
                                player_id=int(player_id),
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
                            
                            await db.create_player_stats(message.author.id, initial_stats)
                            await db.update_player_leaderboard(
                                message.author.id,
                                ign,
                                r_code
                            )
                            await db.update_player_leaderboard_ranks()
                            
                            # Assign region role
                            if cog and isinstance(i.user, discord.Member):
                                role_assigned = await cog.assign_region_role(i.user, r_code)
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
                                            title="🆕 New Player Registration (Thread - Screenshot)",
                                            color=discord.Color.blue(),
                                            timestamp=discord.utils.utcnow()
                                        )
                                        log_embed.add_field(name="Player", value=f"{message.author.mention} ({message.author})", inline=False)
                                        log_embed.add_field(name="IGN", value=ign, inline=True)
                                        log_embed.add_field(name="Player ID", value=str(player_id), inline=True)
                                        log_embed.add_field(name="Region", value=r_code.upper(), inline=True)
                                        log_embed.set_thumbnail(url=message.author.display_avatar.url)
                                        log_embed.set_footer(text=f"User ID: {message.author.id} • Method: Thread Screenshot")
                                        
                                        await log_channel.send(embed=log_embed)
                            except Exception as log_error:
                                print(f"Error sending registration log: {log_error}")

                            await thread.send(f"✅ Registration successful! {role_msg}\nThis thread will be deleted in 10 seconds.")
                            await asyncio.sleep(10)
                            await thread.delete()

                        except Exception as e:
                            await thread.send(f"❌ Registration failed: {str(e)}")
                            asyncio.create_task(self.delete_thread_after_delay(thread, 12))
                    
                    button.callback = region_callback
                    region_view.add_item(button)
                
                await interaction.message.edit(
                    content="Please select your region:",
                    embed=None,
                    view=region_view
                )
            
            async def cancel_callback(interaction: discord.Interaction):
                if interaction.user.id != message.author.id:
                    await interaction.response.send_message("This is not your registration!", ephemeral=True)
                    return
                    
                await interaction.response.defer()
                await thread.send("Registration cancelled. Please try again with a new screenshot.")
                asyncio.create_task(self.delete_thread_after_delay(thread, 12))
            
            confirm_button = discord.ui.Button(
                label="Confirm",
                style=discord.ButtonStyle.success,
                custom_id="confirm"
            )
            confirm_button.callback = confirm_callback
            
            cancel_button = discord.ui.Button(
                label="Cancel",
                style=discord.ButtonStyle.danger,
                custom_id="cancel"
            )
            cancel_button.callback = cancel_callback
            
            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)
            
            await thread.send(embed=embed, view=confirm_view)
            
        except asyncio.TimeoutError:
            await thread.send("Registration timed out. Thread will be deleted in 10 seconds.")
            await asyncio.sleep(10)
            await thread.delete()

    @discord.ui.button(label="Manual Registration", style=discord.ButtonStyle.secondary, custom_id="reg_manual")
    async def manual_registration(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(f"🔧 Manual Registration button clicked by {interaction.user.name}")
        
        # Defer immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        print(f"✓ Interaction deferred")
        
        # Check if already registered
        try:
            existing_player = await db.get_player(interaction.user.id)
            if existing_player:
                await interaction.followup.send("You are already registered!", ephemeral=True)
                print(f"⚠️ User {interaction.user.name} is already registered")
                return
        except Exception as e:
            print(f"❌ Error checking registration: {e}")

        try:
            print(f"✓ Creating thread...")
            # Create private thread
            thread = await interaction.channel.create_thread(
                name=f"Registration-{interaction.user.name}",
                auto_archive_duration=1440
            )
            print(f"✓ Thread created: {thread.name} (ID: {thread.id})")
            
            # Add user to thread
            # Add user to thread
            await thread.add_user(interaction.user)
            print(f"✓ Added {interaction.user.name} to thread")
            
            # Add staff members to thread
            admin_role_id = int(cfg('ROLE_ADMINISTRATOR_ID', 0)) if cfg('ROLE_ADMINISTRATOR_ID') else None
            staff_role_id = int(cfg('ROLE_STAFF_ID', 0)) if cfg('ROLE_STAFF_ID') else None
            mod_role_id = int(cfg('ROLE_MODERATOR_ID', 0)) if cfg('ROLE_MODERATOR_ID') else None
            
            print(f"🔍 Looking for staff with role IDs: Admin={admin_role_id}, Staff={staff_role_id}, Mod={mod_role_id}")
            
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

            await interaction.followup.send(f"Registration started in {thread.mention}", ephemeral=True)
            print(f"✅ Registration thread created successfully for {interaction.user.name}")
        except Exception as e:
            print(f"❌ Error creating registration thread: {e}")
            await interaction.followup.send(f"❌ Error creating thread: {str(e)}", ephemeral=True)
            return

        # Send instructions in thread
        await thread.send(
            f"{interaction.user.mention} Please provide the following information:\n"
            "1. Your IGN (In-Game Name)\n"
            "2. Your In-game ID\n"
            "3. Your Region (NA/EU/AP/KR/BR/LATAM/JP)"
        )

        try:
            registration_data = {}
            
            # Get IGN
            await thread.send("What is your IGN?")
            msg = await interaction.client.wait_for(
                'message',
                timeout=300,
                check=lambda m: m.author.id == interaction.user.id and m.channel.id == thread.id
            )
            registration_data['ign'] = msg.content

            # Get ID
            await thread.send("What is your In-game ID?")
            msg = await interaction.client.wait_for(
                'message',
                timeout=300,
                check=lambda m: m.author.id == interaction.user.id and m.channel.id == thread.id
            )
            try:
                registration_data['id'] = int(msg.content)
            except ValueError:
                await thread.send("Invalid ID format. Registration cancelled.")
                await asyncio.sleep(5)
                await thread.delete()
                return

            # Get Region
            valid_regions = ['na', 'eu', 'ap', 'kr', 'br', 'latam', 'jp']
            await thread.send(
                "What is your Region?\n"
                "Valid options: NA, EU, AP, KR, BR, LATAM, JP"
            )
            
            while True:
                msg = await interaction.client.wait_for(
                    'message',
                    timeout=300,
                    check=lambda m: m.author.id == interaction.user.id and m.channel.id == thread.id
                )
                region = msg.content.lower()
                if region in valid_regions:
                    registration_data['region'] = region
                    break
                await thread.send("Invalid region. Please choose from: NA, EU, AP, KR, BR, LATAM, JP")

            # Process registration
            try:
                # If APAC, ask if they're Indian
                if registration_data['region'] == 'ap':
                    await thread.send("Are you from India? (Reply: yes or no)")
                    
                    while True:
                        msg = await interaction.client.wait_for(
                            'message',
                            timeout=300,
                            check=lambda m: m.author.id == interaction.user.id and m.channel.id == thread.id
                        )
                        response = msg.content.lower()
                        if response in ['yes', 'no']:
                            is_indian = (response == 'yes')
                            break
                        await thread.send("Please reply with 'yes' or 'no'")
                    
                    # Create player
                    player = await db.create_player(
                        discord_id=interaction.user.id,
                        ign=registration_data['ign'],
                        player_id=registration_data['id'],
                        region=registration_data['region']
                    )
                    
                    initial_stats = {
                        "kills": 0,
                        "deaths": 0,
                        "assists": 0,
                        "matches_played": 0,
                        "wins": 0,
                        "losses": 0,
                        "mvps": 0
                    }
                    
                    await db.create_player_stats(interaction.user.id, initial_stats)
                    await db.update_player_leaderboard(
                        interaction.user.id,
                        registration_data['ign'],
                        registration_data['region']
                    )
                    await db.update_player_leaderboard_ranks()
                    
                    # Assign roles
                    cog = interaction.client.get_cog('Registration')
                    role_msg = ""
                    if cog and isinstance(interaction.user, discord.Member):
                        if is_indian:
                            ap_assigned = await cog.assign_region_role(interaction.user, "ap")
                            india_assigned = await cog.assign_region_role(interaction.user, "india")
                            if ap_assigned and india_assigned:
                                role_msg = "✅ APAC and India roles assigned!"
                            elif ap_assigned:
                                role_msg = "✅ APAC role assigned! ⚠️ Could not assign India role."
                            else:
                                role_msg = "⚠️ Could not assign region roles."
                        else:
                            ap_assigned = await cog.assign_region_role(interaction.user, "ap")
                            role_msg = "✅ APAC role assigned!" if ap_assigned else "⚠️ Could not assign region role."
                    
                    # Send log
                    try:
                        log_channel_id = cfg('LOG_CHANNEL_ID')
                        if log_channel_id:
                            log_channel = interaction.client.get_channel(int(log_channel_id))
                            if log_channel:
                                log_embed = discord.Embed(
                                    title="🆕 New Player Registration (Thread - Manual)",
                                    color=discord.Color.blue(),
                                    timestamp=discord.utils.utcnow()
                                )
                                log_embed.add_field(name="Player", value=f"{interaction.user.mention} ({interaction.user})", inline=False)
                                log_embed.add_field(name="IGN", value=registration_data['ign'], inline=True)
                                log_embed.add_field(name="Player ID", value=str(registration_data['id']), inline=True)
                                region_display = "AP (India)" if is_indian else "AP"
                                log_embed.add_field(name="Region", value=region_display, inline=True)
                                log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                                log_embed.set_footer(text=f"User ID: {interaction.user.id} • Method: Thread Manual")
                                await log_channel.send(embed=log_embed)
                    except Exception as log_error:
                        print(f"Error sending registration log: {log_error}")
                    
                    await thread.send(f"✅ Registration successful! {role_msg}\nThis thread will be deleted in 10 seconds.")
                    await asyncio.sleep(10)
                    await thread.delete()
                    
                else:
                    # Non-APAC regions
                    # Create new player in database
                    player = await db.create_player(
                        discord_id=interaction.user.id,
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
                    
                    await db.create_player_stats(interaction.user.id, initial_stats)
                    await db.update_player_leaderboard(
                        interaction.user.id,
                        registration_data['ign'],
                        registration_data['region']
                    )
                    await db.update_player_leaderboard_ranks()
                    
                    # Assign region role
                    cog = interaction.client.get_cog('Registration')
                    if cog and isinstance(interaction.user, discord.Member):
                        role_assigned = await cog.assign_region_role(interaction.user, registration_data['region'])
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
                                    title="🆕 New Player Registration (Thread - Manual)",
                                    color=discord.Color.blue(),
                                    timestamp=discord.utils.utcnow()
                                )
                                log_embed.add_field(name="Player", value=f"{interaction.user.mention} ({interaction.user})", inline=False)
                                log_embed.add_field(name="IGN", value=registration_data['ign'], inline=True)
                                log_embed.add_field(name="Player ID", value=str(registration_data['id']), inline=True)
                                log_embed.add_field(name="Region", value=registration_data['region'].upper(), inline=True)
                                log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                                log_embed.set_footer(text=f"User ID: {interaction.user.id} • Method: Thread Manual")
                                
                                await log_channel.send(embed=log_embed)
                    except Exception as log_error:
                        print(f"Error sending registration log: {log_error}")

                    await thread.send(f"✅ Registration successful! {role_msg}\nThis thread will be deleted in 10 seconds.")
                    await asyncio.sleep(10)
                    await thread.delete()

            except Exception as e:
                await thread.send(f"❌ Registration failed: {str(e)}")
                asyncio.create_task(self.delete_thread_after_delay(thread, 12))

        except asyncio.TimeoutError:
            await thread.send("Registration timed out. Thread will be deleted in 10 seconds.")
            await asyncio.sleep(10)
            await thread.delete()

    async def delete_thread_after_delay(self, thread, hours):
        """Delete thread after specified hours"""
        await asyncio.sleep(hours * 3600)  # Convert hours to seconds
        try:
            await thread.delete()
        except:
            pass

class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path(__file__).parent.parent / "data"
        self.scoring_config = self.load_scoring_config()
        self.registration_channel_id = int(cfg('CHANNEL_PLAYER_REG_ID', 0)) if cfg('CHANNEL_PLAYER_REG_ID') else None
        self._instructions_sent = False
        
        # Region role mappings
        self.region_roles = {
            'na': int(cfg('ROLE_AMERICAS_ID', 0)) if cfg('ROLE_AMERICAS_ID') else None,
            'br': int(cfg('ROLE_AMERICAS_ID', 0)) if cfg('ROLE_AMERICAS_ID') else None,
            'latam': int(cfg('ROLE_AMERICAS_ID', 0)) if cfg('ROLE_AMERICAS_ID') else None,
            'eu': int(cfg('ROLE_EMEA_ID', 0)) if cfg('ROLE_EMEA_ID') else None,
            'ap': int(cfg('ROLE_APAC_ID', 0)) if cfg('ROLE_APAC_ID') else None,
            'kr': int(cfg('ROLE_APAC_ID', 0)) if cfg('ROLE_APAC_ID') else None,
            'jp': int(cfg('ROLE_APAC_ID', 0)) if cfg('ROLE_APAC_ID') else None,
            'india': int(cfg('INDIA_ROLE_ID', 0)) if cfg('INDIA_ROLE_ID') else None,
        }
    
    async def assign_region_role(self, member: discord.Member, region: str) -> bool:
        """Assign region-based role to a member"""
        try:
            role_id = self.region_roles.get(region.lower())
            if not role_id:
                print(f"⚠️ No role ID configured for region: {region}")
                return False
            
            role = member.guild.get_role(role_id)
            if not role:
                print(f"⚠️ Role not found with ID: {role_id} for region: {region}")
                return False
            
            await member.add_roles(role, reason=f"Registered with region: {region.upper()}")
            print(f"✅ Assigned {role.name} role to {member.name} for region {region.upper()}")
            return True
        except discord.Forbidden:
            print(f"❌ No permission to assign role for {member.name}")
            return False
        except Exception as e:
            print(f"❌ Error assigning role: {e}")
            return False
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Send registration UI when bot starts"""
        # Only send once
        if self._instructions_sent:
            return
        
        if not self.registration_channel_id:
            print("⚠️  CHANNEL_PLAYER_REG_ID not set in .env file. Skipping registration UI message.")
            print("💡 Tip: Add CHANNEL_PLAYER_REG_ID to your .env file to enable auto-registration UI.")
            return
        
        try:
            channel = self.bot.get_channel(self.registration_channel_id)
            if not channel:
                print(f"❌ Registration channel not found with ID: {self.registration_channel_id}")
                print(f"💡 Tip: Make sure the channel exists and the bot has access to it.")
                return
            
            # Purge all messages in the channel first
            print(f"🧹 Purging all messages in {channel.name}...")
            deleted = await channel.purge(limit=100)  # Purge up to 100 messages
            print(f"🗑️ Deleted {len(deleted)} messages from {channel.name}")
            
            # Create registration UI embed
            embed = discord.Embed(
                title="Player Registration",
                description="Choose your preferred registration method to get started.",
                color=0xFF4654  # Valorant red
            )
            
            embed.add_field(
                name="Screenshot Registration",
                value="Upload your profile screenshot and let the bot automatically extract your IGN and ID.",
                inline=False
            )
            
            embed.add_field(
                name="Manual Registration",
                value="Manually enter your IGN, In-game ID, and region.",
                inline=False
            )
            
            embed.add_field(
                name="How It Works",
                value=(
                    "1. Click one of the buttons below\n"
                    "2. A private thread will be created for you\n"
                    "3. Follow the instructions in the thread\n"
                    "4. Complete your registration\n"
                    "5. The thread will be automatically deleted"
                ),
                inline=False
            )
            
            # Add persistent view
            view = RegistrationView()
            await channel.send(embed=embed, view=view)
            
            self._instructions_sent = True
            print(f"✅ Registration UI posted in {channel.name}")
            
        except Exception as e:
            print(f"❌ Error sending registration UI: {e}")
    
    def load_scoring_config(self):
        """Load scoring configuration from JSON file"""
        config_file = self.data_dir / "scoring_config.json"
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading scoring config: {e}")
            # Return default config
            return {
                "player_scoring": {
                    "weights": {
                        "kill_points": 2.0,
                        "assist_points": 1.0,
                        "death_penalty": 0.5,
                        "win_points": 10.0,
                        "participation_points": 1.0
                    },
                    "bonus_multipliers": {
                        "kd_ratio_above_1.5": 1.1,
                        "kd_ratio_above_2.0": 1.2,
                        "win_rate_above_60": 1.05,
                        "win_rate_above_75": 1.15
                    }
                }
            }

    @app_commands.command(
        name="register",
        description="Start the registration process for Valorant Mobile"
    )
    async def register(self, interaction: discord.Interaction):
        """Start the registration process with screenshot or manual options"""
        # Check if already registered
        existing_player = await db.get_player(interaction.user.id)
        if existing_player:
            await interaction.response.send_message(
                "You are already registered!",
                ephemeral=True
            )
            return

        view = RegistrationView()
        await interaction.response.send_message(
            "**Choose Registration Method:**",
            view=view,
            ephemeral=True
        )
    
    def calculate_player_score(self, stats: dict):
        """Calculate player leaderboard score based on scoring config"""
        weights = self.scoring_config["player_scoring"]["weights"]
        bonuses = self.scoring_config["player_scoring"]["bonus_multipliers"]

        kills = stats.get("kills", 0)
        deaths = stats.get("deaths", 0)
        assists = stats.get("assists", 0)
        wins = stats.get("wins", 0)
        matches = stats.get("matches_played", 0)
        
        # Check minimum matches requirement
        min_matches = self.scoring_config.get("leaderboard_settings", {}).get("min_matches_for_ranking", 1)
        if matches < min_matches:
            return 0
        
        # Base score calculation
        score = (
            kills * weights["kill_points"] +
            assists * weights["assist_points"] -
            deaths * weights["death_penalty"] +
            wins * weights["win_points"] +
            matches * weights["participation_points"]
        )
        
        # Apply bonus multipliers
        multiplier = 1.0
        
        # K/D ratio bonuses
        if deaths > 0:
            kd_ratio = kills / deaths
            if kd_ratio >= 2.0:
                multiplier *= bonuses.get("kd_ratio_above_2.0", 1.2)
            elif kd_ratio >= 1.5:
                multiplier *= bonuses.get("kd_ratio_above_1.5", 1.1)
        
        # Win rate bonuses
        if matches > 0:
            win_rate = (wins / matches) * 100
            if win_rate >= 75:
                multiplier *= bonuses.get("win_rate_above_75", 1.15)
            elif win_rate >= 60:
                multiplier *= bonuses.get("win_rate_above_60", 1.05)
        
        score *= multiplier
        return max(0, score)  # Never return negative score
        
    async def update_nickname(self, member: discord.Member, ign: str, stats: dict):
        """Update member's nickname to show points and IGN"""
        try:
            points = self.calculate_player_score(stats)
            new_nickname = f"[{int(points)}] {ign}"
            
            # Discord nickname limit is 32 characters
            if len(new_nickname) > 32:
                # Truncate IGN if needed
                max_ign_length = 32 - len(f"[{int(points)}] ")
                truncated_ign = ign[:max_ign_length]
                new_nickname = f"[{int(points)}] {truncated_ign}"
            
            await member.edit(nick=new_nickname)
            return True
        except discord.Forbidden:
            # Bot doesn't have permission to change nickname
            return False
        except Exception as e:
            print(f"Error updating nickname: {e}")
            return False

    @app_commands.command(name="register", description="Register for the Valorant Mobile tournament")
    @app_commands.describe(
        ign="Your in-game name (Example: VALM#1234)",
        id="Your numeric in-game ID (Example: 12345)",
        region="Select your region from the list"
    )
    @app_commands.choices(region=[
        app_commands.Choice(name="🌎 North America (NA)", value="na"),
        app_commands.Choice(name="🌍 Europe (EU)", value="eu"),
        app_commands.Choice(name="🌏 Asia-Pacific (AP)", value="ap"),
        app_commands.Choice(name="🇰🇷 Korea (KR)", value="kr"),
        app_commands.Choice(name="🇧🇷 Brazil (BR)", value="br"),
        app_commands.Choice(name="🌎 Latin America (LATAM)", value="latam"),
        app_commands.Choice(name="🇯🇵 Japan (JP)", value="jp")
    ])
    async def register(self, interaction: discord.Interaction, ign: str, id: int, region: app_commands.Choice[str]):
        """Register for the tournament with your IGN, numeric ID, and region."""
        # Check if already registered
        existing_player = await db.get_player(interaction.user.id)
        if existing_player:
            await interaction.response.send_message(
                "You are already registered!",
                ephemeral=True
            )
            return

        # Check if IGN exists
        existing_ign = await db.get_player_by_ign(ign)
        if existing_ign:
            embed = discord.Embed(
                title="❌ Registration Failed",
                description=f"The IGN **{ign}** is already registered!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Why?",
                value=f"IGN matching is case-insensitive.\n"
                      f"Your IGN: `{ign}`\n"
                      f"Existing IGN: `{existing_ign['ign']}`\n"
                      f"These are considered the same.",
                inline=False
            )
            embed.add_field(
                name="Solution",
                value="Please choose a different in-game name.",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            # Create new player in database
            player = await db.create_player(
                discord_id=interaction.user.id,
                ign=ign,
                player_id=id,
                region=region.value
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
            
            # Create initial player stats
            await db.create_player_stats(interaction.user.id, initial_stats)
            
            # Add player to global leaderboard with initial stats
            try:
                await db.update_player_leaderboard(
                    interaction.user.id,
                    ign,
                    region.value
                )
                await db.update_player_leaderboard_ranks()
                print(f"✅ Added {ign} to player leaderboard")
            except Exception as e:
                print(f"⚠️ Error adding player to leaderboard: {e}")

            embed = discord.Embed(
                title="✅ Registration Successful!",
                description=f"Welcome to the tournament, {interaction.user.mention}!",
                color=discord.Color.green()
            )
            embed.add_field(name="IGN", value=ign, inline=True)
            embed.add_field(name="ID", value=str(id), inline=True)
            embed.add_field(name="Region", value=region.name, inline=True)
            embed.add_field(name="Starting Points", value="0 (play matches to earn points!)", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Send log to logs channel
            try:
                log_channel_id = cfg('LOG_CHANNEL_ID')
                if log_channel_id:
                    log_channel = self.bot.get_channel(int(log_channel_id))
                    if log_channel:
                        log_embed = discord.Embed(
                            title="🆕 New Player Registration",
                            color=discord.Color.blue(),
                            timestamp=discord.utils.utcnow()
                        )
                        log_embed.add_field(name="Player", value=f"{interaction.user.mention} ({interaction.user})", inline=False)
                        log_embed.add_field(name="IGN", value=ign, inline=True)
                        log_embed.add_field(name="Player ID", value=str(id), inline=True)
                        log_embed.add_field(name="Region", value=region.name, inline=True)
                        log_embed.add_field(name="Discord ID", value=str(interaction.user.id), inline=True)
                        log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                        log_embed.set_footer(text=f"User ID: {interaction.user.id} • Method: Manual")
                        
                        await log_channel.send(embed=log_embed)
            except Exception as log_error:
                print(f"Error sending registration log: {log_error}")

        except Exception as e:
            print(f"Registration error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred during registration. Please try again or contact an admin.",
                ephemeral=True
            )

    @app_commands.command(name="update_ign", description="Update your in-game name")
    @app_commands.describe(new_ign="Your new in-game name")
    async def update_ign(self, interaction: discord.Interaction, new_ign: str):
        """Update your in-game name."""
        # Get current player
        player = await db.get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message(
                "❌ You are not registered! Use `/register` first.",
                ephemeral=True
            )
            return

        # Check if new IGN exists
        existing_ign = await db.get_player_by_ign(new_ign)
        if existing_ign and existing_ign['discord_id'] != interaction.user.id:
            embed = discord.Embed(
                title="❌ IGN Update Failed",
                description=f"The IGN **{new_ign}** is already registered by another player!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Why?",
                value=f"IGN matching is case-insensitive.\n"
                      f"Your new IGN: `{new_ign}`\n"
                      f"Existing IGN: `{existing_ign['ign']}`\n"
                      f"These are considered the same.",
                inline=False
            )
            embed.add_field(
                name="Solution",
                value="Please choose a different in-game name.",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            old_ign = player['ign']
            
            # Update player's IGN in database
            await db.update_player_ign(interaction.user.id, new_ign)
            
            embed = discord.Embed(
                title="✅ IGN Updated!",
                description=f"Your in-game name has been successfully updated.",
                color=discord.Color.green()
            )
            embed.add_field(name="Old IGN", value=f"`{old_ign}`", inline=True)
            embed.add_field(name="New IGN", value=f"**{new_ign}**", inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"IGN update error: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while updating your IGN. Please try again or contact an admin.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Registration(bot))


