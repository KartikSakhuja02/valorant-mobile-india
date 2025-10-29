"""
🚀 Quick Agent Template Extractor
Automatically extracts agent icons from Valorant scoreboards using pre-calculated positions.

This assumes standard 1920x1080 screenshots. If your screenshots are different resolution,
you may need to adjust the positions.

Usage:
    python quick_crop_templates.py
"""

import cv2
import os
from pathlib import Path

class QuickCropper:
    def __init__(self):
        self.screenshots_dir = Path("screenshots")
        self.templates_dir = Path("data/agent_templates")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Standard agent icon positions for 1920x1080 screenshots
        # These are approximate - you may need to adjust based on your screenshots
        # Format: (x, y, width, height) for each of the 10 agent positions
        self.icon_positions_1080p = [
            # Team A (top 5)
            (50, 250, 80, 80),   # Player 1
            (50, 330, 80, 80),   # Player 2
            (50, 410, 80, 80),   # Player 3
            (50, 490, 80, 80),   # Player 4
            (50, 570, 80, 80),   # Player 5
            # Team B (bottom 5)
            (50, 700, 80, 80),   # Player 6
            (50, 780, 80, 80),   # Player 7
            (50, 860, 80, 80),   # Player 8
            (50, 940, 80, 80),   # Player 9
            (50, 1020, 80, 80),  # Player 10
        ]
    
    def extract_icons_from_screenshot(self, screenshot_path):
        """Extract all 10 agent icons from a screenshot"""
        img = cv2.imread(str(screenshot_path))
        if img is None:
            print(f"❌ Failed to load {screenshot_path}")
            return []
        
        height, width = img.shape[:2]
        print(f"\n📸 Processing {screenshot_path.name} ({width}x{height})")
        
        # Scale positions if not 1080p
        scale_x = width / 1920
        scale_y = height / 1080
        
        icons = []
        for i, (x, y, w, h) in enumerate(self.icon_positions_1080p):
            # Scale position
            x1 = int(x * scale_x)
            y1 = int(y * scale_y)
            x2 = int((x + w) * scale_x)
            y2 = int((y + h) * scale_y)
            
            # Crop icon
            icon = img[y1:y2, x1:x2]
            
            if icon.size > 0:
                icons.append((i+1, icon))
            else:
                print(f"   ⚠️  Failed to crop icon {i+1}")
        
        return icons
    
    def show_icons_for_naming(self, icons, screenshot_name):
        """Show icons in a grid and let user name them"""
        if not icons:
            return
        
        print(f"\n🎯 Showing {len(icons)} icons from {screenshot_name}")
        print("   Close the preview window when done naming")
        
        # Create a grid to show all icons
        rows = 2
        cols = 5
        icon_size = 150  # Display size
        
        # Create blank canvas
        canvas = 255 * np.ones((rows * icon_size + 50, cols * icon_size, 3), dtype=np.uint8)
        
        # Place icons on canvas
        for idx, (slot, icon) in enumerate(icons):
            row = idx // cols
            col = idx % cols
            
            # Resize icon for display
            display_icon = cv2.resize(icon, (icon_size - 10, icon_size - 10))
            
            # Place on canvas
            y1 = row * icon_size + 5
            x1 = col * icon_size + 5
            y2 = y1 + display_icon.shape[0]
            x2 = x1 + display_icon.shape[1]
            
            canvas[y1:y2, x1:x2] = display_icon
            
            # Add label
            label = f"Slot {slot}"
            cv2.putText(canvas, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # Show canvas
        cv2.imshow("Agent Icons - Identify and Name Them", canvas)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # Get names from user
        print("\n📝 Enter agent names for each slot (or 'skip' to skip):")
        for slot, icon in icons:
            agent_name = input(f"   Slot {slot}: ").strip().lower()
            
            if agent_name and agent_name != 'skip':
                output_path = self.templates_dir / f"{agent_name}.png"
                cv2.imwrite(str(output_path), icon)
                print(f"      ✅ Saved {agent_name}.png")
    
    def run_auto_extract(self):
        """Automatically extract icons and show them for naming"""
        screenshots = list(self.screenshots_dir.glob("*.png")) + \
                     list(self.screenshots_dir.glob("*.jpg"))
        
        if not screenshots:
            print("❌ No screenshots found in 'screenshots/' folder!")
            return
        
        print(f"📁 Found {len(screenshots)} screenshots")
        
        for screenshot in screenshots:
            icons = self.extract_icons_from_screenshot(screenshot)
            if icons:
                self.show_icons_for_naming(icons, screenshot.name)
                
                cont = input("\n   Process next screenshot? (y/n): ").strip().lower()
                if cont != 'y':
                    break
        
        print("\n✅ Done!")

def calibrate_positions():
    """Helper to find the correct icon positions for your screenshots"""
    screenshots_dir = Path("screenshots")
    screenshots = list(screenshots_dir.glob("*.png")) + list(screenshots_dir.glob("*.jpg"))
    
    if not screenshots:
        print("❌ No screenshots found!")
        return
    
    # Load first screenshot
    img = cv2.imread(str(screenshots[0]))
    if img is None:
        print("❌ Failed to load screenshot!")
        return
    
    print("\n🎯 CALIBRATION MODE")
    print("=" * 70)
    print("Click on the agent icons in order (1-10)")
    print("This will help determine the correct positions for your screenshots")
    print("=" * 70)
    
    points = []
    
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
            cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
            cv2.putText(img, str(len(points)), (x+10, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Calibration", img)
            
            if len(points) == 10:
                print("\n✅ Got all 10 positions!")
                print("\nPaste this into the icon_positions_1080p list:")
                print("[")
                for i, (px, py) in enumerate(points):
                    print(f"    ({px-40}, {py-40}, 80, 80),  # Player {i+1}")
                print("]")
    
    cv2.namedWindow("Calibration")
    cv2.setMouseCallback("Calibration", mouse_callback)
    cv2.imshow("Calibration", img)
    
    print("\nClick on each agent icon (1-10)...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    import numpy as np
    
    print("\n" + "="*70)
    print("🚀 QUICK AGENT TEMPLATE EXTRACTOR")
    print("="*70)
    print("\nChoose mode:")
    print("  1. Auto-extract (uses pre-defined positions)")
    print("  2. Calibrate positions (find positions for your screenshots)")
    
    choice = input("\nYour choice (1/2): ").strip()
    
    if choice == "2":
        calibrate_positions()
    else:
        cropper = QuickCropper()
        cropper.run_auto_extract()
