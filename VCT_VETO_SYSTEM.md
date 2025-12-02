# VCT-Style Map Veto System

## Overview
The bot now implements a professional VCT (Valorant Champions Tour) style map veto system with distinct ban/pick phases, side selection for picked maps, and coin toss for decider maps.

---

## Veto Formats

### BO1 (Best of 1)
**Sequence:**
1. Team A bans
2. Team B bans
3. Team A bans
4. Team B bans
5. Team A bans
6. Team B bans
7. **Remaining map = Decider**
8. Coin toss for side selection

**Result:** 1 map with coin toss for sides

---

### BO3 (Best of 3)
**Sequence:**
1. Team A bans
2. Team B bans
3. Team A picks Map 1 (chooses side)
4. Team B picks Map 2 (chooses side)
5. Team A bans
6. Team B bans
7. **Remaining map = Decider**
8. Coin toss for side selection

**Result:** 3 maps (2 picks with chosen sides + 1 decider with coin toss)

---

### BO5 (Best of 5)
**Sequence:**
1. Team A bans
2. Team B bans
3. Team A picks Map 1 (chooses side)
4. Team B picks Map 2 (chooses side)
5. Team A picks Map 3 (chooses side)
6. Team B picks Map 4 (chooses side)
7. **Remaining map = Decider**
8. Coin toss for side selection

**Result:** 5 maps (4 picks with chosen sides + 1 decider with coin toss)

---

## Team Designation
- **Team A** = Coin toss winner (goes first in veto)
- **Team B** = Coin toss loser (goes second in veto)

---

## How It Works

### 1. Ban Phase
- Acting team captain receives DM with 🚫 red ban buttons
- Other captain sees waiting message
- Banned map is removed from pool
- Both captains notified of the ban

### 2. Pick Phase  
- Acting team captain receives DM with ✅ green pick buttons
- After picking, captain immediately chooses side (⚔️ Attack or 🛡️ Defense)
- Other captain automatically gets opposite side
- Both captains notified of pick and sides

### 3. Decider Map
- Last remaining map automatically becomes decider
- **Coin toss** determines which team chooses side (NOT knife round)
- Toss winner picks Attack or Defense
- Both teams notified of result

### 4. Final Summary
Beautiful embed showing:
- Team names (Team A vs Team B)
- All banned maps
- Map pool with sides:
  - Picked maps show which team starts on which side
  - Decider map shows coin toss result

---

## Map Pool
- Ascent
- Bind
- Breeze
- Fracture
- Haven
- Icebox
- Split

---

## Technical Implementation

### Key Functions
- `start_banning_maps()` - Initializes veto with format-specific sequence
- `process_next_veto_step()` - State machine handling ban/pick/decider flow
- `send_veto_ui()` - Sends ban or pick buttons to acting captain
- `handle_veto_action()` - Processes ban/pick selections
- `handle_side_selection()` - Records side choice for picked maps
- `do_coin_toss_for_decider()` - Random toss for decider map
- `handle_decider_side_selection()` - Records side from coin toss winner
- `finalize_veto()` - Shows final summary and notifies LFS channel

### View Classes
- `MapVetoView` - Universal view for ban/pick actions (color-coded buttons)
- `SideSelectionView` - Two-button view for Attack/Defense choice
- `MapBanView` - Legacy view kept for compatibility

### State Tracking
Each match stores:
```python
match_data = {
    'toss_winner': captain_id,
    'toss_loser': captain_id,
    'team_a_id': winner_id,  # Team A
    'team_b_id': loser_id,   # Team B
    'team_a_name': name,
    'team_b_name': name,
    'format': 'bo1/bo3/bo5',
    'banned_maps': [],
    'picked_maps': [(map, team, side), ...],
    'decider_map': name,
    'veto_step': 0,
    'sides': {map: {'picker': id, 'side': side}},
    'available_maps': [...],
    'veto_sequence': [('ban', 'A'), ('ban', 'B'), ...]
}
```

---

## User Experience

### Captain Perspective
1. Win/lose coin toss → designated Team A or B
2. Receive veto prompts in sequence
3. Click ban (red) or pick (green) buttons
4. For picks: immediately choose Attack or Defense
5. For decider: coin toss winner chooses side
6. Receive final summary with all maps and sides

### Display
All messages use Discord embeds with:
- 🚫 for bans
- ✅ for picks
- ⚔️ for Attack
- 🛡️ for Defense
- 🪙 for coin toss
- Color-coded buttons (red=ban, green=pick, danger=Attack, primary=Defense)

---

## Example BO3 Veto Flow

1. **Team A bans Fracture** → 6 maps left
2. **Team B bans Split** → 5 maps left  
3. **Team A picks Ascent, chooses Attack** → Map 1: Ascent (Team A: Attack, Team B: Defense)
4. **Team B picks Haven, chooses Defense** → Map 2: Haven (Team B: Defense, Team A: Attack)
5. **Team A bans Icebox** → 2 maps left
6. **Team B bans Bind** → 1 map left
7. **Breeze = Decider** → Coin toss
8. **Coin toss: Team A wins, chooses Attack** → Map 3: Breeze (Team A: Attack, Team B: Defense)

**Final Map Pool:**
- Map 1: Ascent (Team A starts Attack)
- Map 2: Haven (Team B starts Defense)
- Map 3: Breeze (Decider - Team A starts Attack via coin toss)

---

## Deployment

### Pull Changes on Raspberry Pi
```bash
cd ~/valorant-mobile-india
git pull origin main
sudo systemctl restart valorant-bot
```

### Verify
- Check bot is online
- Test scrim matching with all 3 formats
- Verify ban/pick buttons work
- Verify side selection works
- Verify coin toss works for decider
- Verify final summary shows correctly

---

## Notes
- Old knife round system **removed** - now uses coin toss
- Decider map side selection is **random** (50/50)
- All veto actions are **private** (DMs only)
- Final summary sent to both captains AND LFS channel
- System supports all 3 competitive formats correctly
