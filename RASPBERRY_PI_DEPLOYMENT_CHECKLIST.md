# Raspberry Pi Deployment Checklist - Tesseract OCR

## 🚀 Quick Deployment Steps

### 1. Update Code from GitHub
```bash
cd ~/VALM2
git pull origin main
```

### 2. Install Tesseract OCR System Package
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng
```

**Expected output:**
```
tesseract-ocr is already the newest version (x.x.x)
```

### 3. Verify Tesseract Installation
```bash
tesseract --version
```

**Expected output:**
```
tesseract 4.x.x or 5.x.x
 leptonica-x.x.x
```

### 4. Check Language Packs Installed
```bash
tesseract --list-langs
```

**Expected output should include:**
```
List of available languages (3):
chi_sim
eng
osd
```

### 5. Install Python Package (if not already installed)
```bash
pip install pytesseract
```

### 6. Restart Bot
```bash
pm2 restart valm-bot
```

### 7. Check Bot Logs
```bash
pm2 logs valm-bot --lines 50
```

**Look for:**
- ✅ No errors about missing pytesseract
- ✅ Bot loads cogs/ocr.py successfully
- ✅ `/scan` command registered

### 8. Test `/scan` Command

**In Discord:**
1. Upload VALORANT Mobile scoreboard screenshot
2. Run `/scan` command with attachment
3. Check bot response

**Expected behavior:**
- Bot shows: "🔍 Analyzing screenshot with Tesseract OCR..."
- Bot extracts map name, scores, Win/Defeat text, players
- Bot displays results embed with Team A (Cyan) and Team B (Red)

### 9. Monitor Console Output

**Check logs for:**
```bash
pm2 logs valm-bot
```

**Expected output:**
```
📸 Processing screenshot: image.png
📐 Image size: (1920, 1080)
📄 Extracted text:
[OCR text output]
🏆 Found: 获胜 (Win)
📊 Scores: 13 - 7
🎮 Found 10 K/D/A entries
✅ Extracted 10 players
🎨 Detecting player team colors...
  Row 0: CYAN
  Row 1: CYAN
  ...
✅ Final teams: Cyan=5, Red=5
```

## ⚠️ Troubleshooting

### Issue: "pytesseract not installed" warning
```bash
pip install pytesseract
pm2 restart valm-bot
```

### Issue: "TesseractNotFoundError"
```bash
sudo apt-get install tesseract-ocr
pm2 restart valm-bot
```

### Issue: Can't read Chinese (获胜/败北)
```bash
sudo apt-get install tesseract-ocr-chi-sim
pm2 restart valm-bot
```

### Issue: Bot not responding to /scan
```bash
# Check bot logs
pm2 logs valm-bot --lines 100

# Restart bot
pm2 restart valm-bot

# Verify bot is running
pm2 status
```

### Issue: Poor OCR accuracy
**Solution:**
- Use 1080p or higher resolution screenshots
- Ensure scoreboard is fully visible (not cropped)
- Check image is not blurry or compressed
- Try re-uploading original screenshot (not edited)

## 🔍 Verification Tests

### Test 1: Basic OCR
```bash
python3 -c "
from PIL import Image
import pytesseract
import io

# Test Chinese support
test_text = pytesseract.image_to_string(
    Image.new('RGB', (100, 100), color='white'),
    lang='eng+chi_sim'
)
print('✅ Tesseract working with Chinese support')
"
```

### Test 2: Bot Import
```bash
python3 -c "
import sys
sys.path.append('/home/pi/VALM2')
from cogs.ocr import SimpleOCRScanner
print('✅ OCR cog imports successfully')
"
```

### Test 3: Full Bot Test
```bash
# Start bot and watch logs
pm2 restart valm-bot
pm2 logs valm-bot
```

## 📊 Performance Expectations

- **OCR Speed**: 1-3 seconds per screenshot
- **Memory Usage**: ~50-100MB additional (Tesseract)
- **CPU Usage**: Brief spike during OCR processing
- **Accuracy**: 90%+ for structured text (scores, stats)

## 🎉 Success Criteria

✅ Tesseract installed and working  
✅ Chinese language pack detected  
✅ Bot restarts without errors  
✅ `/scan` command works in Discord  
✅ Extracts map name correctly  
✅ Detects Win (获胜) or Defeat (败北)  
✅ Parses scores (e.g., "13 - 7")  
✅ Extracts 10 players with K/D/A  
✅ Color detection assigns cyan/red teams  
✅ Gold players balanced properly (4v5 → 5v5)  
✅ Results embed displays correctly  

## 📝 Notes

- **No API Key Needed**: Tesseract runs completely offline
- **No Cost**: Free and open source
- **Language Support**: English + Chinese built-in
- **Backward Compatible**: `/scan` command interface unchanged
- **Fallback**: Position-based team assignment if color detection fails

---

**Deployment Date**: _____________  
**Deployed By**: _____________  
**Status**: ☐ Not Started | ☐ In Progress | ☐ Complete | ☐ Failed  
**Notes**: _____________
