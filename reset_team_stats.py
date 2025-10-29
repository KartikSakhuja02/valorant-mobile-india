"""
Clear all team stats (resets recent matches, wins, losses, etc.)
"""
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

async def reset_team_stats():
    # Load .env file
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL must be set in .env file")
    
    # Connect to database
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("Resetting all team stats...")
        
        # Option 1: Delete all team_stats records
        result = await conn.execute("DELETE FROM team_stats")
        print(f"✅ Cleared all team_stats records: {result}")
        
        # Option 2: Also reset wins/losses in teams table (optional)
        reset_teams = input("\nDo you also want to reset wins/losses in teams table? (yes/no): ").strip().lower()
        if reset_teams == 'yes':
            await conn.execute("""
                UPDATE teams 
                SET wins = 0, losses = 0
            """)
            print("✅ Reset all team wins and losses to 0")
        
        print("\n✅ Team stats reset complete!")
        
    except Exception as e:
        print(f"❌ Error during reset: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(reset_team_stats())
