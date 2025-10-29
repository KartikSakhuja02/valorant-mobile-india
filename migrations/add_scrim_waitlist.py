"""
Add scrim_waitlist table for notify feature
Run this to add the waitlist table to your database
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv('DATABASE_URL')

async def add_waitlist_table():
    """Add scrim_waitlist table"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Update scrim_requests status enum to include 'in_progress'
        await conn.execute("""
            ALTER TABLE scrim_requests
            DROP CONSTRAINT IF EXISTS check_status
        """)
        print("✅ Dropped old status constraint")
        
        await conn.execute("""
            ALTER TABLE scrim_requests
            ADD CONSTRAINT check_status CHECK (status IN ('pending', 'matched', 'expired', 'cancelled', 'in_progress'))
        """)
        print("✅ Updated scrim_requests status constraint to include 'in_progress'")
        
        # Create scrim_waitlist table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scrim_waitlist (
                id SERIAL PRIMARY KEY,
                request_id INTEGER NOT NULL,
                captain_discord_id BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_request FOREIGN KEY (request_id) REFERENCES scrim_requests(id) ON DELETE CASCADE,
                CONSTRAINT unique_waitlist UNIQUE (request_id, captain_discord_id)
            )
        """)
        print("✅ Created scrim_waitlist table")
        
        # Create index for faster lookups
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scrim_waitlist_request 
            ON scrim_waitlist(request_id)
        """)
        print("✅ Created waitlist index")
        
        print("\n🎉 Scrim waitlist table added successfully!")
        
    except Exception as e:
        print(f"❌ Error adding waitlist table: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_waitlist_table())
