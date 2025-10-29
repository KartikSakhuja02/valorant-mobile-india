"""
Update scrim_matches table to add new status values for chat relay and map banning
Run this script to update the check constraint
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

async def update_status_constraint():
    """Update the status check constraint to include new values"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Drop the old constraint
        await conn.execute("""
            ALTER TABLE scrim_matches 
            DROP CONSTRAINT IF EXISTS check_match_status
        """)
        print("✅ Dropped old check_match_status constraint")
        
        # Add new constraint with additional status values
        await conn.execute("""
            ALTER TABLE scrim_matches 
            ADD CONSTRAINT check_match_status 
            CHECK (status IN ('pending_approval', 'approved', 'declined', 'expired', 'chat_active', 'map_banning', 'completed'))
        """)
        print("✅ Added new check_match_status constraint with chat_active, map_banning, and completed")
        
        print("\n🎉 Status constraint updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating constraint: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(update_status_constraint())
