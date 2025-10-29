"""
Quick bot startup test - loads bot and checks for errors
"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test_bot():
    """Test bot initialization."""
    try:
        print("Testing imports...")
        import discord
        from discord.ext import commands
        import services.db as db
        print("✅ Imports successful")
        
        print("\nTesting database connection...")
        pool = await db.get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM teams")
            print(f"✅ Database connection successful ({result} teams in database)")
        
        print("\nTesting team staff functions...")
        # Test get_team_staff with a non-existent team (should return empty dict)
        staff = await db.get_team_staff(999999)
        print(f"✅ get_team_staff works (empty result: {staff == {}})")
        
        print("\nChecking cog files...")
        import os
        cog_files = [f for f in os.listdir('cogs') if f.endswith('.py') and not f.startswith('_')]
        print(f"✅ Found {len(cog_files)} cog files")
        
        # Check if team_staff.py exists
        if 'team_staff.py' in cog_files:
            print("✅ team_staff.py cog found")
        else:
            print("❌ team_staff.py cog NOT found")
        
        print("\n✅ All tests passed!")
        await db.close_pool()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_bot())
    sys.exit(0 if result else 1)
