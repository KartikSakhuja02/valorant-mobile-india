"""
Migration: Add timezone column and remove region from scrim_requests
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
    """Add timezone column to scrim_requests table"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("Starting migration: Add timezone to scrim_requests...")
        
        # Add timezone column
        await conn.execute("""
            ALTER TABLE scrim_requests
            ADD COLUMN IF NOT EXISTS timezone VARCHAR(10);
        """)
        print("✅ Added timezone column")
        
        # Migrate existing data (set all to IST as default)
        await conn.execute("""
            UPDATE scrim_requests
            SET timezone = 'IST'
            WHERE timezone IS NULL;
        """)
        print("✅ Migrated existing requests to IST timezone")
        
        # Make region column nullable (remove NOT NULL constraint)
        await conn.execute("""
            ALTER TABLE scrim_requests
            ALTER COLUMN region DROP NOT NULL;
        """)
        print("✅ Removed NOT NULL constraint from region column")
        
        # Set default value for region column for backward compatibility
        await conn.execute("""
            ALTER TABLE scrim_requests
            ALTER COLUMN region SET DEFAULT 'global';
        """)
        print("✅ Set default value for region column")
        
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
