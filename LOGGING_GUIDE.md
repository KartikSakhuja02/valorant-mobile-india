# Logging System Guide

## Overview
The bot now sends detailed logs to a designated Discord channel for all major events including player registrations, team operations, and match results.

## Setup

### 1. Configure Log Channel
Add the following to your `.env` file:
```env
LOG_CHANNEL_ID=your_channel_id_here
```

**How to get your channel ID:**
1. Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
2. Right-click on the channel you want to use for logs
3. Click "Copy ID"
4. Paste it in your `.env` file

### 2. Channel Permissions
Make sure the bot has these permissions in the log channel:
- ✅ View Channel
- ✅ Send Messages
- ✅ Embed Links
- ✅ Attach Files (optional, for future features)

## Log Types

### 🆕 Player Registration (Manual)
**Color:** Blue  
**Triggered by:** `/register` command

**Information Logged:**
- Player mention and username
- In-game name (IGN)
- Player ID
- Region selected
- Discord ID
- Player avatar
- Registration method: Manual
- Timestamp

---

### 🆕 Player Registration (OCR)
**Color:** Purple  
**Triggered by:** `/ocr-register` command (after approval)

**Information Logged:**
- Player mention and username
- In-game name (IGN) extracted from screenshot
- Player ID extracted from screenshot
- Region selected
- Discord ID
- Player avatar
- Registration method: OCR
- Timestamp

---

### 🏆 Team Registration
**Color:** Gold  
**Triggered by:** `/register-team` command

**Information Logged:**
- Team name
- Team tag
- Region
- Captain mention and username
- Captain IGN
- Captain Discord ID
- Captain avatar
- Timestamp

---

### 👥 Player Joined Team
**Color:** Green  
**Triggered by:** When a player accepts a team invitation

**Information Logged:**
- Team name and tag
- New member mention and username
- Team captain mention and username
- Total team members count
- New member avatar
- Player Discord ID
- Timestamp

---

### 📊 Match Recorded
**Color:** Orange  
**Triggered by:** `/scan` command (when match results are saved)

**Information Logged:**
- Map name
- Final score (Team 1 vs Team 2)
- Winner (Team 1 🔵 / Team 2 🔴 / Draw)
- Team names (if available, otherwise "Randoms")
- Number of players
- MVP player(s) name(s)
- Who scanned the match
- Match ID
- Timestamp

---

## Log Format

All logs are sent as Discord embeds with:
- **Title:** Event type with emoji
- **Color:** Event-specific color
- **Fields:** Organized information about the event
- **Thumbnail:** User avatar (when applicable)
- **Footer:** Additional context (User ID, Match ID, etc.)
- **Timestamp:** When the event occurred (UTC)

## Example Log Messages

### Player Registration
```
🆕 New Player Registration
━━━━━━━━━━━━━━━━━━━━━━━
Player: @Username (Username#1234)
IGN: PlayerName#TAG
Player ID: 123456
Region: 🌎 North America (NA)
Discord ID: 987654321012345678

Footer: User ID: 987654321012345678 • Method: Manual
```

### Team Registration
```
🏆 New Team Registration
━━━━━━━━━━━━━━━━━━━━━━━
Team Name: Team Phoenix
Team Tag: [PHX]
Region: 🌎 North America (NA)
Captain: @CaptainUser (CaptainUser#1234)
Captain IGN: CaptainIGN#TAG
Discord ID: 123456789012345678

Footer: Team Captain ID: 123456789012345678
```

### Match Recorded
```
📊 New Match Recorded
━━━━━━━━━━━━━━━━━━━━━━━
Map: Bind
Score: 13 - 11
Winner: Team 1 🔵
Teams: Team Phoenix vs Team Dragons
Players: 10
MVP: PlayerName#TAG
Scanned By: @ScannerUser

Footer: Match ID: abc123xyz
```

## Benefits

1. **Audit Trail:** Complete history of all bot activities
2. **Monitoring:** Real-time visibility of tournament activities
3. **Moderation:** Easy tracking of player and team registrations
4. **Analytics:** Data for tournament statistics and insights
5. **Troubleshooting:** Quick reference for support issues

## Privacy Notes

- All logs contain Discord IDs for administrative purposes
- Logs are only visible to members with access to the log channel
- Consider making the log channel admin-only
- IGNs and player IDs are stored as they are provided by users

## Troubleshooting

**Logs not appearing?**
1. ✅ Check that `LOG_CHANNEL_ID` is set in `.env`
2. ✅ Verify the channel ID is correct
3. ✅ Ensure bot has proper permissions in the log channel
4. ✅ Check bot console for error messages like "Error sending [event] log"

**Partial information in logs?**
- Some fields may show "Unknown" or "N/A" if data is missing
- This is expected for optional fields or when data retrieval fails
- The core event information will always be logged

## Future Enhancements

Potential logging features to add:
- ✨ Player profile updates (IGN changes, etc.)
- ✨ Team member removals/kicks
- ✨ Match disputes or admin interventions
- ✨ Leaderboard position changes
- ✨ Tournament phase transitions
- ✨ Administrative actions (warnings, bans, etc.)
