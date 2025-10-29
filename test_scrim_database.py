"""
Quick test script to verify scrim system is working
Run this after setting up the database tables
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

async def test_database():
    """Test database connection and tables"""
    print("🧪 Testing Scrim System Database...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Check if scrim_requests table exists
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'scrim_requests'
            )
        """)
        
        if result:
            print("✅ scrim_requests table exists")
        else:
            print("❌ scrim_requests table NOT FOUND - run create_scrim_tables.py first!")
            return
        
        # Check if scrim_matches table exists
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'scrim_matches'
            )
        """)
        
        if result:
            print("✅ scrim_matches table exists")
        else:
            print("❌ scrim_matches table NOT FOUND - run create_scrim_tables.py first!")
            return
        
        # Count records
        request_count = await conn.fetchval("SELECT COUNT(*) FROM scrim_requests")
        match_count = await conn.fetchval("SELECT COUNT(*) FROM scrim_matches")
        
        print(f"\n📊 Database Stats:")
        print(f"   • Scrim Requests: {request_count}")
        print(f"   • Scrim Matches: {match_count}")
        
        # Test insert and delete
        print("\n🔬 Testing insert/delete operations...")
        
        test_request = await conn.fetchrow("""
            INSERT INTO scrim_requests 
            (captain_discord_id, team_id, region, match_type, time_slot)
            VALUES (123456789, NULL, 'apac', 'bo3', '7PM IST')
            RETURNING *
        """)
        print(f"✅ Test insert successful: ID {test_request['id']}")
        
        await conn.execute("DELETE FROM scrim_requests WHERE id = $1", test_request['id'])
        print("✅ Test delete successful")
        
        print("\n🎉 All tests passed! Scrim system database is ready!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_database())
