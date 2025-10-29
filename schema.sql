-- Schema for VALM tournament database

-- Players table
CREATE TABLE players (
    discord_id BIGINT PRIMARY KEY,
    ign TEXT NOT NULL,
    player_id INTEGER NOT NULL,
    region TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ign),
    UNIQUE(player_id)
);

-- Create index for case-insensitive IGN lookups
CREATE INDEX idx_players_ign_lower ON players (LOWER(ign));

-- Player statistics table
CREATE TABLE player_stats (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT REFERENCES players(discord_id),
    tournament_id INTEGER NOT NULL,
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    matches_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    mvps INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, tournament_id)
);

-- Create index for faster leaderboard queries
CREATE INDEX idx_player_stats_score ON player_stats (player_id, tournament_id);

-- Add trigger for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_players_updated_at
    BEFORE UPDATE ON players
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_stats_updated_at
    BEFORE UPDATE ON player_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Teams table
CREATE TABLE teams (
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
CREATE INDEX idx_teams_name_lower ON teams (LOWER(name));
CREATE INDEX idx_teams_tag_lower ON teams (LOWER(tag));
CREATE INDEX idx_teams_captain ON teams (captain_id);

-- Team members junction table (many-to-many)
CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    player_id BIGINT NOT NULL REFERENCES players(discord_id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, player_id)
);

-- Create index for faster member lookups
CREATE INDEX idx_team_members_player ON team_members (player_id);
CREATE INDEX idx_team_members_team ON team_members (team_id);

-- Add triggers for teams table
CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();