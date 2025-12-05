-- ============================================
-- Migration: Create team_staff table
-- This creates a separate table for team managers and coaches
-- Run this on your remote PostgreSQL database
-- ============================================

-- Step 1: Create team_staff table
CREATE TABLE IF NOT EXISTS team_staff (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    coach_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
    manager_1_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
    manager_2_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id)
);

-- Step 2: Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_team_staff_team ON team_staff(team_id);
CREATE INDEX IF NOT EXISTS idx_team_staff_coach ON team_staff(coach_id);
CREATE INDEX IF NOT EXISTS idx_team_staff_manager1 ON team_staff(manager_1_id);
CREATE INDEX IF NOT EXISTS idx_team_staff_manager2 ON team_staff(manager_2_id);

-- Step 3: Migrate existing data from teams table (if columns exist)
DO $$
BEGIN
    -- Check if the old columns exist in teams table
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'teams' 
        AND column_name IN ('manager_1_id', 'manager_2_id', 'coach_id')
    ) THEN
        -- Migrate data to new table
        INSERT INTO team_staff (team_id, coach_id, manager_1_id, manager_2_id, created_at, updated_at)
        SELECT id, coach_id, manager_1_id, manager_2_id, created_at, updated_at
        FROM teams
        WHERE coach_id IS NOT NULL OR manager_1_id IS NOT NULL OR manager_2_id IS NOT NULL
        ON CONFLICT (team_id) DO NOTHING;
        
        RAISE NOTICE 'Data migrated from teams table to team_staff';
        
        -- Drop old columns from teams table
        ALTER TABLE teams DROP COLUMN IF EXISTS manager_1_id;
        ALTER TABLE teams DROP COLUMN IF EXISTS manager_2_id;
        ALTER TABLE teams DROP COLUMN IF EXISTS coach_id;
        
        RAISE NOTICE 'Old columns removed from teams table';
    ELSE
        RAISE NOTICE 'No old columns found in teams table - skipping migration';
    END IF;
END $$;

-- Step 4: Create or replace the update trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Step 5: Add trigger to team_staff table
DROP TRIGGER IF EXISTS update_team_staff_updated_at ON team_staff;

CREATE TRIGGER update_team_staff_updated_at
    BEFORE UPDATE ON team_staff
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Step 6: Verify the migration
DO $$
DECLARE
    row_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO row_count FROM team_staff;
    RAISE NOTICE 'team_staff table has % row(s)', row_count;
END $$;

-- Done!
-- The team_staff table is now ready to use
