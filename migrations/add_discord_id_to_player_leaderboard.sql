-- Add discord_id column to player_leaderboard if it doesn't exist
-- This migration fixes the "column discord_id does not exist" error

-- Check if the column exists, if not add it
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
