# Setting up LFS Channel ID

## Quick Setup

1. **Create the Discord channel** named `looking-for-scrim`

2. **Get the Channel ID:**
   - Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
   - Right-click on the `looking-for-scrim` channel
   - Click "Copy Channel ID"

3. **Add to .env file:**
   ```env
   LFS_CHANNEL_ID=YOUR_CHANNEL_ID_HERE
   ```
   Example:
   ```env
   LFS_CHANNEL_ID=1234567890123456789
   ```

4. **Restart the bot:**
   ```bash
   python bot.py
   ```

5. **Verify:**
   - Check the bot console for: `✅ LFS instructions sent to channel: looking-for-scrim`
   - Check the channel for the instructions embed message

## What the Bot Sends

When the bot starts, it will send a beautifully formatted embed in the LFS channel with:

- 📝 Message format instructions
- 💡 Examples (BO3, BO5)
- ✅ Valid match types (BO1, BO3, BO5)
- 🌍 Valid regions (APAC, EMEA, AMERICAS, INDIA)
- 🔄 How the matching process works
- ⚙️ Available commands
- 💬 Reminder to enable DMs

## Troubleshooting

**Bot doesn't send the message:**
- Check that `LFS_CHANNEL_ID` is set in `.env`
- Verify the channel ID is correct (no quotes, just numbers)
- Ensure bot has permissions to send messages in that channel
- Check bot console for error messages

**Message appears but users can't use it:**
- Ensure users have permission to send messages in the channel
- Verify bot has permission to add reactions
- Check bot can DM users (users must enable DMs from server members)

---

**Note:** The bot will only send the instructions message once when it starts. If you want to send it again, restart the bot!
