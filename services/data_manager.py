import json
from pathlib import Path
from typing import Dict, Optional

class DataManager:
    _instance = None
    _agent_descriptions = None
    _confusion_pairs = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance

    @property
    def agent_descriptions(self) -> Dict:
        if self._agent_descriptions is None:
            self._load_agent_descriptions()
        return self._agent_descriptions

    @property
    def confusion_pairs(self) -> Dict:
        if self._confusion_pairs is None:
            self._load_confusion_pairs()
        return self._confusion_pairs

    def _load_agent_descriptions(self):
        """Load agent descriptions from JSON file"""
        try:
            file_path = Path(__file__).parent.parent / "data" / "agent_descriptions.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._agent_descriptions = json.load(f)
                    print(f"Loaded {len(self._agent_descriptions)} agent descriptions")
            else:
                print(f"Agent descriptions file not found at {file_path}")
                self._agent_descriptions = {}
        except Exception as e:
            print(f"Error loading agent descriptions: {e}")
            self._agent_descriptions = {}

    def _load_confusion_pairs(self):
        """Load confusion pairs from JSON file"""
        try:
            file_path = Path(__file__).parent.parent / "data" / "confused_agents.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._confusion_pairs = json.load(f)
                    print(f"Loaded {len(self._confusion_pairs)} confusion pairs")
            else:
                print(f"Confusion pairs file not found at {file_path}")
                self._confusion_pairs = {}
        except Exception as e:
            print(f"Error loading confusion pairs: {e}")
            self._confusion_pairs = {}

# Create singleton instance
data_manager = DataManager()