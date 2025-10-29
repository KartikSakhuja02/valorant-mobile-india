import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services import db

async def test_connection():
    try:
        # Try to get player stats
        discord_id = int(input("Enter your Discord ID to test: "))
        
        # Test player retrieval
        player = await db.get_player(discord_id)
        print("\nPlayer data:", player)
        
        if player:
            # Test stats retrieval
            stats = await db.get_player_stats(discord_id)
            print("\nPlayer stats:", stats)
        else:
            print("\nNo player found with that Discord ID")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await db.close_pool()

if __name__ == "__main__":
    asyncio.run(test_connection())