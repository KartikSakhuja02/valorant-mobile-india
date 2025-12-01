import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio

class DMPurge(commands.Cog):
    """DM Purge disabled - Messages are kept permanently"""
    
    def __init__(self, bot):
        self.bot = bot
        self.dm_channels = {}  # Track DM channels with timestamp: {channel_id: last_purge_time}
        self.notified_users = set()  # Track users who have been notified about purging
        # self.purge_task.start()  # DISABLED - No automatic purging
        print("ℹ️ DM Purge system DISABLED - Messages will NOT be purged automatically")
    
    def cog_unload(self):
        pass  # self.purge_task.cancel()  # DISABLED
    
    # @tasks.loop(minutes=30)  # DISABLED - No automatic purging
    # async def purge_task(self):
    #     """Purge all DM messages every 30 minutes - DISABLED"""
    #     pass
    
    # @purge_task.before_loop  # DISABLED
    # async def before_purge_task(self):
    #     """Wait until bot is ready before starting the purge task - DISABLED"""
    #     pass
    
    # async def initial_purge(self):
    #     """Purge existing messages on bot startup - DISABLED"""
    #     pass
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Track DM channels - NO PURGING (DISABLED)"""
        # Only track DM messages
        if isinstance(message.channel, discord.DMChannel):
            # Add channel to tracking dict
            if message.channel.id not in self.dm_channels:
                self.dm_channels[message.channel.id] = datetime.utcnow()
            
            # DISABLED: No purging or notifications
            pass

async def setup(bot):
    await bot.add_cog(DMPurge(bot))
