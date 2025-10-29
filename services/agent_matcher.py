"""
Agent Matcher Service - Image-based agent detection using computer vision
Uses template matching and feature comparison with reference agent images
"""

import os
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

class AgentMatcher:
    def __init__(self, agent_images_dir: str = "imports/agents images"):
        """
        Initialize the agent matcher with reference agent images
        
        Args:
            agent_images_dir: Directory containing reference agent portrait images
        """
        self.agent_images_dir = Path(agent_images_dir)
        self.agent_templates = {}
        self.agent_names = {}
        self.load_agent_templates()
    
    def load_agent_templates(self):
        """Load all agent reference images and create templates for matching"""
        if not self.agent_images_dir.exists():
            logger.error(f"Agent images directory not found: {self.agent_images_dir}")
            return
        
        # Mapping of filename patterns to agent names
        agent_mapping = {
            "astra": "Astra",
            "breach": "Breach",
            "brimstone": "Brimstone",
            "chamber": "Chamber",
            "cypher": "Cypher",
            "deadlock": "Deadlock",
            "fade": "Fade",
            "gekko": "Gekko",
            "harbor": "Harbor",
            "jett": "Jett",
            "kayo": "KAY/O",
            "killjoy": "Killjoy",
            "neon": "Neon",
            "omen": "Omen",
            "phoenix": "Phoenix",
            "raze": "Raze",
            "reyna": "Reyna",
            "sage": "Sage",
            "skye": "Skye",
            "sova": "Sova",
            "viper": "Viper",
            "yoru": "Yoru",
            "clove": "Clove",
            "iso": "Iso",
            "vyse": "Vyse"
        }
        
        for image_file in self.agent_images_dir.glob("*.png"):
            filename = image_file.stem.lower()
            
            # Find matching agent name
            for pattern, agent_name in agent_mapping.items():
                if pattern in filename:
                    try:
                        # Load image with OpenCV
                        template = cv2.imread(str(image_file))
                        if template is not None:
                            # Resize to standard size for consistency (64x64)
                            template = cv2.resize(template, (64, 64))
                            self.agent_templates[agent_name] = template
                            self.agent_names[agent_name] = agent_name
                            logger.info(f"Loaded agent template: {agent_name}")
                        else:
                            logger.warning(f"Failed to load image: {image_file}")
                    except Exception as e:
                        logger.error(f"Error loading {image_file}: {e}")
                    break
        
        logger.info(f"Loaded {len(self.agent_templates)} agent templates")
    
    def match_agent(self, portrait_image: np.ndarray, threshold: float = 0.6) -> Tuple[Optional[str], float]:
        """
        Match a cropped agent portrait against reference images
        
        Args:
            portrait_image: Cropped agent portrait from screenshot (numpy array)
            threshold: Minimum similarity score (0-1) to consider a match
            
        Returns:
            Tuple of (agent_name, confidence_score)
        """
        if not self.agent_templates:
            logger.warning("No agent templates loaded")
            return None, 0.0
        
        # Resize portrait to match template size
        try:
            portrait_resized = cv2.resize(portrait_image, (64, 64))
        except Exception as e:
            logger.error(f"Error resizing portrait: {e}")
            return None, 0.0
        
        best_match = None
        best_score = 0.0
        
        # Try multiple matching methods and combine scores
        for agent_name, template in self.agent_templates.items():
            # Method 1: Template Matching (Normalized Cross-Correlation)
            result = cv2.matchTemplate(portrait_resized, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            score_tm = max_val
            
            # Method 2: Structural Similarity (SSIM-like via histogram comparison)
            portrait_hsv = cv2.cvtColor(portrait_resized, cv2.COLOR_BGR2HSV)
            template_hsv = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)
            
            hist_portrait = cv2.calcHist([portrait_hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            hist_template = cv2.calcHist([template_hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            
            hist_portrait = cv2.normalize(hist_portrait, hist_portrait).flatten()
            hist_template = cv2.normalize(hist_template, hist_template).flatten()
            
            score_hist = cv2.compareHist(hist_portrait, hist_template, cv2.HISTCMP_CORREL)
            
            # Combine scores (weighted average)
            combined_score = (0.7 * score_tm + 0.3 * score_hist)
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = agent_name
        
        # Only return match if above threshold
        if best_score >= threshold:
            logger.info(f"Matched agent: {best_match} (confidence: {best_score:.2f})")
            return best_match, best_score
        else:
            logger.warning(f"No confident match found. Best: {best_match} ({best_score:.2f})")
            return None, best_score
    
    def extract_agent_portraits(self, screenshot_path: str) -> List[Tuple[np.ndarray, dict]]:
        """
        Extract agent portraits from a Valorant scoreboard screenshot
        
        Args:
            screenshot_path: Path to the scoreboard screenshot
            
        Returns:
            List of tuples (portrait_image, metadata) for each player
        """
        try:
            # Load screenshot
            img = cv2.imread(screenshot_path)
            if img is None:
                logger.error(f"Failed to load screenshot: {screenshot_path}")
                return []
            
            height, width = img.shape[:2]
            
            # Valorant scoreboard layout (approximate positions)
            # Agent portraits are typically in a vertical list on the left side
            # These coordinates may need adjustment based on resolution
            
            portraits = []
            
            # Estimate portrait positions (5 players per team, 10 total)
            # Assuming 1920x1080 resolution, adjust proportionally
            
            # Agent portraits are typically around x=50-150, starting y=200
            portrait_width = int(width * 0.04)  # ~4% of screen width
            portrait_height = int(height * 0.08)  # ~8% of screen height
            
            start_x = int(width * 0.05)  # 5% from left
            start_y = int(height * 0.20)  # 20% from top
            
            y_spacing = int(height * 0.10)  # 10% vertical spacing between portraits
            
            # Extract 10 portraits (5 per team)
            for i in range(10):
                y_pos = start_y + (i * y_spacing)
                
                # Crop portrait region
                portrait = img[y_pos:y_pos+portrait_height, start_x:start_x+portrait_width]
                
                if portrait.size > 0:
                    metadata = {
                        'player_index': i,
                        'team': 'Team 1' if i < 5 else 'Team 2',
                        'position': (start_x, y_pos)
                    }
                    portraits.append((portrait, metadata))
            
            logger.info(f"Extracted {len(portraits)} agent portraits from screenshot")
            return portraits
            
        except Exception as e:
            logger.error(f"Error extracting portraits: {e}")
            return []
    
    def detect_agents_from_screenshot(self, screenshot_path: str, threshold: float = 0.6) -> List[dict]:
        """
        Full pipeline: Extract portraits and match agents
        
        Args:
            screenshot_path: Path to scoreboard screenshot
            threshold: Minimum confidence for agent matching
            
        Returns:
            List of dicts with player_index, agent_name, and confidence
        """
        portraits = self.extract_agent_portraits(screenshot_path)
        results = []
        
        for portrait, metadata in portraits:
            agent_name, confidence = self.match_agent(portrait, threshold)
            
            result = {
                'player_index': metadata['player_index'],
                'team': metadata['team'],
                'agent': agent_name if agent_name else 'Unknown',
                'confidence': confidence
            }
            results.append(result)
        
        return results


# Global instance
_agent_matcher = None

def get_agent_matcher() -> AgentMatcher:
    """Get or create the global AgentMatcher instance"""
    global _agent_matcher
    if _agent_matcher is None:
        _agent_matcher = AgentMatcher()
    return _agent_matcher
