# Agent Detection Implementation Guide

## Overview
The bot now detects and displays which agent each player used during matches when scanning scoreboard screenshots.

## What Was Changed

### 1. Updated Gemini AI Prompt (`cogs/ocr.py`)
**Location:** Line 362 - `PROMPT_TEMPLATE`

**Changes Made:**
- Added agent detection instructions to the Gemini prompt
- Provided list of all available VALORANT agents
- Instructed AI to identify agents from the circular portrait icons in each player row
- Returns agent name in JSON format along with IGN and stats

**Example Output:**
```json
{
  "players": [
    {"ign":"PlayerName", "agent":"Jett", "kills":16, "deaths":10, "assists":7},
    {"ign":"Player2", "agent":"Sage", "kills":13, "deaths":8, "assists":4}
  ]
}
```

### 2. Updated Match Display Format (`cogs/ocr.py`)
**Location:** Lines 1078-1120 - `format_player_line` function

**Changes Made:**
- Added `agent = p.get('agent', 'Unknown')` to extract agent from player data
- Updated display format to show: `PlayerName (Agent) • K/D/A • Points`

**Display Examples:**
- Registered player: `✅ **Chiku.Zr** (Jett) • 16/10/7 • 1250 pts (+40)`
- Unregistered player: `❌ PlayerName (Sage) • 13/8/4`

### 3. Match History Already Supports Agents
**Location:** `cogs/match_history.py` - Lines 68-79

The match history display was already configured to show agents:
```python
f"{mvp_star}`{p['agent']:<10}` {p['ign']:<20} {p['kills']}/{p['deaths']}/{p['assists']}"
```

**Display Format:**
```
⭐`Jett      ` PlayerName           16/10/7
  `Sage      ` Player2              13/8/4
```

## How It Works

### Scanning Process
1. User uploads scoreboard screenshot using `/scan`
2. Image is sent to Gemini AI with updated prompt
3. AI identifies:
   - Each player's agent from the circular portrait icon
   - Player IGN
   - K/D/A stats
   - Map and score
4. Data is returned as JSON with agent information included

### Data Flow
```
Screenshot → Gemini AI → JSON (with agents) → Database → Display
```

### Database Storage
Agent information is stored in the `match_players` table:
- Column: `agent` (TEXT)
- Example values: "Jett", "Sage", "Phoenix", etc.

## Supported Agents

The AI is trained to recognize all VALORANT agents:

**Duelists:**
- Jett, Phoenix, Reyna, Raze, Yoru, Neon, Iso

**Initiators:**
- Sova, Breach, Skye, KAY/O, Fade, Gekko

**Controllers:**
- Brimstone, Omen, Viper, Astra, Harbor, Clove

**Sentinels:**
- Sage, Cypher, Killjoy, Chamber, Deadlock, Vyse

## Display Locations

### 1. Match Scan Results (`/scan`)
Shows agents immediately after scanning:
```
📊 MATCH RESULTS

Score: 13 - 9
Status: Team A wins
Players: 5 registered • 5 unregistered

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🟢 Team A 🏆
⭐ ✅ **Chiku.Zr** (Jett) • `16/10/7` • 1250 pts `(+40)`
✅ **Andyyyyy** (Sage) • `13/8/4` • 980 pts `(+30)`
✅ **DarkWiz.Zr** (Phoenix) • `13/8/6` • 1100 pts `(+32)`
✅ **Kan4Ki** (Reyna) • `12/13/3` • 890 pts `(+27)`
✅ **SPNX.kirmada** (Raze) • `12/10/2` • 950 pts `(+26)`

### 🔴 Team B
❌ Remz.Zr (Omen) • `9/9/8`
❌ Fateh.Zr (Brimstone) • `8/9/4`
❌ Zanis7 (Viper) • `6/13/4`
❌ Ir0nic (Cypher) • `7/13/2`
❌ ~ZensU (Sova) • `7/10/1`
```

### 2. Match History (`/matches`)
Shows agents in historical match data:
```
Match on Ascent
Score: 13 - 9
📅 2025-10-19 at 14:30

🔵 Team 1 (13)
⭐`Jett      ` Chiku.Zr            16/10/7
  `Sage      ` Andyyyyy            13/8/4
  `Phoenix   ` DarkWiz.Zr          13/8/6

🔴 Team 2 (9)
  `Omen      ` Remz.Zr             9/9/8
  `Brimstone ` Fateh.Zr            8/9/4
```

### 3. Match Logs (Admin Channel)
Logs include MVP information which shows which agent the MVP played:
```
📊 New Match Recorded
━━━━━━━━━━━━━━━━━━━━━━━
Map: Ascent
Score: 13 - 9
Winner: Team 1 🔵
MVP: Chiku.Zr
Players: 10
Scanned By: @ModeratorName
```

## Fallback Behavior

If the AI cannot identify an agent:
- Agent field will show: `"Unknown"`
- Display will show: `PlayerName (Unknown) • K/D/A`
- Match will still be saved successfully

## Benefits

1. **Better Match Analysis**: See team compositions and agent picks
2. **Agent Performance Tracking**: Can analyze which agents players perform best on
3. **Meta Insights**: Track which agents are most popular
4. **Complete Match Records**: Historical data now includes agent information
5. **Professional Display**: Matches look more complete and informative

## Testing

To test agent detection:
1. Upload a scoreboard screenshot using `/scan`
2. Check that each player line shows their agent in parentheses
3. Use `/matches` to verify agents are displayed in history
4. Check database to confirm agents are stored correctly

**Example Test:**
```sql
SELECT ign, agent, kills, deaths, assists 
FROM match_players 
WHERE match_id = 1;
```

## Troubleshooting

**Agents showing as "Unknown"?**
- Screenshot quality might be too low
- Agent portraits might be obscured
- AI might need clearer examples
- This is expected occasionally and won't break functionality

**Agents not displaying?**
- Check database has `agent` column in `match_players` table
- Verify Gemini API is working correctly
- Check OCR extraction logs for errors

**Wrong agent detected?**
- Agent portraits can be similar (especially for new players)
- Can be manually corrected in future versions
- Consider adding agent correction buttons (like IGN correction)

## Future Enhancements

Potential improvements:
- ✨ Add agent correction buttons (similar to IGN correction)
- ✨ Track agent win rates per player
- ✨ Show most played agents in `/profile`
- ✨ Add agent-specific statistics
- ✨ Team composition analysis
- ✨ Agent pick/ban tracking
- ✨ Meta reports showing agent popularity

## Technical Details

**Database Schema:**
```sql
-- match_players table includes:
agent TEXT  -- Agent name (e.g., "Jett", "Sage")
```

**JSON Response Format:**
```json
{
  "map": "Ascent",
  "score": {"top": 13, "bottom": 9},
  "players": [
    {
      "ign": "PlayerName",
      "agent": "Jett",
      "kills": 16,
      "deaths": 10,
      "assists": 7
    }
  ]
}
```

**Display Format:**
- Scan results: `PlayerName (Agent) • K/D/A • Points`
- Match history: `` `Agent      ` PlayerName            K/D/A ``

## Conclusion

Agent detection is now fully integrated into the match scanning and display system. The AI automatically identifies agents from scoreboard screenshots, and this information is stored in the database and displayed in all relevant locations (scan results, match history, logs).
