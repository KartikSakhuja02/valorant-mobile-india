import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def create_team_leaderboard_tables():
    """Create regional team leaderboard tables"""
    
    # Database connection using DATABASE_URL
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL must be set in .env file")
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Drop old player leaderboard tables
        print("🗑️ Dropping old player leaderboard tables...")
        await conn.execute("DROP TABLE IF EXISTS leaderboard_global CASCADE")
        await conn.execute("DROP TABLE IF EXISTS leaderboard_apac CASCADE")
        await conn.execute("DROP TABLE IF EXISTS leaderboard_emea CASCADE")
        await conn.execute("DROP TABLE IF EXISTS leaderboard_americas CASCADE")
        await conn.execute("DROP TABLE IF EXISTS leaderboard_india CASCADE")
        print("✅ Old tables dropped")
        
        # Define team leaderboard regions
        regions = ['global', 'apac', 'emea', 'americas', 'india']
        
        for region in regions:
            table_name = f'team_leaderboard_{region}'
            
            print(f"\n📊 Creating {table_name}...")
            
            # Create team leaderboard table
            create_table_query = f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                team_id BIGINT PRIMARY KEY REFERENCES teams(id) ON DELETE CASCADE,
                team_name VARCHAR(100) NOT NULL,
                team_tag VARCHAR(10) NOT NULL,
                region VARCHAR(50) NOT NULL,
                total_matches INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                win_rate DECIMAL(5,2) DEFAULT 0.00,
                total_rounds_won INTEGER DEFAULT 0,
                total_rounds_lost INTEGER DEFAULT 0,
                round_diff INTEGER DEFAULT 0,
                points DECIMAL(10,2) DEFAULT 0.00,
                rank INTEGER DEFAULT 0,
                logo_url TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            '''
            
            await conn.execute(create_table_query)
            print(f"✅ Table {table_name} created")
            
            # Create indexes for performance
            print(f"📇 Creating indexes for {table_name}...")
            
            await conn.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_{table_name}_rank 
                ON {table_name}(rank);
            ''')
            
            await conn.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_{table_name}_points 
                ON {table_name}(points DESC);
            ''')
            
            await conn.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_{table_name}_region 
                ON {table_name}(region);
            ''')
            
            await conn.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_{table_name}_win_rate 
                ON {table_name}(win_rate DESC);
            ''')
            
            print(f"✅ Indexes created for {table_name}")
            
            # Create trigger for auto-updating timestamp
            print(f"⚡ Creating auto-update trigger for {table_name}...")
            
            await conn.execute(f'''
                CREATE OR REPLACE FUNCTION update_{table_name}_timestamp()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.last_updated = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            ''')
            
            await conn.execute(f'''
                DROP TRIGGER IF EXISTS trigger_update_{table_name}_timestamp 
                ON {table_name};
            ''')
            
            await conn.execute(f'''
                CREATE TRIGGER trigger_update_{table_name}_timestamp
                BEFORE UPDATE ON {table_name}
                FOR EACH ROW
                EXECUTE FUNCTION update_{table_name}_timestamp();
            ''')
            
            print(f"✅ Auto-update trigger created for {table_name}")
        
        print("\n" + "="*60)
        print("✅ All team leaderboard tables created successfully!")
        print("="*60)
        print("\nCreated tables:")
        for region in regions:
            print(f"  - team_leaderboard_{region}")
        
        print("\nRegion Mapping:")
        print("  - APAC: AP, KR, JP")
        print("  - EMEA: EU")
        print("  - Americas: NA, BR, LATAM")
        print("  - India: Teams with 'India' region or role-based")
        print("  - Global: All teams")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_team_leaderboard_tables())
