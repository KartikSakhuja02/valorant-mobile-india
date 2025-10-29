# Fix Applied: Profile Match History Error

## Issue
When running the profile command, you encountered:
```
AttributeError: 'str' object has no attribute 'get'
```

## Root Cause
The database query returns the `players` field as a **JSON string**, not as a Python list. The PostgreSQL `json_agg()` function creates JSON data, but when retrieved by asyncpg, it comes back as a string that needs to be parsed.

## Solution Applied

### Before (Broken):
```python
for player in match_data.get('players', []):
    if player.get('player_id') == member.id:  # ERROR: player is a string!
        player_match_data = player
        break
```

### After (Fixed):
```python
# Parse players JSON if it's a string
players = match_data.get('players', [])
if isinstance(players, str):
    players = json.loads(players)

# Now iterate over parsed list
for player in players:
    if player.get('player_id') == member.id:  # Works! player is now a dict
        player_match_data = player
        break
```

## Code Location
**File:** `cogs/profiles.py`  
**Lines:** Around 245-260 (in the match history loop)

## What Changed
1. Added check to see if `players` is a string
2. If it's a string, parse it using `json.loads()`
3. Now the loop iterates over actual dictionaries instead of strings

## Testing
To test the fix:
1. Reload your bot
2. Do `/profile` command
3. Match history should now display correctly with:
   - Map images
   - Agent icons (circular)
   - Team scores (green for wins, red for losses)
   - K/D/A stats (yellow)
   - Map names (colored by win/loss)

## Notes
- The `json` module is already imported at the top of the file (line 7)
- This fix applies to **all 10 matches** in the history
- The configuration from `test_profile_image.py` is correctly applied
- Black backgrounds with 3px padding are preserved

## Database Structure Reminder
The `get_player_match_history()` function in `services/db.py` returns:
```sql
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
    )
) as players
```

This creates a JSON array, which asyncpg returns as a string that must be parsed.
