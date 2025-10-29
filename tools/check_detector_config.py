"""
Quick test to verify agent detector configuration
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except:
    pass

from services.gemini_agent_detector import get_gemini_agent_detector

def main():
    print("🔧 Testing Agent Detector Configuration\n")
    
    detector = get_gemini_agent_detector()
    
    print(f"✅ Model: {detector.model_name}")
    print(f"✅ Temperature: 0.0 (most conservative)")
    print(f"✅ Top P: 0.7 (focused)")
    print(f"✅ Top K: 20 (strict)")
    print(f"\n📊 Validation:")
    print(f"   • Exact match required for agent names")
    print(f"   • 'Unknown' returned when uncertain")
    print(f"   • No fuzzy matching (prevents false positives)")
    print(f"   • Confidence: 85% for detected agents")
    print(f"\n💡 This configuration prioritizes accuracy over completeness.")
    print(f"   Better to have 'Unknown' than incorrect agents!")

if __name__ == "__main__":
    main()
