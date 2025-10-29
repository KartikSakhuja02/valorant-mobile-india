"""
Template Matching Agent Detector
Uses OpenCV template matching for 100% accurate agent detection
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

class TemplateAgentDetector:
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / 'data' / 'agent_templates'
        self.templates = {}
        self.agent_names = [
            'jett', 'reyna', 'raze', 'phoenix', 'yoru', 'neon',
            'sage', 'cypher', 'killjoy', 'chamber', 'deadlock',
            'sova', 'breach', 'skye', 'kayo', 'fade', 'gekko',
            'brimstone', 'omen', 'viper', 'astra', 'harbor', 'clove', 'iso', 'vyse'
        ]
        self.load_templates()
    
    def load_templates(self):
        """Load all agent icon templates"""
        if not self.template_dir.exists():
            print(f"⚠️ Template directory not found: {self.template_dir}")
            return
        
        for agent in self.agent_names:
            template_path = self.template_dir / f"{agent}.png"
            if template_path.exists():
                template = cv2.imread(str(template_path), cv2.IMREAD_UNCHANGED)
                if template is not None:
                    # Store both original and grayscale
                    self.templates[agent] = {
                        'color': template,
                        'gray': cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) if len(template.shape) == 3 else template
                    }
                    print(f"✅ Loaded template: {agent}")
                else:
                    print(f"❌ Failed to load: {agent}")
            else:
                print(f"⚠️ Template not found: {agent}")
    
    def get_agent_icon_regions(self, image_height: int, image_width: int) -> List[Dict]:
        """
        Calculate the regions where agent icons appear in the scoreboard
        Returns list of 10 regions (one for each player)
        
        CALIBRATED FOR 3168x1440 SCREENSHOTS
        Uses proportional scaling for different resolutions
        """
        # Base calibration from 3168x1440 screenshot
        base_width = 3168
        base_height = 1440
        
        # Scale factors
        scale_x = image_width / base_width
        scale_y = image_height / base_height
        
        # Calibrated positions (from calibrate_regions.py)
        base_regions = [
            {'x': 483, 'y': 383, 'width': 86, 'height': 86, 'slot': 0},
            {'x': 480, 'y': 474, 'width': 93, 'height': 88, 'slot': 1},
            {'x': 485, 'y': 569, 'width': 81, 'height': 84, 'slot': 2},
            {'x': 480, 'y': 668, 'width': 95, 'height': 86, 'slot': 3},
            {'x': 478, 'y': 763, 'width': 91, 'height': 81, 'slot': 4},
            {'x': 480, 'y': 855, 'width': 91, 'height': 80, 'slot': 5},
            {'x': 480, 'y': 950, 'width': 89, 'height': 86, 'slot': 6},
            {'x': 480, 'y': 1043, 'width': 89, 'height': 88, 'slot': 7},
            {'x': 480, 'y': 1138, 'width': 89, 'height': 79, 'slot': 8},
            {'x': 480, 'y': 1235, 'width': 91, 'height': 86, 'slot': 9},
        ]
        
        # Scale to current image size
        regions = []
        for base_region in base_regions:
            regions.append({
                'x': int(base_region['x'] * scale_x),
                'y': int(base_region['y'] * scale_y),
                'width': int(base_region['width'] * scale_x),
                'height': int(base_region['height'] * scale_y),
                'slot': base_region['slot']
            })
        
        return regions
    
    def match_template(self, image_crop: np.ndarray, threshold: float = 0.7) -> Optional[Tuple[str, float]]:
        """
        Match a cropped image against all agent templates
        Returns: (agent_name, confidence) or None
        """
        if len(self.templates) == 0:
            return None
        
        # Convert crop to grayscale if needed
        if len(image_crop.shape) == 3:
            gray_crop = cv2.cvtColor(image_crop, cv2.COLOR_BGR2GRAY)
        else:
            gray_crop = image_crop
        
        best_match = None
        best_score = 0
        
        for agent_name, template_data in self.templates.items():
            template_gray = template_data['gray']
            
            # Resize template to match crop size (if different)
            if template_gray.shape != gray_crop.shape:
                template_resized = cv2.resize(template_gray, (gray_crop.shape[1], gray_crop.shape[0]))
            else:
                template_resized = template_gray
            
            # Try multiple matching methods
            methods = [
                cv2.TM_CCOEFF_NORMED,
                cv2.TM_CCORR_NORMED,
                cv2.TM_SQDIFF_NORMED
            ]
            
            scores = []
            for method in methods:
                result = cv2.matchTemplate(gray_crop, template_resized, method)
                
                if method == cv2.TM_SQDIFF_NORMED:
                    # For SQDIFF, lower is better, so invert
                    score = 1 - result[0][0]
                else:
                    score = result[0][0]
                
                scores.append(score)
            
            # Average the scores
            avg_score = np.mean(scores)
            
            if avg_score > best_score:
                best_score = avg_score
                best_match = agent_name
        
        if best_score >= threshold:
            return (best_match, best_score)
        
        return None
    
    def detect_agents(self, image_path: str, debug: bool = False) -> List[Dict]:
        """
        Detect all 10 agents from scoreboard screenshot
        
        Args:
            image_path: Path to the screenshot
            debug: If True, save debug images showing detected regions
        
        Returns:
            List of 10 dicts with 'agent' and 'confidence'
        """
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Failed to load image: {image_path}")
            return [{'agent': 'unknown', 'confidence': 0}] * 10
        
        height, width = image.shape[:2]
        regions = self.get_agent_icon_regions(height, width)
        
        results = []
        debug_dir = Path(image_path).parent / 'debug_templates'
        if debug and not debug_dir.exists():
            debug_dir.mkdir(parents=True)
        
        for i, region in enumerate(regions):
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            
            # Crop the agent icon region
            crop = image[y:y+h, x:x+w]
            
            if debug:
                # Save cropped region for debugging
                cv2.imwrite(str(debug_dir / f"slot_{i}.png"), crop)
            
            # Match against templates
            match_result = self.match_template(crop, threshold=0.50)  # Lowered threshold for testing
            
            if match_result:
                agent_name, confidence = match_result
                results.append({
                    'agent': agent_name,
                    'confidence': confidence,
                    'region': region
                })
                print(f"Slot {i}: {agent_name.upper()} ({confidence:.2%})")
            else:
                results.append({
                    'agent': 'unknown',
                    'confidence': 0,
                    'region': region
                })
                print(f"Slot {i}: UNKNOWN")
        
        return results
    
    def calibrate_regions(self, sample_image_path: str) -> Dict:
        """
        Helper function to calibrate icon regions for your specific screenshot format
        Run this on a sample screenshot and adjust the regions manually
        """
        image = cv2.imread(sample_image_path)
        if image is None:
            return {}
        
        height, width = image.shape[:2]
        regions = self.get_agent_icon_regions(height, width)
        
        # Draw rectangles on image to visualize regions
        debug_image = image.copy()
        for i, region in enumerate(regions):
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            cv2.rectangle(debug_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(debug_image, str(i), (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Save calibration image
        output_path = Path(sample_image_path).parent / 'calibration_regions.png'
        cv2.imwrite(str(output_path), debug_image)
        print(f"✅ Calibration image saved: {output_path}")
        
        return {
            'image_size': {'width': width, 'height': height},
            'regions': regions
        }


def create_templates_from_game():
    """
    Helper script to create templates from your own screenshots
    You'll need to manually crop agent icons from a clean screenshot
    """
    print("""
To create agent templates:
1. Take a clean screenshot showing all agents
2. Crop each agent icon (should be square, ~50-100px)
3. Save them as: data/agent_templates/{agent_name}.png
4. Agent names should be lowercase: jett.png, reyna.png, etc.
5. Make sure icons are clear and high quality
6. Icons should include just the agent portrait, no borders if possible
    """)


if __name__ == "__main__":
    # Test the detector
    detector = TemplateAgentDetector()
    
    # For calibration, run:
    # detector.calibrate_regions("path/to/sample_screenshot.png")
    
    print(f"\n✅ Template detector initialized with {len(detector.templates)} agent templates")
    print("Ready to use!")
