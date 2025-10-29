"""
Check team_stats table structure
"""
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

async def check_table():
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
        print("Checking team_stats table structure...\n")
        
        # Get table columns
        columns = await conn.fetch("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'team_stats'
            ORDER BY ordinal_position
        """)
        
        if columns:
            print("✅ team_stats table exists with columns:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
        else:
            print("❌ team_stats table does not exist!")
            print("\nRun: python create_team_stats_table.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_table())
