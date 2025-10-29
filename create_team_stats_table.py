"""
Create team_stats table to store aggregated team statistics
"""
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

async def create_table():
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
        print("Creating team_stats table...")
        
        # Create team_stats table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS team_stats (
                team_id INTEGER PRIMARY KEY REFERENCES teams(id) ON DELETE CASCADE,
                total_matches INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                total_losses INTEGER DEFAULT 0,
                win_rate DECIMAL(5,2) DEFAULT 0.00,
                last_match_id INTEGER REFERENCES matches(id) ON DELETE SET NULL,
                recent_matches JSONB DEFAULT '[]'::jsonb,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("✅ Successfully created team_stats table")
        
        # Create trigger to auto-update updated_at
        await conn.execute("""
            CREATE OR REPLACE FUNCTION update_team_stats_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            DROP TRIGGER IF EXISTS team_stats_updated_at ON team_stats;
            
            CREATE TRIGGER team_stats_updated_at
            BEFORE UPDATE ON team_stats
            FOR EACH ROW
            EXECUTE FUNCTION update_team_stats_timestamp();
        """)
        
        print("✅ Successfully created auto-update trigger")
        
    except Exception as e:
        print(f"❌ Error during table creation: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_table())
