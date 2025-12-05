"""
Migration: Create team_staff table for storing team managers and coaches
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
    """Create team_staff table and migrate existing data if needed."""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("🔄 Creating team_staff table...")
        
        # Create team_staff table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS team_staff (
                id BIGSERIAL PRIMARY KEY,
                team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
                coach_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
                manager_1_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
                manager_2_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team_id)
            );
        """)
        
        print("✅ team_staff table created!")
        
        # Create indexes for faster lookups
        print("🔄 Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_team_staff_team ON team_staff(team_id);
            CREATE INDEX IF NOT EXISTS idx_team_staff_coach ON team_staff(coach_id);
            CREATE INDEX IF NOT EXISTS idx_team_staff_manager1 ON team_staff(manager_1_id);
            CREATE INDEX IF NOT EXISTS idx_team_staff_manager2 ON team_staff(manager_2_id);
        """)
        
        print("✅ Indexes created!")
        
        # Check if teams table has old columns
        print("🔄 Checking for old columns in teams table...")
        has_old_columns = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'teams' 
                AND column_name IN ('manager_1_id', 'manager_2_id', 'coach_id')
            )
        """)
        
        if has_old_columns:
            print("🔄 Migrating data from teams table...")
            # Migrate existing data
            migrated = await conn.execute("""
                INSERT INTO team_staff (team_id, coach_id, manager_1_id, manager_2_id, created_at, updated_at)
                SELECT id, coach_id, manager_1_id, manager_2_id, created_at, updated_at
                FROM teams
                WHERE coach_id IS NOT NULL OR manager_1_id IS NOT NULL OR manager_2_id IS NOT NULL
                ON CONFLICT (team_id) DO NOTHING
            """)
            print(f"✅ Migrated data: {migrated}")
            
            # Drop old columns
            print("🔄 Removing old columns from teams table...")
            await conn.execute("""
                ALTER TABLE teams DROP COLUMN IF EXISTS manager_1_id;
                ALTER TABLE teams DROP COLUMN IF EXISTS manager_2_id;
                ALTER TABLE teams DROP COLUMN IF EXISTS coach_id;
            """)
            print("✅ Old columns removed!")
        else:
            print("ℹ️ No old columns found in teams table")
        
        # Add trigger for updating timestamps
        print("🔄 Adding update trigger...")
        await conn.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
            
            DROP TRIGGER IF EXISTS update_team_staff_updated_at ON team_staff;
            
            CREATE TRIGGER update_team_staff_updated_at
                BEFORE UPDATE ON team_staff
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)
        
        print("✅ Trigger added!")
        
        # Verify table
        count = await conn.fetchval("SELECT COUNT(*) FROM team_staff")
        print(f"\n📊 team_staff table has {count} row(s)")
        
        # Show structure
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'team_staff'
            ORDER BY ordinal_position
        """)
        print("\n📋 Table structure:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']}")
        
        print("\n🎉 Migration complete! You can now use /team-profile command.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
