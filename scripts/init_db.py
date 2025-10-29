import asyncio
import asyncpg
import json
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set in .env file")

async def init_db():
    """Initialize database schema."""
    # Connect to database
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Create tables
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS players (
                discord_id BIGINT PRIMARY KEY,
                ign TEXT NOT NULL,
                player_id INTEGER NOT NULL,
                region TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ign),
                UNIQUE(player_id)
            )
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS player_stats (
                id BIGSERIAL PRIMARY KEY,
                player_id BIGINT REFERENCES players(discord_id),
                tournament_id INTEGER NOT NULL,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                matches_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                mvps INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_id, tournament_id)
            )
        ''')

        # Create indexes for performance
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_players_ign_lower ON players (LOWER(ign))')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_player_stats_score ON player_stats (player_id, tournament_id)')

        # Migrate existing data from JSON files
        data_dir = Path(__file__).parent / 'data'
        players_file = data_dir / 'players.json'
        if players_file.exists():
            with open(players_file, 'r', encoding='utf-8') as f:
                players = json.load(f)
                
                # Migrate each player
                for player in players:
                    try:
                        # Insert player
                        await conn.execute('''
                            INSERT INTO players (discord_id, ign, player_id, region)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (discord_id) DO UPDATE 
                            SET ign = $2, player_id = $3, region = $4
                        ''', 
                            player['discord_id'],
                            player['ign'],
                            player['id'],
                            player['region']
                        )
                        
                        # Get season 1 stats
                        stats = player.get('stats', {}).get('1', {})
                        
                        # Insert stats
                        await conn.execute('''
                            INSERT INTO player_stats (
                                player_id,
                                tournament_id,
                                kills,
                                deaths,
                                assists,
                                matches_played,
                                wins,
                                losses,
                                mvps
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                            ON CONFLICT (player_id, tournament_id) DO UPDATE
                            SET
                                kills = $3,
                                deaths = $4,
                                assists = $5,
                                matches_played = $6,
                                wins = $7,
                                losses = $8,
                                mvps = $9
                        ''',
                            player['discord_id'],
                            1,  # tournament_id
                            stats.get('kills', 0),
                            stats.get('deaths', 0),
                            stats.get('assists', 0),
                            stats.get('matches_played', 0),
                            stats.get('wins', 0),
                            stats.get('losses', 0),
                            stats.get('mvps', 0)
                        )
                        
                        print(f"Migrated player {player['ign']}")
                    
                    except Exception as e:
                        print(f"Error migrating player {player.get('ign', 'unknown')}: {e}")

        print("Database initialization complete")

    except Exception as e:
        print(f"Error during database initialization: {e}")
        raise
    
    finally:
        await conn.close()

async def main():
    await init_db()

if __name__ == "__main__":
    asyncio.run(main())