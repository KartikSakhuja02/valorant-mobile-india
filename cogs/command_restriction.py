import discord
from discord.ext import commands
from discord import app_commands
import os

class CommandRestriction(commands.Cog):
    """Restricts bot commands to specific channels only"""
    
    def __init__(self, bot):
        self.bot = bot
        # Get the allowed command channel ID from environment or config
        self.allowed_channel_id = None
        
        # Try to get from environment first
        channel_id = os.environ.get('BOT_COMMANDS_CHANNEL_ID') or os.environ.get('bot_commands_channel_id')
        
        if channel_id:
            try:
                self.allowed_channel_id = int(channel_id)
                print(f"✅ Bot commands restricted to channel ID: {self.allowed_channel_id}")
                
                # Add interaction check for slash commands
                self.bot.tree.interaction_check = self.slash_command_check
            except ValueError:
                print("⚠️ Invalid BOT_COMMANDS_CHANNEL_ID in environment")
        else:
            print("⚠️ BOT_COMMANDS_CHANNEL_ID not set - commands will work in all channels")
    
    async def slash_command_check(self, interaction: discord.Interaction) -> bool:
        """Global check for all slash commands"""
        # Allow DM commands
        if isinstance(interaction.channel, discord.DMChannel):
            return True
        
        # If no restriction is set, allow all channels
        if self.allowed_channel_id is None:
            return True
        
        # Check if command is in the allowed channel
        if interaction.channel_id == self.allowed_channel_id:
            return True
        
        # Not in allowed channel - send error and block
        allowed_channel = self.bot.get_channel(self.allowed_channel_id)
        channel_mention = allowed_channel.mention if allowed_channel else f"<#{self.allowed_channel_id}>"
        
        embed = discord.Embed(
            title="❌ Wrong Channel",
            description=(
                f"Slash commands can only be used in {channel_mention}!\n\n"
                f"Please go to the bot commands channel."
            ),
            color=0xFF0000
        )
        
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except:
                pass
        
        return False
    
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Check if command is being used in allowed channel"""
        # Skip DM commands (allow them)
        if isinstance(ctx.channel, discord.DMChannel):
            return
        
        # If no restriction is set, allow all channels
        if self.allowed_channel_id is None:
            return
        
        # Check if command is in the allowed channel
        if ctx.channel.id != self.allowed_channel_id:
            # Delete the command message if possible
            try:
                await ctx.message.delete()
            except:
                pass
            
            # Send ephemeral warning
            try:
                allowed_channel = self.bot.get_channel(self.allowed_channel_id)
                channel_mention = allowed_channel.mention if allowed_channel else f"<#{self.allowed_channel_id}>"
                
                embed = discord.Embed(
                    title="❌ Wrong Channel",
                    description=(
                        f"Bot commands can only be used in {channel_mention}!\n\n"
                        f"Please go to the bot commands channel to use this command."
                    ),
                    color=0xFF0000
                )
                
                # Send and auto-delete after 5 seconds
                msg = await ctx.send(embed=embed, delete_after=5)
            except:
                pass
            
            # Prevent command from executing
            raise commands.CheckFailure("Command used in wrong channel")
    
    @commands.command(name='setbotchannel')
    @commands.has_permissions(administrator=True)
    async def set_bot_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel where bot commands are allowed (Admin only)"""
        if channel is None:
            channel = ctx.channel
        
        self.allowed_channel_id = channel.id
        
        # Update the interaction check with new channel
        self.bot.tree.interaction_check = self.slash_command_check
        
        embed = discord.Embed(
            title="✅ Bot Commands Channel Set",
            description=(
                f"Bot commands are now restricted to {channel.mention}\n\n"
                f"**Channel ID:** {channel.id}\n\n"
                f"⚠️ **Important:** Add this to your .env file:\n"
                f"```\nBOT_COMMANDS_CHANNEL_ID={channel.id}\n```"
            ),
            color=0x00FF00
        )
        
        await ctx.send(embed=embed)
        print(f"✅ Bot commands channel set to: {channel.name} ({channel.id})")

async def setup(bot):
    await bot.add_cog(CommandRestriction(bot))
