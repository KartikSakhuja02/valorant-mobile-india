"""
YOLO-based Agent Detector for VALORANT
Uses YOLOv8 model (best.pt) to detect agents from scoreboard screenshots
"""

from pathlib import Path
from typing import List, Dict, Any
import cv2
import numpy as np

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️ ultralytics not installed. Run: pip install ultralytics")


class YOLOAgentDetector:
    """Detects VALORANT agents using YOLOv8 model"""
    
    def __init__(self, model_path: str = None):
        """
        Initialize YOLO agent detector
        
        Args:
            model_path: Path to best.pt model file
        """
        if not YOLO_AVAILABLE:
            raise ImportError("ultralytics package not installed. Run: pip install ultralytics")
        
        # Default model path
        if model_path is None:
            model_path = Path(__file__).parent.parent / "imports" / "agents images" / "agent_weight" / "best.pt"
        
        self.model_path = Path(model_path)
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"YOLO model not found at {self.model_path}")
        
        # Load YOLO model
        print(f"Loading YOLO model from {self.model_path}...")
        try:
            self.model = YOLO(str(self.model_path))
            print("✅ YOLO model loaded successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to load YOLO model: {e}. The model file may be corrupted. Please retrain or download a valid model.")
        
        # Agent name mapping (YOLO class index -> Agent name)
        # This should match your training labels
        self.agent_names = self._get_agent_names()
    
    def _get_agent_names(self) -> Dict[int, str]:
        """
        Get agent name mapping from model
        
        Returns:
            Dictionary mapping class index to agent name
        """
        # Try to get names from model
        if hasattr(self.model, 'names'):
            return self.model.names
        
        # Fallback to standard VALORANT agent list (alphabetically by class index)
        # You may need to adjust this based on your actual training labels
        return {
            0: "Astra",
            1: "Breach",
            2: "Brimstone",
            3: "Chamber",
            4: "Clove",
            5: "Cypher",
            6: "Deadlock",
            7: "Fade",
            8: "Gekko",
            9: "Harbor",
            10: "Iso",
            11: "Jett",
            12: "KAY/O",
            13: "Killjoy",
            14: "Neon",
            15: "Omen",
            16: "Phoenix",
            17: "Raze",
            18: "Reyna",
            19: "Sage",
            20: "Skye",
            21: "Sova",
            22: "Viper",
            23: "Vyse",
            24: "Yoru"
        }
    
    def detect_agents_from_screenshot(self, image_path: str, confidence_threshold: float = 0.25) -> Dict[str, Any]:
        """
        Detect agents from a scoreboard screenshot
        
        Args:
            image_path: Path to the screenshot image
            confidence_threshold: Minimum confidence for detections (0.0 - 1.0) - Default lowered to 0.25
        
        Returns:
            Dictionary with 'agents' list (10 agents in order) and 'map' name
        """
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        # Run YOLO detection
        results = self.model(img, conf=confidence_threshold, verbose=False)
        
        # Process detections
        agents = ['Unknown'] * 10
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # Get class index and confidence
                cls_idx = int(box.cls[0].cpu().numpy())
                confidence = float(box.conf[0].cpu().numpy())
                
                # Get agent name
                agent_name = self.agent_names.get(cls_idx, "Unknown")
                
                # Calculate center Y position (for row ordering)
                center_y = (y1 + y2) / 2
                
                detections.append({
                    'agent': agent_name,
                    'confidence': confidence,
                    'y_position': center_y,
                    'bbox': (x1, y1, x2, y2)
                })
        
        # Sort detections by Y position (top to bottom)
        detections.sort(key=lambda d: d['y_position'])
        
        # Assign agents to slots (top 10)
        for i, detection in enumerate(detections[:10]):
            agents[i] = detection['agent']
            print(f"  Row {i+1}: {detection['agent']} (confidence: {detection['confidence']:.2f})")
        
        # Try to detect map (currently not implemented in YOLO, return Unknown)
        # You can add map detection logic here if your model supports it
        detected_map = 'Unknown'
        
        return {
            'agents': agents,
            'map': detected_map,
            'detections': detections  # Include raw detections for debugging
        }
    
    def detect_with_visualization(self, image_path: str, output_path: str = None, confidence_threshold: float = 0.25):
        """
        Detect agents and save visualization with bounding boxes
        
        Args:
            image_path: Path to the screenshot image
            output_path: Path to save visualization (optional)
            confidence_threshold: Minimum confidence for detections - Default lowered to 0.25
        
        Returns:
            Dictionary with detection results
        """
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        # Run YOLO detection
        results = self.model(img, conf=confidence_threshold, verbose=False)
        
        # Draw bounding boxes
        annotated_img = results[0].plot()
        
        # Save if output path provided
        if output_path:
            cv2.imwrite(str(output_path), annotated_img)
            print(f"✅ Visualization saved to {output_path}")
        
        # Get detection results
        return self.detect_agents_from_screenshot(image_path, confidence_threshold)


def get_yolo_agent_detector(model_path: str = None) -> YOLOAgentDetector:
    """
    Factory function to get YOLOAgentDetector instance
    
    Args:
        model_path: Path to best.pt model file (optional)
    
    Returns:
        YOLOAgentDetector instance
    """
    return YOLOAgentDetector(model_path)


if __name__ == "__main__":
    # Test the detector
    print("Testing YOLO Agent Detector...")
    
    try:
        detector = get_yolo_agent_detector()
        print(f"Model loaded with {len(detector.agent_names)} agent classes")
        print(f"Agent names: {list(detector.agent_names.values())}")
    except Exception as e:
        print(f"❌ Failed to initialize detector: {e}")
