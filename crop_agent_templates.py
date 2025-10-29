"""
🎯 Interactive Agent Icon Cropper
This script helps you create template images for agent detection by:
1. Showing you each screenshot
2. Letting you click to select agent icons
3. Automatically saving with the correct agent name
4. Tracking which agents you still need

Usage:
    python crop_agent_templates.py
"""

import cv2
import os
import json
from pathlib import Path

# All 25 Valorant agents (lowercase)
ALL_AGENTS = [
    'astra', 'breach', 'brimstone', 'chamber', 'clove',
    'cypher', 'deadlock', 'fade', 'gekko', 'harbor',
    'iso', 'jett', 'kayo', 'killjoy', 'neon',
    'omen', 'phoenix', 'raze', 'reyna', 'sage',
    'skye', 'sova', 'viper', 'vyse', 'yoru'
]

class AgentCropper:
    def __init__(self):
        self.screenshots_dir = Path("C:\\Users\\karti\\OneDrive\\Documents\\VALM2\\Screenshots\\ss-20251027T051025Z-1-001")
        self.templates_dir = Path("data/agent_templates")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Track what we've cropped
        self.cropped_agents = set()
        self.load_existing_templates()
        
        # For mouse click handling
        self.points = []
        self.current_image = None
        self.current_display = None
        
    def load_existing_templates(self):
        """Load list of agents we already have templates for"""
        for template_file in self.templates_dir.glob("*.png"):
            agent_name = template_file.stem.lower()
            if agent_name in ALL_AGENTS:
                self.cropped_agents.add(agent_name)
        
        print(f"✅ Found {len(self.cropped_agents)} existing templates")
        if self.cropped_agents:
            print(f"   Already have: {', '.join(sorted(self.cropped_agents))}")
    
    def get_missing_agents(self):
        """Get list of agents we still need"""
        return [a for a in ALL_AGENTS if a not in self.cropped_agents]
    
    def redraw_display(self):
        """Redraw the display with current points and rectangle"""
        # Work on original image, then resize for display
        temp_img = self.current_image.copy()
        
        # Draw points on original size image
        for i, (x, y) in enumerate(self.points):
            cv2.circle(temp_img, (x, y), 8, (0, 255, 0), -1)
            cv2.putText(temp_img, str(i+1), (x+15, y-15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        # Draw rectangle if we have 2 points
        if len(self.points) == 2:
            cv2.rectangle(temp_img, self.points[0], self.points[1], (0, 255, 0), 4)
        
        # Resize to 1920x1080 for display
        self.current_display = cv2.resize(temp_img, (1920, 1080), interpolation=cv2.INTER_AREA)
        cv2.imshow("Crop Agent Icons", self.current_display)
    
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks for selecting crop area - OPTIMIZED"""
        if event == cv2.EVENT_LBUTTONDOWN and len(self.points) < 2:
            # Scale coordinates back to original image size
            scale_x = self.original_width / 1920
            scale_y = self.original_height / 1080
            original_x = int(x * scale_x)
            original_y = int(y * scale_y)
            
            self.points.append((original_x, original_y))
            print(f"   ✅ Point {len(self.points)} selected: ({original_x}, {original_y})")
            
            # Only redraw if we have exactly 2 points
            if len(self.points) == 2:
                print("   🎯 Both corners selected! Drawing rectangle...")
                self.redraw_display()
    
    def crop_from_screenshot(self, screenshot_path):
        """Interactive cropping from a single screenshot - OPTIMIZED"""
        # Read image
        self.current_image = cv2.imread(str(screenshot_path))
        if self.current_image is None:
            print(f"❌ Failed to load {screenshot_path}")
            return False
        
        # Store original dimensions for coordinate scaling
        self.original_height, self.original_width = self.current_image.shape[:2]
        print(f"   📐 Original size: {self.original_width}x{self.original_height}")
        
        # Resize for display (1920x1080)
        self.current_display = cv2.resize(self.current_image, (1920, 1080), interpolation=cv2.INTER_AREA)
        
        # Create window
        cv2.namedWindow("Crop Agent Icons", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Crop Agent Icons", 1920, 1080)
        cv2.setMouseCallback("Crop Agent Icons", self.mouse_callback)
        
        print(f"\n📸 Cropping from: {screenshot_path.name}")
        print("=" * 70)
        
        while True:
            # Reset points only (don't recreate image every time)
            self.points = []
            
            # Create instructions overlay ONCE
            instructions = self.current_display.copy()
            
            # Add semi-transparent overlay for text
            overlay = instructions.copy()
            cv2.rectangle(overlay, (10, 10), (700, 200), (0, 0, 0), -1)
            instructions = cv2.addWeighted(instructions, 0.7, overlay, 0.3, 0)
            
            # Add text instructions
            y_offset = 35
            cv2.putText(instructions, "INSTRUCTIONS:", (20, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            y_offset += 35
            cv2.putText(instructions, "1. Click TOP-LEFT corner of agent icon", (20, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            y_offset += 30
            cv2.putText(instructions, "2. Click BOTTOM-RIGHT corner of agent icon", (20, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            y_offset += 30
            cv2.putText(instructions, "3. Type agent name and press ENTER", (20, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            y_offset += 40
            cv2.putText(instructions, "Press 'N' for next screenshot | 'Q' to quit", (20, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.imshow("Crop Agent Icons", instructions)
            
            # Wait for user to select area - OPTIMIZED with faster refresh
            while len(self.points) < 2:
                key = cv2.waitKey(50) & 0xFF  # Faster refresh rate
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    return False
                elif key == ord('n'):
                    return True  # Next screenshot
            
            # Get crop coordinates (these are in original image coordinates)
            x1, y1 = self.points[0]
            x2, y2 = self.points[1]
            
            # Ensure correct order
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            
            # Show preview with rectangle
            self.redraw_display()
            cv2.waitKey(100)  # Small delay to ensure display updates
            
            # Get agent name
            print("\n🎯 Area selected!")
            print(f"   Missing agents: {', '.join(self.get_missing_agents())}")
            agent_name = input("   Enter agent name (or 'skip'/'next'/'quit'): ").strip().lower()
            
            if agent_name == 'quit' or agent_name == 'q':
                cv2.destroyAllWindows()
                return False
            elif agent_name == 'next' or agent_name == 'n':
                return True
            elif agent_name == 'skip' or agent_name == 's':
                continue
            elif agent_name not in ALL_AGENTS:
                print(f"   ⚠️  '{agent_name}' is not a valid agent name!")
                print(f"   Valid agents: {', '.join(ALL_AGENTS)}")
                continue
            
            # Crop and save
            cropped = self.current_image[y1:y2, x1:x2]
            output_path = self.templates_dir / f"{agent_name}.png"
            cv2.imwrite(str(output_path), cropped)
            
            self.cropped_agents.add(agent_name)
            print(f"   ✅ Saved {agent_name}.png ({cropped.shape[1]}x{cropped.shape[0]})")
            print(f"   📊 Progress: {len(self.cropped_agents)}/25 agents")
            
            # Ask if they want to crop more from this screenshot
            continue_crop = input("   Crop another icon from this screenshot? (y/n): ").strip().lower()
            if continue_crop != 'y':
                return True
    
    def run(self):
        """Main interactive loop"""
        print("\n" + "="*70)
        print("🎯 VALORANT AGENT ICON CROPPER")
        print("="*70)
        print(f"📊 Progress: {len(self.cropped_agents)}/25 agents")
        
        missing = self.get_missing_agents()
        if not missing:
            print("\n✅ All 25 agents already have templates!")
            print("   Delete templates from data/agent_templates/ if you want to recreate them.")
            return
        
        print(f"\n📝 Still need: {', '.join(missing)}")
        print("\n" + "="*70)
        
        # Get all screenshots
        screenshots = list(self.screenshots_dir.glob("*.png")) + \
                     list(self.screenshots_dir.glob("*.jpg")) + \
                     list(self.screenshots_dir.glob("*.jpeg"))
        
        if not screenshots:
            print("❌ No screenshots found in 'screenshots/' folder!")
            print("   Add some Valorant scoreboard screenshots and try again.")
            return
        
        print(f"📁 Found {len(screenshots)} screenshots\n")
        
        # Process each screenshot
        for i, screenshot in enumerate(screenshots):
            print(f"\n[{i+1}/{len(screenshots)}] Processing {screenshot.name}...")
            
            should_continue = self.crop_from_screenshot(screenshot)
            if not should_continue:
                break
            
            # Check if we're done
            missing = self.get_missing_agents()
            if not missing:
                print("\n" + "="*70)
                print("🎉 SUCCESS! All 25 agents have templates!")
                print("="*70)
                break
        
        cv2.destroyAllWindows()
        
        # Final summary
        print("\n" + "="*70)
        print("📊 FINAL SUMMARY")
        print("="*70)
        print(f"✅ Completed: {len(self.cropped_agents)}/25 agents")
        
        missing = self.get_missing_agents()
        if missing:
            print(f"❌ Still missing: {', '.join(missing)}")
            print("\n💡 Tips:")
            print("   - Look for screenshots with these agents")
            print("   - Run this script again to continue")
        else:
            print("✅ All agents complete! Ready for template matching!")
            print("\n🚀 Next steps:")
            print("   1. Test with: /scan [scoreboard image]")
            print("   2. Check terminal logs for detection confidence")
            print("   3. Re-crop any agents with low confidence")

if __name__ == "__main__":
    try:
        cropper = AgentCropper()
        cropper.run()
    except KeyboardInterrupt:
        print("\n\n👋 Cropping cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
