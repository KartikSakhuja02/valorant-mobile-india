-- ============================================================================
-- VALM2 Database Setup Script
-- Complete database schema for PostgreSQL on Linux
-- ============================================================================

-- Drop existing tables if they exist (optional - comment out if you want to keep existing data)
-- DROP TABLE IF EXISTS scrim_waitlist CASCADE;
-- DROP TABLE IF EXISTS scrim_avoid_list CASCADE;
-- DROP TABLE IF EXISTS scrim_matches CASCADE;
-- DROP TABLE IF EXISTS scrim_requests CASCADE;
-- DROP TABLE IF EXISTS matches CASCADE;
-- DROP TABLE IF EXISTS agent_usage CASCADE;
-- DROP TABLE IF EXISTS team_stats CASCADE;
-- DROP TABLE IF EXISTS team_staff CASCADE;
-- DROP TABLE IF EXISTS team_members CASCADE;
-- DROP TABLE IF EXISTS teams CASCADE;
-- DROP TABLE IF EXISTS player_stats CASCADE;
-- DROP TABLE IF EXISTS players CASCADE;

-- ============================================================================
-- Core Player Tables
-- ============================================================================

-- Players table
CREATE TABLE IF NOT EXISTS players (
    discord_id BIGINT PRIMARY KEY,
    ign TEXT NOT NULL,
    player_id BIGINT NOT NULL,
    region TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ign),
    UNIQUE(player_id)
);

-- Create index for case-insensitive IGN lookups
CREATE INDEX IF NOT EXISTS idx_players_ign_lower ON players (LOWER(ign));

-- Player statistics table
CREATE TABLE IF NOT EXISTS player_stats (
    id BIGSERIAL PRIMARY KEY,
    discord_id BIGINT REFERENCES players(discord_id) ON DELETE CASCADE,
    tournament_id INTEGER NOT NULL DEFAULT 1,
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    matches_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    mvps INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(discord_id, tournament_id)
);

-- Create index for faster leaderboard queries
CREATE INDEX IF NOT EXISTS idx_player_stats_score ON player_stats (discord_id, tournament_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_kills ON player_stats (kills DESC);

-- Agent usage tracking table
CREATE TABLE IF NOT EXISTS agent_usage (
    id BIGSERIAL PRIMARY KEY,
    discord_id BIGINT REFERENCES players(discord_id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    matches_played INTEGER DEFAULT 0,
    total_kills INTEGER DEFAULT 0,
    total_deaths INTEGER DEFAULT 0,
    total_assists INTEGER DEFAULT 0,
    mvps INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(discord_id, agent_name)
);

-- Create index for agent usage queries
CREATE INDEX IF NOT EXISTS idx_agent_usage_player ON agent_usage (discord_id);
CREATE INDEX IF NOT EXISTS idx_agent_usage_agent ON agent_usage (agent_name);

-- ============================================================================
-- Team Tables
-- ============================================================================

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    tag TEXT NOT NULL UNIQUE,
    captain_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    region TEXT NOT NULL,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    logo_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster team lookups
CREATE INDEX IF NOT EXISTS idx_teams_name_lower ON teams (LOWER(name));
CREATE INDEX IF NOT EXISTS idx_teams_tag_lower ON teams (LOWER(tag));
CREATE INDEX IF NOT EXISTS idx_teams_captain ON teams (captain_id);
CREATE INDEX IF NOT EXISTS idx_teams_region ON teams (region);

-- Team members junction table (many-to-many)
CREATE TABLE IF NOT EXISTS team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    player_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, player_id)
);

-- Create index for faster member lookups
CREATE INDEX IF NOT EXISTS idx_team_members_player ON team_members (player_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members (team_id);

-- Team staff table (managers and coach)
CREATE TABLE IF NOT EXISTS team_staff (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE UNIQUE,
    manager_1_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
    manager_2_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
    coach_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for staff lookups
CREATE INDEX IF NOT EXISTS idx_team_staff_team ON team_staff (team_id);

-- Team statistics table
CREATE TABLE IF NOT EXISTS team_stats (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE UNIQUE,
    total_matches INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_losses INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0.0,
    recent_matches JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for team stats lookups
CREATE INDEX IF NOT EXISTS idx_team_stats_team ON team_stats (team_id);
CREATE INDEX IF NOT EXISTS idx_team_stats_wins ON team_stats (total_wins DESC);

-- ============================================================================
-- Match Tables
-- ============================================================================

-- Matches table (for storing match results)
CREATE TABLE IF NOT EXISTS matches (
    id BIGSERIAL PRIMARY KEY,
    match_type TEXT NOT NULL DEFAULT 'scrim',
    team_a_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    team_b_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    team1_score INTEGER NOT NULL,
    team2_score INTEGER NOT NULL,
    map_name TEXT NOT NULL,
    players JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for match queries
CREATE INDEX IF NOT EXISTS idx_matches_team_a ON matches (team_a_id);
CREATE INDEX IF NOT EXISTS idx_matches_team_b ON matches (team_b_id);
CREATE INDEX IF NOT EXISTS idx_matches_created ON matches (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_matches_players ON matches USING GIN (players);

-- ============================================================================
-- Scrim System Tables
-- ============================================================================

-- Scrim requests table
CREATE TABLE IF NOT EXISTS scrim_requests (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    team_name TEXT NOT NULL,
    captain_discord_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    match_type TEXT NOT NULL,
    region TEXT NOT NULL,
    requested_time TIMESTAMP WITH TIME ZONE NOT NULL,
    requested_timezone TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for scrim request queries
CREATE INDEX IF NOT EXISTS idx_scrim_requests_status ON scrim_requests (status);
CREATE INDEX IF NOT EXISTS idx_scrim_requests_team ON scrim_requests (team_id);
CREATE INDEX IF NOT EXISTS idx_scrim_requests_captain ON scrim_requests (captain_discord_id);
CREATE INDEX IF NOT EXISTS idx_scrim_requests_time ON scrim_requests (requested_time);

-- Scrim matches table (confirmed matches)
CREATE TABLE IF NOT EXISTS scrim_matches (
    id SERIAL PRIMARY KEY,
    request_id_1 INTEGER NOT NULL REFERENCES scrim_requests(id) ON DELETE CASCADE,
    request_id_2 INTEGER NOT NULL REFERENCES scrim_requests(id) ON DELETE CASCADE,
    team_1_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    team_2_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    team_1_name TEXT NOT NULL,
    team_2_name TEXT NOT NULL,
    captain_1_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    captain_2_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    match_type TEXT NOT NULL,
    region TEXT NOT NULL,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    timezone TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending_approval',
    map_ban_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for scrim match queries
CREATE INDEX IF NOT EXISTS idx_scrim_matches_status ON scrim_matches (status);
CREATE INDEX IF NOT EXISTS idx_scrim_matches_captain1 ON scrim_matches (captain_1_id);
CREATE INDEX IF NOT EXISTS idx_scrim_matches_captain2 ON scrim_matches (captain_2_id);
CREATE INDEX IF NOT EXISTS idx_scrim_matches_team1 ON scrim_matches (team_1_id);
CREATE INDEX IF NOT EXISTS idx_scrim_matches_team2 ON scrim_matches (team_2_id);

-- Scrim waitlist table (captains waiting for a specific request)
CREATE TABLE IF NOT EXISTS scrim_waitlist (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES scrim_requests(id) ON DELETE CASCADE,
    captain_discord_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(request_id, captain_discord_id)
);

-- Create indexes for waitlist queries
CREATE INDEX IF NOT EXISTS idx_scrim_waitlist_request ON scrim_waitlist (request_id);
CREATE INDEX IF NOT EXISTS idx_scrim_waitlist_captain ON scrim_waitlist (captain_discord_id);

-- Scrim avoid list table (temporary blocks between captains)
CREATE TABLE IF NOT EXISTS scrim_avoid_list (
    id SERIAL PRIMARY KEY,
    captain_1_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    captain_2_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(captain_1_id, captain_2_id)
);

-- Create indexes for avoid list queries
CREATE INDEX IF NOT EXISTS idx_avoid_list_captain1 ON scrim_avoid_list (captain_1_id);
CREATE INDEX IF NOT EXISTS idx_avoid_list_captain2 ON scrim_avoid_list (captain_2_id);
CREATE INDEX IF NOT EXISTS idx_avoid_list_expires ON scrim_avoid_list (expires_at);

-- ============================================================================
-- Triggers and Functions
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to all tables with updated_at
DROP TRIGGER IF EXISTS update_players_updated_at ON players;
CREATE TRIGGER update_players_updated_at
    BEFORE UPDATE ON players
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_player_stats_updated_at ON player_stats;
CREATE TRIGGER update_player_stats_updated_at
    BEFORE UPDATE ON player_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_agent_usage_updated_at ON agent_usage;
CREATE TRIGGER update_agent_usage_updated_at
    BEFORE UPDATE ON agent_usage
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_teams_updated_at ON teams;
CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_team_staff_updated_at ON team_staff;
CREATE TRIGGER update_team_staff_updated_at
    BEFORE UPDATE ON team_staff
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_team_stats_updated_at ON team_stats;
CREATE TRIGGER update_team_stats_updated_at
    BEFORE UPDATE ON team_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_scrim_requests_updated_at ON scrim_requests;
CREATE TRIGGER update_scrim_requests_updated_at
    BEFORE UPDATE ON scrim_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_scrim_matches_updated_at ON scrim_matches;
CREATE TRIGGER update_scrim_matches_updated_at
    BEFORE UPDATE ON scrim_matches
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Cleanup Function (to remove expired avoid list entries)
-- ============================================================================

CREATE OR REPLACE FUNCTION cleanup_expired_avoid_list()
RETURNS void AS $$
BEGIN
    DELETE FROM scrim_avoid_list
    WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Database Setup Complete
-- ============================================================================

-- Verify tables were created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
