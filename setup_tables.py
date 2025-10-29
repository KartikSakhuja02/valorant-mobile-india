import asyncio
from services.db import get_pool, close_pool

async def setup_tables():
    """Create all required database tables if they don't exist."""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        # Create matches table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                map_name VARCHAR(50),
                team1_score INTEGER,
                team2_score INTEGER,
                tournament_id INTEGER DEFAULT 1
            )
        """)

        # Create match_players table for individual performances
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS match_players (
                id SERIAL PRIMARY KEY,
                match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
                player_id BIGINT REFERENCES players(discord_id) ON DELETE CASCADE,
                agent VARCHAR(50),
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                score INTEGER DEFAULT 0,
                mvp BOOLEAN DEFAULT false,
                team INTEGER CHECK (team IN (1, 2)), -- 1 for Team A, 2 for Team B
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for faster lookups
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_match_players_match ON match_players(match_id);
            CREATE INDEX IF NOT EXISTS idx_match_players_player ON match_players(player_id);
            CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(created_at DESC);
        """)

async def main():
    """Main entry point for database setup."""
    try:
        await setup_tables()
        print("✅ Successfully created/updated database tables!")
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
    finally:
        await close_pool()

if __name__ == "__main__":
    asyncio.run(main())
