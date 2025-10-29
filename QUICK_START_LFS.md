# 🚀 Quick Start - Looking for Scrim System

## ⚡ Setup in 3 Steps (5 minutes)

### Step 1: Create Database Tables (2 min)
```bash
python create_scrim_tables.py
```

Expected output:
```
✅ Created scrim_requests table
✅ Created scrim_matches table
✅ Created indexes
🎉 All scrim tables created successfully!
```

### Step 2: Create Discord Channel (1 min)
1. Go to your Discord server
2. Create a new text channel
3. Name it exactly: `looking-for-scrim`
4. Set permissions (optional):
   - Everyone can view, read, send messages
   - Bot has all permissions

### Step 3: Restart Bot (1 min)
```bash
python bot.py
```

The scrim cog loads automatically!

---

## ✅ Test It Works (2 min)

### 1. Verify Database
```bash
python test_scrim_database.py
```

Should see:
```
✅ scrim_requests table exists
✅ scrim_matches table exists
✅ Test insert successful
✅ Test delete successful
🎉 All tests passed!
```

### 2. Test in Discord

**Post in #looking-for-scrim:**
```
LFS BO3
7PM IST, APAC
```

**Expected:**
- ✅ Bot reacts to your message
- 📝 Bot replies with confirmation
- 💬 Wait for another user to post similar request
- 📨 Both receive DMs with approve/decline buttons

---

## 📝 Usage

### For Users - Post Format:
```
LFS BO3
7PM IST, APAC
```

**Valid match types:** BO1, BO3, BO5  
**Valid regions:** APAC, EMEA, AMERICAS, INDIA

### Commands:
- `/cancel-scrim` - Cancel your pending request

---

## 📚 Need More Info?

- **Full Documentation:** `LFS_SYSTEM_GUIDE.md`
- **User Guide:** `LFS_MESSAGE_FORMAT.md`
- **Implementation Details:** `SCRIM_IMPLEMENTATION_SUMMARY.md`

---

## 🐛 Troubleshooting

**Bot doesn't respond?**
- Check channel name is `looking-for-scrim` (exact spelling)
- Restart the bot
- Check console for errors

**No DMs received?**
- Users must enable DMs from server members
- Check Discord Privacy Settings → Server Privacy Settings

**Database errors?**
- Verify DATABASE_URL in .env
- Ensure PostgreSQL is running
- Re-run create_scrim_tables.py

---

## ✅ You're Ready!

The LFS system is now live and ready to use! 🎉

Share the message format with your community:
```
LFS [BO1/BO3/BO5]
[TIME], [REGION]
```

Happy scrimming! 🎮
