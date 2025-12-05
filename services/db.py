import os
import asyncpg
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load .env from root directory
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set in .env file")

_pool: Optional[asyncpg.Pool] = None

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10
        )
    return _pool

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

# Player operations
async def create_player(discord_id: int, ign: str, player_id: int, region: str) -> Dict[str, Any]:
    """Create a new player and initialize their stats."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Insert player
            player = await conn.fetchrow("""
                INSERT INTO players (discord_id, ign, player_id, region)
                VALUES ($1, $2, $3, $4)
                RETURNING *
            """, discord_id, ign, player_id, region)
            
            # Initialize stats
            await conn.execute("""
                INSERT INTO player_stats (player_id, tournament_id)
                VALUES ($1, $2)
            """, discord_id, 1)  # Default to tournament_id 1
            
            return dict(player)

async def get_player(discord_id: int) -> Optional[Dict[str, Any]]:
    """Get player data and their stats."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # First check if player exists at all
        player_exists = await conn.fetchrow("""
            SELECT * FROM players WHERE discord_id = $1
        """, discord_id)
        
        if not player_exists:
            return None
        
        # Then get full data with stats
        player = await conn.fetchrow("""
            SELECT p.*, ps.kills, ps.deaths, ps.assists, 
                   ps.matches_played, ps.wins, ps.losses, ps.mvps
            FROM players p
            LEFT JOIN player_stats ps ON p.discord_id = ps.player_id
            WHERE p.discord_id = $1 AND (ps.tournament_id = 1 OR ps.tournament_id IS NULL)
        """, discord_id)
        return dict(player) if player else dict(player_exists)

async def get_player_by_ign(ign: str) -> Optional[Dict[str, Any]]:
    """Check if IGN exists (case insensitive)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        player = await conn.fetchrow("""
            SELECT * FROM players WHERE LOWER(ign) = LOWER($1)
        """, ign)
        return dict(player) if player else None

async def update_player_ign(discord_id: int, new_ign: str) -> None:
    """Update a player's IGN."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE players
            SET ign = $1
            WHERE discord_id = $2
        """, new_ign, discord_id)

async def update_player_id(discord_id: int, new_player_id: int) -> None:
    """Update a player's in-game Player ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE players
            SET player_id = $1
            WHERE discord_id = $2
        """, new_player_id, discord_id)

async def update_player_region(discord_id: int, new_region: str) -> None:
    """Update a player's region."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE players
            SET region = $1
            WHERE discord_id = $2
        """, new_region, discord_id)

async def update_player_india_status(discord_id: int, is_india: bool) -> None:
    """Update a player's India status."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Check if column exists, if not this will be a no-op
        try:
            await conn.execute("""
                UPDATE players
                SET is_india = $1
                WHERE discord_id = $2
            """, is_india, discord_id)
        except Exception:
            # Column might not exist, ignore error
            pass

async def update_player_stats(discord_id: int, stats_update: Dict[str, int]):
    """Update player stats for the current tournament."""
    pool = await get_pool()
    
    # Build the update query dynamically based on provided stats
    set_clauses = []
    values = [discord_id]  # Start with discord_id
    for i, (key, value) in enumerate(stats_update.items(), start=2):
        set_clauses.append(f"{key} = ${i}")
        values.append(value)
    
    if not set_clauses:
        return
    
    query = f"""
        UPDATE player_stats
        SET {', '.join(set_clauses)}
        WHERE player_id = $1 AND tournament_id = 1
    """
    
    async with pool.acquire() as conn:
        await conn.execute(query, *values)

async def get_player_stats(discord_id: int) -> Optional[Dict[str, Any]]:
    """Get player stats for the current tournament."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT kills, deaths, assists, matches_played, wins, losses, mvps
            FROM player_stats
            WHERE player_id = $1 AND tournament_id = 1
        """, discord_id)
        return dict(stats) if stats else None

async def create_player_stats(discord_id: int, initial_stats: Dict[str, int]):
    """Create initial player stats for the tournament."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Build the insert query dynamically based on provided stats
        columns = ['player_id', 'tournament_id']
        values = [discord_id, 1]  # Default to tournament_id 1
        value_placeholders = ['$1', '$2']

        for i, (key, value) in enumerate(initial_stats.items(), start=3):
            columns.append(key)
            values.append(value)
            value_placeholders.append(f'${i}')

        query = f"""
            INSERT INTO player_stats 
            ({', '.join(columns)})
            VALUES ({', '.join(value_placeholders)})
            ON CONFLICT (player_id, tournament_id) DO UPDATE
            SET {', '.join(f"{col} = EXCLUDED.{col}" for col in columns[2:])}
        """

        await conn.execute(query, *values)

async def get_leaderboard(limit: int = 10) -> list[Dict[str, Any]]:
    """Get the top players by score."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                p.discord_id,
                p.ign,
                p.region,
                ps.kills,
                ps.deaths,
                ps.assists,
                ps.matches_played,
                ps.wins,
                ps.losses,
                ps.mvps,
                CASE 
                    WHEN ps.matches_played >= 3 THEN
                        ps.kills * 100 + 
                        ps.assists * 50 + 
                        ps.deaths * -50 + 
                        ps.wins * 500 + 
                        ps.matches_played * 100
                    ELSE 0
                END as score
            FROM players p
            JOIN player_stats ps ON p.discord_id = ps.player_id
            WHERE ps.tournament_id = 1
            ORDER BY score DESC
            LIMIT $1
        """, limit)
        return [dict(row) for row in rows]
async def cleanup_database():
    """Clean up the database and reset all sequences."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Truncate tables in proper order
            await conn.execute("""
                TRUNCATE TABLE player_stats, players RESTART IDENTITY CASCADE
            """)

async def reset_sequences():
    """Reset all sequences in the database to their minimum values."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Reset player_stats sequence
            await conn.execute("""
                ALTER SEQUENCE player_stats_id_seq RESTART WITH 1
            """)
            # Reset the sequence's is_called flag
            await conn.execute("""
                SELECT setval('player_stats_id_seq', 1, false)
            """)

async def get_all_players_with_stats() -> list:
    """Get all players with their stats for leaderboard."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        players = await conn.fetch("""
            SELECT p.*, ps.kills, ps.deaths, ps.assists,
                   ps.matches_played, ps.wins, ps.losses, ps.mvps
            FROM players p
            LEFT JOIN player_stats ps ON p.discord_id = ps.player_id
            WHERE ps.tournament_id = 1
            ORDER BY ps.wins DESC, ps.kills DESC
        """)
        return [dict(p) for p in players]

async def get_all_players() -> list:
    """Get all registered players with their stats."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT p.*, ps.kills, ps.deaths, ps.assists, 
                   ps.matches_played, ps.wins, ps.losses, ps.mvps
            FROM players p
            LEFT JOIN player_stats ps ON p.discord_id = ps.player_id
            WHERE ps.tournament_id = 1
        """)
        return [dict(row) for row in rows]

# Match history functions
async def get_player_match_history(discord_id: int, limit: int = 5) -> list:
    """Get a player's recent matches with full details."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        matches = await conn.fetch("""
            WITH player_matches AS (
                SELECT DISTINCT m.id, m.created_at, m.map_name, 
                       m.team1_score, m.team2_score
                FROM matches m
                JOIN match_players mp ON m.id = mp.match_id
                WHERE mp.player_id = $1
                ORDER BY m.created_at DESC
                LIMIT $2
            )
            SELECT 
                pm.*,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'player_id', mp.player_id,
                            'agent', mp.agent,
                            'kills', mp.kills,
                            'deaths', mp.deaths,
                            'assists', mp.assists,
                            'score', mp.score,
                            'mvp', mp.mvp,
                            'team', mp.team,
                            'ign', p.ign
                        ) ORDER BY mp.team, mp.score DESC
                    ) FILTER (WHERE mp.player_id IS NOT NULL),
                    '[]'::json
                ) as players
            FROM player_matches pm
            JOIN match_players mp ON pm.id = mp.match_id
            JOIN players p ON mp.player_id = p.discord_id
            GROUP BY pm.id, pm.created_at, pm.map_name, 
                     pm.team1_score, pm.team2_score
            ORDER BY pm.created_at DESC
        """, discord_id, limit)
        return [dict(match) for match in matches]

async def get_recent_matches(limit: int = 10) -> list:
    """Get most recent matches across all players."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        matches = await conn.fetch("""
            SELECT 
                m.id, m.created_at, m.map_name,
                m.team1_score, m.team2_score,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'player_id', mp.player_id,
                            'agent', mp.agent,
                            'kills', mp.kills,
                            'deaths', mp.deaths,
                            'assists', mp.assists,
                            'score', mp.score,
                            'mvp', mp.mvp,
                            'team', mp.team,
                            'ign', p.ign
                        ) ORDER BY mp.team, mp.score DESC
                    ) FILTER (WHERE mp.player_id IS NOT NULL),
                    '[]'::json
                ) as players
            FROM matches m
            JOIN match_players mp ON m.id = mp.match_id
            JOIN players p ON mp.player_id = p.discord_id
            GROUP BY m.id, m.created_at, m.map_name,
                     m.team1_score, m.team2_score
            ORDER BY m.created_at DESC
            LIMIT $1
        """, limit)
        return [dict(match) for match in matches]

# Import existing data (one-time migration helper)
async def import_json_data(json_data: list):
    """Import existing JSON data into PostgreSQL."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            for player in json_data:
                # Insert player
                await conn.execute("""
                    INSERT INTO players (discord_id, ign, player_id, region)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (discord_id) DO NOTHING
                """, player['discord_id'], player['ign'], player['id'], player['region'])
                
                # Insert stats
                stats = player['stats']['1']  # Assuming tournament_id 1
                await conn.execute("""
                    INSERT INTO player_stats (
                        player_id, tournament_id, kills, deaths, assists,
                        matches_played, wins, losses, mvps
                    ) VALUES ($1, 1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (player_id, tournament_id) DO UPDATE SET
                        kills = EXCLUDED.kills,
                        deaths = EXCLUDED.deaths,
                        assists = EXCLUDED.assists,
                        matches_played = EXCLUDED.matches_played,
                        wins = EXCLUDED.wins,
                        losses = EXCLUDED.losses,
                        mvps = EXCLUDED.mvps
                """, player['discord_id'], stats['kills'], stats['deaths'],
                    stats['assists'], stats['matches_played'], stats['wins'],
                    stats['losses'], stats['mvps'])

async def save_match_results(match_data: dict):
    """Save match results including player stats. Returns the match ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Create match record with team IDs
            match = await conn.fetchrow("""
                INSERT INTO matches (team1_score, team2_score, map_name, tournament_id, team_a_id, team_b_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, created_at
            """, match_data['team1_score'], match_data['team2_score'], 
                 match_data['map'], 1,  # Default to tournament_id 1
                 match_data.get('team_a_id'), match_data.get('team_b_id'))
            
            match_id = match['id']
            match_timestamp = match['created_at'].isoformat()
            
            # Add player performances
            for player in match_data['players']:
                # Get agent, default to 'Unknown' if not provided
                agent = player.get('agent', 'Unknown')
                
                await conn.execute("""
                    INSERT INTO match_players 
                    (match_id, player_id, agent, kills, deaths, assists, score, mvp, team)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, match['id'], player['discord_id'], agent,
                     player['kills'], player['deaths'], player['assists'],
                     player['score'], player['mvp'], player['team'])
                
                # Update player's overall stats
                await conn.execute("""
                    UPDATE player_stats 
                    SET kills = kills + $2,
                        deaths = deaths + $3,
                        assists = assists + $4,
                        matches_played = matches_played + 1,
                        wins = wins + $5,
                        losses = losses + $6,
                        mvps = mvps + $7
                    WHERE player_id = $1 AND tournament_id = 1
                """, player['discord_id'], player['kills'], player['deaths'],
                     player['assists'], 1 if player['won'] else 0,
                     0 if player['won'] else 1, 1 if player['mvp'] else 0)
            
            return {
                'match_id': match_id,
                'timestamp': match_timestamp
            }

async def get_match_history(player_id: int, limit: int = 5) -> list:
    """Get a player's recent match history."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        matches = await conn.fetch("""
            SELECT m.id, m.team1_score, m.team2_score, m.map_name,
                   mp.agent, mp.kills, mp.deaths, mp.assists, mp.score,
                   mp.mvp, mp.team,
                   m.created_at
            FROM matches m
            JOIN match_players mp ON m.id = mp.match_id
            WHERE mp.player_id = $1
            ORDER BY m.created_at DESC
            LIMIT $2
        """, player_id, limit)
        return [dict(match) for match in matches]

async def get_team_matches(team_id: int, limit: int = 5) -> list:
    """Get a team's recent match history."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        matches = await conn.fetch("""
            SELECT m.id, m.team1_score, m.team2_score, m.map_name,
                   m.team_a_id, m.team_b_id,
                   ta.name as team_a_name, ta.tag as team_a_tag,
                   tb.name as team_b_name, tb.tag as team_b_tag,
                   m.created_at
            FROM matches m
            LEFT JOIN teams ta ON m.team_a_id = ta.id
            LEFT JOIN teams tb ON m.team_b_id = tb.id
            WHERE m.team_a_id = $1 OR m.team_b_id = $1
            ORDER BY m.created_at DESC
            LIMIT $2
        """, team_id, limit)
        return [dict(match) for match in matches]


# ============================================================================
# Team Management Functions
# ============================================================================

async def create_team(name: str, tag: str, captain_id: int, region: str, logo_url: str = None) -> Dict[str, Any]:
    """Create a new team with the captain as the first member."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Create team
            team = await conn.fetchrow("""
                INSERT INTO teams (name, tag, captain_id, region, logo_url)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
            """, name, tag, captain_id, region, logo_url)
            
            # Add captain as first member
            await conn.execute("""
                INSERT INTO team_members (team_id, player_id)
                VALUES ($1, $2)
            """, team['id'], captain_id)
            
            # Initialize team stats
            await conn.execute("""
                INSERT INTO team_stats (team_id, total_matches, total_wins, total_losses, win_rate, recent_matches)
                VALUES ($1, 0, 0, 0, 0.0, '[]'::jsonb)
            """, team['id'])
            
            return dict(team)

async def get_team_by_id(team_id: int) -> Optional[Dict[str, Any]]:
    """Get team by ID with member list."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        team = await conn.fetchrow("""
            SELECT t.*, 
                   COALESCE(
                       json_agg(
                           json_build_object(
                               'discord_id', tm.player_id,
                               'ign', p.ign,
                               'joined_at', tm.joined_at
                           ) ORDER BY tm.joined_at
                       ) FILTER (WHERE tm.player_id IS NOT NULL),
                       '[]'::json
                   ) as members
            FROM teams t
            LEFT JOIN team_members tm ON t.id = tm.team_id
            LEFT JOIN players p ON tm.player_id = p.discord_id
            WHERE t.id = $1
            GROUP BY t.id
        """, team_id)
        return dict(team) if team else None

async def get_team_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get team by name (case-insensitive)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        team = await conn.fetchrow("""
            SELECT t.*, 
                   COALESCE(
                       json_agg(
                           json_build_object(
                               'discord_id', tm.player_id,
                               'ign', p.ign,
                               'joined_at', tm.joined_at
                           ) ORDER BY tm.joined_at
                       ) FILTER (WHERE tm.player_id IS NOT NULL),
                       '[]'::json
                   ) as members
            FROM teams t
            LEFT JOIN team_members tm ON t.id = tm.team_id
            LEFT JOIN players p ON tm.player_id = p.discord_id
            WHERE LOWER(t.name) = LOWER($1)
            GROUP BY t.id
        """, name)
        return dict(team) if team else None

async def get_team_by_captain(captain_id: int) -> Optional[Dict[str, Any]]:
    """Get team by captain's discord ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        team = await conn.fetchrow("""
            SELECT t.*, 
                   COALESCE(
                       json_agg(
                           json_build_object(
                               'discord_id', tm.player_id,
                               'ign', p.ign,
                               'joined_at', tm.joined_at
                           ) ORDER BY tm.joined_at
                       ) FILTER (WHERE tm.player_id IS NOT NULL),
                       '[]'::json
                   ) as members
            FROM teams t
            LEFT JOIN team_members tm ON t.id = tm.team_id
            LEFT JOIN players p ON tm.player_id = p.discord_id
            WHERE t.captain_id = $1
            GROUP BY t.id
        """, captain_id)
        return dict(team) if team else None

async def get_player_team(player_id: int) -> Optional[Dict[str, Any]]:
    """Get the team a player belongs to."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        team = await conn.fetchrow("""
            SELECT t.*, 
                   COALESCE(
                       json_agg(
                           json_build_object(
                               'discord_id', tm.player_id,
                               'ign', p.ign,
                               'joined_at', tm.joined_at
                           ) ORDER BY tm.joined_at
                       ) FILTER (WHERE tm.player_id IS NOT NULL),
                       '[]'::json
                   ) as members
            FROM teams t
            JOIN team_members tm ON t.id = tm.team_id
            LEFT JOIN team_members tm2 ON t.id = tm2.team_id
            LEFT JOIN players p ON tm2.player_id = p.discord_id
            WHERE tm.player_id = $1
            GROUP BY t.id
        """, player_id)
        return dict(team) if team else None

async def add_team_member(team_id: int, player_id: int) -> None:
    """Add a player to a team."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO team_members (team_id, player_id)
            VALUES ($1, $2)
            ON CONFLICT (team_id, player_id) DO NOTHING
        """, team_id, player_id)

async def remove_team_member(team_id: int, player_id: int) -> None:
    """Remove a player from a team."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM team_members
            WHERE team_id = $1 AND player_id = $2
        """, team_id, player_id)

async def update_team_record(team_id: int, won: bool) -> None:
    """Update team's win/loss record."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if won:
            await conn.execute("""
                UPDATE teams
                SET wins = wins + 1
                WHERE id = $1
            """, team_id)
        else:
            await conn.execute("""
                UPDATE teams
                SET losses = losses + 1
                WHERE id = $1
            """, team_id)

async def update_team_logo(team_id: int, logo_url: str) -> None:
    """Update team's logo URL."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE teams
            SET logo_url = $1
            WHERE id = $2
        """, logo_url, team_id)



async def delete_team(team_id: int) -> None:
    """Delete a team (cascade deletes members)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM teams WHERE id = $1
        """, team_id)

async def get_all_teams(region: str = None) -> list:
    """Get all teams, optionally filtered by region."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if region:
            teams = await conn.fetch("""
                SELECT t.*, 
                       (SELECT COUNT(*) FROM team_members WHERE team_id = t.id) as member_count
                FROM teams t
                WHERE t.region = $1
                ORDER BY t.created_at DESC
            """, region)
        else:
            teams = await conn.fetch("""
                SELECT t.*, 
                       (SELECT COUNT(*) FROM team_members WHERE team_id = t.id) as member_count
                FROM teams t
                ORDER BY t.created_at DESC
            """)
        return [dict(team) for team in teams]

async def update_team_stats(team_id: int, match_data: dict) -> None:
    """Update team_stats table with latest match information."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Get current stats
        stats = await conn.fetchrow("""
            SELECT recent_matches FROM team_stats WHERE team_id = $1
        """, team_id)
        
        # Prepare new match entry
        new_match = {
            'match_id': match_data.get('match_id'),
            'opponent_id': match_data.get('opponent_id'),
            'opponent_name': match_data.get('opponent_name'),
            'map': match_data.get('map'),
            'score_for': match_data.get('score_for'),
            'score_against': match_data.get('score_against'),
            'won': match_data.get('won'),
            'timestamp': match_data.get('timestamp')
        }
        
        # Get existing matches or initialize empty list
        import json
        if stats and stats['recent_matches']:
            recent_matches = json.loads(stats['recent_matches']) if isinstance(stats['recent_matches'], str) else stats['recent_matches']
        else:
            recent_matches = []
        
        # Add new match at the beginning (newest first)
        recent_matches.insert(0, new_match)
        
        # Keep only last 10 matches
        recent_matches = recent_matches[:10]
        
        # Calculate stats
        total_matches = len(recent_matches)
        total_wins = sum(1 for m in recent_matches if m.get('won'))
        total_losses = total_matches - total_wins
        win_rate = (total_wins / total_matches * 100) if total_matches > 0 else 0
        
        # Update or insert stats
        await conn.execute("""
            INSERT INTO team_stats (team_id, total_matches, total_wins, total_losses, win_rate, last_match_id, recent_matches)
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
            ON CONFLICT (team_id) 
            DO UPDATE SET 
                total_matches = $2,
                total_wins = $3,
                total_losses = $4,
                win_rate = $5,
                last_match_id = $6,
                recent_matches = $7::jsonb
        """, team_id, total_matches, total_wins, total_losses, win_rate, 
             match_data.get('match_id'), json.dumps(recent_matches))

async def get_team_stats(team_id: int) -> Optional[Dict[str, Any]]:
    """Get team statistics including recent matches."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT * FROM team_stats WHERE team_id = $1
        """, team_id)
        return dict(stats) if stats else None


# ============================================================================
# Team Leaderboard Functions
# ============================================================================

async def update_team_leaderboard(team_id: int, team_name: str, team_tag: str, region: str, 
                                  logo_url: str = None, is_india: bool = False):
    """Update team stats in all relevant leaderboard tables."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Get team stats
        team_stats = await conn.fetchrow("""
            SELECT total_matches, total_wins, total_losses, win_rate, recent_matches
            FROM team_stats
            WHERE team_id = $1
        """, team_id)
        
        if not team_stats:
            return
        
        # Calculate rounds won/lost from recent matches
        total_rounds_won = 0
        total_rounds_lost = 0
        
        recent_matches = team_stats['recent_matches']
        
        # Parse recent_matches if it's a string (JSON)
        if isinstance(recent_matches, str):
            import json as json_module
            try:
                recent_matches = json_module.loads(recent_matches)
            except:
                recent_matches = []
        
        # Ensure recent_matches is a list
        if not isinstance(recent_matches, list):
            recent_matches = []
        
        for match in recent_matches:
            if isinstance(match, dict) and match.get('team_id') == team_id:
                total_rounds_won += match.get('rounds_won', 0)
                total_rounds_lost += match.get('rounds_lost', 0)
        
        round_diff = total_rounds_won - total_rounds_lost
        
        # Calculate points (wins * 3 + round_diff * 0.1)
        points = (team_stats['total_wins'] * 3.0) + (round_diff * 0.1)
        
        # Region mapping
        region_lower = region.lower()
        region_map = {
            'ap': 'apac',
            'kr': 'apac',
            'jp': 'apac',
            'eu': 'emea',
            'na': 'americas',
            'br': 'americas',
            'latam': 'americas'
        }
        
        regional_table = region_map.get(region_lower)
        
        # Update global leaderboard
        await conn.execute("""
            INSERT INTO team_leaderboard_global 
            (team_id, team_name, team_tag, region, total_matches, wins, losses, win_rate,
             total_rounds_won, total_rounds_lost, round_diff, points, logo_url)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT (team_id) 
            DO UPDATE SET 
                team_name = $2,
                team_tag = $3,
                region = $4,
                total_matches = $5,
                wins = $6,
                losses = $7,
                win_rate = $8,
                total_rounds_won = $9,
                total_rounds_lost = $10,
                round_diff = $11,
                points = $12,
                logo_url = $13
        """, team_id, team_name, team_tag, region, team_stats['total_matches'],
             team_stats['total_wins'], team_stats['total_losses'], team_stats['win_rate'],
             total_rounds_won, total_rounds_lost, round_diff, points, logo_url)
        
        # Update regional leaderboard
        if regional_table:
            await conn.execute(f"""
                INSERT INTO team_leaderboard_{regional_table}
                (team_id, team_name, team_tag, region, total_matches, wins, losses, win_rate,
                 total_rounds_won, total_rounds_lost, round_diff, points, logo_url)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (team_id)
                DO UPDATE SET
                    team_name = $2,
                    team_tag = $3,
                    region = $4,
                    total_matches = $5,
                    wins = $6,
                    losses = $7,
                    win_rate = $8,
                    total_rounds_won = $9,
                    total_rounds_lost = $10,
                    round_diff = $11,
                    points = $12,
                    logo_url = $13
            """, team_id, team_name, team_tag, region, team_stats['total_matches'],
                 team_stats['total_wins'], team_stats['total_losses'], team_stats['win_rate'],
                 total_rounds_won, total_rounds_lost, round_diff, points, logo_url)
        
        # Update India leaderboard if team is from India or has India tag
        if is_india or region.lower() == 'india':
            await conn.execute("""
                INSERT INTO team_leaderboard_india
                (team_id, team_name, team_tag, region, total_matches, wins, losses, win_rate,
                 total_rounds_won, total_rounds_lost, round_diff, points, logo_url)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (team_id)
                DO UPDATE SET
                    team_name = $2,
                    team_tag = $3,
                    region = $4,
                    total_matches = $5,
                    wins = $6,
                    losses = $7,
                    win_rate = $8,
                    total_rounds_won = $9,
                    total_rounds_lost = $10,
                    round_diff = $11,
                    points = $12,
                    logo_url = $13
            """, team_id, team_name, team_tag, region, team_stats['total_matches'],
                 team_stats['total_wins'], team_stats['total_losses'], team_stats['win_rate'],
                 total_rounds_won, total_rounds_lost, round_diff, points, logo_url)

async def update_team_leaderboard_ranks(leaderboard_type: str = 'global'):
    """Update ranks for a specific team leaderboard based on points."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(f"""
            UPDATE team_leaderboard_{leaderboard_type} lb
            SET rank = ranked.rank
            FROM (
                SELECT team_id, ROW_NUMBER() OVER (ORDER BY points DESC, win_rate DESC, total_matches DESC) as rank
                FROM team_leaderboard_{leaderboard_type}
            ) ranked
            WHERE lb.team_id = ranked.team_id
        """)

async def get_team_leaderboard(leaderboard_type: str = 'global', limit: int = 15):
    """Get team leaderboard data for a specific region."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Update ranks first
        await update_team_leaderboard_ranks(leaderboard_type)
        
        # Fetch leaderboard
        teams = await conn.fetch(f"""
            SELECT rank, team_name, team_tag, region, total_matches, wins, losses, win_rate,
                   total_rounds_won, total_rounds_lost, round_diff, points, logo_url
            FROM team_leaderboard_{leaderboard_type}
            ORDER BY rank ASC
            LIMIT $1
        """, limit)
        
        return [dict(t) for t in teams]

# ============================================================================
# Player Leaderboard Functions
# ============================================================================

async def update_player_leaderboard(player_id: int, ign: str, region: str):
    """Update player stats in the global leaderboard table."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Get player stats
        player_stats = await conn.fetchrow("""
            SELECT kills, deaths, assists, matches_played, wins, losses, mvps
            FROM player_stats
            WHERE player_id = $1
        """, player_id)
        
        if not player_stats:
            return
        
        # Calculate points using scoring config
        import json as json_module
        config_path = Path(__file__).parent.parent / 'data' / 'scoring_config.json'
        with open(config_path, 'r') as f:
            config = json_module.load(f)
        
        weights = config['player_scoring']['weights']
        bonuses = config['player_scoring']['bonus_multipliers']
        
        kills = player_stats['kills']
        deaths = player_stats['deaths']
        assists = player_stats['assists']
        wins = player_stats['wins']
        matches = player_stats['matches_played']
        mvps = player_stats['mvps']
        losses = player_stats['losses']
        
        # Base score
        points = (
            kills * weights['kill_points'] +
            assists * weights['assist_points'] -
            deaths * weights['death_penalty'] +
            wins * weights['win_points'] +
            matches * weights['participation_points']
        )
        
        # Apply multipliers
        multiplier = 1.0
        if deaths > 0:
            kd = kills / deaths
            if kd >= 2.0:
                multiplier *= bonuses.get('kd_ratio_above_2.0', 1.2)
            elif kd >= 1.5:
                multiplier *= bonuses.get('kd_ratio_above_1.5', 1.1)
        
        if matches > 0:
            wr = (wins / matches) * 100
            if wr >= 75:
                multiplier *= bonuses.get('win_rate_above_75', 1.15)
            elif wr >= 60:
                multiplier *= bonuses.get('win_rate_above_60', 1.05)
        
        points = max(0, points * multiplier)
        
        # Update player leaderboard
        await conn.execute("""
            INSERT INTO player_leaderboard 
            (player_id, ign, region, kills, deaths, assists, matches_played, wins, losses, mvps, points)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (player_id) 
            DO UPDATE SET 
                ign = $2,
                region = $3,
                kills = $4,
                deaths = $5,
                assists = $6,
                matches_played = $7,
                wins = $8,
                losses = $9,
                mvps = $10,
                points = $11
        """, player_id, ign, region, kills, deaths, assists, matches, wins, losses, mvps, points)

async def update_player_leaderboard_ranks():
    """Update ranks for the player leaderboard based on points."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE player_leaderboard lb
            SET rank = ranked.rank
            FROM (
                SELECT player_id, ROW_NUMBER() OVER (ORDER BY points DESC, kills DESC, wins DESC) as rank
                FROM player_leaderboard
            ) ranked
            WHERE lb.player_id = ranked.player_id
        """)

async def get_player_leaderboard(limit: int = 100):
    """Get global player leaderboard data."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Update ranks first
        await update_player_leaderboard_ranks()
        
        # Fetch leaderboard
        players = await conn.fetch("""
            SELECT rank, ign, region, kills, deaths, assists, matches_played, wins, losses, mvps, points
            FROM player_leaderboard
            ORDER BY rank ASC
            LIMIT $1
        """, limit)
        
        return [dict(p) for p in players]


# ===== SCRIM OPERATIONS =====

async def create_scrim_request(captain_discord_id: int, team_id: Optional[int], region: str,
                               match_type: str, time_slot: str, timezone: str, expires_at=None) -> Dict[str, Any]:
    """Create a new scrim request with timezone."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        request = await conn.fetchrow("""
            INSERT INTO scrim_requests (captain_discord_id, team_id, region, match_type, time_slot, timezone, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        """, captain_discord_id, team_id, region.lower(), match_type.lower(), time_slot, timezone.upper(), expires_at)
        return dict(request)


async def get_pending_scrim_requests(exclude_captain_id: Optional[int] = None) -> list:
    """Get all pending scrim requests, optionally excluding a specific captain."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if exclude_captain_id:
            requests = await conn.fetch("""
                SELECT sr.*, t.name as team_name, t.tag as team_tag
                FROM scrim_requests sr
                LEFT JOIN teams t ON sr.team_id = t.id
                WHERE sr.status = 'pending' 
                  AND sr.captain_discord_id != $1
                  AND (sr.expires_at IS NULL OR sr.expires_at > NOW())
                ORDER BY sr.created_at ASC
            """, exclude_captain_id)
        else:
            requests = await conn.fetch("""
                SELECT sr.*, t.name as team_name, t.tag as team_tag
                FROM scrim_requests sr
                LEFT JOIN teams t ON sr.team_id = t.id
                WHERE sr.status = 'pending'
                  AND (sr.expires_at IS NULL OR sr.expires_at > NOW())
                ORDER BY sr.created_at ASC
            """)
        return [dict(r) for r in requests]


async def get_scrim_request_by_id(request_id: int) -> Optional[Dict[str, Any]]:
    """Get a scrim request by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        request = await conn.fetchrow("""
            SELECT sr.*, t.name as team_name, t.tag as team_tag
            FROM scrim_requests sr
            LEFT JOIN teams t ON sr.team_id = t.id
            WHERE sr.id = $1
        """, request_id)
        return dict(request) if request else None


async def update_scrim_request_status(request_id: int, status: str):
    """Update the status of a scrim request."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE scrim_requests
            SET status = $1
            WHERE id = $2
        """, status, request_id)


async def create_scrim_match(request_id_1: int, request_id_2: int, 
                             captain_1_id: int, captain_2_id: int,
                             team_1_id: Optional[int], team_2_id: Optional[int],
                             region: str, match_type: str, time_slot: str) -> Dict[str, Any]:
    """Create a scrim match pairing."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        match = await conn.fetchrow("""
            INSERT INTO scrim_matches 
            (request_id_1, request_id_2, captain_1_discord_id, captain_2_discord_id, 
             team_1_id, team_2_id, region, match_type, time_slot)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """, request_id_1, request_id_2, captain_1_id, captain_2_id, 
             team_1_id, team_2_id, region.lower(), match_type.lower(), time_slot)
        return dict(match)


async def get_scrim_match_by_id(match_id: int) -> Optional[Dict[str, Any]]:
    """Get a scrim match by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        match = await conn.fetchrow("""
            SELECT sm.*,
                   t1.name as team_1_name, t1.tag as team_1_tag,
                   t2.name as team_2_name, t2.tag as team_2_tag
            FROM scrim_matches sm
            LEFT JOIN teams t1 ON sm.team_1_id = t1.id
            LEFT JOIN teams t2 ON sm.team_2_id = t2.id
            WHERE sm.id = $1
        """, match_id)
        return dict(match) if match else None


async def update_scrim_match_approval(match_id: int, captain_num: int, approved: bool):
    """Update approval status for a captain (1 or 2)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if captain_num == 1:
            await conn.execute("""
                UPDATE scrim_matches
                SET captain_1_approved = $1
                WHERE id = $2
            """, approved, match_id)
        else:
            await conn.execute("""
                UPDATE scrim_matches
                SET captain_2_approved = $1
                WHERE id = $2
            """, approved, match_id)


async def update_scrim_match_status(match_id: int, status: str):
    """Update the status of a scrim match."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE scrim_matches
            SET status = $1
            WHERE id = $2
        """, status, match_id)


async def update_scrim_match_format(match_id: int, match_type: str):
    """Update the match type/format of a scrim match."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE scrim_matches
            SET match_type = $1
            WHERE id = $2
        """, match_type, match_id)


async def get_captain_pending_matches(captain_discord_id: int) -> list:
    """Get all pending/active scrim matches for a captain."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        matches = await conn.fetch("""
            SELECT sm.*,
                   t1.name as team_1_name, t1.tag as team_1_tag,
                   t2.name as team_2_name, t2.tag as team_2_tag
            FROM scrim_matches sm
            LEFT JOIN teams t1 ON sm.team_1_id = t1.id
            LEFT JOIN teams t2 ON sm.team_2_id = t2.id
            WHERE (sm.captain_1_discord_id = $1 OR sm.captain_2_discord_id = $1)
              AND sm.status IN ('pending_approval', 'chat_active', 'map_banning')
            ORDER BY sm.matched_at DESC
        """, captain_discord_id)
        return [dict(m) for m in matches]


async def expire_old_scrim_requests():
    """Mark old scrim requests as expired."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE scrim_requests
            SET status = 'expired'
            WHERE status = 'pending'
              AND expires_at IS NOT NULL
              AND expires_at < NOW()
        """)


async def cancel_scrim_request(request_id: int):
    """Cancel a scrim request."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE scrim_requests
            SET status = 'cancelled'
            WHERE id = $1
        """, request_id)


async def add_to_avoid_list(captain_1_id: int, captain_2_id: int, hours: int = 24):
    """Add two captains to the avoid list for specified hours."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        expires_at = datetime.utcnow() + timedelta(hours=hours)
        await conn.execute("""
            INSERT INTO scrim_avoid_list (captain_1_discord_id, captain_2_discord_id, expires_at)
            VALUES ($1, $2, $3)
        """, captain_1_id, captain_2_id, expires_at)


async def check_avoid_list(captain_1_id: int, captain_2_id: int) -> bool:
    """Check if two captains are in the avoid list."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow("""
            SELECT id FROM scrim_avoid_list
            WHERE ((captain_1_discord_id = $1 AND captain_2_discord_id = $2)
               OR (captain_1_discord_id = $2 AND captain_2_discord_id = $1))
              AND expires_at > NOW()
        """, captain_1_id, captain_2_id)
        return result is not None


async def clean_avoid_list():
    """Remove expired entries from avoid list."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM scrim_avoid_list
            WHERE expires_at < NOW()
        """)


async def get_captain_pending_request(captain_id: int) -> Optional[Dict[str, Any]]:
    """Get a captain's pending scrim request."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        request = await conn.fetchrow("""
            SELECT * FROM scrim_requests
            WHERE captain_discord_id = $1
              AND status = 'pending'
            ORDER BY created_at DESC
            LIMIT 1
        """, captain_id)
        return dict(request) if request else None


async def get_team_pending_request(team_id: int) -> Optional[Dict[str, Any]]:
    """Get a team's pending scrim request (by any member)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        request = await conn.fetchrow("""
            SELECT * FROM scrim_requests
            WHERE team_id = $1
              AND status = 'pending'
            ORDER BY created_at DESC
            LIMIT 1
        """, team_id)
        return dict(request) if request else None


async def get_scrim_request_status(request_id: int) -> Optional[str]:
    """Get the status of a scrim request."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow("""
            SELECT status FROM scrim_requests
            WHERE id = $1
        """, request_id)
        return result['status'] if result else None


async def add_to_scrim_waitlist(request_id: int, captain_id: int):
    """Add a captain to the waitlist for a scrim request."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO scrim_waitlist (request_id, captain_discord_id, created_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (request_id, captain_discord_id) DO NOTHING
        """, request_id, captain_id)


async def get_scrim_waitlist(request_id: int) -> list:
    """Get all captains waiting for a scrim request."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT captain_discord_id FROM scrim_waitlist
            WHERE request_id = $1
        """, request_id)
        return [row['captain_discord_id'] for row in rows]


async def clear_scrim_waitlist(request_id: int):
    """Clear all waitlist entries for a request (when match is successful)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            DELETE FROM scrim_waitlist
            WHERE request_id = $1
        """, request_id)


# ============= ADMIN TEAM REGISTRATION FUNCTIONS =============

async def get_team_by_name(team_name: str):
    """Get team by name"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        team = await conn.fetchrow(
            "SELECT * FROM teams WHERE LOWER(name) = LOWER($1)",
            team_name
        )
        return dict(team) if team else None


async def get_player_by_discord_id(discord_id: int):
    """Get player by Discord ID"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        player = await conn.fetchrow(
            "SELECT * FROM player_leaderboard WHERE discord_id = $1",
            discord_id
        )
        return dict(player) if player else None


async def create_player_leaderboard(discord_id: int, ign: str, team_id: int, region: str):
    """Create a new player in the leaderboard"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        player = await conn.fetchrow("""
            INSERT INTO player_leaderboard 
            (discord_id, ign, team_id, region, kills, deaths, assists, mvps, points, created_at)
            VALUES ($1, $2, $3, $4, 0, 0, 0, 0, 0, NOW())
            RETURNING *
        """, discord_id, ign, team_id, region)
        return dict(player) if player else None


async def update_player_team(discord_id: int, team_id: int):
    """Update player's team"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE player_leaderboard
            SET team_id = $1, updated_at = NOW()
            WHERE discord_id = $2
        """, team_id, discord_id)


# ============= TEAM MANAGEMENT FUNCTIONS =============

async def add_player_to_team(team_id: int, discord_id: int, ign: str):
    """Add a player to a team."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Update player's team_id
            await conn.execute("""
                UPDATE players
                SET team_id = $1, updated_at = CURRENT_TIMESTAMP
                WHERE discord_id = $2
            """, team_id, discord_id)
            
            # Get current team members
            team = await conn.fetchrow("SELECT members FROM teams WHERE id = $1", team_id)
            members = team['members'] if team else []
            
            if isinstance(members, str):
                import json
                members = json.loads(members)
            
            # Add new member
            new_member = {
                'discord_id': discord_id,
                'ign': ign,
                'kills': 0,
                'deaths': 0,
                'assists': 0
            }
            members.append(new_member)
            
            # Update team members
            await conn.execute("""
                UPDATE teams
                SET members = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, json.dumps(members), team_id)


async def remove_player_from_team(team_id: int, discord_id: int):
    """Remove a player from a team."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Remove player's team_id
            await conn.execute("""
                UPDATE players
                SET team_id = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE discord_id = $1
            """, discord_id)
            
            # Get current team members
            team = await conn.fetchrow("SELECT members FROM teams WHERE id = $1", team_id)
            members = team['members'] if team else []
            
            if isinstance(members, str):
                import json
                members = json.loads(members)
            
            # Remove member
            members = [m for m in members if isinstance(m, dict) and m.get('discord_id') != discord_id]
            
            # Update team members
            await conn.execute("""
                UPDATE teams
                SET members = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, json.dumps(members), team_id)


async def transfer_team_captainship(team_id: int, new_captain_id: int):
    """Transfer team captainship to another member."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE teams
            SET captain_id = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """, new_captain_id, team_id)


async def add_team_coach(team_id: int, coach_id: int):
    """Add a coach to the team."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Check if team_staff record exists
        staff = await conn.fetchrow("""
            SELECT * FROM team_staff WHERE team_id = $1
        """, team_id)
        
        if staff:
            # Update existing record
            await conn.execute("""
                UPDATE team_staff
                SET coach_id = $1, updated_at = CURRENT_TIMESTAMP
                WHERE team_id = $2
            """, coach_id, team_id)
        else:
            # Create new record
            await conn.execute("""
                INSERT INTO team_staff (team_id, coach_id, created_at, updated_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, team_id, coach_id)


async def remove_team_coach(team_id: int):
    """Remove the coach from the team."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE team_staff
            SET coach_id = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE team_id = $1
        """, team_id)


async def add_team_manager(team_id: int, manager_id: int, slot: int):
    """Add a manager to the team (slot 1 or 2)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Check if team_staff record exists
        staff = await conn.fetchrow("""
            SELECT * FROM team_staff WHERE team_id = $1
        """, team_id)
        
        if slot == 1:
            if staff:
                await conn.execute("""
                    UPDATE team_staff
                    SET manager_1_id = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE team_id = $2
                """, manager_id, team_id)
            else:
                await conn.execute("""
                    INSERT INTO team_staff (team_id, manager_1_id, created_at, updated_at)
                    VALUES ($1, $2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, team_id, manager_id)
        else:  # slot 2
            if staff:
                await conn.execute("""
                    UPDATE team_staff
                    SET manager_2_id = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE team_id = $2
                """, manager_id, team_id)
            else:
                await conn.execute("""
                    INSERT INTO team_staff (team_id, manager_2_id, created_at, updated_at)
                    VALUES ($1, $2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, team_id, manager_id)


async def remove_team_manager(team_id: int, slot: int):
    """Remove a manager from the team (slot 1 or 2)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if slot == 1:
            await conn.execute("""
                UPDATE team_staff
                SET manager_1_id = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE team_id = $1
            """, team_id)
        else:  # slot 2
            await conn.execute("""
                UPDATE team_staff
                SET manager_2_id = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE team_id = $1
            """, team_id)


async def get_team_staff(team_id: int) -> Dict[str, Any]:
    """Get all staff members for a team (managers and coach) from team_staff table."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        staff = await conn.fetchrow("""
            SELECT 
                ts.coach_id,
                ts.manager_1_id,
                ts.manager_2_id,
                c.ign as coach_ign,
                m1.ign as manager_1_ign,
                m2.ign as manager_2_ign
            FROM team_staff ts
            LEFT JOIN players c ON ts.coach_id = c.discord_id
            LEFT JOIN players m1 ON ts.manager_1_id = m1.discord_id
            LEFT JOIN players m2 ON ts.manager_2_id = m2.discord_id
            WHERE ts.team_id = $1
        """, team_id)
        
        if not staff:
            return {}
        
        return dict(staff)

