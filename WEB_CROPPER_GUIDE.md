# 🌐 Web-Based Template Cropper Guide

Since OpenCV isn't working, use this **browser-based solution** instead!

---

## 🚀 Quick Start (3 Steps)

### Step 1: Open the Web Tool
```bash
# Just double-click this file:
web_crop_templates.html
```
It will open in your browser (Chrome, Edge, Firefox - any works!)

---

### Step 2: Crop All 25 Agents

1. **Drag & drop** a screenshot onto the upload area
   - Or click to browse for a file

2. **Click and drag** to select an agent icon
   - Click top-left corner
   - Drag to bottom-right corner
   - A green box will appear

3. **Select agent name** from the dropdown
   - Automatically suggests the next missing agent

4. **Click "Save Template"**
   - Downloads as `agentname.png`

5. **Repeat** for all visible agents in that screenshot

6. **Click "Next Screenshot"** to load another image

7. Keep going until you have all 25 agents!

---

### Step 3: Organize Templates

After downloading all templates, run:
```bash
python organize_templates.py
```

This will:
- Find all downloaded templates (`astra.png`, `jett.png`, etc.)
- Move them to `data/agent_templates/`
- Delete from Downloads folder
- Show you what's complete and what's missing

---

## ✨ Features

### Progress Tracking
- Shows "X / 25 Agents" progress bar
- Remembers what you've already cropped
- Lists missing agents in red

### Smart Features
- Auto-suggests next missing agent
- Preview before saving
- Works with any screenshot resolution
- Saves to Downloads folder automatically

### Keyboard Shortcuts
- None needed! Just click and drag

---

## 📋 Workflow Example

```
1. Open web_crop_templates.html
2. Drag screenshot #1 onto page
3. Crop Jett icon → Save
4. Crop Sage icon → Save
5. Crop Omen icon → Save
   ... (3/25 complete)
6. Click "Next Screenshot"
7. Drag screenshot #2
8. Crop Reyna icon → Save
   ... (4/25 complete)
9. Repeat until 25/25
10. Run: python organize_templates.py
11. Done! ✅
```

---

## 💡 Tips

### For Best Results:
1. **Use clear screenshots** - Not blurry or low-res
2. **Crop tightly** - Include just the icon, not names/stats
3. **One template per agent** - You only need one good crop
4. **Check preview** - Shows on the right side before saving

### Finding Icons:
- Look for circular/square portraits in the scoreboard
- Usually on the left side of each player row
- 10 icons per screenshot (5 per team)

### If You Make a Mistake:
- Click "Reset Selection" to try again
- Just don't click "Save Template"
- Page remembers what you've saved (uses browser storage)

---

## 🔧 Troubleshooting

### Page won't load?
- Make sure you have a modern browser
- Try right-click → Open with → Chrome/Edge

### Can't see the canvas?
- Upload a screenshot first
- Must be PNG or JPG format

### Downloads not saving?
- Check browser permissions
- Look in your Downloads folder
- Browser might ask permission first time

### Lost progress?
- Don't clear browser data
- Progress is saved automatically
- Can close and reopen anytime

---

## 🎯 After You're Done

1. **Run organizer:**
   ```bash
   python organize_templates.py
   ```

2. **Verify all 25 agents:**
   - Check `data/agent_templates/` folder
   - Should have 25 PNG files

3. **Test with bot:**
   ```
   /scan [upload scoreboard]
   ```

4. **Check terminal logs:**
   - Should show "Template Matching" detection
   - Look for confidence percentages
   - Should be 80%+ for good templates

---

## 📱 Alternative: Use Paint

If web tool doesn't work, manual method:

1. Open screenshot in Paint
2. Use Select tool → Crop to icon
3. File → Save As → `agentname.png`
4. Move to `data/agent_templates/`
5. Repeat 25 times

---

## ✅ Checklist

- [ ] Open `web_crop_templates.html`
- [ ] Upload screenshots one by one
- [ ] Crop all 25 agents
- [ ] Run `organize_templates.py`
- [ ] Verify 25 files in `data/agent_templates/`
- [ ] Test with `/scan` command
- [ ] Check detection confidence
- [ ] Re-crop any low confidence agents

---

## 🎉 Benefits of Web Tool

✅ No Python dependencies needed
✅ No OpenCV installation
✅ Works on any computer with a browser
✅ Visual preview before saving
✅ Progress tracking
✅ Can't accidentally overwrite files
✅ Simple drag-and-drop
✅ Auto-downloads to correct format

---

## Need Help?

If the web tool doesn't work:
1. Check browser console (F12) for errors
2. Try a different browser
3. Use the manual Paint method
4. Check screenshot file format (should be PNG/JPG)

---

Ready? Just open **web_crop_templates.html** and start cropping! 🎯
