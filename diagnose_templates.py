"""
Template Matching Diagnostic Tool
Checks if templates are loaded and tests detection on a screenshot
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.template_agent_detector import TemplateAgentDetector
import cv2

def diagnose():
    print("\n" + "="*70)
    print("🔍 TEMPLATE MATCHING DIAGNOSTICS")
    print("="*70)
    
    # Initialize detector
    print("\n1️⃣ Initializing Template Detector...")
    detector = TemplateAgentDetector()
    
    # Check templates
    print(f"\n2️⃣ Checking Templates...")
    print(f"   Template directory: {detector.template_dir}")
    print(f"   Templates loaded: {len(detector.templates)}")
    
    if len(detector.templates) == 0:
        print("\n❌ NO TEMPLATES LOADED!")
        print("   Please create templates using web_crop_templates.html")
        return
    
    print("\n   ✅ Available templates:")
    for agent_name in sorted(detector.templates.keys()):
        template = detector.templates[agent_name]['color']
        print(f"      - {agent_name:12s} ({template.shape[1]}x{template.shape[0]} pixels)")
    
    # Find a test screenshot
    print(f"\n3️⃣ Looking for test screenshots...")
    screenshots_dir = Path("screenshots")
    
    # Try user's specific folder
    user_folder = Path(r"C:\Users\karti\OneDrive\Documents\VALM2\Screenshots\ss-20251027T051025Z-1-001")
    if user_folder.exists():
        screenshots = list(user_folder.glob("*.png")) + list(user_folder.glob("*.jpg"))
    else:
        screenshots = list(screenshots_dir.glob("*.png")) + list(screenshots_dir.glob("*.jpg"))
    
    if not screenshots:
        print("   ❌ No screenshots found!")
        print(f"      Looked in: {screenshots_dir}")
        print(f"      Also tried: {user_folder}")
        return
    
    test_image = screenshots[0]
    print(f"   ✅ Using test image: {test_image.name}")
    
    # Load and check image
    img = cv2.imread(str(test_image))
    if img is None:
        print(f"   ❌ Failed to load image!")
        return
    
    height, width = img.shape[:2]
    print(f"   📐 Image size: {width}x{height}")
    
    # Calculate regions
    print(f"\n4️⃣ Calculating Agent Icon Regions...")
    regions = detector.get_agent_icon_regions(height, width)
    print(f"   Total regions: {len(regions)}")
    print(f"   First region: x={regions[0]['x']}, y={regions[0]['y']}, w={regions[0]['width']}, h={regions[0]['height']}")
    
    # Create calibration image
    print(f"\n5️⃣ Creating Calibration Image...")
    calibration_result = detector.calibrate_regions(str(test_image))
    print(f"   ✅ Check 'calibration_regions.png' to see if boxes align with agent icons")
    
    # Try detection
    print(f"\n6️⃣ Testing Template Matching...")
    print(f"   This will save cropped regions to temp/debug_templates/")
    
    results = detector.detect_agents(str(test_image), debug=True)
    
    print(f"\n📊 Detection Results:")
    detected_count = sum(1 for r in results if r['agent'] != 'unknown')
    print(f"   Detected: {detected_count}/10 agents")
    
    print(f"\n   Detailed breakdown:")
    for i, r in enumerate(results):
        agent = r['agent']
        conf = r['confidence']
        status = "✅" if agent != 'unknown' else "❌"
        print(f"   {status} Slot {i+1}: {agent.upper():12s} (confidence: {conf:.1%})")
    
    # Final recommendations
    print(f"\n" + "="*70)
    print("💡 RECOMMENDATIONS:")
    print("="*70)
    
    if len(detector.templates) < 5:
        print("⚠️  You only have a few templates. Crop more agents to improve detection.")
    
    if detected_count == 0:
        print("❌ No agents detected! Possible issues:")
        print("   1. Check calibration_regions.png - are the green boxes on agent icons?")
        print("   2. If not, the region positions need adjustment")
        print("   3. Check temp/debug_templates/ - do the cropped images show agent icons?")
        print("   4. Your templates might not match the screenshot format")
    elif detected_count < 5:
        print("⚠️  Low detection rate. Possible issues:")
        print("   1. Templates might be from different screenshot resolution")
        print("   2. Region positions might need fine-tuning")
        print("   3. Crop more agent templates from your actual screenshots")
    else:
        print("✅ Detection is working! Create more templates to detect all agents.")
    
    print(f"\n📁 Files to check:")
    print(f"   - calibration_regions.png (in screenshot folder)")
    print(f"   - temp/debug_templates/*.png (cropped regions)")
    print(f"   - data/agent_templates/*.png (your templates)")

if __name__ == "__main__":
    try:
        diagnose()
    except Exception as e:
        print(f"\n❌ Error during diagnostics: {e}")
        import traceback
        traceback.print_exc()
