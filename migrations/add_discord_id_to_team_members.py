"""
Migration: Add discord_id column to team_members table
This allows proper tracking of team member Discord IDs
"""

import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

async def migrate():
    """Add discord_id column to team_members table if it doesn't exist."""
    
    # Get database connection details
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'valorant_tournament')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    print(f"Connecting to database: {db_name} at {db_host}:{db_port}")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        print("✓ Connected to database")
        
        # Check if column already exists
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'team_members' 
            AND column_name = 'discord_id';
        """
        
        result = await conn.fetchval(check_query)
        
        if result:
            print("✓ Column 'discord_id' already exists in team_members table")
        else:
            print("Adding 'discord_id' column to team_members table...")
            
            # Add the discord_id column
            alter_query = """
                ALTER TABLE team_members 
                ADD COLUMN IF NOT EXISTS discord_id BIGINT;
            """
            
            await conn.execute(alter_query)
            print("✓ Added discord_id column")
            
            # Migrate existing data from player_id to discord_id
            print("Migrating existing player_id data to discord_id...")
            
            migrate_data_query = """
                UPDATE team_members 
                SET discord_id = player_id 
                WHERE discord_id IS NULL AND player_id IS NOT NULL;
            """
            
            result = await conn.execute(migrate_data_query)
            print(f"✓ Migrated data: {result}")
            
            # Optional: Add index for better performance
            print("Adding index on discord_id...")
            
            index_query = """
                CREATE INDEX IF NOT EXISTS idx_team_members_discord_id 
                ON team_members(discord_id);
            """
            
            await conn.execute(index_query)
            print("✓ Added index on discord_id")
        
        # Close connection
        await conn.close()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(migrate())
    exit(0 if success else 1)
