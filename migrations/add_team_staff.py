"""
Migration: Add team staff (managers and coach) columns to teams table
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from root directory
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set in .env file")

async def migrate():
    """Add manager and coach columns to teams table."""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("Adding team staff columns...")
        
        # Add manager_1, manager_2, and coach columns
        await conn.execute("""
            ALTER TABLE teams 
            ADD COLUMN IF NOT EXISTS manager_1_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS manager_2_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS coach_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL;
        """)
        
        print("✅ Team staff columns added successfully!")
        
        # Create indexes for faster lookups
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_teams_manager_1 ON teams (manager_1_id);
            CREATE INDEX IF NOT EXISTS idx_teams_manager_2 ON teams (manager_2_id);
            CREATE INDEX IF NOT EXISTS idx_teams_coach ON teams (coach_id);
        """)
        
        print("✅ Indexes created successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
