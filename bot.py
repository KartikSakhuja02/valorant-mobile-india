import discord
import json
import os
from discord.ext import commands
from pathlib import Path

# Prefer environment variables for secrets/config. If python-dotenv is installed
# and a .env file exists, load it. This is optional and fails silently.
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except Exception:
    pass

# Helper to get config values (env preferred, fallback to config.json if present)
_CONFIG_JSON = None
def _load_config_json():
    global _CONFIG_JSON
    if _CONFIG_JSON is not None:
        return _CONFIG_JSON
    try:
        path = Path(__file__).parent / 'config.json'
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                _CONFIG_JSON = json.load(f)
                return _CONFIG_JSON
    except Exception:
        _CONFIG_JSON = {}
    _CONFIG_JSON = {}
    return _CONFIG_JSON

def cfg(key, default=None):
    # environment variable names use upper case
    val = os.environ.get(key)
    if val is not None:
        return val
    # try config.json fallback
    return _load_config_json().get(key, default)

# Bot setup
# Enable necessary intents for message content and guilds
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content in channels
intents.guilds = True  # Required for guild/channel access
bot = commands.Bot(command_prefix='!', intents=intents)

async def log_to_channel(message):
    channel_id = cfg('LOG_CHANNEL_ID') or cfg('log_channel_id')
    if channel_id:  # Only try to send if we have a non-null channel ID
        try:
            channel = await bot.fetch_channel(int(channel_id))
            await channel.send(message)
        except discord.NotFound:
            print("Log channel not found. Please check the channel ID in config.json.")
        except discord.Forbidden:
            print("I don't have permission to send messages in the log channel.")
        except Exception as e:
            print(f"Error sending log message: {e}")
    else:
        # Just print to console if no log channel is configured
        print(f"Log: {message}")

import asyncio

# Load cogs at startup (before bot.run)
async def load_cogs():
    """Load all cogs from the cogs directory"""
    cog_load_tasks = []
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            cog_load_tasks.append(bot.load_extension(f'cogs.{filename[:-3]}'))
    
    # Wait for all cogs to load
    if cog_load_tasks:
        results = await asyncio.gather(*cog_load_tasks, return_exceptions=True)
        loaded_count = sum(1 for r in results if not isinstance(r, Exception))
        print(f'Loaded {loaded_count} cogs')
        
        # Only log errors
        for filename, result in zip(os.listdir('./cogs'), results):
            if isinstance(result, Exception):
                print(f'Failed to load {filename}: {result}')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('------')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Error syncing slash commands: {e}")

@bot.command()
@commands.is_owner()
async def sync(ctx):
    """Syncs the slash commands with Discord."""
    try:
        synced = await bot.tree.sync()
        log_msg = f"Synced {len(synced)} slash commands successfully."
        await ctx.send(log_msg)
        await log_to_channel(log_msg)
    except Exception as e:
        log_msg = f"Error syncing slash commands: {e}"
        await ctx.send(log_msg)
        await log_to_channel(log_msg)

@bot.command()
@commands.is_owner()
async def load(ctx, extension):
    """Loads a cog."""
    try:
        await bot.load_extension(f'cogs.{extension}')
        log_msg = f'Loaded cog: {extension}'
        await ctx.send(log_msg)
        await log_to_channel(log_msg)
    except Exception as e:
        log_msg = f'Failed to load cog {extension}: {e}'
        await ctx.send(log_msg)
        await log_to_channel(log_msg)

@bot.command()
@commands.is_owner()
async def unload(ctx, extension):
    """Unloads a cog."""
    try:
        await bot.unload_extension(f'cogs.{extension}')
        log_msg = f'Unloaded cog: {extension}'
        await ctx.send(log_msg)
        await log_to_channel(log_msg)
    except Exception as e:
        log_msg = f'Failed to unload cog {extension}: {e}'
        await ctx.send(log_msg)
        await log_to_channel(log_msg)

@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    """Reloads a cog."""
    try:
        await bot.reload_extension(f'cogs.{extension}')
        log_msg = f'Reloaded cog: {extension}'
        await ctx.send(log_msg)
        await log_to_channel(log_msg)
    except Exception as e:
        log_msg = f'Failed to reload cog {extension}: {e}'
        await ctx.send(log_msg)
        await log_to_channel(log_msg)

# Run the bot
if __name__ == "__main__":
    try:
        token = cfg('TOKEN') or cfg('token')
        if not token:
            print("Bot token not found. Please set TOKEN in your environment or .env file.")
            raise SystemExit(1)
        
        # Load cogs before running the bot
        async def main():
            async with bot:
                # Register persistent views BEFORE loading cogs
                from cogs.registration import RegistrationView
                from cogs.registration_helpdesk import HelpdeskView
                bot.add_view(RegistrationView())
                bot.add_view(HelpdeskView())
                print("✅ Registered persistent views")
                
                await load_cogs()
                await bot.start(token)
        
        # Use asyncio.run with proper exception handling
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("Bot stopped by user")
        except Exception as e:
            print(f"Error running bot: {e}")
            import traceback
            traceback.print_exc()
        
    except discord.LoginFailure as e:
        print(f"Login failed: {e}. Please check your token in environment variables.")
    except Exception as e:
        print(f"An error occurred: {e}")
