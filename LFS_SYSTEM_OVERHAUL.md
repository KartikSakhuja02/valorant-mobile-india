# LFS System - Complete Overhaul Summary

## 🎯 Features Implemented

### 1. **Team Membership Requirement** ✅
- Users MUST be registered to a team (as captain or member) before posting LFS
- System checks both `get_team_by_captain()` and `get_player_team()` functions
- Error message shown if user is not in any team

### 2. **Team Name Display** ✅
- Team name and tag shown prominently in all scrim requests
- Format: `Team Name [TAG]`
- Displayed in:
  - Confirmation message after posting LFS
  - All scrim request embeds
  - Match notifications

### 3. **Auto Message Purge** ✅  
- User messages in LFS channel are deleted immediately after processing
- Error messages auto-delete after 15 seconds
- Confirmation messages auto-delete after 15 seconds
- Keeps channel clean

### 4. **Show ALL Scrim Requests** ✅
- **New Flow:** Instead of auto-matching, captains see ALL available requests
- When Captain 1 posts LFS:
  1. Their request is stored
  2. They receive DM showing ALL pending requests in their region
  3. ALL other captains receive DM about this NEW request
- Each request shows as a separate embed with buttons

### 5. **Status Updates for In-Progress Matches** ✅
- When Captain A accepts Captain B's request:
  - Both requests marked as `in_progress`
  - Other captains see "⚠️ This team is currently scheduling with another team"
  - Accept button is disabled for in-progress requests
- Database field: `scrim_requests.status = 'in_progress'`

### 6. **Notify Waitlist Button** ✅
- Each scrim request embed has two buttons:
  - `✅ Accept Scrim` - Accept this scrim request
  - `🔔 Notify Me` - Get notified if scrim becomes available
- Waitlist stored in new `scrim_waitlist` table
- Waitlisted captains get notified when:
  - A scrim enters "in_progress" status
  - A scrim gets cancelled/declines and becomes available again

## 📊 Database Changes

### New Table: `scrim_waitlist`
```sql
CREATE TABLE scrim_waitlist (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES scrim_requests(id) ON DELETE CASCADE,
    captain_discord_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(request_id, captain_discord_id)
);
```

### Updated: `scrim_requests` Status
- Added new status: `in_progress`
- Status values: `pending`, `matched`, `expired`, `cancelled`, `in_progress`

## 🔄 New Flow Example

### Scenario: 3 Captains Looking for Scrims

1. **Captain 1 posts LFS**
   - Request stored in database
   - Captain 1 receives DM: "No other requests yet"

2. **Captain 2 posts LFS** 
   - Request stored in database
   - Captain 2 receives DM showing Captain 1's request (with buttons)
   - Captain 1 receives DM about Captain 2's new request (with buttons)

3. **Captain 3 posts LFS**
   - Request stored in database
   - Captain 3 receives DM showing Captain 1 + Captain 2's requests
   - Captain 1 & 2 receive DM about Captain 3's new request

4. **Captain 1 accepts Captain 3's request**
   - Both requests marked as `in_progress`
   - Captain 1 & 3 receive approval buttons
   - Captain 2 sees Captain 1 & 3's requests show: "⚠️ This team is currently scheduling"
   - Accept buttons disabled for Captain 2

5. **Captain 2 clicks "🔔 Notify Me" on Captain 3's request**
   - Captain 2 added to waitlist for Captain 3's request
   - If Captain 3's match with Captain 1 fails, Captain 2 gets notified

## 🆕 New Functions Added

### `cogs/scrim.py`
- `send_all_scrim_requests()` - Send all pending requests to a captain
- `notify_other_captains()` - Notify all captains about new request
- `create_scrim_match_from_requests()` - Create match when captain accepts
- `notify_waitlist()` - Notify waitlisted captains about status changes

### `services/db.py`
- `get_captain_pending_request()` - Get captain's current pending request
- `get_scrim_request_status()` - Get status of a specific request
- `get_team_by_id()` - Get team by ID with members
- `add_to_scrim_waitlist()` - Add captain to waitlist
- `get_scrim_waitlist()` - Get all captains waiting for a request

## 🎨 New UI Components

### `ScrimRequestView` Class
- Two buttons per scrim request:
  1. **✅ Accept Scrim** - Accept and create match
  2. **🔔 Notify Me** - Join waitlist
- Buttons auto-disable when:
  - Request is in avoid list
  - Request status is `in_progress`
  - Request no longer exists

## 📝 Message Formats

### Scrim Request Embed (DM)
```
🎮 Scrim Request
━━━━━━━━━━━━━━━━
Team: Team Name [TAG]
Match Type: BO3
Time Slot: 7PM IST
Region: APAC

[Buttons: ✅ Accept Scrim] [🔔 Notify Me]
```

### In-Progress Status
```
⚠️ This team is currently scheduling with another team.
[Buttons disabled]
```

### Waitlist Notification
```
📊 Scrim Status Update

Team A vs Team B is now in scheduling progress.
You'll be notified if this scrim doesn't get scheduled!
```

## 🚀 Migration Required

Run this command before using the new features:
```bash
python migrations\add_scrim_waitlist.py
```

This will:
1. Update `scrim_requests` status constraint
2. Create `scrim_waitlist` table
3. Add necessary indexes

## ✨ Benefits

1. **More Control** - Captains choose who to scrim with
2. **Better Visibility** - See all available teams at once
3. **Fair System** - Everyone gets equal opportunity
4. **Smart Notifications** - Only relevant updates sent
5. **Clean Channel** - Auto-purge keeps LFS channel tidy
6. **Team Requirement** - Only registered teams can scrim
7. **Waitlist Feature** - Never miss a scrim opportunity

## 🔧 Configuration

No new environment variables needed. Uses existing:
- `LFS_CHANNEL_ID` - The looking-for-scrim channel ID

## 🎮 User Experience

### Before (Old System)
1. Post LFS → Auto-matched with first available team → No choice

### After (New System)  
1. Post LFS → See ALL teams looking → Choose who to scrim → Accept/Notify

## 📱 Captain Workflow

1. **Post LFS** in `#looking-for-scrim` channel
   ```
   LFS BO3
   7PM IST, APAC
   ```

2. **Check DMs** - Bot shows all available teams

3. **Review Options:**
   - See team names, match types, time slots
   - Check if teams are in-progress or avoided
   
4. **Take Action:**
   - Click `✅ Accept Scrim` to match with that team
   - Click `🔔 Notify Me` to get notified later

5. **Approve Match** - Both captains must approve

6. **Chat Relay** - Chat system activates

This system gives captains full control over their scrim partners!
