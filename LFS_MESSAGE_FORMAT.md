# 🎮 Looking for Scrim - Message Format Guide

## ✅ Correct Format

Post this in the `#looking-for-scrim` channel:

```
LFS BO3
7PM IST, APAC
```

### Template:
```
LFS [MATCH_TYPE]
[TIME], [REGION]
```

---

## 📋 Valid Options

### Match Types:
- `BO1` - Best of 1
- `BO3` - Best of 3
- `BO5` - Best of 5

### Regions:
- `APAC` - Asia Pacific
- `EMEA` - Europe, Middle East, Africa
- `AMERICAS` - North & South America
- `INDIA` - India

---

## 💡 Examples

### Example 1: BO1 in EMEA
```
LFS BO1
9PM CET, EMEA
```

### Example 2: BO5 in AMERICAS
```
LFS BO5
6PM EST, AMERICAS
```

### Example 3: BO3 in INDIA
```
LFS BO3
8PM IST, INDIA
```

### Example 4: BO3 in APAC
```
LFS BO3
7PM JST, APAC
```

---

## ❌ Invalid Formats

### Wrong: Missing LFS prefix
```
BO3
7PM IST, APAC
```

### Wrong: Invalid match type
```
LFS BO2
7PM IST, APAC
```

### Wrong: Invalid region
```
LFS BO3
7PM IST, EU
```
*Note: Use EMEA instead of EU*

### Wrong: Missing comma
```
LFS BO3
7PM IST APAC
```

### Wrong: Missing second line
```
LFS BO3
```

---

## 🔔 What Happens After You Post?

1. ✅ **Bot reacts** to your message (confirms received)
2. 📝 **Bot creates** your scrim request in database
3. 🔍 **Bot searches** for matching teams:
   - Same region
   - Same match type
4. 💬 **If match found:**
   - You receive a **DM** with opponent details
   - Opponent also receives a **DM**
   - Both have **Approve** and **Decline** buttons
5. ✅ **If both approve:**
   - Match is confirmed!
   - Coordinate details directly with opponent

---

## 📱 DM Notification Example

When a match is found, you'll receive:

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

---

## 🎯 Tips

- ✅ Post in `#looking-for-scrim` channel only
- ✅ Make sure your time zone is clear (e.g., IST, EST, CET)
- ✅ Enable DMs from server members to receive notifications
- ✅ Only one pending request at a time per captain
- ✅ Requests expire after 24 hours
- ✅ Use `/cancel-scrim` to cancel your request

---

## ⚙️ Commands

### `/cancel-scrim`
Cancel your current pending scrim request.

**Usage:**
```
/cancel-scrim
```

---

## ❓ FAQ

**Q: Can I post multiple requests?**
A: No, only one pending request at a time. Cancel the first one to post a new one.

**Q: What if no one matches my request?**
A: Your request stays active for 24 hours. New requests will be matched against yours.

**Q: What if I don't receive a DM?**
A: Enable DMs from server members in your Discord privacy settings.

**Q: Can I change my request after posting?**
A: Use `/cancel-scrim` and post a new request.

**Q: What happens if I decline a match?**
A: Your request stays active and will be matched with other teams.

**Q: What if both teams approve?**
A: Both captains receive a confirmation DM. Coordinate match details directly.

---

**Need help?** Contact server admins or check `#help` channel.
