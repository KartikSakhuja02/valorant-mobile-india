import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def create_player_leaderboard_table():
    """Create global player leaderboard table"""
    
    # Database connection using DATABASE_URL
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL must be set in .env file")
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("📊 Creating player_leaderboard table...")
        
        # Create player leaderboard table
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS player_leaderboard (
            player_id BIGINT PRIMARY KEY REFERENCES players(discord_id) ON DELETE CASCADE,
            ign VARCHAR(100) NOT NULL,
            region VARCHAR(50) NOT NULL,
            kills INTEGER DEFAULT 0,
            deaths INTEGER DEFAULT 0,
            assists INTEGER DEFAULT 0,
            matches_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            mvps INTEGER DEFAULT 0,
            points DECIMAL(10,2) DEFAULT 0.00,
            rank INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        
        await conn.execute(create_table_query)
        print("✅ Table player_leaderboard created")
        
        # Create indexes for performance
        print("📇 Creating indexes for player_leaderboard...")
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_player_leaderboard_rank 
            ON player_leaderboard(rank);
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_player_leaderboard_points 
            ON player_leaderboard(points DESC);
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_player_leaderboard_region 
            ON player_leaderboard(region);
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_player_leaderboard_kills 
            ON player_leaderboard(kills DESC);
        ''')
        
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_player_leaderboard_wins 
            ON player_leaderboard(wins DESC);
        ''')
        
        print("✅ Indexes created for player_leaderboard")
        
        # Create trigger for auto-updating timestamp
        print("⚡ Creating auto-update trigger for player_leaderboard...")
        
        await conn.execute('''
            CREATE OR REPLACE FUNCTION update_player_leaderboard_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.last_updated = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        ''')
        
        await conn.execute('''
            DROP TRIGGER IF EXISTS trigger_update_player_leaderboard_timestamp 
            ON player_leaderboard;
        ''')
        
        await conn.execute('''
            CREATE TRIGGER trigger_update_player_leaderboard_timestamp
            BEFORE UPDATE ON player_leaderboard
            FOR EACH ROW
            EXECUTE FUNCTION update_player_leaderboard_timestamp();
        ''')
        
        print("✅ Auto-update trigger created for player_leaderboard")
        
        print("\n" + "="*60)
        print("✅ Player leaderboard table created successfully!")
        print("="*60)
        print("\nCreated table:")
        print("  - player_leaderboard (global rankings)")
        print("\nIndexes:")
        print("  - rank, points DESC, region, kills DESC, wins DESC")
        print("\nScoring Formula:")
        print("  - Base: kills×2 + assists×1 - deaths×0.5 + wins×10 + matches×1")
        print("  - K/D Multiplier: ≥2.0 (×1.2), ≥1.5 (×1.1)")
        print("  - Win Rate Multiplier: ≥75% (×1.15), ≥60% (×1.05)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_player_leaderboard_table())
