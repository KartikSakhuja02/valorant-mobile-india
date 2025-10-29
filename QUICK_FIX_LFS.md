# Quick Fix: LFS Channel Setup

## Option 1: Using the Helper Command (Easiest!)

1. **Start your bot** (even without the channel ID set)
   ```bash
   python bot.py
   ```

2. **Run this command in Discord** (as admin):
   ```
   /lfs-setup
   ```

3. **Copy the channel ID** from the bot's response

4. **Add to .env file:**
   ```env
   LFS_CHANNEL_ID=1234567890123456789
   ```

5. **Restart the bot** - Instructions will appear automatically!

---

## Option 2: Manual Setup

1. **Enable Developer Mode in Discord:**
   - Settings → Advanced → Developer Mode (toggle ON)

2. **Get Channel ID:**
   - Right-click on `#looking-for-scrim` channel
   - Click "Copy Channel ID"

3. **Add to .env:**
   ```env
   LFS_CHANNEL_ID=YOUR_COPIED_ID_HERE
   ```

4. **Restart bot**

---

## Troubleshooting

**"Channel not found" error:**
- Create a channel named exactly: `looking-for-scrim`
- Make sure bot has access to the channel

**Bot doesn't send message:**
- Check console for: `⚠️ LFS_CHANNEL_ID not set in .env file`
- Verify the ID in .env has no quotes or spaces
- Restart the bot after editing .env

**Success looks like:**
```
✅ LFS instructions sent to channel: looking-for-scrim
```

---

**TIP:** Use `/lfs-setup` command - it's the easiest way!
