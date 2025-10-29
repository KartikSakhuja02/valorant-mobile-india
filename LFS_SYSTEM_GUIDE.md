# Looking for Scrim (LFS) System Setup Guide

## 🎯 Overview
The LFS system allows team captains to find scrim matches automatically. When a captain posts in the `looking-for-scrim` channel, the bot matches them with other teams in the same region and sends DMs to both captains for approval.

## 📋 Features
- ✅ Automatic scrim matching based on region and match type
- ✅ DM notifications to both captains with approve/decline buttons
- ✅ Support for BO1, BO3, and BO5 matches
- ✅ Region filtering (APAC, EMEA, AMERICAS, INDIA)
- ✅ 24-hour request expiration
- ✅ PostgreSQL database storage

## 🔧 Setup Instructions

### 1. Create Database Tables
Run the setup script to create the necessary tables:
```bash
python create_scrim_tables.py
```

This creates two tables:
- `scrim_requests` - Stores all scrim requests
- `scrim_matches` - Stores matched scrim pairs with approval status

### 2. Create Discord Channel
Create a text channel named exactly: `looking-for-scrim`

The bot will only respond to LFS messages in this channel.

### 3. Restart Bot
The scrim cog will load automatically when you restart the bot.

## 📝 Usage

### For Captains

**Post a scrim request in #looking-for-scrim:**

```
LFS BO3
7PM IST, APAC
```

**Format:**
- Line 1: `LFS BO1` or `LFS BO3` or `LFS BO5`
- Line 2: `TIME, REGION`

**Valid Regions:**
- APAC
- EMEA
- AMERICAS
- INDIA

### What Happens Next

1. ✅ Bot confirms your request with a reaction
2. 🔍 Bot searches for matching teams (same region + match type)
3. 💬 If match found, **both captains receive a DM** with:
   - Opponent team details
   - Match type, region, and time
   - **Approve** and **Decline** buttons

4. ✅ **If both captains approve:**
   - Match is confirmed
   - Both captains receive final confirmation DM
   - Teams coordinate match details directly

5. ❌ **If either captain declines:**
   - Match is cancelled
   - Both requests remain active for new matches

## 🎮 Commands

### `/cancel-scrim`
Cancel your pending scrim request(s).

## 🗄️ Database Schema

### scrim_requests
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| captain_discord_id | BIGINT | Captain's Discord ID |
| team_id | INTEGER | Team ID (nullable) |
| region | VARCHAR(20) | Region (apac/emea/americas/india) |
| match_type | VARCHAR(10) | Match type (bo1/bo3/bo5) |
| time_slot | VARCHAR(100) | Requested time |
| status | VARCHAR(20) | pending/matched/expired/cancelled |
| created_at | TIMESTAMP | Request creation time |
| expires_at | TIMESTAMP | Expiration time (24h default) |

### scrim_matches
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| request_id_1 | INTEGER | First request ID |
| request_id_2 | INTEGER | Second request ID |
| captain_1_discord_id | BIGINT | Captain 1 Discord ID |
| captain_2_discord_id | BIGINT | Captain 2 Discord ID |
| team_1_id | INTEGER | Team 1 ID (nullable) |
| team_2_id | INTEGER | Team 2 ID (nullable) |
| region | VARCHAR(20) | Region |
| match_type | VARCHAR(10) | Match type |
| time_slot | VARCHAR(100) | Match time |
| status | VARCHAR(20) | pending_approval/approved/declined/expired |
| captain_1_approved | BOOLEAN | Captain 1 approval status |
| captain_2_approved | BOOLEAN | Captain 2 approval status |
| created_at | TIMESTAMP | Creation time |
| matched_at | TIMESTAMP | Match time |

## 🔐 Database Functions Added to `services/db.py`

- `create_scrim_request()` - Create new scrim request
- `get_pending_scrim_requests()` - Get pending requests by region
- `get_scrim_request_by_id()` - Get specific request
- `update_scrim_request_status()` - Update request status
- `create_scrim_match()` - Create matched scrim
- `get_scrim_match_by_id()` - Get match details
- `update_scrim_match_approval()` - Update captain approval
- `update_scrim_match_status()` - Update match status
- `get_captain_pending_matches()` - Get captain's pending matches
- `expire_old_scrim_requests()` - Expire old requests
- `cancel_scrim_request()` - Cancel a request

## 📊 Example Flow

1. **Captain A posts:**
   ```
   LFS BO3
   7PM IST, APAC
   ```
   ✅ Request created and stored

2. **Captain B posts:**
   ```
   LFS BO3
   8PM IST, APAC
   ```
   ✅ Match found! (same region + match type)

3. **Both captains receive DMs:**
   ```
   🎮 SCRIM MATCH FOUND!
   
   Your Team: Team Alpha [ALF]
   Opponent: Team Beta [BET]
   Match Type: BO3
   Region: APAC
   Time: 7PM IST
   
   Do you want to scrim with this team?
   [✅ Approve] [❌ Decline]
   ```

4. **Captain A clicks Approve:**
   - Waiting for Captain B...

5. **Captain B clicks Approve:**
   - ✅ Match confirmed!
   - Both receive confirmation DM with full details

## 🛠️ Customization

### Change Channel Name
Edit `cogs/scrim.py` line 162:
```python
self.lfs_channel_name = "your-channel-name"
```

### Change Expiration Time
Edit `cogs/scrim.py` line 258:
```python
expires_at = datetime.utcnow() + timedelta(hours=48)  # 48 hours instead of 24
```

### Add More Regions
1. Update database constraint in `create_scrim_tables.py`
2. Add region to valid_regions list in `cogs/scrim.py` line 212

## ⚠️ Important Notes

- Captains must have DMs enabled to receive match notifications
- Requests expire after 24 hours automatically
- Only one pending match per captain at a time
- Bot must be restarted after creating database tables
- Channel name must be exactly `looking-for-scrim` (case-sensitive)

## 🐛 Troubleshooting

**Bot doesn't respond to LFS messages:**
- Check channel name is exactly `looking-for-scrim`
- Verify bot has permission to read messages and add reactions
- Check bot console for errors

**DMs not received:**
- Ensure users have DMs enabled from server members
- Check bot has permission to DM users

**Database errors:**
- Ensure `create_scrim_tables.py` ran successfully
- Check DATABASE_URL in .env file is correct
- Verify PostgreSQL is running

## 📈 Future Enhancements (Optional)

- Add ELO-based matchmaking
- Support for custom time ranges
- Scrim history and statistics
- Automatic match scheduling in tournament system
- Blacklist system for problematic teams
- Rating system after matches

---

**Status:** ✅ Ready to deploy
**Version:** 1.0
**Created:** October 23, 2025
