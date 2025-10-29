"""
Add missing columns to team_stats table
"""
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

async def add_columns():
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
        print("Adding missing columns to team_stats table...")
        
        # Add missing columns
        await conn.execute("""
            ALTER TABLE team_stats 
            ADD COLUMN IF NOT EXISTS total_matches INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS total_wins INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS total_losses INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS win_rate DECIMAL(5,2) DEFAULT 0.00,
            ADD COLUMN IF NOT EXISTS last_match_id INTEGER REFERENCES matches(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS recent_matches JSONB DEFAULT '[]'::jsonb
        """)
        
        print("✅ Successfully added missing columns to team_stats table")
        
        # Verify columns
        columns = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'team_stats'
            ORDER BY ordinal_position
        """)
        
        print("\n📋 Current team_stats columns:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_columns())
