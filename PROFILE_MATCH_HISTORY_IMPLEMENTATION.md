# Profile Match History Implementation

## Overview
The profile system has been updated to display the last 10 matches with visual elements including map images, agent icons, scores, K/D/A stats, and map names.

## Changes Made

### 1. Font Update
- **Changed from:** `Lato-Bold.ttf`
- **Changed to:** `Poppins-Bold.ttf`
- **Location:** `cogs/profiles.py` line 39

### 2. Match History Display
- **Number of matches:** 10 (increased from 5)
- **Database query:** Fetches last 10 matches using `db.get_player_match_history(member.id, limit=10)`

### 3. Configuration System
Each match has individual configuration for:
- **Map Image:** Position (X, Y offset), Width, Height
- **Agent Icon:** Position (X, Y offset), Size
- **Score Text:** Position (X, Y offset), Font size
- **K/D/A Text:** Position (X, Y offset), Font size
- **Map Name Text:** Position (X, Y offset), Font size

#### Match Layout Configuration
```python
# Matches 1-4: Custom positioned (top row)
FIRST:   map_x=300,  agent_x=320,  score_x=475,  kda_x=329,  map_name_x=450
SECOND:  map_x=635,  agent_x=655,  score_x=800,  kda_x=660,  map_name_x=795
THIRD:   map_x=970,  agent_x=1000, score_x=1140, kda_x=1002, map_name_x=1120
FOURTH:  map_x=1310, agent_x=1330, score_x=1490, kda_x=1335, map_name_x=1465

# Matches 5-10: Standard layout (if visible)
FIFTH through TENTH: map_x=100, agent_x=220, score_x=320, kda_x=470, map_name_x=650
```

### 4. Visual Features

#### Black Backgrounds for Text
All text elements have black backgrounds for better visibility:
- **Score Background Padding:** 3 pixels
- **K/D/A Background Padding:** 3 pixels  
- **Map Name Background Padding:** 3 pixels

#### Color Coding
- **Win Color:** `#00ff00` (Green) - Used for score and map name when player wins
- **Loss Color:** `#ff0000` (Red) - Used for score and map name when player loses
- **K/D/A Color:** `#ffff23` (Yellow) - Always used for K/D/A text

#### Circular Agent Icons
- Agent images are masked into circles using PIL ellipse
- Transparent background (RGBA)
- Size varies per match (85px for first 4, 80px for others)

### 5. Map Images
- **Location:** `imports/maps/{map_name}.jpg`
- **Required maps:** Ascent, Bind, Haven, Split, Icebox, Breeze, Lotus
- **Fallback:** White rectangle outline if map image not found

### 6. Agent Images
- **Location:** `imports/agents images/`
- **Case-insensitive search:** Finds agent files by matching agent name
- **Fallback:** White circle outline if agent image not found

## Workflow

### 1. User does `/scan`
- Gemini Vision API detects agents and map
- Map name saved to `matches` table in database
- Agents saved to `match_players` table

### 2. User does `/profile`
- Fetches last 10 matches from database
- For each match:
  - Loads map image from `imports/maps/`
  - Loads agent icon from `imports/agents images/`
  - Calculates win/loss based on team scores
  - Draws black backgrounds for text
  - Draws colored text (green for wins, red for losses, yellow for K/D/A)
- Generates profile image with match history
- Sends image to Discord

## Database Requirements

### Matches Table
Must have these columns:
- `match_id` - Unique identifier
- `map_name` - Name of the map (from Gemini detection)
- `team1_score` - Team A final score
- `team2_score` - Team B final score
- `created_at` - Match timestamp

### Match Players Table
Must have these columns:
- `match_id` - References matches table
- `player_id` - Discord user ID
- `agent` - Agent name (from Gemini detection)
- `team` - Team letter ('A' or 'B')
- `kills` - Kill count
- `deaths` - Death count
- `assists` - Assist count

## File Structure
```
VALM/
├── cogs/
│   └── profiles.py (UPDATED - Main profile command with match history)
├── imports/
│   ├── font/
│   │   └── Poppins-Bold.ttf (Font for profile text)
│   ├── maps/
│   │   ├── Ascent.jpg
│   │   ├── Bind.jpg
│   │   ├── Haven.jpg
│   │   ├── Split.jpg
│   │   ├── Icebox.jpg
│   │   ├── Breeze.jpg
│   │   └── Lotus.jpg
│   ├── agents images/
│   │   └── (Various agent icon files)
│   └── profile/
│       └── Profile.jpg (Profile template background)
└── tools/
    └── test_profile_image.py (Test script - for alignment testing)
```

## Testing

### Test Script
Use `tools/test_profile_image.py` to test positioning:
```powershell
python tools\test_profile_image.py
```
Output: `test/test_profile.jpg`

### Configuration Adjustment
To adjust positioning in production:
1. Open `cogs/profiles.py`
2. Find the `match_configs` array (around line 165)
3. Modify X positions, Y offsets, sizes, or font sizes
4. Reload the bot to apply changes

## Next Steps

### 1. Add Missing Map Images
Currently only `Ascent.jpg` exists. Add the remaining 6 maps:
- `Bind.jpg`
- `Haven.jpg`
- `Split.jpg`
- `Icebox.jpg`
- `Breeze.jpg`
- `Lotus.jpg`

Location: `imports/maps/`

### 2. Test with Real Data
1. Do `/scan` on a match screenshot
2. Verify map and agents are saved to database
3. Do `/profile` to see match history
4. Check positioning and adjust if needed

### 3. Adjust Padding (Optional)
In `cogs/profiles.py`, find these lines (around line 161):
```python
SCORE_BG_PADDING = 3
KDA_BG_PADDING = 3
MAP_NAME_BG_PADDING = 3
```
Increase numbers for thicker backgrounds, decrease for thinner.

## Troubleshooting

### Issue: Text not visible
- **Solution:** Increase padding values (SCORE_BG_PADDING, etc.)

### Issue: Map image not showing
- **Check:** File exists at `imports/maps/{map_name}.jpg`
- **Check:** Map name in database matches file name exactly
- **Check:** File is a valid JPG image

### Issue: Agent icon not showing
- **Check:** Agent files exist in `imports/agents images/`
- **Check:** Agent name in database matches file name (case-insensitive)
- **Check:** Agent images are valid image files

### Issue: Positioning is off
- **Solution:** Use test script to adjust positions
- **Solution:** Modify `match_configs` array in profiles.py

### Issue: Font error
- **Check:** `imports/font/Poppins-Bold.ttf` exists
- **Fallback:** Change back to `Lato-Bold.ttf` if needed

## Notes
- All positioning uses absolute pixel values
- Y offsets can be negative (matches 2-4 use negative offsets)
- Configuration matches test script exactly (test_profile_image.py)
- Black backgrounds use `textbbox` for precise text bounds
- Circular masking uses PIL ellipse for smooth edges
