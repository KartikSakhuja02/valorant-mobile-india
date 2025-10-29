"""
Create leaderboard tables for different regions
"""
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

async def create_leaderboard_tables():
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
        print("Creating leaderboard tables...\n")
        
        # Create main leaderboard table (for all regions)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard_global (
                id SERIAL PRIMARY KEY,
                player_id BIGINT REFERENCES players(discord_id) ON DELETE CASCADE,
                ign TEXT NOT NULL,
                region TEXT NOT NULL,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                matches_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                mvps INTEGER DEFAULT 0,
                points DECIMAL(10,2) DEFAULT 0.00,
                rank INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_id)
            )
        """)
        print("✅ Created leaderboard_global table")
        
        # Create APAC leaderboard (AP, KR, JP combined)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard_apac (
                id SERIAL PRIMARY KEY,
                player_id BIGINT REFERENCES players(discord_id) ON DELETE CASCADE,
                ign TEXT NOT NULL,
                region TEXT NOT NULL,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                matches_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                mvps INTEGER DEFAULT 0,
                points DECIMAL(10,2) DEFAULT 0.00,
                rank INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_id)
            )
        """)
        print("✅ Created leaderboard_apac table (AP, KR, JP)")
        
        # Create EMEA leaderboard (EU combined)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard_emea (
                id SERIAL PRIMARY KEY,
                player_id BIGINT REFERENCES players(discord_id) ON DELETE CASCADE,
                ign TEXT NOT NULL,
                region TEXT NOT NULL,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                matches_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                mvps INTEGER DEFAULT 0,
                points DECIMAL(10,2) DEFAULT 0.00,
                rank INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_id)
            )
        """)
        print("✅ Created leaderboard_emea table (EU)")
        
        # Create Americas leaderboard (NA, BR, LATAM combined)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard_americas (
                id SERIAL PRIMARY KEY,
                player_id BIGINT REFERENCES players(discord_id) ON DELETE CASCADE,
                ign TEXT NOT NULL,
                region TEXT NOT NULL,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                matches_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                mvps INTEGER DEFAULT 0,
                points DECIMAL(10,2) DEFAULT 0.00,
                rank INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_id)
            )
        """)
        print("✅ Created leaderboard_americas table (NA, BR, LATAM)")
        
        # Create India leaderboard (role-based)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard_india (
                id SERIAL PRIMARY KEY,
                player_id BIGINT REFERENCES players(discord_id) ON DELETE CASCADE,
                ign TEXT NOT NULL,
                region TEXT NOT NULL,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                matches_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                mvps INTEGER DEFAULT 0,
                points DECIMAL(10,2) DEFAULT 0.00,
                rank INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_id)
            )
        """)
        print("✅ Created leaderboard_india table (role-based)")
        
        # Create indexes for better query performance
        print("\nCreating indexes...")
        
        tables = ['global', 'apac', 'emea', 'americas', 'india']
        for table in tables:
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_leaderboard_{table}_rank 
                ON leaderboard_{table}(rank);
            """)
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_leaderboard_{table}_points 
                ON leaderboard_{table}(points DESC);
            """)
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_leaderboard_{table}_region 
                ON leaderboard_{table}(region);
            """)
            print(f"✅ Created indexes for leaderboard_{table}")
        
        # Create trigger to auto-update timestamp
        await conn.execute("""
            CREATE OR REPLACE FUNCTION update_leaderboard_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.last_updated = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        print("\n✅ Created timestamp update function")
        
        # Add triggers to all leaderboard tables
        for table in tables:
            await conn.execute(f"""
                DROP TRIGGER IF EXISTS leaderboard_{table}_updated_at ON leaderboard_{table};
                
                CREATE TRIGGER leaderboard_{table}_updated_at
                BEFORE UPDATE ON leaderboard_{table}
                FOR EACH ROW
                EXECUTE FUNCTION update_leaderboard_timestamp();
            """)
            print(f"✅ Added auto-update trigger to leaderboard_{table}")
        
        print("\n" + "="*60)
        print("✅ All leaderboard tables created successfully!")
        print("="*60)
        print("\n📋 Region Mapping:")
        print("  • Global: All players")
        print("  • APAC: AP, KR, JP")
        print("  • EMEA: EU")
        print("  • Americas: NA, BR, LATAM")
        print("  • India: Role-based (any region)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_leaderboard_tables())
