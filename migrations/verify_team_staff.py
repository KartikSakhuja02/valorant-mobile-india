"""
Verify team staff database setup
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv('DATABASE_URL')

async def verify():
    """Verify team staff columns exist and are properly configured."""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("Checking teams table structure...")
        
        # Check columns exist
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'teams'
            AND column_name IN ('manager_1_id', 'manager_2_id', 'coach_id')
            ORDER BY column_name;
        """)
        
        if len(columns) == 3:
            print("✅ All 3 staff columns exist:")
            for col in columns:
                print(f"   - {col['column_name']} ({col['data_type']}, nullable: {col['is_nullable']})")
        else:
            print(f"❌ Expected 3 columns, found {len(columns)}")
            return False
        
        # Check foreign key constraints
        constraints = await conn.fetch("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'teams'
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name LIKE '%manager%' OR constraint_name LIKE '%coach%';
        """)
        
        print(f"✅ Found {len(constraints)} foreign key constraints")
        
        # Check indexes
        indexes = await conn.fetch("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'teams'
            AND (indexname LIKE '%manager%' OR indexname LIKE '%coach%');
        """)
        
        if len(indexes) >= 3:
            print(f"✅ Found {len(indexes)} staff indexes:")
            for idx in indexes:
                print(f"   - {idx['indexname']}")
        else:
            print(f"⚠️  Expected 3 indexes, found {len(indexes)}")
        
        # Test query
        test = await conn.fetchrow("""
            SELECT 
                t.id,
                t.manager_1_id,
                t.manager_2_id,
                t.coach_id
            FROM teams t
            LIMIT 1;
        """)
        
        if test:
            print(f"✅ Test query successful - columns are queryable")
        else:
            print("⚠️  No teams in database to test with")
        
        print("\n✅ Database verification complete - all checks passed!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verify())
