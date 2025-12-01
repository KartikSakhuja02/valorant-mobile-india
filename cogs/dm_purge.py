import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio

class DMPurge(commands.Cog):
    """Automatically purges DM messages every 30 minutes for privacy"""
    
    def __init__(self, bot):
        self.bot = bot
        self.dm_channels = {}  # Track DM channels with timestamp: {channel_id: last_purge_time}
        self.notified_users = set()  # Track users who have been notified about purging
        self.purge_task.start()
        print("✅ DM Purge system initialized - Messages will be purged every 30 minutes")
    
    def cog_unload(self):
        self.purge_task.cancel()
    
    @tasks.loop(minutes=30)
    async def purge_task(self):
        """Purge all DM messages every 30 minutes"""
        try:
            purged_count = 0
            channels_purged = 0
            
            # Create a copy of dm_channels to avoid modification during iteration
            channels_to_purge = list(self.dm_channels.keys())
            
            for channel_id in channels_to_purge:
                try:
                    channel = await self.bot.fetch_channel(channel_id)
                    
                    if isinstance(channel, discord.DMChannel):
                        # Delete all bot messages
                        deleted = 0
                        async for message in channel.history(limit=None):
                            try:
                                # Only bot can delete its own messages
                                if message.author.id == self.bot.user.id:
                                    await message.delete()
                                    deleted += 1
                                    await asyncio.sleep(0.3)  # Rate limit protection
                            except discord.NotFound:
                                pass
                            except discord.Forbidden:
                                pass
                            except Exception as e:
                                print(f"Error deleting message: {e}")
                        
                        if deleted > 0:
                            purged_count += deleted
                            channels_purged += 1
                            self.dm_channels[channel_id] = datetime.utcnow()
                            
                            # Send reminder about privacy
                            try:
                                embed = discord.Embed(
                                    title="🔒 Automatic Privacy Cleanup",
                                    description=(
                                        f"✅ **{deleted} bot messages** have been purged from this DM.\n\n"
                                        "**⚠️ User Messages:**\n"
                                        "Discord doesn't allow bots to delete your messages.\n"
                                        "To clear your messages, please:\n"
                                        "• Right-click on each message → Delete\n"
                                        "• Or close this DM to clear your view\n\n"
                                        "**Next automatic purge:** In 30 minutes"
                                    ),
                                    color=0x00FF00,
                                    timestamp=datetime.utcnow()
                                )
                                embed.set_footer(text="Bot messages auto-purge every 30 minutes")
                                await channel.send(embed=embed, delete_after=600)  # Delete after 10 minutes
                            except:
                                pass
                
                except discord.NotFound:
                    # Channel no longer exists, remove from tracking
                    if channel_id in self.dm_channels:
                        del self.dm_channels[channel_id]
                except Exception as e:
                    print(f"Error purging DM channel {channel_id}: {e}")
            
            if channels_purged > 0:
                print(f"✅ Purged {purged_count} bot messages from {channels_purged} DM channels")
        
        except Exception as e:
            print(f"Error in DM purge task: {e}")
            import traceback
            traceback.print_exc()
    
    @purge_task.before_loop
    async def before_purge_task(self):
        """Wait until bot is ready before starting the purge task"""
        await self.bot.wait_until_ready()
        print("🔒 DM Purge task starting - Initial purge will begin now")
        
        # Run initial purge on startup
        try:
            await self.initial_purge()
        except Exception as e:
            print(f"Error during initial purge: {e}")
            import traceback
            traceback.print_exc()
    
    async def initial_purge(self):
        """Purge existing messages on bot startup"""
        try:
            purged_count = 0
            channels_purged = 0
            
            print("🔍 Scanning for existing DM channels to purge...")
            
            # Get all cached DM channels
            for user in self.bot.users:
                # Skip the bot itself
                if user.bot or user.id == self.bot.user.id:
                    continue
                    
                if user.dm_channel:
                    try:
                        channel = user.dm_channel
                        deleted = 0
                        
                        print(f"   Purging DM with {user.name}...")
                        
                        # Delete ALL bot messages (no time limit)
                        async for message in channel.history(limit=None):
                            try:
                                # Only delete bot's messages
                                if message.author.id == self.bot.user.id:
                                    await message.delete()
                                    deleted += 1
                                    await asyncio.sleep(0.3)  # Rate limit protection
                            except discord.NotFound:
                                pass
                            except discord.Forbidden:
                                pass
                            except Exception:
                                pass
                        
                        if deleted > 0:
                            purged_count += deleted
                            channels_purged += 1
                            self.dm_channels[channel.id] = datetime.utcnow()
                            print(f"   ✅ Purged {deleted} messages from {user.name}")
                            
                            # Send initial privacy notice
                            try:
                                embed = discord.Embed(
                                    title="🔒 Bot Restarted - DMs Cleaned",
                                    description=(
                                        f"✅ **{deleted} bot messages** have been purged.\n\n"
                                        "**⚠️ About User Messages:**\n"
                                        "Discord API prevents bots from deleting your messages.\n"
                                        "To clear your messages manually:\n"
                                        "• Right-click each message → Delete\n"
                                        "• Or close this DM to clear your view\n\n"
                                        "**Bot messages auto-purge every 30 minutes**"
                                    ),
                                    color=0x3498DB,
                                    timestamp=datetime.utcnow()
                                )
                                embed.set_footer(text="Privacy protection enabled")
                                await channel.send(embed=embed, delete_after=600)
                            except:
                                pass
                    
                    except Exception as e:
                        print(f"Error purging DM with {user.name}: {e}")
            
            if channels_purged > 0:
                print(f"✅ Initial purge complete: {purged_count} bot messages from {channels_purged} DM channels")
            else:
                print("ℹ️ No cached DM channels found at startup. Channels will be purged when users send messages.")
        
        except Exception as e:
            print(f"Error during initial purge: {e}")
            import traceback
            traceback.print_exc()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Track DM channels and notify users about purging"""
        # Only track DM messages
        if isinstance(message.channel, discord.DMChannel):
            # Add channel to tracking dict
            if message.channel.id not in self.dm_channels:
                self.dm_channels[message.channel.id] = datetime.utcnow()
            
            # If this is a new user, purge old bot messages and notify
            if message.author.id not in self.notified_users and not message.author.bot:
                self.notified_users.add(message.author.id)
                
                # Purge ALL old bot messages in this DM channel
                try:
                    deleted = 0
                    async for old_message in message.channel.history(limit=None):
                        try:
                            # Only delete bot's messages
                            if old_message.author.id == self.bot.user.id:
                                await old_message.delete()
                                deleted += 1
                                await asyncio.sleep(0.3)
                        except:
                            pass
                    
                    if deleted > 0:
                        print(f"✅ Purged {deleted} old bot messages from DM with {message.author.name}")
                except Exception as e:
                    print(f"Error purging old messages: {e}")
                
                # Send privacy notice to new users
                try:
                    embed = discord.Embed(
                        title="🔒 Privacy & Auto-Cleanup Active",
                        description=(
                            "Welcome! Your privacy is important.\n\n"
                            "✅ **Bot messages** are automatically deleted every 30 minutes\n"
                            "⚠️ **Your messages** cannot be deleted by the bot (Discord limitation)\n\n"
                            "**To clear your messages manually:**\n"
                            "• Right-click on each message → Delete\n"
                            "• Or close this DM and reopen to start fresh\n\n"
                            "This ensures bot responses don't clutter your DMs!"
                        ),
                        color=0x3498DB,
                        timestamp=datetime.utcnow()
                    )
                    embed.set_footer(text="Bot auto-cleanup: Every 30 minutes")
                    
                    await message.channel.send(embed=embed, delete_after=600)  # Delete after 10 minutes
                except Exception as e:
                    print(f"Error sending privacy notice: {e}")

async def setup(bot):
    await bot.add_cog(DMPurge(bot))
