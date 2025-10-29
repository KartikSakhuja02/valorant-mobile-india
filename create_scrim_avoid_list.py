"""
Create scrim_avoid_list table to track captains who shouldn't be matched together
Run this script to create the table
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv('DATABASE_URL')

async def create_avoid_list_table():
    """Create scrim_avoid_list table"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Create scrim_avoid_list table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scrim_avoid_list (
                id SERIAL PRIMARY KEY,
                captain_1_discord_id BIGINT NOT NULL,
                captain_2_discord_id BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)
        print("✅ Created scrim_avoid_list table")
        
        # Create index for faster lookups
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scrim_avoid_captains 
            ON scrim_avoid_list(captain_1_discord_id, captain_2_discord_id, expires_at)
        """)
        print("✅ Created index on scrim_avoid_list")
        
        print("\n🎉 Scrim avoid list table created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_avoid_list_table())
