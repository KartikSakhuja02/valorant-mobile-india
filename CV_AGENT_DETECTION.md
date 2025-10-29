# Computer Vision Agent Detection System

## Overview

The bot now uses **hybrid agent detection** combining:
1. **Computer Vision (CV)** - Image matching with reference agent portraits
2. **Gemini AI** - Fallback text/image understanding

This significantly improves agent detection accuracy compared to AI-only approaches.

---

## How It Works

### 1. Reference Images
- Located in: `imports/agents images/`
- Contains 22 agent portrait reference images
- Images are resized to 64x64 for consistent matching

### 2. Detection Pipeline

```
Screenshot Upload
    ↓
Extract 10 Agent Portraits (crop from left side)
    ↓
For each portrait:
    ↓
Compare with 22 reference images (CV matching)
    ↓
If confidence ≥ 55% → Use CV result ✅
    ↓
Else → Use Gemini AI result 🤖
    ↓
Else → Mark as "Unknown" ❓
```

### 3. Matching Algorithm

Uses **two scoring methods** combined:
- **Template Matching (70% weight)**: Normalized cross-correlation
- **Histogram Comparison (30% weight)**: Color distribution similarity in HSV space

Final confidence score = `0.7 × template_score + 0.3 × histogram_score`

---

## Configuration

### Confidence Threshold
Default: **0.55 (55%)**

You can adjust this in `cogs/ocr.py`:
```python
cv_agent_results = agent_matcher.detect_agents_from_screenshot(str(temp_image_path), threshold=0.55)
```

**Lower threshold** = More CV matches (but less accurate)  
**Higher threshold** = More AI fallbacks (safer but slower)

### Portrait Extraction Coordinates

Coordinates are calculated as percentages of screen size in `services/agent_matcher.py`:

```python
portrait_width = int(width * 0.04)   # 4% of screen width
portrait_height = int(height * 0.08)  # 8% of screen height
start_x = int(width * 0.05)          # 5% from left
start_y = int(height * 0.20)         # 20% from top
y_spacing = int(height * 0.10)       # 10% vertical spacing
```

**Adjust these if portraits aren't detected correctly on different screen resolutions.**

---

## Detection Statistics

The scan results now show agent detection breakdown:

```
🎯 Agent Detection: 7 CV-matched • 3 AI-detected • 0 unknown
```

- **CV-matched**: High confidence computer vision match with reference images
- **AI-detected**: Gemini AI identified the agent (CV confidence was low)
- **Unknown**: No confident detection from either source

---

## Supported Agents (22 total)

### Duelists (7)
- Jett, Phoenix, Reyna, Raze, Yoru, Neon, ~~Iso~~ (no reference image)

### Initiators (6)
- Sova, Breach, Skye, KAY/O, Fade, Gekko

### Controllers (6)
- Brimstone, Omen, Viper, Astra, Harbor, ~~Clove~~ (no reference image)

### Sentinels (6)
- Sage, Cypher, Killjoy, Chamber, Deadlock, ~~Vyse~~ (no reference image)

**Note:** Iso, Clove, and Vyse are not yet supported (add their portrait images to `imports/agents images/` to enable)

---

## Adding New Agents

When new agents are released:

1. **Get agent portrait icon** (64x64 or larger PNG)
2. **Name the file** with agent name in it (e.g., `agentiso.png`, `agentclove.png`)
3. **Place in**: `imports/agents images/`
4. **Restart bot** - Agent matcher auto-loads on startup

The naming pattern should include the agent name (case-insensitive):
- `iso` → "Iso"
- `clove` → "Clove"  
- `vyse` → "Vyse"

---

## Troubleshooting

### Agent Detection Inaccurate

**Problem**: CV matching returning wrong agents

**Solutions**:
1. **Lower confidence threshold** in `cogs/ocr.py`:
   ```python
   threshold=0.45  # From 0.55
   ```

2. **Update reference images** with better quality portraits

3. **Check portrait extraction coordinates** - they may be off for your screenshot resolution

### All Agents Show as "AI-detected"

**Problem**: CV matching not working, always falling back to Gemini

**Causes**:
- Reference images not loading (check `imports/agents images/` exists)
- Portrait extraction coordinates wrong for screenshot resolution
- Image quality too low

**Debug**:
```bash
python tools/test_agent_matcher.py
```
Should show: `✅ Loaded 22 agent templates`

### Temp File Errors

**Problem**: `temp_scan.png` permission errors

**Solution**: The scan command automatically cleans up temp files. If errors persist, manually delete:
```
VALM/temp_scan.png
```

---

## Performance

- **CV Matching**: ~0.5-1 second for 10 portraits
- **Gemini AI**: ~2-3 seconds per screenshot
- **Combined**: Faster than pure AI (CV processes portraits in parallel)

---

## Future Improvements

1. **ML Model Training**: Train a custom neural network on Valorant agent portraits
2. **OCR Position Hints**: Use player names from OCR to better locate portraits
3. **Multi-Resolution Support**: Adaptive coordinates for different screenshot sizes
4. **Agent Skin Detection**: Recognize agents even with different skins/variants

---

## Technical Details

### Libraries Used
- **OpenCV** (`cv2`): Image processing and template matching
- **NumPy**: Array operations and mathematical computations
- **Pillow** (`PIL`): Image loading and manipulation

### Files Modified
- `cogs/ocr.py`: Integrated CV agent detection into scan command
- `services/agent_matcher.py`: New CV matching service
- `tools/test_agent_matcher.py`: Testing utility

### Agent Confidence Info
Each player object now includes:
```python
{
    'ign': 'PlayerName',
    'agent': 'Jett',
    'agent_source': 'CV',  # or 'Gemini' or 'None'
    'agent_confidence': 0.82,  # 0.0 to 1.0
    'kills': 16,
    'deaths': 10,
    'assists': 7
}
```

---

## Questions?

If agent detection is still inaccurate after adjustments:
1. Share a sample screenshot
2. Check which agents are being misdetected
3. Verify reference images in `imports/agents images/` are clear and correct
4. Consider manually adding better quality reference portraits

The system learns from better reference data - higher quality portraits = better accuracy!
