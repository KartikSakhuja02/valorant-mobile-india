# Agent Detection Feature

## Overview
The bot now automatically detects which agent each player used in a match by analyzing the agent portrait icons in the scoreboard screenshot using Gemini AI.

## How It Works

### 1. **AI-Powered Detection**
When you use `/scan` with a match screenshot, the Gemini AI:
- Identifies the circular agent portrait icons on the left side of each player row
- Recognizes which VALORANT agent each portrait represents
- Extracts the agent name along with player IGN and stats

### 2. **Supported Agents**
The system can detect all VALORANT agents:

**Duelists:**
- Jett, Phoenix, Reyna, Raze, Yoru, Neon, Iso

**Initiators:**
- Sova, Breach, Skye, KAY/O, Fade, Gekko

**Controllers:**
- Brimstone, Omen, Viper, Astra, Harbor, Clove

**Sentinels:**
- Sage, Cypher, Killjoy, Chamber, Deadlock, Vyse

### 3. **Display Format**

When you scan a match, players are displayed as:
```
✅ **PlayerName** (Jett) • `16/10/7` • 1234 pts `(+34)`
✅ **AnotherPlayer** (Sage) • `13/8/4` • 987 pts `(+28)`
```

Format breakdown:
- ✅/❌ - Registration status
- **PlayerName** - In-game name
- **(Agent)** - Agent they played
- `K/D/A` - Kill/Death/Assist stats
- Points and match points (for registered players)

### 4. **Database Storage**
Agent information is stored in the PostgreSQL database:
- **Table:** `match_players`
- **Column:** `agent` (VARCHAR(50))
- Stored along with other match stats (kills, deaths, assists, etc.)

## Match History
When viewing match history with `/matches`, agents are displayed in a formatted table:
```
⭐ Jett          PlayerName           16/10/7
  Sage          OtherPlayer          13/8/4
  Phoenix       ThirdPlayer          12/9/5
```

## Features

### ✅ Automatic Detection
- No manual input required
- AI identifies agents from portrait icons
- Works with any screenshot resolution

### ✅ Fallback Handling
- If agent can't be detected, shows "Unknown"
- Manual correction available through admin commands (future feature)

### ✅ Complete Integration
- Agents saved to database with match results
- Displayed in match scans
- Shown in match history
- Included in match logs

## Example Output

### During Match Scan:
```
## 📊 MATCH RESULTS

**Score:** 13 - 11
**Status:** Team A wins
**Players:** 8 registered • 2 unregistered

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🟢 Team A 🏆
⭐ ✅ **Chiku.Zr** (Jett) • `16/10/7` • 2450 pts `(+39)`
✅ **Andyyyyy** (Sage) • `13/8/4` • 1876 pts `(+30)`
✅ **DarkWiz.Zr** (Phoenix) • `13/8/6` • 1923 pts `(+32)`
✅ **Kan4Ki** (Reyna) • `12/13/3` • 1654 pts `(+27)`
✅ **SPNX.kirmada** (Raze) • `12/10/2` • 1589 pts `(+26)`

### 🔴 Team B
⭐ ✅ **Remz.Zr** (Omen) • `9/9/8` • 1234 pts `(+26)`
✅ **Fateh.Zr** (Brimstone) • `8/9/4` • 1098 pts `(+20)`
❌ Zanis7 (Viper) • `6/13/4`
❌ Ir0nic (Cypher) • `7/13/2`
✅ **~ZensU** (Sova) • `7/10/1` • 876 pts `(+15)`
```

### In Match History:
```
Match on Ascent
Score: 13 - 11
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔵 Team 1 (13)
⭐ Jett          Chiku.Zr             16/10/7
  Sage          Andyyyyy             13/8/4
  Phoenix       DarkWiz.Zr           13/8/6
  Reyna         Kan4Ki               12/13/3
  Raze          SPNX.kirmada         12/10/2

🔴 Team 2 (11)
⭐ Omen          Remz.Zr              9/9/8
  Brimstone     Fateh.Zr             8/9/4
  Viper         Zanis7               6/13/4
  Cypher        Ir0nic               7/13/2
  Sova          ~ZensU               7/10/1
```

## Technical Details

### Gemini AI Prompt
The AI is instructed to:
1. Focus on circular portrait icons
2. Identify agent from icon appearance
3. Use exact agent name spelling
4. Fall back to "Unknown" if unclear

### Data Flow
```
Screenshot → Gemini AI → JSON with agents → Database → Display
```

### JSON Structure
```json
{
  "map": "Ascent",
  "score": {"top": 13, "bottom": 11},
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

## Benefits

1. **Better Match Context**: Know which agents were played
2. **Strategy Analysis**: See agent composition per team
3. **Player Preferences**: Track which agents players use most
4. **Complete Records**: Full match data with agent information

## Future Enhancements

Potential features to add:
- Agent performance statistics per player
- Most played agents leaderboard
- Team composition analysis
- Agent win rate tracking
- Agent-specific MVPs

## Troubleshooting

**Agent shows as "Unknown":**
- Screenshot quality might be too low
- Agent icon might be obscured or cropped
- New agent not yet in AI training data
- Solution: Gemini will do its best, but some edge cases may occur

**Wrong agent detected:**
- Similar looking agent icons might be confused
- Screenshot resolution affects accuracy
- Solution: Manual correction available (contact admin)

## Notes

- Agent detection uses the same Gemini AI that reads player stats
- No additional API calls or costs
- Works automatically with existing `/scan` command
- Agent images folder is for future reference only
