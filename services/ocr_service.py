"""
OCR Service for registration
Handles OCR processing for profile screenshots
"""

import aiohttp
import base64
from io import BytesIO
from PIL import Image
import os
from pathlib import Path

# Helper function to load config
def cfg(key, default=None):
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
    except Exception:
        pass

    val = os.environ.get(key)
    if val is not None:
        return val
    
    # Try config.json
    try:
        config_path = Path(__file__).parent.parent / 'config.json'
        if config_path.exists():
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get(key, default)
    except Exception:
        pass
    
    return default

class OCRService:
    def __init__(self):
        self.gemini_api_key = cfg('GEMINI_API_KEY')
        
    async def process_screenshot(self, attachment) -> tuple[bool, str, str]:
        """
        Process a screenshot to extract IGN and ID
        Returns: (success, ign, player_id)
        """
        try:
            if not self.gemini_api_key:
                return False, "Gemini API key not configured", ""
            
            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as response:
                    if response.status != 200:
                        return False, "Failed to download image", ""
                    
                    image_data = await response.read()
                    image = Image.open(BytesIO(image_data))
                    
                    # Resize if too large
                    max_size = 1600
                    if max(image.size) > max_size:
                        ratio = max_size / max(image.size)
                        new_size = tuple(int(dim * ratio) for dim in image.size)
                        image = image.resize(new_size, Image.LANCZOS)
                    
                    # Convert to base64
                    buffered = BytesIO()
                    image.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    # Gemini prompt for profile extraction
                    prompt = """
You are analyzing a VALORANT Mobile player profile screenshot.

Your task: Extract the player's IGN (username) and Player ID (numeric ID).

Look for:
- IGN: The player name/username (may be displayed at top of screen, profile section, or player card)
- Player ID: A numeric code, may have # symbol (example: #12345 or 12345)

Return ONLY valid JSON (no markdown, no code blocks):
{"ign": "found_username", "id": "numeric_id"}

If IGN not found: {"ign": null, "id": null}
If ID not found: {"ign": "found_username", "id": null}

Examples:
- If you see "DarkWizard #5432" return: {"ign": "DarkWizard", "id": "5432"}
- If you see username "ProPlayer" and ID "98765" return: {"ign": "ProPlayer", "id": "98765"}

CRITICAL: Return ONLY the JSON object, nothing else.
"""
                    
                    # Try multiple Gemini models (using correct API versions)
                    models = [
                        ("v1", "gemini-2.5-flash"),
                        ("v1", "gemini-2.0-flash"),
                        ("v1beta", "gemini-2.0-flash-exp"),
                    ]
                    
                    for version, model in models:
                        try:
                            url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent"
                            
                            payload = {
                                "contents": [{
                                    "parts": [
                                        {"text": prompt},
                                        {
                                            "inline_data": {
                                                "mime_type": "image/png",
                                                "data": img_str
                                            }
                                        }
                                    ]
                                }]
                            }
                            
                            async with session.post(
                                url,
                                params={"key": self.gemini_api_key},
                                json=payload,
                                headers={"Content-Type": "application/json"}
                            ) as resp:
                                if resp.status != 200:
                                    error_text = await resp.text()
                                    print(f"❌ Gemini API error ({model}): {resp.status} - {error_text}")
                                    continue
                                
                                data = await resp.json()
                                text_response = data['candidates'][0]['content']['parts'][0]['text']
                                print(f"🔍 Gemini response ({model}): {text_response}")
                                
                                # Parse JSON response - try multiple patterns
                                import re
                                import json
                                
                                # Try to find JSON in the response
                                json_match = re.search(r'\{[^{}]*"ign"[^{}]*"id"[^{}]*\}', text_response, re.DOTALL)
                                if not json_match:
                                    # Try broader match
                                    json_match = re.search(r'\{.*?\}', text_response, re.DOTALL)
                                
                                if json_match:
                                    try:
                                        result = json.loads(json_match.group())
                                        ign = result.get('ign')
                                        player_id = result.get('id')
                                        
                                        print(f"📝 Extracted - IGN: {ign}, ID: {player_id}")
                                        
                                        # Clean up ID (remove # if present)
                                        if player_id:
                                            player_id = str(player_id).replace('#', '').strip()
                                        
                                        # Validate we got both values
                                        if ign and player_id and ign != "null" and player_id != "null":
                                            # Validate ID is numeric
                                            try:
                                                int(player_id)
                                                print(f"✅ OCR Success - IGN: {ign}, ID: {player_id}")
                                                return True, ign, player_id
                                            except ValueError:
                                                print(f"⚠️ ID not numeric: {player_id}")
                                                continue
                                        else:
                                            print(f"⚠️ Missing IGN or ID (IGN={ign}, ID={player_id})")
                                    except json.JSONDecodeError as e:
                                        print(f"⚠️ JSON parse error: {e}")
                                        continue
                                else:
                                    print(f"⚠️ No JSON found in response")
                        
                        except Exception as e:
                            print(f"❌ OCR error with {model}: {e}")
                            continue
                    
                    return False, "Could not extract IGN and ID from image", ""
                            
        except Exception as e:
            return False, f"Error processing screenshot: {str(e)}", ""

# Create singleton instance
ocr_service = OCRService()