"""
Test script for Gemini Vision Agent Detector
Tests agent detection using Google's Gemini Vision API
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print("✅ Loaded .env file")
except Exception as e:
    print(f"⚠️ Could not load .env: {e}")

from services.gemini_agent_detector import get_gemini_agent_detector
import os

def main():
    print("🧪 Testing Gemini Vision Agent Detector\n")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        print("Please set GEMINI_API_KEY in your .env file")
        return
    
    # Initialize detector
    try:
        detector = get_gemini_agent_detector()
        print(f"✅ Gemini Vision Agent Detector initialized")
        print(f"📊 Supported agents: {len(detector.get_supported_agents())}")
        print(f"\n🎮 Agent List:")
        for i, agent in enumerate(detector.get_supported_agents(), 1):
            print(f"   {i:2d}. {agent}")
        print("\n" + "=" * 60)
    except Exception as e:
        print(f"❌ Failed to initialize detector: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test with a sample image if provided
    test_image = "test/sample_scoreboard.png"
    
    if not Path(test_image).exists():
        print(f"\n💡 To test agent detection:")
        print(f"   1. Place a Valorant scoreboard screenshot at: {test_image}")
        print(f"   2. Run this script again")
        print(f"   OR")
        print(f"   3. Use /scan command in Discord with your bot")
        return
    
    # Run detection
    print(f"\n🔍 Detecting agents in: {test_image}")
    print("⏳ Processing with Gemini Vision API...")
    
    try:
        agents = detector.detect_agents_from_screenshot(test_image)
        
        print(f"\n✅ Detection Complete!")
        print(f"\n📋 Detected Agents (Top to Bottom):")
        print("-" * 40)
        
        for i, agent in enumerate(agents, 1):
            emoji = "✅" if agent != "Unknown" else "❓"
            print(f"   {emoji} Player {i:2d}: {agent}")
        
        # Statistics
        detected = sum(1 for a in agents if a != "Unknown")
        unknown = sum(1 for a in agents if a == "Unknown")
        
        print(f"\n📊 Detection Statistics:")
        print(f"   ✅ Detected: {detected}/10")
        print(f"   ❓ Unknown: {unknown}/10")
        print(f"   🎯 Accuracy: {(detected/10)*100:.0f}%")
        
    except Exception as e:
        print(f"\n❌ Detection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
