"""
Add wins and losses columns to teams table
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
        print("Adding wins and losses columns to teams table...")
        
        # Add wins and losses columns
        await conn.execute("""
            ALTER TABLE teams 
            ADD COLUMN IF NOT EXISTS wins INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS losses INTEGER DEFAULT 0
        """)
        
        print("✅ Successfully added wins and losses columns to teams table")
        
        # Verify columns
        columns = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'teams'
            ORDER BY ordinal_position
        """)
        
        print("\n📋 Current teams table columns:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_columns())
