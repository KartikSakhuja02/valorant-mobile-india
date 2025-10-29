"""
Create scrim tables in PostgreSQL database
Run this script to set up the tables for the Looking for Scrim (LFS) system
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

async def create_tables():
    """Create all scrim-related tables"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Create scrim_requests table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scrim_requests (
                id SERIAL PRIMARY KEY,
                captain_discord_id BIGINT NOT NULL,
                team_id INTEGER,
                region VARCHAR(20) NOT NULL,
                match_type VARCHAR(10) NOT NULL,
                time_slot VARCHAR(100) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                CONSTRAINT fk_team FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL,
                CONSTRAINT check_region CHECK (region IN ('apac', 'emea', 'americas', 'india')),
                CONSTRAINT check_match_type CHECK (match_type IN ('bo1', 'bo3', 'bo5')),
                CONSTRAINT check_status CHECK (status IN ('pending', 'matched', 'expired', 'cancelled'))
            )
        """)
        print("✅ Created scrim_requests table")
        
        # Create scrim_matches table to track matched scrims
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS scrim_matches (
                id SERIAL PRIMARY KEY,
                request_id_1 INTEGER NOT NULL,
                request_id_2 INTEGER NOT NULL,
                captain_1_discord_id BIGINT NOT NULL,
                captain_2_discord_id BIGINT NOT NULL,
                team_1_id INTEGER,
                team_2_id INTEGER,
                region VARCHAR(20) NOT NULL,
                match_type VARCHAR(10) NOT NULL,
                time_slot VARCHAR(100) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending_approval',
                captain_1_approved BOOLEAN DEFAULT FALSE,
                captain_2_approved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_request_1 FOREIGN KEY (request_id_1) REFERENCES scrim_requests(id) ON DELETE CASCADE,
                CONSTRAINT fk_request_2 FOREIGN KEY (request_id_2) REFERENCES scrim_requests(id) ON DELETE CASCADE,
                CONSTRAINT fk_team_1 FOREIGN KEY (team_1_id) REFERENCES teams(id) ON DELETE SET NULL,
                CONSTRAINT fk_team_2 FOREIGN KEY (team_2_id) REFERENCES teams(id) ON DELETE SET NULL,
                CONSTRAINT check_match_status CHECK (status IN ('pending_approval', 'approved', 'declined', 'expired'))
            )
        """)
        print("✅ Created scrim_matches table")
        
        # Create indexes for faster lookups
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scrim_requests_region_status 
            ON scrim_requests(region, status)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scrim_requests_captain 
            ON scrim_requests(captain_discord_id)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scrim_matches_status 
            ON scrim_matches(status)
        """)
        
        print("✅ Created indexes")
        
        print("\n🎉 All scrim tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_tables())
