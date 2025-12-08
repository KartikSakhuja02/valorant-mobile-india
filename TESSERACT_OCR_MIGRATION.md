# Tesseract OCR Migration Guide

## Overview
Successfully migrated from **Gemini Vision API** to **Tesseract OCR** for the `/scan` command.

## Why Tesseract?
- ✅ **Free** - No API costs
- ✅ **Offline** - Works without internet for OCR processing
- ✅ **Open Source** - Full control over text extraction
- ✅ **Chinese Support** - Can read 获胜 (Win) and 败北 (Defeat)

## Changes Made

### 1. Dependencies Updated
**Removed:**
- `json`, `base64`, `asyncio`, `aiohttp` (Gemini API dependencies)
- `google-generativeai`
- `GEMINI_API_KEY` configuration

**Added:**
- `pytesseract` - Python wrapper for Tesseract OCR
- `re` - Regex for parsing OCR text output

### 2. Code Structure

#### Before (Gemini API):
```python
async def call_gemini_api(image_bytes: bytes) -> Optional[Dict]:
    # ~80 lines of API calls with model fallback
    # Sent image + prompt to Gemini
    # Parsed JSON response
```

#### After (Tesseract OCR):
```python
def extract_text_from_image(image: Image.Image) -> str:
    # Extract all text using Tesseract
    custom_config = r'--oem 3 --psm 6 -l eng+chi_sim'
    return pytesseract.image_to_string(image, config=custom_config)

def extract_match_data(image: Image.Image) -> Optional[Dict]:
    # Parse text to extract:
    # - Map name (Chinese + English)
    # - Win/Defeat text (获胜/败北)
    # - Scores (10 - 5)
    # - Player names and K/D/A stats
```

### 3. What Stayed the Same
✅ Color detection functions (cyan/red/gold team assignment)  
✅ Team balancing logic (4v5 → 5v5)  
✅ Display results embed  
✅ Win/Defeat interpretation  

## Installation Instructions

### On Raspberry Pi

1. **Install Tesseract OCR system package:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng
```

2. **Install Python wrapper:**
```bash
pip install pytesseract pillow
```

3. **Verify installation:**
```bash
tesseract --version
# Should show: tesseract 4.x.x or higher
```

4. **Update bot code:**
```bash
cd ~/VALM2
git pull origin main
pm2 restart valm-bot
```

### On Windows (Development)

1. **Download Tesseract installer:**
   - https://github.com/UB-Mannheim/tesseract/wiki
   - Install to: `C:\Program Files\Tesseract-OCR`

2. **Install Python packages:**
```bash
pip install pytesseract pillow
```

3. **Configure pytesseract path (if needed):**
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## How It Works

### Text Extraction Process
1. **Image Input**: User uploads VALORANT Mobile screenshot via `/scan`
2. **Tesseract OCR**: Extracts all text using English + Chinese language packs
3. **Regex Parsing**:
   - **Map Name**: Search for Chinese map names (亚海悬城 → Ascent) or English names
   - **Win/Defeat**: Look for 获胜 (Win) or 败北 (Defeat) characters
   - **Scores**: Match patterns like `10 - 5` or `10  5`
   - **K/D/A Stats**: Match patterns like `17 / 10 / 5` or `17/10/5`
   - **Player Names**: Extract text before K/D/A patterns

4. **Color Detection**: Still uses HSV color analysis to assign cyan/red/gold teams
5. **Smart Team Assignment**: Gold players assigned to balance 4v5 → 5v5

### OCR Configuration
```python
custom_config = r'--oem 3 --psm 6 -l eng+chi_sim'
```
- `--oem 3`: LSTM neural net mode (best accuracy)
- `--psm 6`: Assume uniform block of text
- `-l eng+chi_sim`: Use English + Simplified Chinese language data

## Troubleshooting

### Issue: "pytesseract not installed"
**Solution:**
```bash
pip install pytesseract
```

### Issue: "TesseractNotFoundError"
**Solution (Linux/Mac):**
```bash
sudo apt-get install tesseract-ocr
```

**Solution (Windows):**
- Download installer: https://github.com/UB-Mannheim/tesseract/wiki
- Add to PATH or set `pytesseract.pytesseract.tesseract_cmd`

### Issue: Can't read Chinese characters
**Solution:**
```bash
sudo apt-get install tesseract-ocr-chi-sim
```

### Issue: Poor OCR accuracy
**Solutions:**
- Use higher resolution screenshots (1080p or higher)
- Ensure scoreboard is fully visible
- Avoid cropped or blurry images
- Check lighting/contrast in game

## Testing

### Test the conversion locally:
```python
# Test OCR on sample image
python -c "
from PIL import Image
import pytesseract
img = Image.open('test_screenshot.png')
text = pytesseract.image_to_string(img, lang='eng+chi_sim')
print(text)
"
```

### Test in Discord:
1. Upload VALORANT Mobile scoreboard screenshot
2. Run `/scan` command
3. Check console output for:
   - ✅ Extracted text preview
   - ✅ Map name detection
   - ✅ Win/Defeat text found
   - ✅ Score extraction
   - ✅ K/D/A patterns matched
   - ✅ Team colors assigned

## Performance Notes

- **Speed**: Tesseract is fast (~1-2 seconds per screenshot)
- **Accuracy**: Good for structured text (scoreboard), may need tuning for player names
- **Offline**: Works without internet (unlike Gemini API)
- **Cost**: Completely free (no API quota/limits)

## Fallback Behavior

If Tesseract can't extract enough data:
- Minimum 8 players required (tolerates 2 missing)
- Falls back to position-based team assignment (rows 0-4 = cyan, 5-9 = red)
- Uses color detection as primary team assignment method

## Next Steps

1. ✅ Push changes to GitHub
2. ✅ Install Tesseract on Raspberry Pi
3. ✅ Test with real screenshots
4. 🔄 Fine-tune regex patterns if needed
5. 🔄 Adjust OCR config for better accuracy

---

**Migration Date**: January 2025  
**Status**: ✅ Complete  
**Breaking Changes**: None (same command interface)
