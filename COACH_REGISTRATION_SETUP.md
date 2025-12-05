# Coach Registration System Setup Guide

## Overview
The coach registration system allows users to register as coaches for teams through a clean UI interface.

## Features
- ✅ Minimalistic button-based UI
- ✅ Private thread creation for registration
- ✅ Dropdown menu to select teams
- ✅ Approval system (captain/manager must approve)
- ✅ DM notifications to captain and managers
- ✅ Admin logging
- ✅ Automatic thread closure

## Setup Instructions

### 1. Create Coach Registration Channel
Create a new channel in your Discord server for coach registration (e.g., `#coach-registration`).

### 2. Add Channel ID to .env
On your **remote server**, edit your `.env` file and add:

```env
CHANNEL_COACH_REG_ID=YOUR_CHANNEL_ID_HERE
```

**To get the channel ID:**
1. Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
2. Right-click the coach registration channel
3. Click "Copy ID"
4. Paste the ID in your .env file

### 3. Setup the UI
Run this command in the coach registration channel:
```
/setup-coach-registration
```

This will post the registration embed with the "Register as Coach" button.

## How It Works

### User Flow:
1. User clicks "🎓 Register as Coach" button
2. Bot creates a private thread
3. User sees dropdown with all available teams
4. User selects a team
5. Bot sends approval request to captain and managers via DM
6. Captain/Manager clicks Accept or Decline
7. If accepted:
   - User is added as coach
   - Notification sent to thread
   - Logged to admin logs
   - Thread closes automatically
8. If declined:
   - User is notified
   - Thread closes automatically

### Captain/Manager DM:
- Receives embed with coach details
- Two buttons: "✅ Accept" and "❌ Decline"
- Only captain and managers can approve
- 10-minute timeout on approval buttons

### Admin Logging:
The bot logs coach registrations to the `LOG_CHANNEL_ID` with:
- Coach name and IGN
- Team name and tag
- Who approved the request
- Timestamp and IDs

## Validation Rules

- ✅ Team must not already have a coach (1 coach max per team)
- ✅ Only captain or managers can approve requests
- ✅ Coach must be approved before being added
- ✅ Thread auto-closes after approval/decline

## Commands

### Admin Commands:
- `/setup-coach-registration` - Sets up the registration UI in current channel

## Files Modified

### New Files:
- `cogs/coach_registration.py` - Main cog file
- `.env.example` - Updated with new channel ID

### Files to Update on Remote Server:
- `.env` - Add `CHANNEL_COACH_REG_ID=your_channel_id`

## Troubleshooting

### Button Not Working:
- Check bot has "Create Private Threads" permission
- Verify bot is online
- Check if persistent views are registered (restart bot)

### Dropdown Empty:
- Ensure teams are registered in the database
- Check database connection

### Approval Not Working:
- Verify captain/manager have DMs enabled
- Check if user has correct role
- Verify team_staff table has correct data

### Thread Not Closing:
- Check bot has "Manage Threads" permission
- Verify no errors in console logs

## Testing Checklist

- [ ] Create coach registration channel
- [ ] Add CHANNEL_COACH_REG_ID to .env
- [ ] Restart bot
- [ ] Run /setup-coach-registration
- [ ] Click "Register as Coach" button
- [ ] Verify private thread created
- [ ] Select team from dropdown
- [ ] Check captain receives DM
- [ ] Check managers receive DM (if exist)
- [ ] Captain clicks Accept
- [ ] Verify coach added to team
- [ ] Check notification in thread
- [ ] Check admin log
- [ ] Verify thread auto-closes

## Support

If you encounter issues:
1. Check bot console logs
2. Verify .env configuration
3. Check bot permissions
4. Test with a fresh team

---

**Version:** 1.0  
**Last Updated:** December 2025
