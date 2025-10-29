# 🎯 Template Cropping Tutorial for Agent Detection

## Overview
This guide will help you create perfect agent icon templates from your Valorant screenshots for 100% accurate agent detection.

---

## 📁 Setup

### 1. Create the Templates Directory
```bash
mkdir data\agent_templates
```

### 2. What You Need
- Your screenshots from the `screenshots` folder
- Any image editor (Paint, Photoshop, GIMP, or even Python script)
- About 15-30 minutes

---

## 🎨 Cropping Guidelines

### Agent Icon Specifications
- **Size**: Approximately 80x80 to 120x120 pixels (exact size doesn't matter, template matching auto-scales)
- **Content**: ONLY the agent's face/icon, no background
- **Format**: PNG with transparency (if possible) or clean background
- **Quality**: Clear, not blurry

### What to Crop
✅ **DO INCLUDE:**
- The agent's face/portrait
- The circular or square frame around the icon
- Clear, visible features

❌ **DON'T INCLUDE:**
- Player names
- Score numbers
- Team colors (blue/red backgrounds)
- Any UI elements outside the icon

---

## 🖼️ Manual Cropping Methods

### Method 1: Using Windows Paint (Easiest)

1. **Open Screenshot**
   - Right-click screenshot → Open with → Paint

2. **Locate Agent Icons**
   - They appear in a horizontal row on the scoreboard
   - Usually in the middle section of the screen

3. **Select & Crop**
   - Use the "Select" tool (rectangular selection)
   - Draw a tight box around ONE agent icon
   - Click "Crop" button
   - Save as: `data/agent_templates/[agentname].png`
   
4. **Repeat for All Agents**
   - Open original screenshot again
   - Crop the next agent
   - Save with correct agent name

### Method 2: Using Python Script (Automated)

I can create a script that:
- Shows you the screenshot
- Lets you click corners to define crop area
- Saves with agent name automatically
- Moves to next agent

Would you like me to create this script?

---

## 📝 Naming Convention

### Required Agent Names (case-insensitive)
Save each template with these EXACT names:

```
astra.png
breach.png
brimstone.png
chamber.png
clove.png
cypher.png
deadlock.png
fade.png
gekko.png
harbor.png
iso.png
jett.png
kayo.png
killjoy.png
neon.png
omen.png
phoenix.png
raze.png
reyna.png
sage.png
skye.png
sova.png
viper.png
vyse.png
yoru.png
```

### File Structure
```
data/
└── agent_templates/
    ├── astra.png
    ├── breach.png
    ├── brimstone.png
    ├── chamber.png
    ├── clove.png
    ... (25 total files)
```

---

## 🔍 Finding Agent Icons in Screenshots

### Typical Screenshot Layout
```
┌─────────────────────────────────────────┐
│                                         │
│  [HEADER with Map Name]                 │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ Team A Players (Blue side)       │  │
│  │ [Icon] [Name] [Agent] [Stats]    │  │ <- Crop these icons
│  │ [Icon] [Name] [Agent] [Stats]    │  │
│  │ [Icon] [Name] [Agent] [Stats]    │  │
│  │ [Icon] [Name] [Agent] [Stats]    │  │
│  │ [Icon] [Name] [Agent] [Stats]    │  │
│  └──────────────────────────────────┘  │
│                                         │
│           [SCORE: 10 - 3]               │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ Team B Players (Red side)        │  │
│  │ [Icon] [Name] [Agent] [Stats]    │  │ <- Crop these icons
│  │ [Icon] [Name] [Agent] [Stats]    │  │
│  │ [Icon] [Name] [Agent] [Stats]    │  │
│  │ [Icon] [Name] [Agent] [Stats]    │  │
│  │ [Icon] [Name] [Agent] [Stats]    │  │
│  └──────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

The icons are the small circular/square images on the left of each player row.

---

## 🎯 Quality Tips

### For Best Results:
1. **Use High-Quality Screenshots**
   - 1920x1080 or higher resolution
   - Clear, not compressed
   - No blur or motion

2. **Crop Consistently**
   - Try to crop all icons with similar padding
   - Keep the same aspect ratio
   - Center the agent's face

3. **One Agent = One Template**
   - You only need ONE template per agent
   - Use the clearest icon you can find
   - Can crop from any screenshot that has that agent

4. **Test As You Go**
   - After cropping 5-10 agents, test with `/scan`
   - Check terminal logs for detection confidence
   - Adjust crops if confidence is low

---

## 🚀 Quick Start Workflow

### Step-by-Step:
1. **Pick a good screenshot** from `screenshots/` folder
   - Look for one with clear, visible agent icons
   
2. **Open in Paint/image editor**

3. **Crop the first agent icon you see**
   - Draw a tight rectangle around it
   - Crop and save as `data/agent_templates/[agent].png`

4. **Repeat for each unique agent** you can find
   - Look through different screenshots
   - Try to get all 25 agents

5. **Test the bot**
   ```
   /scan [upload scoreboard]
   ```
   - Check terminal for "Template Matching" logs
   - Look for confidence percentages

---

## 🐍 Automated Cropping Script (Optional)

Would you like me to create a Python script that:
- Opens each screenshot interactively
- Shows you where the agent icons are
- Lets you click to crop them
- Automatically saves with proper names
- Validates you have all 25 agents?

This would save you a LOT of time!

---

## 📊 Verification

### How to Check Your Templates:
1. **File Count**
   ```bash
   dir data\agent_templates\*.png
   ```
   Should show 25 PNG files

2. **Test Detection**
   - Use `/scan` command with any scoreboard
   - Check terminal logs:
   ```
   🎯 Using Hybrid Detector...
   ✅ Template matching: astra (confidence: 95.3%)
   ✅ Template matching: jett (confidence: 92.1%)
   ```

3. **Review Unknowns**
   - If some agents show "Unknown", their templates may need adjustment
   - Re-crop those specific agents with better quality

---

## ❓ Troubleshooting

### "Low confidence" or "Unknown" agents
- **Solution**: Re-crop that agent's template
- Use a clearer screenshot
- Crop with more/less padding
- Make sure the agent's face is centered

### "All agents detected as same agent"
- **Solution**: Your templates might be too similar
- Make sure you're cropping different agents
- Check file names are correct

### "No templates loaded"
- **Solution**: Check directory exists
- Verify files are named correctly (lowercase, .png extension)
- Check file permissions

---

## 💡 Pro Tips

1. **Start with common agents** (Jett, Sage, Omen, Reyna, etc.)
2. **Use the CLEAREST screenshot** you have for each agent
3. **Crop a bit generously** - include the full icon frame
4. **Test frequently** - don't crop all 25 before testing
5. **Keep originals** - save cropped templates in a backup folder too

---

## 🎓 Next Steps

After creating templates:
1. ✅ Templates created → Test with `/scan`
2. ✅ Good detection → You're done!
3. ❌ Poor detection → Adjust specific templates
4. 🔧 Fine-tune → Use calibration mode if needed

---

## Need Help?

If you want me to create the automated cropping script, just ask! It will make this process much faster and more accurate.
