# Command Status Report

## ✅ EXISTING COMMANDS

### Player Commands
- ✅ `/register` - Player registration (cogs/registration.py)
- ✅ `/profile` - View player profile (cogs/profiles.py)
- ✅ `/lb` - Leaderboard (cogs/leaderboards.py)
- ✅ `/leave-team` - Leave current team (cogs/teams.py)
- ✅ `/team-profile` - View team profile (cogs/profiles.py)

### Scrim Commands
- ✅ `/lfs-setup` - Setup LFS channel (cogs/scrim.py)
- ✅ `/cancel-scrim` - Cancel scrim request (cogs/scrim.py)

### Match Commands
- ✅ `/scan` - OCR scan match results (cogs/ocr.py)

### Admin Commands
- ✅ `/add-coach` - Add team coach (cogs/team_staff.py)
- ✅ `/add-manager` - Add team manager (cogs/team_staff.py)
- ✅ `/remove-coach` - Remove team coach (cogs/team_staff.py)
- ✅ `/remove-manager` - Remove team manager (cogs/team_staff.py)
- ✅ `/edit-player` - Edit player info (cogs/admin.py)
- ✅ `/edit-kda` - Edit player K/D/A (cogs/admin.py)
- ✅ `/edit-record` - Edit team record (cogs/admin.py)
- ✅ `/delete-player` - Delete player (cogs/admin.py)
- ✅ `/ban-player` - Ban player (cogs/admin.py)
- ✅ `/unban-player` - Unban player (cogs/admin.py)
- ✅ `/ban-team` - Ban team (cogs/admin.py)
- ✅ `/unban-team` - Unban team (cogs/admin.py)
- ✅ `/admin-logs` - View admin logs (cogs/admin.py)
- ✅ `/recalculate-leaderboards` - Recalculate LB (cogs/admin.py)
- ✅ `/clear-team-stats` - Clear team stats (cogs/admin.py)
- ✅ `/archive-season` - Archive season (cogs/admin.py)
- ✅ `/export-data` - Export data (cogs/admin.py)

### Team Management
- ✅ `/register-team` - Register team (cogs/teams.py)
- ✅ `/disband` - Disband team (cogs/teams.py)
- ✅ `/invite-player` - Invite player to team (cogs/teams.py)
- ✅ `/kick-player` - Kick player from team (cogs/teams.py)
- ✅ `/set-logo` - Set team logo (cogs/teams.py)
- ✅ `/view-staff` - View team staff (cogs/team_staff.py)
- ✅ `/update_ign` - Update IGN (cogs/registration.py)

---

## ❌ MISSING COMMANDS (Need to be implemented)

### Player Commands (HIGH PRIORITY)
- ❌ `/stats [user]` - View detailed player statistics
- ❌ `/leaderboard [region]` - View player rankings (currently only `/lb` exists)
- ❌ `/create-team <name> <tag> <region>` - Create team via command
- ❌ `/join-team <team_name>` - Request to join team
- ❌ `/team-info [team_name]` - View team information
- ❌ `/team-stats [team_name]` - View team statistics
- ❌ `/team-leaderboard [region]` - View team rankings

### Scrim System (HIGH PRIORITY)
- ❌ `/lfs` - Post Looking For Scrim request
- ❌ `/accept-scrim` - Accept scrim proposal
- ❌ `/decline-scrim` - Decline scrim proposal
- ❌ `/join-waitlist <request_id>` - Join scrim waitlist
- ❌ `/avoid-team <team_name>` - Avoid team for 6 hours

### Match Reporting
- ❌ `/submit-match` - Submit match results (currently only `/scan` exists)
- ❌ `/match-history [team_name]` - View match history

### Admin Commands (MEDIUM PRIORITY)
- ❌ `/force-register-player` - Force register player
- ❌ `/force-register-team` - Force register team
- ❌ `/add-player <team> <user>` - Add player to team
- ❌ `/remove-player <team> <user>` - Remove player from team
- ❌ `/delete-team <team_name>` - Delete team
- ❌ `/transfer-captain` - Transfer captain role
- ❌ `/set-team-staff` - Set team staff (coach/managers)
- ❌ `/force-submit-match` - Submit match on behalf of teams
- ❌ `/delete-match <match_id>` - Delete match
- ❌ `/edit-match <match_id>` - Edit match details
- ❌ `/cancel-scrim-request <id>` - Cancel any scrim request
- ❌ `/match-teams <id1> <id2>` - Manually match scrim requests
- ❌ `/clear-expired-scrims` - Remove expired scrims
- ❌ `/unregister-player <user>` - Unregister player
- ❌ `/update-player-stats` - Manually update stats
- ❌ `/reset-player-stats` - Reset player stats

### System Commands (LOW PRIORITY)
- ❌ `/sync` - Sync slash commands
- ❌ `/reload <cog>` - Reload cog
- ❌ `/purge <amount>` - Delete messages
- ❌ `/announce <message>` - Send announcement

### Help & Info (LOW PRIORITY)
- ❌ `/help [command]` - View help
- ❌ `/bot-info` - View bot info
- ❌ `/ping` - Check latency

### Utility (LOW PRIORITY)
- ❌ `/region-role` - Get region role
- ❌ `/verify` - Verify registration

---

## 📊 SUMMARY

**Total Commands Listed:** 58
**Existing Commands:** 30 (52%)
**Missing Commands:** 28 (48%)

### Priority Breakdown
- **HIGH PRIORITY (User-Facing):** 15 commands
- **MEDIUM PRIORITY (Admin Tools):** 10 commands
- **LOW PRIORITY (Utility/System):** 3 commands

---

## 🔧 NOTES

1. **Team Profile Interactive Buttons** - Already implemented (add/remove player, transfer captain, add/remove coach/manager)
2. **OCR System** - Working but needs fixes (color detection issues)
3. **Registration Systems** - Both player and team registration working with inactivity timeout
4. **Database Functions** - Most core functions exist in services/db.py

---

## 📝 RECOMMENDATION

Focus on implementing HIGH PRIORITY commands first:
1. `/lfs` - Critical for scrim system
2. `/stats` and `/leaderboard` - Core player features
3. `/team-info` and `/team-stats` - Core team features
4. Scrim acceptance/decline system
5. `/match-history` - Important for teams

The interactive button systems (team profile, registration) are already implemented and working well.
