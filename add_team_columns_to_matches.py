"""
Migration script to add team_a_id and team_b_id columns to matches table
"""
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

async def migrate():
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
        print("Adding team columns to matches table...")
        
        # Add team_a_id and team_b_id columns to matches table
        await conn.execute("""
            ALTER TABLE matches 
            ADD COLUMN IF NOT EXISTS team_a_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS team_b_id INTEGER REFERENCES teams(id) ON DELETE SET NULL
        """)
        
        print("✅ Successfully added team_a_id and team_b_id columns to matches table")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
