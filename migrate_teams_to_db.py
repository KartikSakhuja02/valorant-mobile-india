"""
Migration script to add teams tables to PostgreSQL database
Run this once to create the teams tables
"""
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set in .env file")

async def migrate():
    """Apply teams table migration"""
    print("🔄 Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("📊 Creating teams tables...")
        
        # Create teams table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                tag TEXT NOT NULL UNIQUE,
                captain_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
                region TEXT NOT NULL,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                logo_url TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✅ Created teams table")
        
        # Create indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_teams_name_lower ON teams (LOWER(name))
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_teams_tag_lower ON teams (LOWER(tag))
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_teams_captain ON teams (captain_id)
        """)
        print("  ✅ Created teams indexes")
        
        # Create team_members junction table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                id SERIAL PRIMARY KEY,
                team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                player_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
                joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team_id, player_id)
            )
        """)
        print("  ✅ Created team_members table")
        
        # Create indexes for team_members
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_team_members_player ON team_members (player_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members (team_id)
        """)
        print("  ✅ Created team_members indexes")
        
        # Add trigger for teams table
        await conn.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        """)
        
        await conn.execute("""
            DROP TRIGGER IF EXISTS update_teams_updated_at ON teams
        """)
        await conn.execute("""
            CREATE TRIGGER update_teams_updated_at
                BEFORE UPDATE ON teams
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column()
        """)
        print("  ✅ Created teams trigger")
        
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("  1. Update your code to use the new database functions")
        print("  2. Optionally migrate existing teams.json data")
        print("  3. Restart your bot\n")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
