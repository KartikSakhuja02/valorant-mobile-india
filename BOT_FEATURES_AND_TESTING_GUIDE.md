# 🎮 VALORANT Mobile India Tournament Bot - Complete Features & Testing Guide

## 📋 Table of Contents
- [Setup & Running the Bot](#setup--running-the-bot)
- [Testing Prerequisites](#testing-prerequisites)
- [Feature Categories](#feature-categories)
  - [1. Player Registration System](#1-player-registration-system)
  - [2. Team Management System](#2-team-management-system)
  - [3. Team Staff Management](#3-team-staff-management)
  - [4. Profile & Statistics](#4-profile--statistics)
  - [5. Match Scanning (OCR)](#5-match-scanning-ocr)
  - [6. Scrim/LFS System](#6-scrimlfs-system)
  - [7. Leaderboards](#7-leaderboards)
  - [8. Admin Commands](#8-admin-commands)
  - [9. Utility Features](#9-utility-features)
- [Database Schema](#database-schema)
- [24/7 Deployment Checklist](#247-deployment-checklist)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Setup & Running the Bot

### 1. **Environment Setup**

#### Required Files:
- `.env` file with all configuration (see template below)
- `config.json` (optional fallback)
- PostgreSQL database

#### `.env` Template:
```env
# Discord Bot Token
TOKEN=your_bot_token_here

# Guild/Server Configuration
GUILD_ID=your_guild_id

# Channel Configuration
LOG_CHANNEL_ID=your_log_channel_id
BOT_COMMANDS_CHANNEL_ID=your_bot_commands_channel_id
LFS_CHANNEL_ID=your_lfs_channel_id
CHANNEL_PLAYER_REG_ID=your_player_registration_channel_id
CHANNEL_TEAM_REG_ID=your_team_registration_channel_id
CHANNEL_PLAYER_FORCE_REG_ID=your_admin_player_reg_channel_id
CHANNEL_TEAM_INTERACTIVE_REG_ID=your_admin_team_reg_channel_id

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# API Keys
GEMINI_API_KEY=your_gemini_api_key

# Role IDs
ROLE_STAFF_ID=your_staff_role_id
ROLE_MODERATOR_ID=your_moderator_role_id
ROLE_ADMINISTRATOR_ID=your_administrator_role_id
INDIA_ROLE_ID=your_india_role_id
ROLE_APAC_ID=your_apac_role_id
ROLE_EMEA_ID=your_emea_role_id
ROLE_AMERICAS_ID=your_americas_role_id
```

### 2. **Install Dependencies**
```powershell
# Install Python packages
pip install -r requirements.txt

# Required packages:
# - discord.py >= 2.6.4
# - asyncpg
# - Pillow
# - opencv-python
# - numpy
# - aiohttp
# - python-dotenv
# - pandas
# - google-generativeai
```

### 3. **Database Setup**
```powershell
# Initialize database (creates tables)
python scripts/init_db.py

# Run migrations if needed
python scripts/migrate.py
```

### 4. **Run the Bot**
```powershell
# Start the bot
python bot.py

# Expected output:
# ✅ Registered persistent views
# Loaded X cogs
# Logged in as BotName
# Synced X slash commands
```

---

## 🧪 Testing Prerequisites

### Required Test Accounts:
1. **Admin Account** - For testing admin commands
2. **Regular User Accounts (3-10)** - For testing player registration, teams, scrims
3. **Test Server** - Discord server with all channels configured

### Required Assets:
1. **Profile Screenshots** - Valid VALORANT Mobile profile images
2. **Match Screenshots** - Valid scoreboard screenshots for OCR testing
3. **Team Logo Images** - For team logo testing

### Test Data Checklist:
- [ ] At least 5 registered players
- [ ] At least 2 registered teams (5+ players each)
- [ ] Sample match data in database
- [ ] Test LFS channel with permissions

---

## 📚 Feature Categories

## 1. Player Registration System

### **A. Interactive Registration (UI Buttons)**

**Commands:**
- `/register` - Shows registration UI with buttons

**Features:**
- **Screenshot Registration** - Upload profile screenshot for auto-detection
- **Manual Registration** - Enter IGN, ID, and region manually

**How to Test:**

1. **Screenshot Registration:**
```
Step 1: Run /register in player registration channel
Step 2: Click "Screenshot Registration" button
Step 3: Bot creates private thread
Step 4: Upload valid VALORANT Mobile profile screenshot
Step 5: Bot auto-detects IGN and Player ID using OCR
Step 6: Confirm or edit the detected information
Step 7: Select region (NA/EU/AP/KR/BR/LATAM/JP)
Step 8: Select if you have India role (if applicable)
Step 9: Bot saves to database and assigns region role

Expected: 
- ✅ Thread created with staff auto-added
- ✅ OCR detects IGN and ID correctly
- ✅ Region role assigned
- ✅ Player saved in database
```

2. **Manual Registration:**
```
Step 1: Run /register in player registration channel
Step 2: Click "Manual Registration" button
Step 3: Enter IGN when prompted
Step 4: Enter Player ID (numeric) when prompted
Step 5: Select region from buttons
Step 6: Confirm registration

Expected:
- ✅ Thread created
- ✅ All information collected
- ✅ Player registered successfully
```

**Edge Cases to Test:**
- ❌ Already registered user (should reject)
- ❌ Invalid screenshot format
- ❌ Timeout (10 minutes inactivity)
- ❌ Thread closure and cleanup

### **B. Registration Helpdesk**

**Features:**
- Help button for registration issues
- Staff notification system

**How to Test:**
```
Step 1: Find helpdesk message in player reg channel
Step 2: Click "Need Help?" button
Step 3: Bot creates private thread
Step 4: Staff members are auto-added and @mentioned
Step 5: User can explain issue
Step 6: Staff can assist via thread

Expected:
- ✅ Thread created with user
- ✅ All staff/mods auto-added
- ✅ Staff @mention sent
```

### **C. Update IGN**

**Command:** `/update_ign <new_ign>` (Legacy command)

**How to Test:**
```
Step 1: Register as a player
Step 2: Run /update_ign new_name_here
Step 3: Bot updates IGN in database
Step 4: Run /profile to confirm change

Expected:
- ✅ IGN updated
- ✅ Stats preserved
- ✅ Profile shows new IGN
```

### **D. Interactive Profile Editing** ⭐ NEW

**Command:** `/profile` (shows edit buttons on your own profile)

**Features:**
- **Edit IGN** - Change your in-game name
- **Edit Player ID** - Update your player ID
- **Change Region** - Switch regions (NA/EU/AP/KR/BR/LATAM/JP)
- **India Status** - Toggle India status if set incorrectly

**How to Test:**

1. **Edit IGN:**
```
Step 1: Run /profile (your own profile)
Step 2: Click "Edit IGN" button
Step 3: Modal appears with text input
Step 4: Enter new IGN
Step 5: Submit modal
Step 6: Bot updates IGN and confirms
Step 7: Run /profile again to see change

Expected:
- ✅ Modal opens
- ✅ IGN updated in database
- ✅ Confirmation message sent
- ✅ Profile shows new IGN
```

2. **Edit Player ID:**
```
Step 1: Run /profile
Step 2: Click "Edit Player ID" button
Step 3: Enter new Player ID (numeric)
Step 4: Submit
Step 5: Bot validates and updates

Expected:
- ✅ Player ID updated
- ✅ Validates numeric input
- ❌ Rejects non-numeric input
```

3. **Change Region:**
```
Step 1: Run /profile
Step 2: Click "Change Region" button
Step 3: Bot shows region selection buttons
Step 4: Click desired region (NA/EU/AP/KR/BR/LATAM/JP)
Step 5: Bot updates region
Step 6: Buttons disable after selection

Expected:
- ✅ Region buttons appear
- ✅ Selected region saved
- ✅ Buttons disabled after selection
- ✅ Confirmation sent
```

4. **India Status:**
```
Step 1: Run /profile
Step 2: Click "India Status" button
Step 3: Bot shows current status
Step 4: Click "Yes, I'm from India" or "No, I'm not from India"
Step 5: Bot updates status

Expected:
- ✅ Current status shown
- ✅ New status saved
- ✅ Buttons disabled after selection
- ✅ Confirmation sent
```

**Important Notes:**
- ✅ Edit buttons only visible on YOUR OWN profile
- ❌ Cannot edit other players' profiles
- ✅ All changes take effect immediately
- ✅ Stats are preserved during updates
- ✅ All edits are ephemeral (only you see them)

---

## 2. Team Management System

### **A. Team Registration**

**Command:** `/register-team <name> <tag> <region>`

**Parameters:**
- `name` - Team name (unique)
- `tag` - Team tag (2-4 characters)
- `region` - Region choice (NA/EU/ASIA/SEA/LATAM/OCE)

**How to Test:**
```
Step 1: Must be registered player first
Step 2: Run /register-team name:"Team Alpha" tag:"TA" region:ASIA
Step 3: Bot creates team with you as captain
Step 4: Run /team-profile name:"Team Alpha" to verify

Expected:
- ✅ Team created
- ✅ You are captain
- ✅ Team has 0 players (captain not auto-added)
- ✅ Stats initialized to 0
```

**Edge Cases:**
- ❌ Duplicate team name
- ❌ Already in a team
- ❌ Invalid tag format

### **B. Interactive Team Registration (Admin)**

**Command:** `/register-team-interactive` (Admin only)

**Features:**
- UI-based team creation flow
- Add players during creation
- Region selection with buttons

**How to Test:**
```
Step 1: Admin runs /register-team-interactive in admin team reg channel
Step 2: Bot creates thread
Step 3: Enter team name
Step 4: Enter team tag
Step 5: Select region using buttons
Step 6: Add players one by one (mention them)
Step 7: Click "Finish" when done
Step 8: Bot creates team with all players

Expected:
- ✅ Team created
- ✅ All players added to roster
- ✅ Captain assigned
```

### **C. Invite Player**

**Command:** `/invite-player <player>`

**How to Test:**
```
Step 1: Be a team captain
Step 2: Run /invite-player @PlayerName
Step 3: Player receives DM with Accept/Decline buttons
Step 4: Player clicks Accept
Step 5: Bot adds player to team
Step 6: Run /team-profile to verify

Expected:
- ✅ Invitation sent
- ✅ Player receives DM
- ✅ Accept adds to team
- ✅ Decline cancels invitation
```

**Edge Cases:**
- ❌ Not team captain
- ❌ Player already in team
- ❌ Team full (5 players max)
- ❌ Player not registered

### **D. Leave Team**

**Command:** `/leave-team`

**How to Test:**
```
Step 1: Join a team as non-captain
Step 2: Run /leave-team
Step 3: Confirm leaving
Step 4: Bot removes you from team

Expected:
- ✅ Removed from team roster
- ✅ Team player count decreases
```

**Edge Cases:**
- ❌ Captain leaving (should prompt to transfer captaincy or disband)

### **E. Kick Player (Captain)**

**Command:** `/kick-player <player>`

**How to Test:**
```
Step 1: Be team captain
Step 2: Run /kick-player @PlayerName
Step 3: Confirm kick
Step 4: Bot removes player

Expected:
- ✅ Player removed from team
- ✅ Captain gets confirmation
```

### **F. Disband Team (Captain)**

**Command:** `/disband`

**How to Test:**
```
Step 1: Be team captain
Step 2: Run /disband
Step 3: Confirm disbanding
Step 4: Bot deletes team and removes all players

Expected:
- ✅ Team deleted
- ✅ All players removed
- ✅ Stats preserved in history
```

### **G. Set Team Logo**

**Command:** `/set-logo <logo_image>`

**How to Test:**
```
Step 1: Be team captain
Step 2: Run /set-logo and attach image file
Step 3: Bot validates image (PNG/JPG, max 8MB)
Step 4: Logo saved and displayed on team profile

Expected:
- ✅ Logo uploaded
- ✅ Shows on /team-profile
```

**Edge Cases:**
- ❌ Invalid file format
- ❌ File too large
- ❌ Not captain

---

## 3. Team Staff Management

### **A. Add Manager**

**Command:** `/add-manager <user>`

**Limits:** Max 2 managers per team

**How to Test:**
```
Step 1: Be team captain
Step 2: Run /add-manager @UserName
Step 3: User must be registered player
Step 4: Bot adds user as manager
Step 5: Run /view-staff to verify

Expected:
- ✅ Manager added
- ✅ Shows in team profile
- ✅ Max 2 managers enforced
```

### **B. Remove Manager**

**Command:** `/remove-manager <user>`

**How to Test:**
```
Step 1: Have manager on team
Step 2: Run /remove-manager @ManagerName
Step 3: Bot removes manager

Expected:
- ✅ Manager removed
- ✅ Updated in database
```

### **C. Add Coach**

**Command:** `/add-coach <user>`

**Limits:** Max 1 coach per team

**How to Test:**
```
Step 1: Be team captain
Step 2: Run /add-coach @UserName
Step 3: Bot adds coach

Expected:
- ✅ Coach added
- ✅ Shows in team profile
- ✅ Only 1 coach allowed
```

### **D. Remove Coach**

**Command:** `/remove-coach`

**How to Test:**
```
Step 1: Have coach on team
Step 2: Run /remove-coach
Step 3: Bot removes coach

Expected:
- ✅ Coach removed
```

### **E. View Staff**

**Command:** `/view-staff`

**How to Test:**
```
Step 1: Be in a team
Step 2: Run /view-staff
Step 3: Bot shows managers and coach

Expected:
- ✅ Lists all staff with IGNs
- ✅ Shows empty slots if none
```

---

## 4. Profile & Statistics

### **A. Player Profile**

**Command:** `/profile [user]`

**Features:**
- Shows player stats (K/D/A, Matches, Wins/Losses, Winrate, Points)
- Generates profile image card
- Shows region and team

**How to Test:**
```
Step 1: Register as player and play some matches
Step 2: Run /profile (shows your profile)
Step 3: Run /profile @OtherUser (shows their profile)

Expected:
- ✅ Profile image generated
- ✅ Stats displayed correctly
- ✅ K/D ratio calculated
- ✅ Winrate percentage shown
- ✅ Points total displayed
```

**Profile Image Elements:**
- IGN and Player ID
- Stats (Kills, Deaths, Assists, K/D, Matches, Wins, Losses, Winrate, Points)
- Region badge
- Team name (if in team)

### **B. Team Profile**

**Command:** `/team-profile <name>`

**Features:**
- Shows team information
- Lists all players with stats
- Shows staff (managers, coach)
- Team logo display
- Management buttons (if captain)

**How to Test:**
```
Step 1: Create team with players
Step 2: Run /team-profile name:"Team Alpha"

Expected:
- ✅ Team info shown
- ✅ All players listed
- ✅ Staff shown (managers/coach)
- ✅ Team stats (wins/losses/winrate/points)
- ✅ Captain sees management buttons
```

**Management Buttons (Captain Only):**
- **Manage Players** - Add/remove players
- **Manage Staff** - Add/remove managers/coach
- **Transfer Captain** - Transfer captaincy
- **Change Logo** - Upload new logo

**How to Test Management:**
```
Step 1: Be team captain
Step 2: Run /team-profile name:"YourTeam"
Step 3: Click "Manage Players"
Step 4: Select Add Player or Remove Player
Step 5: Follow prompts

Expected:
- ✅ Buttons only visible to captain
- ✅ Add player sends invitation
- ✅ Remove player kicks from team
- ✅ Transfer captain changes ownership
```

---

## 5. Match Scanning (OCR)

### **A. Scan Match**

**Command:** `/scan <screenshot>`

**Features:**
- Auto-detects match details using Gemini AI + Local detection
- Extracts: Team scores, player stats (K/D/A), agents, map
- Color-based team detection (cyan=Team A, red=Team B)
- Agent detection using YOLO model
- Save match to database with button

**How to Test:**
```
Step 1: Get valid VALORANT Mobile scoreboard screenshot
Step 2: Run /scan and attach screenshot
Step 3: Bot analyzes image (takes 10-30 seconds)
Step 4: Bot returns embed with all match data
Step 5: Click "Save Match" button
Step 6: Bot saves to database and updates player stats

Expected:
- ✅ Team A (cyan) detected correctly
- ✅ Team B (red) detected correctly
- ✅ All 10 players' stats extracted
- ✅ Agents identified correctly
- ✅ Map name detected
- ✅ Scores mapped correctly (left=Team A, right=Team B)
```

**OCR Detection Features:**
1. **Team Detection:** Color analysis (cyan vs red)
2. **Agent Detection:** YOLO model + template matching
3. **Text Extraction:** Gemini AI API
4. **Score Mapping:** Left score = Team A, Right score = Team B
5. **Player Stats:** K/D/A for all 10 players

**Edge Cases to Test:**
- ❌ Invalid screenshot (not a scoreboard)
- ❌ Blurry/low quality image
- ❌ Missing players
- ❌ Unregistered players (bot will notify)

### **B. Save Match**

**Button:** "Save Match" on scan results

**How to Test:**
```
Step 1: Scan a match successfully
Step 2: Click "Save Match" button (only requester can click)
Step 3: Bot validates all players are registered
Step 4: Saves match to database
Step 5: Updates all players' stats:
   - Kills, Deaths, Assists
   - Matches played
   - Wins/Losses (based on team score)
   - MVPs (highest score on winning team)
Step 6: Updates team stats if players are in teams

Expected:
- ✅ Match saved with unique ID
- ✅ All player stats updated
- ✅ Team stats updated
- ✅ Leaderboards recalculated
- ✅ Confirmation message sent
```

---

## 6. Scrim/LFS System

### **A. LFS Request (Looking For Scrim)**

**How it Works:**
- Users post in LFS channel with specific format
- Bot auto-detects and creates scrim request
- Matches teams with compatible requests

**Supported Formats:**

**Format 1 (Traditional):**
```
LFS BO3 8PM IST
APAC
```

**Format 2 (Single Line):**
```
LFS BO3 7PM IST APAC
```

**How to Test:**
```
Step 1: Be team captain
Step 2: Post in LFS channel: "LFS BO3 8PM IST APAC"
Step 3: Bot detects request
Step 4: Bot shows confirmation with options:
   - Edit format
   - Cancel request
Step 5: Bot searches for matching scrims
Step 6: Shows available matches with Accept buttons

Expected:
- ✅ Request created
- ✅ Format detected (BO1/BO3/BO5)
- ✅ Time parsed correctly
- ✅ Timezone converted (IST/EST/PST etc.)
- ✅ Region matched (APAC/EMEA/AMERICAS)
- ✅ Matching scrims shown
```

**LFS Parameters:**
- **Format:** BO1, BO3, BO5, Scrim
- **Time:** 12-hour or 24-hour format (e.g., 7PM, 19:00)
- **Timezone:** IST, EST, PST, GMT, JST, etc. (30+ supported)
- **Region:** APAC, EMEA, AMERICAS, etc.

### **B. Accept Scrim Match**

**How to Test:**
```
Step 1: Two captains post LFS with matching criteria
Step 2: Captain A receives available matches
Step 3: Captain A clicks "Accept" on Captain B's scrim
Step 4: Bot notifies Captain B
Step 5: Captain B approves
Step 6: Bot creates match thread with both captains
Step 7: Toss process begins

Expected:
- ✅ Match notification sent
- ✅ Both captains approve
- ✅ Match thread created
- ✅ Both teams added to thread
```

### **C. Match Setup Flow**

**Automated Flow:**
1. **Toss:** Heads/Tails coin flip
2. **Winner Picks:** Attack or Defense
3. **Map Veto:** VCT-style veto system (BO3/BO5)
4. **Match Confirmation:** Final details shared
5. **Results Submission:** After match completion

**How to Test Toss:**
```
Step 1: Match approved by both captains
Step 2: Bot asks Captain A to call toss
Step 3: Captain A clicks "Heads" or "Tails"
Step 4: Bot flips coin
Step 5: Winner picks Attack or Defense
Step 6: Bot confirms selection

Expected:
- ✅ Random coin flip
- ✅ Winner correctly determined
- ✅ Side selection recorded
```

**How to Test Map Veto (BO3):**
```
Step 1: After toss, veto starts
Step 2: Captain A bans 1 map
Step 3: Captain B bans 1 map
Step 4: Captain A picks Map 1
Step 5: Captain B picks Map 2
Step 6: Captain A bans 1 map
Step 7: Captain B bans 1 map
Step 8: Remaining map is Map 3
Step 9: Bot shows final map order

Expected:
- ✅ Turn-based veto
- ✅ Correct team for each turn
- ✅ Maps removed when banned
- ✅ Final 3 maps selected
```

**Map Pool:**
- Abyss
- Ascent
- Bind
- Breeze
- Fracture
- Haven
- Icebox
- Lotus
- Pearl
- Split
- Sunset

### **D. Match Results Submission**

**How to Test:**
```
Step 1: Complete match setup
Step 2: Bot reminds to submit results
Step 3: Captain uploads screenshot using /scan
Step 4: Captain clicks "Save Match"
Step 5: Bot updates stats for both teams
Step 6: Match thread closed

Expected:
- ✅ Screenshot accepted
- ✅ Stats updated
- ✅ Winner determined
- ✅ Thread archived
```

### **E. Cancel Scrim**

**Command:** `/cancel-scrim`

**How to Test:**
```
Step 1: Create LFS request
Step 2: Run /cancel-scrim
Step 3: Bot shows active requests
Step 4: Select request to cancel
Step 5: Bot cancels and notifies opponent (if matched)

Expected:
- ✅ Request cancelled
- ✅ Removed from queue
- ✅ Opponent notified
```

---

## 7. Leaderboards

### **A. Player Leaderboard**

**Command:** `/lb`

**Features:**
- Shows top players by points
- Pagination (10 players per page)
- Generated image card
- Filters banned players

**How to Test:**
```
Step 1: Have multiple registered players with stats
Step 2: Run /lb
Step 3: Bot shows leaderboard image
Step 4: Click "Next" to see page 2
Step 5: Click "Previous" to go back

Expected:
- ✅ Top 10 players shown
- ✅ Ranked by points
- ✅ Shows IGN, Matches, W/L, K/D, Points
- ✅ Pagination works
- ✅ Banned players excluded
```

**Points Calculation:**
```
Points = (Kills × 100) 
       + (Deaths × -50) 
       + (Wins × 500) 
       + (MVPs × 200) 
       + (Matches × 100)
```

### **B. Team Leaderboard**

**Note:** Team leaderboard uses same `/lb` command, region-specific

**Features:**
- India leaderboard (top 10)
- Regional leaderboards (APAC/EMEA/AMERICAS)
- Shows team name, wins, losses, winrate, points

**How to Test:**
```
Step 1: Create teams with match history
Step 2: Run /lb in India-specific channel (if configured)
Step 3: Bot shows India team leaderboard

Expected:
- ✅ Teams ranked by points
- ✅ Shows W/L record
- ✅ Winrate calculated
- ✅ Points total displayed
```

---

## 8. Admin Commands

**Permission Required:** Administrator, Staff, or Moderator role

### **A. Edit Player**

**Command:** `/edit-player <player> [new_ign] [new_id]`

**How to Test:**
```
Step 1: Be admin
Step 2: Run /edit-player @Player new_ign:"NewName" new_id:12345
Step 3: Bot updates player info
Step 4: Action logged in admin logs

Expected:
- ✅ IGN updated
- ✅ ID updated (if provided)
- ✅ Old data logged
- ✅ Confirmation sent
```

### **B. Edit K/D/A**

**Command:** `/edit-kda <player> <kills> <deaths> <assists>`

**How to Test:**
```
Step 1: Run /edit-kda @Player kills:100 deaths:50 assists:30
Step 2: Bot updates stats
Step 3: Recalculates K/D ratio

Expected:
- ✅ Stats updated
- ✅ K/D recalculated
- ✅ Profile reflects changes
```

### **C. Edit Record**

**Command:** `/edit-record <player> <matches> <wins> <losses>`

**How to Test:**
```
Step 1: Run /edit-record @Player matches:20 wins:15 losses:5
Step 2: Bot updates match record
Step 3: Winrate recalculated

Expected:
- ✅ Matches updated
- ✅ W/L updated
- ✅ Winrate recalculated
```

### **D. Delete Player**

**Command:** `/delete-player <player>`

**How to Test:**
```
Step 1: Run /delete-player @Player
Step 2: Confirm deletion
Step 3: Bot removes player from database
Step 4: Team memberships removed
Step 5: Match history preserved

Expected:
- ✅ Player deleted
- ✅ Teams updated
- ✅ Confirmation sent
- ⚠️ Match history kept for integrity
```

### **E. Ban Player**

**Command:** `/ban-player <player> [reason]`

**How to Test:**
```
Step 1: Run /ban-player @Player reason:"Cheating"
Step 2: Bot marks player as banned
Step 3: Player removed from leaderboards
Step 4: Player can still be on teams but flagged

Expected:
- ✅ Player banned
- ✅ Hidden from leaderboards
- ✅ Ban reason logged
- ✅ Still in database
```

### **F. Unban Player**

**Command:** `/unban-player <player>`

**How to Test:**
```
Step 1: Ban a player first
Step 2: Run /unban-player @Player
Step 3: Bot removes ban flag
Step 4: Player appears in leaderboards again

Expected:
- ✅ Ban removed
- ✅ Visible in leaderboards
- ✅ Action logged
```

### **G. Ban Team**

**Command:** `/ban-team <team_name> [reason]`

**How to Test:**
```
Step 1: Run /ban-team name:"Team Alpha" reason:"Match fixing"
Step 2: Bot bans entire team

Expected:
- ✅ Team banned
- ✅ Hidden from team leaderboards
- ✅ Players can still compete individually
```

### **H. Unban Team**

**Command:** `/unban-team <team_name>`

**How to Test:**
```
Step 1: Run /unban-team name:"Team Alpha"
Step 2: Bot removes team ban

Expected:
- ✅ Team unbanned
- ✅ Visible in leaderboards
```

### **I. Export Data**

**Command:** `/export-data [include_banned]`

**How to Test:**
```
Step 1: Run /export-data include_banned:True
Step 2: Bot generates Excel file with:
   - Players sheet (all player data)
   - Teams sheet (all team data)
   - Matches sheet (all match history)
Step 3: Bot sends file in channel

Expected:
- ✅ Excel file generated
- ✅ All data included
- ✅ Properly formatted sheets
```

### **J. Archive Season**

**Command:** `/archive-season <season_name>`

**How to Test:**
```
Step 1: Run /archive-season season_name:"Season 1"
Step 2: Bot creates backup of all data
Step 3: Data archived with timestamp
Step 4: Current season data preserved

Expected:
- ✅ Backup created
- ✅ Data saved with season name
- ✅ Timestamp recorded
```

### **K. Recalculate Leaderboards**

**Command:** `/recalculate-leaderboards`

**How to Test:**
```
Step 1: Run /recalculate-leaderboards
Step 2: Bot recalculates all points:
   - Player points
   - Team points
   - Rankings updated
Step 3: Confirmation sent

Expected:
- ✅ All points recalculated
- ✅ Rankings updated
- ✅ Summary shown
```

### **L. Admin Logs**

**Command:** `/admin-logs [limit]`

**How to Test:**
```
Step 1: Run /admin-logs limit:20
Step 2: Bot shows recent admin actions:
   - Who performed action
   - What action was performed
   - When it happened
   - Old data (if edit)

Expected:
- ✅ Actions listed chronologically
- ✅ User names shown
- ✅ Timestamps displayed
```

### **M. Clear Team Stats**

**Command:** `/clear-team-stats`

**How to Test:**
```
Step 1: Run /clear-team-stats
Step 2: Confirm clearing
Step 3: Bot resets all team stats to 0:
   - Wins = 0
   - Losses = 0
   - Matches = 0
   - Points = 0

Expected:
- ✅ All team stats reset
- ✅ Team rosters preserved
- ✅ Confirmation sent
- ⚠️ DESTRUCTIVE - Use carefully!
```

### **N. Force Player Registration**

**Command:** `/force_player_reg` (Admin only)

**Features:**
- Admin-assisted registration
- Screenshot or manual entry
- Bypasses normal flow

**How to Test:**
```
Step 1: Admin runs /force_player_reg in admin channel
Step 2: Bot creates private thread
Step 3: Admin enters player info or uploads screenshot
Step 4: Bot registers player

Expected:
- ✅ Admin can register any user
- ✅ OCR still works
- ✅ Player added to database
```

---

## 9. Utility Features

### **A. Command Restriction**

**Features:**
- Restricts commands to specific channel
- Slash commands only work in `BOT_COMMANDS_CHANNEL_ID`
- Admins can use commands anywhere

**How to Test:**
```
Step 1: Try /profile in random channel
Expected: ❌ "Please use commands in #bot-commands"

Step 2: Try /profile in bot-commands channel
Expected: ✅ Command works

Step 3: Admin tries command in random channel
Expected: ✅ Command works (admin bypass)
```

**Admin Command:** `!setbotchannel #channel`

### **B. Match History**

**Command:** `/matches [player] [limit]`

**How to Test:**
```
Step 1: Run /matches (shows recent matches)
Step 2: Run /matches player:@User limit:10
Step 3: Bot shows match history embeds:
   - Map name
   - Team scores
   - Player stats (K/D/A)
   - Agents used
   - MVPs marked with ⭐

Expected:
- ✅ Recent matches shown
- ✅ Player-specific history works
- ✅ Stats formatted correctly
```

### **C. LFS Setup**

**Command:** `/lfs-setup` (Admin only)

**How to Test:**
```
Step 1: Admin runs /lfs-setup
Step 2: Bot responds with current channel ID
Step 3: Admin can update LFS_CHANNEL_ID in .env

Expected:
- ✅ Shows current LFS channel
- ✅ Instructions for updating
```

---

## 📊 Database Schema

### **Tables:**

1. **players**
   - `discord_id` (Primary Key)
   - `ign`, `player_id`, `region`
   - Stats: `kills`, `deaths`, `assists`, `matches_played`, `wins`, `losses`, `mvps`
   - `is_banned`, `ban_reason`
   - `created_at`

2. **teams**
   - `id` (Primary Key)
   - `name` (Unique), `tag`, `region`
   - `captain_id` (Foreign Key → players)
   - `logo_url`
   - Stats: `matches_played`, `wins`, `losses`, `points`
   - `is_banned`, `ban_reason`
   - `created_at`

3. **team_players**
   - `team_id` (Foreign Key → teams)
   - `player_id` (Foreign Key → players)
   - `joined_at`

4. **team_staff**
   - `team_id` (Primary Key, Foreign Key → teams)
   - `manager_1_id`, `manager_2_id` (Foreign Keys → players)
   - `coach_id` (Foreign Key → players)

5. **matches**
   - `id` (Primary Key)
   - `team1_score`, `team2_score`
   - `map_name`
   - `created_at`

6. **match_players**
   - `match_id` (Foreign Key → matches)
   - `player_id` (Foreign Key → players)
   - `team`, `agent`, `kills`, `deaths`, `assists`, `score`, `mvp`

7. **scrim_requests**
   - `id` (Primary Key)
   - `team_id`, `captain_id`
   - `format` (BO1/BO3/BO5), `time`, `timezone`, `region`
   - `status` (pending/matched/completed/cancelled)
   - `created_at`

8. **scrim_waitlist**
   - Stores teams waiting for scrim matches

---

## 🔄 24/7 Deployment Checklist

### **Pre-Deployment:**

- [ ] All `.env` variables configured
- [ ] Database initialized and migrated
- [ ] All channels created and IDs added to `.env`
- [ ] All roles created and IDs added to `.env`
- [ ] Bot invited to server with correct permissions:
  - Administrator (recommended) OR:
    - Read Messages
    - Send Messages
    - Embed Links
    - Attach Files
    - Read Message History
    - Add Reactions
    - Create Private Threads
    - Send Messages in Threads
    - Manage Messages
    - Manage Threads
- [ ] Gemini API key valid and working
- [ ] Test all major features once

### **Deployment Methods:**

#### **Option 1: VPS/Dedicated Server**
```powershell
# Using screen or tmux (Linux)
screen -S valm-bot
python bot.py
# Ctrl+A, D to detach

# Or use systemd service (recommended)
# Create /etc/systemd/system/valm-bot.service
```

#### **Option 2: Docker**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

#### **Option 3: Cloud Platforms**
- Heroku
- Railway
- Google Cloud Run
- AWS EC2
- Azure App Service

### **Monitoring:**

1. **Log Monitoring:**
   - Check console output regularly
   - Monitor `LOG_CHANNEL_ID` in Discord
   - Set up log aggregation (optional)

2. **Health Checks:**
   - Bot online status
   - Command responsiveness
   - Database connection
   - API rate limits (Gemini)

3. **Backup Strategy:**
   - Daily database backups
   - Weekly full backups
   - Store backups off-server

4. **Error Handling:**
   - Bot auto-reconnects on disconnect
   - Database connection pooling
   - Graceful error messages to users

---

## 🐛 Troubleshooting

### **Common Issues:**

#### **1. Bot Not Responding**
```
Check:
- Bot is online in Discord
- Token is valid in .env
- Bot has permissions in channel
- Command is in correct channel (BOT_COMMANDS_CHANNEL_ID)
```

#### **2. Slash Commands Not Showing**
```
Fix:
- Run !sync command (bot owner only)
- Wait 1 hour for global sync
- Or add GUILD_ID to .env for instant guild sync
```

#### **3. Database Errors**
```
Check:
- DATABASE_URL is correct
- PostgreSQL is running
- Database tables exist (run init_db.py)
- Connection pool not exhausted
```

#### **4. OCR Not Working**
```
Check:
- GEMINI_API_KEY is valid
- Image is valid VALORANT Mobile screenshot
- API quota not exceeded
- Image size under 8MB
```

#### **5. Threads Not Creating Staff**
```
Check:
- ROLE_STAFF_ID, ROLE_MODERATOR_ID, ROLE_ADMINISTRATOR_ID are correct
- Staff members have the roles
- Bot has Create Private Threads permission
- Run the enhanced debug logs (see DEBUGGING.md)
```

#### **6. LFS Not Detecting**
```
Check:
- LFS_CHANNEL_ID is correct channel
- Message format matches examples
- User is team captain
- Team is registered
```

#### **7. Profile Images Not Generating**
```
Check:
- imports/profile/Profile.jpg exists
- imports/font/Poppins-Bold.ttf exists
- Pillow installed correctly
- File permissions correct
```

---

## 📝 Testing Checklist

Use this checklist to verify all features:

### **Core Features:**
- [ ] Player registration (screenshot)
- [ ] Player registration (manual)
- [ ] Team registration
- [ ] Team invitation system
- [ ] Team leave/kick/disband
- [ ] Profile generation (player)
- [ ] Profile generation (team)
- [ ] Match scanning with OCR
- [ ] Match saving to database
- [ ] LFS request creation
- [ ] Scrim matching
- [ ] Toss and veto system
- [ ] Leaderboard display
- [ ] Leaderboard pagination

### **Admin Features:**
- [ ] Edit player data
- [ ] Ban/unban players
- [ ] Ban/unban teams
- [ ] Export data to Excel
- [ ] Archive season
- [ ] Recalculate leaderboards
- [ ] View admin logs
- [ ] Force registration

### **Edge Cases:**
- [ ] Already registered user
- [ ] Invalid screenshot
- [ ] Duplicate team name
- [ ] Full team (5 players)
- [ ] Non-captain trying captain commands
- [ ] Timeout handling (10 min inactivity)
- [ ] Thread cleanup after timeout
- [ ] Command in wrong channel
- [ ] Banned user trying to register

### **Performance:**
- [ ] Bot responds within 3 seconds (most commands)
- [ ] OCR completes within 30 seconds
- [ ] Profile generation within 5 seconds
- [ ] Leaderboard generation within 10 seconds
- [ ] Database queries under 1 second

---

## 🎯 Success Criteria

Your bot is ready for 24/7 deployment when:

✅ **All commands work** without errors
✅ **All features tested** at least once
✅ **Edge cases handled** gracefully
✅ **Error messages** are clear to users
✅ **Database backups** configured
✅ **Monitoring** in place
✅ **Auto-restart** configured (systemd/Docker)
✅ **Rate limits** not exceeded
✅ **Permissions** correct
✅ **Staff auto-add** working in threads

---

## 📞 Support

If you encounter issues during testing:

1. Check console logs for errors
2. Check Discord log channel (LOG_CHANNEL_ID)
3. Verify .env configuration
4. Test with minimal setup first
5. Enable debug logging for specific features

**Debug Mode:**
Add to bot.py for verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🔄 Version Info

- **Bot Version:** 2.0
- **Discord.py Version:** 2.6.4+
- **Python Version:** 3.10+
- **Database:** PostgreSQL 13+
- **Last Updated:** December 2025

---

## ✨ Feature Summary

**Total Commands:** 40+
**Total Features:** 65+ (NEW: Interactive Profile Editing)
**Cogs:** 16
**Database Tables:** 8
**Supported Timezones:** 30+
**Supported Regions:** 7
**Max Team Size:** 5 players
**Max Team Staff:** 2 managers + 1 coach

**⭐ Latest Features:**
- Interactive profile editing with buttons
- Edit IGN, Player ID, Region, and India status
- User-friendly modals and button interfaces
- Real-time profile updates

---

**End of Testing Guide** 🎮
