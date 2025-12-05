# 🚀 Quick Deployment Guide - Coach Registration

## What Was Added

✅ **New Cog:** `cogs/coach_registration.py`  
✅ **Documentation:** `COACH_REGISTRATION_SETUP.md`  
✅ **Example Config:** `.env.example` (updated)

## What You Need to Do on Your Remote Server

### Step 1: Pull the Latest Code
```bash
cd /path/to/your/bot
git pull origin main
```

### Step 2: Update Your .env File
Add this line to your `.env` file on the remote server:

```bash
# Add this line to your .env
CHANNEL_COACH_REG_ID=YOUR_COACH_REGISTRATION_CHANNEL_ID
```

**To get your channel ID:**
1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click your coach registration channel
3. Click "Copy ID"
4. Replace `YOUR_COACH_REGISTRATION_CHANNEL_ID` with the copied ID

### Step 3: Restart the Bot
```bash
# If using pm2:
pm2 restart valm-bot

# If using systemd:
sudo systemctl restart valm-bot

# If using screen/tmux:
# Stop the bot (Ctrl+C) and run again:
python bot.py
```

### Step 4: Setup the UI in Discord
1. Go to your coach registration channel in Discord
2. Run this command:
   ```
   /setup-coach-registration
   ```
3. The bot will post a clean embed with a "🎓 Register as Coach" button

## Done! 🎉

Your coach registration system is now live!

## How Users Will Use It

1. **User clicks "Register as Coach"** → Bot creates private thread
2. **User selects team from dropdown** → Bot sends approval to captain/managers
3. **Captain/Manager approves in DM** → User becomes coach
4. **Thread closes automatically** → Logged to admin logs

## Testing

Test it yourself:
1. Click the "Register as Coach" button
2. Select a team you're NOT part of
3. As the captain, check your DMs for approval
4. Click "Accept"
5. Verify the user is added as coach: `/team-profile name:"YourTeam"`

## Troubleshooting

**Button doesn't work:**
- Make sure bot is online
- Check bot has "Create Private Threads" permission
- Restart the bot

**Dropdown is empty:**
- Make sure teams exist in database
- Run `/teams` to see registered teams

**Captain doesn't get DM:**
- Captain must have DMs enabled from server members
- Check if captain ID is correct in database

## Need Help?

Check the full documentation in `COACH_REGISTRATION_SETUP.md`

---

**Git Commit:** `bd6c1fb`  
**Branch:** `main`  
**Status:** ✅ Pushed to GitHub
