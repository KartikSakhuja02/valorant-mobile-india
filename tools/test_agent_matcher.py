"""
Test script for the CV-based agent matcher
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.agent_matcher import get_agent_matcher

def main():
    print("🔍 Testing Agent Matcher...")
    print("=" * 50)
    
    # Initialize matcher
    matcher = get_agent_matcher()
    
    # Check loaded templates
    print(f"\n✅ Loaded {len(matcher.agent_templates)} agent templates:")
    for agent_name in sorted(matcher.agent_templates.keys()):
        print(f"   - {agent_name}")
    
    print("\n" + "=" * 50)
    print("Agent matcher is ready!")
    print("\n💡 To test with a screenshot:")
    print("   1. Use /scan command in Discord")
    print("   2. Upload a Valorant scoreboard screenshot")
    print("   3. Check the agent detection results\n")

if __name__ == "__main__":
    main()
