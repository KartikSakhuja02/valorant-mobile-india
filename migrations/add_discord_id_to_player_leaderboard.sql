-- Add discord_id and team_id columns to player_leaderboard if they don't exist
-- This migration fixes the "column discord_id does not exist" and "column team_id does not exist" errors

-- Add discord_id column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'player_leaderboard' 
        AND column_name = 'discord_id'
    ) THEN
        -- Add the discord_id column
        ALTER TABLE player_leaderboard ADD COLUMN discord_id BIGINT;
        
        -- Copy player_id values to discord_id (they should be the same)
        UPDATE player_leaderboard SET discord_id = player_id;
        
        -- Make it NOT NULL after populating
        ALTER TABLE player_leaderboard ALTER COLUMN discord_id SET NOT NULL;
        
        -- Add index for faster lookups
        CREATE INDEX idx_player_leaderboard_discord_id ON player_leaderboard(discord_id);
        
        RAISE NOTICE 'Added discord_id column to player_leaderboard';
    ELSE
        RAISE NOTICE 'discord_id column already exists in player_leaderboard';
    END IF;
END $$;

-- Add team_id column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'player_leaderboard' 
        AND column_name = 'team_id'
    ) THEN
        -- Add the team_id column (nullable since not all players are on teams)
        ALTER TABLE player_leaderboard ADD COLUMN team_id BIGINT;
        
        -- Add foreign key constraint
        ALTER TABLE player_leaderboard 
        ADD CONSTRAINT fk_player_leaderboard_team 
        FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL;
        
        -- Add index for faster lookups
        CREATE INDEX idx_player_leaderboard_team_id ON player_leaderboard(team_id);
        
        RAISE NOTICE 'Added team_id column to player_leaderboard';
    ELSE
        RAISE NOTICE 'team_id column already exists in player_leaderboard';
    END IF;
END $$;

-- Add updated_at column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'player_leaderboard' 
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE player_leaderboard ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'Added updated_at column to player_leaderboard';
    ELSE
        RAISE NOTICE 'updated_at column already exists in player_leaderboard';
    END IF;
END $$;
