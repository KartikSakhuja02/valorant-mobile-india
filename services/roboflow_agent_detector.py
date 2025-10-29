"""
Roboflow hosted workflow detector wrapper

This module sends an image to a deployed Roboflow workflow URL (the one you pasted)
and converts the JSON response into the same shape used by local detectors
(agents list, map placeholder, and raw detections list).

Usage:
    from services.roboflow_agent_detector import get_roboflow_agent_detector
    det = get_roboflow_agent_detector("https://app.roboflow.com/workflows/...")
    result = det.detect_agents_from_screenshot("/path/to/image.png")
"""

from pathlib import Path
from typing import List, Dict, Any
import json
import requests


class RoboflowAgentDetector:
    def __init__(self, workflow_url: str):
        if not workflow_url:
            raise ValueError("workflow_url must be provided")
        self.workflow_url = workflow_url

    def detect_agents_from_screenshot(self, image_path: str, confidence_threshold: float = 0.25) -> Dict[str, Any]:
        """
        Send image to Roboflow hosted workflow and parse detections.

        Returns a dict with keys: 'agents' (list of 10 agent names), 'map' and 'detections' (list of raw detections)
        """
        p = Path(image_path)
        if not p.exists():
            raise ValueError(f"Image not found: {image_path}")

        # Post the image file (multipart/form-data). Roboflow hosted workflows accept file uploads.
        with p.open("rb") as f:
            files = {"file": (p.name, f, "image/png")}
            # The provided workflow URL may already include query params (e.g., ?dark=true). Send directly.
            resp = requests.post(self.workflow_url, files=files, timeout=30)

        resp.raise_for_status()
        data = resp.json()

        # Roboflow hosted inference commonly returns a JSON with a 'predictions' array
        predictions = data.get("predictions") or data.get("preds") or []

        detections: List[Dict[str, Any]] = []
        for p in predictions:
            # Roboflow fields may include: 'class' or 'label' for text, 'confidence', and bbox coords
            label = p.get("class") or p.get("label") or p.get("name") or p.get("object")
            confidence = float(p.get("confidence", p.get("score", 0)))

            # Try to compute a center Y for ordering. Roboflow often returns 'y' and 'height' (center-based)
            if "y" in p and "height" in p:
                center_y = float(p.get("y"))
            elif "bbox" in p and isinstance(p.get("bbox"), (list, tuple)) and len(p.get("bbox")) >= 4:
                # bbox may be [x1, y1, x2, y2]
                bx = p.get("bbox")
                try:
                    y1 = float(bx[1]); y2 = float(bx[3])
                    center_y = (y1 + y2) / 2.0
                except Exception:
                    center_y = 0.0
            else:
                center_y = 0.0

            detections.append({
                "agent": label or "Unknown",
                "confidence": confidence,
                "y_position": center_y,
                "raw": p,
            })

        # Sort by Y position top-to-bottom
        detections.sort(key=lambda d: d.get("y_position", 0))

        # Build agents list (top 10 rows)
        agents = [d.get("agent", "Unknown") for d in detections[:10]]
        # Pad to 10
        while len(agents) < 10:
            agents.append("Unknown")

        return {"agents": agents, "map": data.get("map", "Unknown"), "detections": detections}


def get_roboflow_agent_detector(workflow_url: str) -> RoboflowAgentDetector:
    return RoboflowAgentDetector(workflow_url)
