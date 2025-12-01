-- Complete Database Schema Update
-- This script will create/update all tables to match the required schema

-- Drop existing tables in correct order (respecting foreign keys)
DROP TABLE IF EXISTS scrim_waitlist CASCADE;
DROP TABLE IF EXISTS scrim_matches CASCADE;
DROP TABLE IF EXISTS scrim_requests CASCADE;
DROP TABLE IF EXISTS scrim_avoid_list CASCADE;
DROP TABLE IF EXISTS match_players CASCADE;
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS player_leaderboard CASCADE;
DROP TABLE IF EXISTS team_leaderboard_americas CASCADE;
DROP TABLE IF EXISTS team_leaderboard_apac CASCADE;
DROP TABLE IF EXISTS team_leaderboard_emea CASCADE;
DROP TABLE IF EXISTS team_leaderboard_global CASCADE;
DROP TABLE IF EXISTS team_leaderboard_india CASCADE;
DROP TABLE IF EXISTS team_members CASCADE;
DROP TABLE IF EXISTS team_stats CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS player_stats CASCADE;
DROP TABLE IF EXISTS players CASCADE;

-- 1. players table
CREATE TABLE players (
    id BIGSERIAL PRIMARY KEY,
    discord_id BIGINT UNIQUE NOT NULL,
    ign TEXT NOT NULL UNIQUE,
    player_id BIGINT NOT NULL UNIQUE,
    region TEXT NOT NULL
);

-- 2. player_stats table
CREATE TABLE player_stats (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    tournament_id INTEGER NOT NULL DEFAULT 1,
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    matches_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    mvps INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    UNIQUE(player_id, tournament_id)
);

-- 3. player_leaderboard table
CREATE TABLE player_leaderboard (
    player_id BIGINT PRIMARY KEY REFERENCES players(discord_id) ON DELETE CASCADE,
    ign TEXT NOT NULL,
    region TEXT NOT NULL,
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    matches_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    mvps INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    rank INTEGER,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. teams table
CREATE TABLE teams (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    tag TEXT NOT NULL,
    captain_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    region TEXT NOT NULL,
    logo_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    manager_1_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
    manager_2_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
    coach_id BIGINT REFERENCES players(discord_id) ON DELETE SET NULL,
    UNIQUE(name),
    UNIQUE(tag)
);

-- 5. team_members table
CREATE TABLE team_members (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    player_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, player_id)
);

-- 6. team_stats table
CREATE TABLE team_stats (
    team_id BIGINT PRIMARY KEY REFERENCES teams(id) ON DELETE CASCADE,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_matches INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_losses INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0.00,
    last_match_id BIGINT,
    recent_matches JSONB DEFAULT '[]'::jsonb
);

-- 7. matches table
CREATE TABLE matches (
    id BIGSERIAL PRIMARY KEY,
    team1_score INTEGER DEFAULT 0,
    team2_score INTEGER DEFAULT 0,
    map_name TEXT,
    tournament_id INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    team_a_id BIGINT REFERENCES teams(id) ON DELETE SET NULL,
    team_b_id BIGINT REFERENCES teams(id) ON DELETE SET NULL
);

-- 8. match_players table
CREATE TABLE match_players (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    player_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    agent TEXT,
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    mvp BOOLEAN DEFAULT FALSE,
    team INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. team_leaderboard_americas table
CREATE TABLE team_leaderboard_americas (
    team_id BIGINT PRIMARY KEY REFERENCES teams(id) ON DELETE CASCADE,
    team_name TEXT NOT NULL,
    team_tag TEXT NOT NULL,
    region TEXT NOT NULL,
    total_matches INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0.00,
    total_rounds_won INTEGER DEFAULT 0,
    total_rounds_lost INTEGER DEFAULT 0,
    round_diff INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    rank INTEGER,
    logo_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. team_leaderboard_apac table
CREATE TABLE team_leaderboard_apac (
    team_id BIGINT PRIMARY KEY REFERENCES teams(id) ON DELETE CASCADE,
    team_name TEXT NOT NULL,
    team_tag TEXT NOT NULL,
    region TEXT NOT NULL,
    total_matches INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0.00,
    total_rounds_won INTEGER DEFAULT 0,
    total_rounds_lost INTEGER DEFAULT 0,
    round_diff INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    rank INTEGER,
    logo_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. team_leaderboard_emea table
CREATE TABLE team_leaderboard_emea (
    team_id BIGINT PRIMARY KEY REFERENCES teams(id) ON DELETE CASCADE,
    team_name TEXT NOT NULL,
    team_tag TEXT NOT NULL,
    region TEXT NOT NULL,
    total_matches INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0.00,
    total_rounds_won INTEGER DEFAULT 0,
    total_rounds_lost INTEGER DEFAULT 0,
    round_diff INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    rank INTEGER,
    logo_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 12. team_leaderboard_global table
CREATE TABLE team_leaderboard_global (
    team_id BIGINT PRIMARY KEY REFERENCES teams(id) ON DELETE CASCADE,
    team_name TEXT NOT NULL,
    team_tag TEXT NOT NULL,
    region TEXT NOT NULL,
    total_matches INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0.00,
    total_rounds_won INTEGER DEFAULT 0,
    total_rounds_lost INTEGER DEFAULT 0,
    round_diff INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    rank INTEGER,
    logo_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 13. team_leaderboard_india table
CREATE TABLE team_leaderboard_india (
    team_id BIGINT PRIMARY KEY REFERENCES teams(id) ON DELETE CASCADE,
    team_name TEXT NOT NULL,
    team_tag TEXT NOT NULL,
    region TEXT NOT NULL,
    total_matches INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2) DEFAULT 0.00,
    total_rounds_won INTEGER DEFAULT 0,
    total_rounds_lost INTEGER DEFAULT 0,
    round_diff INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    rank INTEGER,
    logo_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 14. scrim_requests table
CREATE TABLE scrim_requests (
    id BIGSERIAL PRIMARY KEY,
    captain_discord_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    region TEXT NOT NULL,
    match_type TEXT NOT NULL,
    time_slot TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    timezone TEXT DEFAULT 'UTC'
);

-- 15. scrim_matches table
CREATE TABLE scrim_matches (
    id BIGSERIAL PRIMARY KEY,
    request_id_1 BIGINT REFERENCES scrim_requests(id) ON DELETE SET NULL,
    request_id_2 BIGINT REFERENCES scrim_requests(id) ON DELETE SET NULL,
    captain_1_discord_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    captain_2_discord_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    team_1_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    team_2_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    region TEXT NOT NULL,
    match_type TEXT NOT NULL,
    time_slot TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT DEFAULT 'pending',
    captain_1_approved BOOLEAN DEFAULT FALSE,
    captain_2_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    matched_at TIMESTAMP WITH TIME ZONE
);

-- 16. scrim_avoid_list table
CREATE TABLE scrim_avoid_list (
    id BIGSERIAL PRIMARY KEY,
    captain_1_discord_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    captain_2_discord_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(captain_1_discord_id, captain_2_discord_id)
);

-- 17. scrim_waitlist table
CREATE TABLE scrim_waitlist (
    id BIGSERIAL PRIMARY KEY,
    request_id BIGINT NOT NULL REFERENCES scrim_requests(id) ON DELETE CASCADE,
    captain_discord_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_stats(player_id, tournament_id);
CREATE INDEX IF NOT EXISTS idx_players_discord ON players(discord_id);
CREATE INDEX IF NOT EXISTS idx_players_ign ON players(LOWER(ign));
CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_player ON team_members(player_id);
CREATE INDEX IF NOT EXISTS idx_matches_teams ON matches(team_a_id, team_b_id);
CREATE INDEX IF NOT EXISTS idx_match_players_match ON match_players(match_id);
CREATE INDEX IF NOT EXISTS idx_match_players_player ON match_players(player_id);
CREATE INDEX IF NOT EXISTS idx_scrim_requests_status ON scrim_requests(status, time_slot);
CREATE INDEX IF NOT EXISTS idx_scrim_matches_status ON scrim_matches(status, time_slot);

COMMIT;
