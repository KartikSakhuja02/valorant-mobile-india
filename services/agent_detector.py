# services/agent_detector.py - Local agent detection using template matching
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict
import os

class AgentDetector:
    def __init__(self):
        self.agent_templates = {}
        self.load_agent_templates()
    
    import cv2
import numpy as np
from pathlib import Path
import os

class AgentDetector:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentDetector, cls).__new__(cls)
            cls._instance.agent_templates = {}
            cls._instance.load_agent_templates()
        return cls._instance

    def __init__(self):
        # Constructor is called after __new__
        # All initialization is done in __new__ for singleton
        pass

    def load_agent_templates(self):
        """Load all agent reference images"""
        agents_dir = Path(__file__).parent.parent / "agents images"
        
        # Map filenames to agent names
        agent_name_mapping = {
            "agentjett": "Jett",
            "agentsage": "Sage",
            "agentphoenix": "Phoenix",
            "agentreyna": "Reyna",
            "agentraze": "Raze",
            "agentbreach": "Breach",
            "agentomen": "Omen",
            "agentbrimstone": "Brimstone",
            "agentviper": "Viper",
            "agentcypher": "Cypher",
            "agentsova": "Sova",
            "agentkilljoy": "Killjoy",
            "agentskye": "Skye",
            "agentyoru": "Yoru",
            "agentastra": "Astra",
            "agentkayo": "KAY/O",
            "agentchamber": "Chamber",
            "agentneon": "Neon",
            "agentfade": "Fade",
            "agentharbor": "Harbor",
            "agentgekko": "Gekko",
            "agentdeadlock": "Deadlock",
            "valorant-deadlock-icon": "Deadlock",
            "valorant-skye-icon": "Skye"
        }
        
        if not agents_dir.exists():
            print(f"Warning: Agent images directory not found at {agents_dir}")
            return
        
        for img_file in agents_dir.glob("*.png"):
            # Extract agent name from filename
            filename_lower = img_file.stem.lower()
            
            agent_name = None
            for key, name in agent_name_mapping.items():
                if key in filename_lower:
                    agent_name = name
                    break
            
            if agent_name:
                # Load and store the template
                template = cv2.imread(str(img_file))
                if template is not None:
                    self.agent_templates[agent_name] = template
                    print(f"Loaded template: {agent_name}")
        
        print(f"Total agent templates loaded: {len(self.agent_templates)}")
    
    def detect_agent(self, player_icon: np.ndarray, method=cv2.TM_CCOEFF_NORMED) -> Optional[str]:
        """
        Detect agent from a cropped player icon using template matching
        
        Args:
            player_icon: Cropped agent icon from screenshot (numpy array)
            method: OpenCV template matching method
        
        Returns:
            Agent name or None if no good match
        """
        if not self.agent_templates:
            return None
        
        best_match = None
        best_score = 0
        threshold = 0.6  # Increased threshold for better accuracy
        
        # Convert player icon to BGR if needed
        if len(player_icon.shape) == 2:
            player_icon = cv2.cvtColor(player_icon, cv2.COLOR_GRAY2BGR)
        
        # Try multiple matching methods and average scores
        methods = [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED]
        
        for agent_name, template in self.agent_templates.items():
            # Resize template to match player icon size
            template_resized = cv2.resize(template, (player_icon.shape[1], player_icon.shape[0]))
            
            scores = []
            for method in methods:
                # Perform template matching
                result = cv2.matchTemplate(player_icon, template_resized, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                # For most methods, higher is better
                score = max_val if method in [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED] else 1 - min_val
                scores.append(score)
            
            # Average score across methods
            avg_score = sum(scores) / len(scores)
            
            if avg_score > best_score:
                best_score = avg_score
                best_match = agent_name
        
        # Only return match if confidence is high enough
        if best_score >= threshold:
            print(f"  Detected: {best_match} (confidence: {best_score:.2f})")
            return best_match
        
        print(f"  No confident match (best: {best_score:.2f})")
        return None
    
    def crop_agent_icon_from_screenshot(self, screenshot: np.ndarray, player_row_index: int) -> Optional[np.ndarray]:
        """
        Crop the agent icon from a specific player row in the screenshot
        
        Args:
            screenshot: Full screenshot as numpy array
            player_row_index: Index of player row (0-9)
        
        Returns:
            Cropped agent icon or None
        """
        # Valorant Mobile scoreboard - adjusted coordinates based on typical layout
        height, width = screenshot.shape[:2]
        
        # Calculate row positions - scoreboards typically start around 20% from top
        scoreboard_start_y = int(height * 0.20)  # Start slightly higher
        scoreboard_end_y = int(height * 0.78)    # End around 78%
        scoreboard_height = scoreboard_end_y - scoreboard_start_y
        row_height = scoreboard_height // 10
        
        row_y = scoreboard_start_y + (player_row_index * row_height)
        
        # Agent icon position - typically 3-8% from left edge
        icon_x_start = int(width * 0.03)  # Start at 3%
        icon_x_end = int(width * 0.08)    # End at 8%
        icon_width = icon_x_end - icon_x_start
        
        # Icon height - leave some padding
        icon_y_padding = 8
        icon_height = row_height - (icon_y_padding * 2)
        
        # Crop the agent icon
        try:
            icon = screenshot[
                row_y + icon_y_padding : row_y + icon_y_padding + icon_height,
                icon_x_start : icon_x_end
            ]
            
            # Debug: save cropped icons to see what we're matching
            debug_dir = Path(__file__).parent.parent / "data" / "debug_icons"
            debug_dir.mkdir(exist_ok=True)
            debug_path = debug_dir / f"row_{player_row_index}.png"
            if icon.size > 0:
                cv2.imwrite(str(debug_path), icon)
                print(f"  Saved debug icon: {debug_path}")
            
            return icon if icon.size > 0 else None
        except Exception as e:
            print(f"Error cropping row {player_row_index}: {e}")
            return None
    
    def detect_all_agents(self, screenshot_path: str) -> Dict[int, str]:
        """
        Detect all agents in a screenshot
        
        Args:
            screenshot_path: Path to screenshot file
        
        Returns:
            Dictionary mapping player index (0-9) to agent name
        """
        screenshot = cv2.imread(screenshot_path)
        if screenshot is None:
            return {}
        
        detected_agents = {}
        
        for i in range(10):
            icon = self.crop_agent_icon_from_screenshot(screenshot, i)
            if icon is not None and icon.size > 0:
                agent = self.detect_agent(icon)
                if agent:
                    detected_agents[i] = agent
        
        return detected_agents
