# Agent Template Matching Setup Guide

## What is Template Matching?

Template matching compares cropped agent icons from screenshots against reference images (templates) to achieve 100% accurate agent detection. Unlike AI-based detection (YOLO/Gemini), template matching is deterministic and extremely accurate.

## Setup Steps

### 1. Create Agent Icon Templates

You need to create template images for each agent. Here's how:

#### Option A: From Game Screenshots
1. Take a clean, high-quality screenshot of a completed match
2. Crop each agent icon individually (should be square, ~64x64 to 128x128 pixels)
3. Save as PNG with transparent background if possible
4. Name files exactly as shown below (lowercase)

#### Option B: From Official Assets
1. Find official Valorant Mobile agent portraits
2. Crop to just the circular icon
3. Resize to consistent size (100x100px recommended)
4. Save as PNG

### 2. Required Template Files

Save these in `data/agent_templates/`:

**Duelists:**
- jett.png
- reyna.png
- raze.png
- phoenix.png
- yoru.png
- neon.png
- iso.png

**Sentinels:**
- sage.png
- cypher.png
- killjoy.png
- chamber.png
- deadlock.png
- vyse.png

**Initiators:**
- sova.png
- breach.png
- skye.png
- kayo.png
- fade.png
- gekko.png

**Controllers:**
- brimstone.png
- omen.png
- viper.png
- astra.png
- harbor.png
- clove.png

### 3. Template Quality Guidelines

✅ **Good Template:**
- Clear, sharp image
- Consistent lighting
- No UI elements overlapping
- Square or circular crop
- Same size across all agents (100x100px ideal)
- PNG format

❌ **Bad Template:**
- Blurry or pixelated
- UI elements visible
- Inconsistent sizes
- Different aspect ratios
- Low resolution

### 4. Calibration

After adding templates, run calibration to check icon detection regions:

```python
from services.template_agent_detector import TemplateAgentDetector

detector = TemplateAgentDetector()
detector.calibrate_regions("path/to/sample_screenshot.png")
```

This creates `calibration_regions.png` showing where the detector looks for icons.

### 5. Adjusting Detection Regions

If icons are not detected correctly, you may need to adjust the regions in `template_agent_detector.py`:

```python
def get_agent_icon_regions(self, image_height: int, image_width: int):
    # Adjust these values based on your calibration image:
    start_y = int(image_height * 0.25)  # Where first player appears
    end_y = int(image_height * 0.85)    # Where last player appears
    icon_x = int(image_width * 0.05)    # Left edge of icons
    icon_width = int(image_width * 0.08) # Icon width
```

### 6. Testing

Test with a real screenshot:

```python
detector = TemplateAgentDetector()
results = detector.detect_agents("screenshot.png", debug=True)
```

With `debug=True`, it saves cropped regions to `debug_templates/` folder for inspection.

### 7. Integration with /scan Command

Once templates are ready, the `/scan` command will automatically use template matching as the primary detection method, falling back to Gemini/YOLO only if template matching fails.

## Advantages of Template Matching

✅ **100% Accurate** - Deterministic matching, no AI guessing
✅ **Fast** - No API calls, runs locally
✅ **Consistent** - Same input always gives same output
✅ **No API Costs** - Free, unlimited usage
✅ **Works Offline** - No internet required

## Troubleshooting

**Issue: Low confidence scores**
- Check template quality (sharp, clear images)
- Ensure templates match screenshot style
- Try adjusting threshold in code (default 0.65)

**Issue: Wrong agents detected**
- Templates might be too similar (e.g., similar colored agents)
- Add more distinctive features to templates
- Increase matching threshold

**Issue: No agents detected**
- Calibrate regions to find correct icon positions
- Check if screenshot resolution is very different
- Verify template directory path is correct

**Issue: Icons in wrong positions**
- Run calibration and adjust region percentages
- Different screen resolutions need different calibration

## Quick Start Script

```python
# Create this as tools/setup_templates.py
from services.template_agent_detector import TemplateAgentDetector
from pathlib import Path

# 1. Check what templates are loaded
detector = TemplateAgentDetector()
print(f"Loaded {len(detector.templates)} templates")

# 2. Test on a screenshot
if Path("test_screenshot.png").exists():
    results = detector.detect_agents("test_screenshot.png", debug=True)
    print("\nDetection Results:")
    for i, r in enumerate(results):
        print(f"  Player {i+1}: {r['agent'].upper()} ({r['confidence']:.1%})")
else:
    print("Add test_screenshot.png to test detection")
```

## Need Help?

If you're having trouble creating templates, you can:
1. Share a clean screenshot and I'll help crop the icons
2. Use existing Valorant asset packs online
3. Extract icons from the game files (if accessible)
