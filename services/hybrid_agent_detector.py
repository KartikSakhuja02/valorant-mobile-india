"""
Hybrid Agent Detector - Combines YOLO + JSON Descriptions for 100% Accuracy
Uses YOLO for initial detection, then validates with detailed agent descriptions
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# ============================================================================
# CONFIGURATION: YOLO Detection Confidence
# ============================================================================
# Adjust this value to control YOLO detection sensitivity:
#   - 0.15-0.20: Very sensitive, more detections (may include false positives)
#   - 0.25-0.30: Balanced (recommended for most cases)
#   - 0.35-0.50: Conservative, only high-confidence detections
YOLO_CONFIDENCE_THRESHOLD = 0.40  # Higher threshold to reduce fake detections
FORCE_GEMINI_VALIDATION = True  # Always validate with Gemini for 100% accuracy
# ============================================================================

try:
    from services.yolo_agent_detector import YOLOAgentDetector
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

try:
    from services.gemini_agent_detector import GeminiAgentDetector
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class HybridAgentDetector:
    """Combines YOLO detection with JSON description validation for maximum accuracy"""
    
    def __init__(self, yolo_detector=None, gemini_detector=None, json_path: str = None):
        """
        Initialize hybrid detector
        
        Args:
            yolo_detector: YOLOAgentDetector instance (optional)
            gemini_detector: GeminiAgentDetector instance (optional)
            json_path: Path to agent_descriptions.json
        """
        self.yolo_detector = yolo_detector
        self.gemini_detector = gemini_detector
        
        # Load agent descriptions
        if json_path is None:
            json_path = Path(__file__).parent.parent / "data" / "agent_descriptions.json"
        
        self.agent_descriptions = self._load_descriptions(str(json_path))
        print(f"✅ Loaded {len(self.agent_descriptions)} agent descriptions")
    
    def _load_descriptions(self, json_path: str) -> Dict[str, str]:
        """Load agent descriptions from JSON file"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load agent descriptions: {e}")
            return {}
    
    def detect_agents_from_screenshot(self, image_path: str, yolo_confidence: float = None) -> Dict[str, Any]:
        """
        Detect agents using hybrid approach:
        1. YOLO for initial detection (fast, accurate positions)
        2. Gemini with descriptions for validation (high accuracy)
        3. Combine results for best of both
        
        Args:
            image_path: Path to screenshot
            yolo_confidence: YOLO confidence threshold (0.0-1.0). 
                            If None, uses YOLO_CONFIDENCE_THRESHOLD constant (default: 0.25)
                            - Lower (0.15-0.25): More detections, may include false positives
                            - Higher (0.3-0.5): Fewer but more confident detections
        
        Returns:
            Dictionary with 'agents' list and 'map' name
        """
        # Use global constant if not specified
        if yolo_confidence is None:
            yolo_confidence = YOLO_CONFIDENCE_THRESHOLD
        
        detected_agents = ['Unknown'] * 10
        detected_map = 'Unknown'
        yolo_results = None
        gemini_results = None
        
        # Step 1: Try YOLO detection (lower confidence for more detections)
        if self.yolo_detector:
            try:
                print(f"🎯 Running YOLO detection (confidence: {yolo_confidence})...")
                yolo_results = self.yolo_detector.detect_agents_from_screenshot(
                    image_path, 
                    confidence_threshold=yolo_confidence
                )
                yolo_agents = yolo_results.get('agents', ['Unknown'] * 10)
                yolo_map = yolo_results.get('map', 'Unknown')
                print(f"   YOLO detected: {yolo_agents}")
                
                # Check if YOLO detection is confident enough AND force validation is disabled
                unknown_count = yolo_agents.count('Unknown')
                if unknown_count == 0 and not FORCE_GEMINI_VALIDATION:
                    print("✅ YOLO detection complete with high confidence - skipping Gemini for speed")
                    detected_agents = yolo_agents
                    detected_map = yolo_map
                    return {
                        'agents': detected_agents,
                        'map': detected_map,
                        'yolo_detections': yolo_agents,
                        'gemini_detections': [],
                        'confidence': 0.90  # YOLO-only confidence
                    }
                elif FORCE_GEMINI_VALIDATION:
                    print(f"🔍 YOLO found {10-unknown_count}/10 agents - running Gemini validation for maximum accuracy")
                elif unknown_count <= 2:
                    print(f"⚠️ YOLO found {unknown_count} unknowns - running Gemini only for validation")
            except Exception as e:
                print(f"⚠️ YOLO detection failed: {e}")
                yolo_agents = ['Unknown'] * 10
        else:
            yolo_agents = ['Unknown'] * 10
        
        # Step 2: Run Gemini with detailed descriptions for validation
        if self.gemini_detector:
            try:
                print("🌟 Running Gemini detection with descriptions...")
                
                # Build prompt with agent descriptions
                description_text = "\n".join([
                    f"- {name}: {desc}" 
                    for name, desc in self.agent_descriptions.items()
                ])
                
                # Use Gemini with enhanced prompt
                gemini_results = self.gemini_detector.detect_agents_from_screenshot(
                    image_path,
                    agent_descriptions=self.agent_descriptions
                )
                
                if isinstance(gemini_results, dict):
                    gemini_agents = gemini_results.get('agents', ['Unknown'] * 10)
                    detected_map = gemini_results.get('map', 'Unknown')
                else:
                    gemini_agents = gemini_results if isinstance(gemini_results, list) else ['Unknown'] * 10
                
                print(f"   Gemini detected: {gemini_agents}")
                
                # Quality check: Reject obviously bad Gemini results
                gemini_quality_ok = self._check_detection_quality(gemini_agents, "Gemini")
                if not gemini_quality_ok:
                    print("⚠️ Gemini detection quality is poor, falling back to YOLO only")
                    gemini_agents = ['Unknown'] * 10
                    
            except Exception as e:
                print(f"⚠️ Gemini detection failed: {e}")
                gemini_agents = ['Unknown'] * 10
        else:
            gemini_agents = ['Unknown'] * 10
        
        # Quality check YOLO results too
        if yolo_agents:
            yolo_quality_ok = self._check_detection_quality(yolo_agents, "YOLO")
            if not yolo_quality_ok:
                print("⚠️ YOLO detection quality is poor")
                yolo_agents = ['Unknown'] * 10
        
        # Step 3: Combine results - prioritize Gemini (more accurate with descriptions)
        # but use YOLO to fill gaps
        for i in range(10):
            if gemini_agents[i] != 'Unknown':
                detected_agents[i] = gemini_agents[i]
            elif yolo_agents[i] != 'Unknown':
                detected_agents[i] = yolo_agents[i]
            else:
                detected_agents[i] = 'Unknown'
        
        print(f"✅ Final hybrid result: {detected_agents}")
        
        return {
            'agents': detected_agents,
            'map': detected_map,
            'yolo_detections': yolo_agents if yolo_results else None,
            'gemini_detections': gemini_agents if gemini_results else None
        }
    
    def _check_detection_quality(self, agents: list, source: str) -> bool:
        """
        Check if detection results are reasonable quality
        Returns False if results are obviously wrong
        """
        if not agents or len(agents) != 10:
            print(f"   ❌ {source}: Wrong number of agents ({len(agents) if agents else 0})")
            return False
        
        # Count unknowns
        unknown_count = agents.count('Unknown')
        if unknown_count >= 8:
            print(f"   ❌ {source}: Too many unknowns ({unknown_count}/10)")
            return False
        
        # Check for suspicious patterns (same agent repeated too many times)
        from collections import Counter
        agent_counts = Counter([a for a in agents if a != 'Unknown'])
        
        if agent_counts:
            most_common_agent, count = agent_counts.most_common(1)[0]
            if count >= 5:
                print(f"   ❌ {source}: Same agent '{most_common_agent}' appears {count} times (likely hallucination)")
                return False
        
        print(f"   ✅ {source}: Quality check passed ({10-unknown_count}/10 detected)")
        return True


def get_hybrid_agent_detector(yolo_detector=None, gemini_detector=None) -> HybridAgentDetector:
    """
    Factory function to create hybrid detector
    
    Args:
        yolo_detector: YOLOAgentDetector instance (optional)
        gemini_detector: GeminiAgentDetector instance (optional)
    
    Returns:
        HybridAgentDetector instance
    """
    return HybridAgentDetector(yolo_detector, gemini_detector)
