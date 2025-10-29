# 🗺️ Quick Map Detection Test Guide

## 🚀 **How to Test**

### Step 1: Restart Your Bot
```bash
python bot.py
```

Look for initialization message:
```
✅ Using Gemini model: gemini-2.0-flash-exp
✅ Gemini Vision Agent Detector initialized
```

---

### Step 2: Run /scan Command

In Discord:
```
/scan [upload screenshot]
```

---

### Step 3: Check Console Output

You should see:
```
📏 Image size: (1920, 1080), Mode: RGB
📝 Prompt length: 15234 characters
🤖 Using model: gemini-2.0-flash-exp

📤 Raw Gemini response (agents): ...
✅ Gemini Vision detected agents: ['Jett', 'Sage', ...]

🗺️ Raw map response: Ascent
🗺️ Gemini Vision detected map: Ascent
```

---

### Step 4: Check Discord Embed

The result should show:

```
📊 MATCH RESULTS

Map: Ascent 🗺️          ⬅️ NEW!
Score: 13 - 11
Status: Team A wins
Players: 8 registered • 2 unregistered

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🟢 Team A 🏆
⭐ Player1 (Jett) - 25K/15D/5A
...

🔴 Team B
Player6 (Sage) - 20K/18D/8A
...
```

---

## 📋 **Test Checklist**

### Test Case 1: Chinese Map Name
- [ ] Upload screenshot with "亚海悬城" (Ascent in Chinese)
- [ ] Bot should detect and show: `Map: Ascent 🗺️`
- [ ] Check logs: `🗺️ Raw map response: 亚海悬城` or `Ascent`

### Test Case 2: English Map Name
- [ ] Upload screenshot with "Ascent" (English)
- [ ] Bot should detect and show: `Map: Ascent 🗺️`
- [ ] Check logs: `🗺️ Raw map response: Ascent`

### Test Case 3: Different Maps
Test all 7 maps:
- [ ] Ascent (亚海悬城)
- [ ] Bind (源工重镇)
- [ ] Icebox (极寒冬港)
- [ ] Haven (隐世修所)
- [ ] Split (霓虹町)
- [ ] Breeze (微风岛屿)
- [ ] Fracture (裂变峡谷)

### Test Case 4: No Map Name Visible
- [ ] Upload screenshot where map name is cut off
- [ ] Bot should show: `Map: Unknown 🗺️`

---

## 🔍 **Expected Results**

| Test | Screenshot Shows | Expected Output | Database Stores |
|------|-----------------|-----------------|-----------------|
| 1 | 亚海悬城 | `Map: Ascent 🗺️` | `"map": "Ascent"` |
| 2 | Ascent | `Map: Ascent 🗺️` | `"map": "Ascent"` |
| 3 | 源工重镇 | `Map: Bind 🗺️` | `"map": "Bind"` |
| 4 | 极寒冬港 | `Map: Icebox 🗺️` | `"map": "Icebox"` |
| 5 | (no map visible) | `Map: Unknown 🗺️` | `"map": "Unknown"` |

---

## 🐛 **Troubleshooting**

### Problem: Map shows as "Unknown" every time

**Check:**
1. Is the map name visible in the screenshot?
2. Look at console logs: `🗺️ Raw map response: ...`
3. What did the AI actually see?

**Solution:**
- If AI sees correct name but still shows Unknown → Check `self.map_names` dictionary
- If AI sees wrong text → Screenshot quality issue or map name obscured

### Problem: Wrong map detected

**Example:** Screenshot shows "Ascent" but bot detects "Bind"

**Check:**
1. Console log: `🗺️ Raw map response: ...`
2. Is the AI seeing the wrong text?

**Solution:**
- Screenshot might have multiple text elements
- Try cropping screenshot to focus on scoreboard area
- Check if map name is clearly visible

### Problem: Map detection very slow

**Cause:** Each `/scan` now makes 2 API calls:
- 1 for agent detection
- 1 for map detection

**Impact:**
- ~2-3 seconds longer per scan

**If too slow:**
Can disable map detection temporarily by editing `ocr.py`:
```python
# Comment out map detection
# map_name = self.detect_map_name(image_path)
detected_map = 'Unknown'  # Temporary fallback
```

---

## 📊 **Performance Expectations**

| Metric | Value |
|--------|-------|
| **Detection Accuracy** | ~95% (when map name visible) |
| **API Calls per Scan** | 2 (agents + map) |
| **Additional Time** | +2-3 seconds |
| **API Cost Increase** | +50% (2 calls vs 1) |

---

## 🎯 **Success Criteria**

✅ **Feature Working If:**
1. Discord embed shows `Map: [MapName] 🗺️`
2. Console logs show `🗺️ Detected map: [MapName]`
3. Database stores correct map name
4. Works for both Chinese and English names
5. Shows "Unknown" gracefully when map not visible

---

## 🚀 **Next Steps After Testing**

### If Working Well:
- ✅ Leave feature enabled
- 📊 Start collecting map statistics
- 🎮 Build map-specific leaderboards

### If Issues Found:
- 🔍 Check console logs for details
- 📸 Try different screenshot formats
- 🛠️ May need to adjust detection prompt

### Future Enhancements:
- Add more maps as they release
- Add map-specific player stats
- Filter matches by map
- Show "best map" for each player

---

**Ready to test! Good luck! 🎮✨**
