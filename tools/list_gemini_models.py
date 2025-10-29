"""
List available Gemini models for your API key
"""

import os
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
except Exception:
    pass

import google.generativeai as genai

def main():
    print("🔍 Checking Available Gemini Models\n")
    print("=" * 60)
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        return
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    print("\n📋 Available Models:\n")
    
    try:
        # List all models
        models = genai.list_models()
        
        vision_models = []
        text_models = []
        
        for model in models:
            # Check if model supports generateContent
            if 'generateContent' in model.supported_generation_methods:
                model_name = model.name.replace('models/', '')
                
                # Check if it's a vision model
                if 'vision' in model_name.lower() or '1.5' in model_name or '2.0' in model_name:
                    vision_models.append(model_name)
                else:
                    text_models.append(model_name)
        
        print("🎨 Vision Models (recommended for agent detection):")
        for model in vision_models:
            print(f"   ✅ {model}")
        
        print(f"\n📝 Text Models:")
        for model in text_models:
            print(f"   • {model}")
        
        print("\n" + "=" * 60)
        
        if vision_models:
            print(f"\n💡 Recommended model: {vision_models[0]}")
            print(f"   This will be used for agent detection")
        else:
            print("\n⚠️ No vision models found!")
            print("   Please check your API key has access to Gemini vision models")
            
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
