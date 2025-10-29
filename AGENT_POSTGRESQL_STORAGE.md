# Agent Data PostgreSQL Storage - Implementation Summary

## Overview
Agent information is now fully integrated with the PostgreSQL database, ensuring all match data including which agent each player used is permanently stored and retrievable.

## Database Schema

### Table: `match_players`
Location: `setup_tables.py` (Line 23-36)

```sql
CREATE TABLE IF NOT EXISTS match_players (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    player_id BIGINT REFERENCES players(discord_id) ON DELETE CASCADE,
    agent VARCHAR(50),                    -- ✅ AGENT COLUMN
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    mvp BOOLEAN DEFAULT false,
    team INTEGER CHECK (team IN (1, 2)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Agent Column Details:**
- **Type:** `VARCHAR(50)` - Supports all agent names
- **Nullable:** Yes - Defaults to NULL if not provided
- **Default:** 'Unknown' when agent detection fails
- **Examples:** "Jett", "Sage", "Phoenix", "Reyna", etc.

## Data Flow

### 1. Match Scanning (`/scan`)
```
Screenshot → Gemini AI → JSON with agents → Database Storage
```

**Process:**
1. User uploads screenshot
2. Gemini AI extracts: IGN, Agent, K/D/A
3. OCR creates player_data with agent field
4. `save_match_results()` inserts into database

### 2. Database Insert
Location: `services/db.py` - `save_match_results()` function

```python
# Extract agent with default fallback
agent = player.get('agent', 'Unknown')

# Insert into database
await conn.execute("""
    INSERT INTO match_players 
    (match_id, player_id, agent, kills, deaths, assists, score, mvp, team)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
""", match['id'], player['discord_id'], agent,
     player['kills'], player['deaths'], player['assists'],
     player['score'], player['mvp'], player['team'])
```

**Key Features:**
- ✅ Defaults to 'Unknown' if agent not detected
- ✅ Stores exact agent name from AI detection
- ✅ Part of transaction (rolls back on error)
- ✅ Automatically links to match and player

### 3. Data Retrieval
Location: `services/db.py` - Query functions

```python
# Get player match history with agents
SELECT m.id, m.team1_score, m.team2_score, m.map_name,
       mp.agent, mp.kills, mp.deaths, mp.assists, mp.score,
       mp.mvp, mp.team, m.created_at
FROM matches m
JOIN match_players mp ON m.id = mp.match_id
WHERE mp.player_id = $1
ORDER BY m.created_at DESC
```

## Code Updates Made

### 1. OCR Cog (`cogs/ocr.py`)
Updated all player_data dictionaries to include agent with fallback:

**Lines Updated:**
- Line 973: Team A processing
- Line 990: Team B processing  
- Line 1151: Match data Team A
- Line 1171: Match data Team B
- Line 1270: Fallback Team A
- Line 1289: Fallback Team B

**Change:**
```python
# Before
'agent': p.get('agent')

# After
'agent': p.get('agent', 'Unknown')
```

### 2. Database Service (`services/db.py`)
Updated save function to handle missing agent data:

**Lines Updated:**
- Lines 355-358: Added default handling

**Change:**
```python
# Extract agent with default
agent = player.get('agent', 'Unknown')

# Use in INSERT
..., agent, ...
```

## Data Examples

### Stored in Database
```sql
-- Example match_players record
{
    id: 1,
    match_id: 42,
    player_id: 123456789012345678,
    agent: "Jett",
    kills: 16,
    deaths: 10,
    assists: 7,
    score: 850,
    mvp: true,
    team: 1,
    created_at: "2025-10-19 14:30:00"
}
```

### Retrieved from Database
```python
{
    'agent': 'Jett',
    'ign': 'PlayerName',
    'kills': 16,
    'deaths': 10,
    'assists': 7,
    'mvp': True,
    'team': 1
}
```

## Query Examples

### Get All Matches with Agent Data
```sql
SELECT 
    p.ign,
    mp.agent,
    mp.kills,
    mp.deaths,
    mp.assists,
    m.map_name,
    m.created_at
FROM match_players mp
JOIN players p ON mp.player_id = p.discord_id
JOIN matches m ON mp.match_id = m.id
ORDER BY m.created_at DESC;
```

### Get Agent Usage Statistics
```sql
SELECT 
    mp.agent,
    COUNT(*) as times_played,
    AVG(mp.kills) as avg_kills,
    AVG(mp.deaths) as avg_deaths,
    SUM(CASE WHEN mp.mvp THEN 1 ELSE 0 END) as mvp_count
FROM match_players mp
WHERE mp.player_id = ?
GROUP BY mp.agent
ORDER BY times_played DESC;
```

### Get Most Popular Agents
```sql
SELECT 
    agent,
    COUNT(*) as pick_count,
    ROUND(AVG(kills), 2) as avg_kills,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM match_players), 2) as pick_rate
FROM match_players
WHERE agent != 'Unknown'
GROUP BY agent
ORDER BY pick_count DESC
LIMIT 10;
```

## Features Enabled by Database Storage

### Current Features
✅ Match history shows agents per player
✅ Agents stored permanently with match data
✅ Can query historical agent usage
✅ MVP tracking includes agent played

### Potential Future Features
🔮 Player agent statistics (most played, win rate per agent)
🔮 Team composition analysis
🔮 Meta reports (agent popularity over time)
🔮 Agent performance comparisons
🔮 Player agent proficiency rankings
🔮 Match filtering by agent picks

## Error Handling

### Missing Agent Data
```python
# In OCR extraction
agent = player.get('agent', 'Unknown')

# In database save
agent = player.get('agent', 'Unknown')
```

**Result:** Always stores a value, never NULL

### AI Detection Failure
- Agent shows as "Unknown"
- Match still saves successfully
- Can be manually corrected later

### Database Errors
- Part of transaction (all or nothing)
- Rollback on failure
- Error logged to console

## Migration Notes

### For Existing Data
If you have existing matches without agent data:

```sql
-- Set default for old matches
UPDATE match_players 
SET agent = 'Unknown' 
WHERE agent IS NULL;
```

### Schema Check
Verify agent column exists:
```sql
-- Check column exists
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'match_players' 
AND column_name = 'agent';
```

## Testing

### Verify Agent Storage
1. Scan a match with `/scan`
2. Check database:
```sql
SELECT agent, ign, kills, deaths, assists 
FROM match_players 
ORDER BY id DESC 
LIMIT 10;
```

3. View match history with `/matches`
4. Confirm agents appear in display

### Test Queries
```sql
-- Count matches with agent data
SELECT 
    COUNT(*) as total_matches,
    COUNT(CASE WHEN agent != 'Unknown' THEN 1 END) as with_agents,
    COUNT(CASE WHEN agent = 'Unknown' THEN 1 END) as without_agents
FROM match_players;
```

## Performance

### Indexed Columns
- `match_id` - Fast match lookups
- `player_id` - Fast player queries
- `created_at` - Fast date-based queries

### Storage Impact
- Agent name: ~10-20 bytes per player
- Negligible impact on database size
- No performance degradation

## Conclusion

Agent data is now fully integrated into the PostgreSQL database:
- ✅ Stored during match scanning
- ✅ Retrieved in match history
- ✅ Available for analytics
- ✅ Error-resistant with defaults
- ✅ Part of transactional saves

All agent information is permanently stored and can be used for current displays and future features like agent statistics and meta analysis.
