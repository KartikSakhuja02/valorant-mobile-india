"""
Gemini Vision API Agent Detector
Uses Google's Gemini Vision to identify Valorant agents from screenshots
"""

import google.generativeai as genai
from pathlib import Path
import json
from PIL import Image
import os
import re
from typing import List, Dict, Optional

class GeminiAgentDetector:
    """
    Uses Gemini Vision API to detect Valorant agents from portraits
    Focuses specifically on agent identification with high accuracy
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini agent detector
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Try different model names (prioritize latest vision models)
        model_candidates = [
            'gemini-2.0-flash-exp',      # Latest experimental flash model
            'gemini-2.0-flash',           # Stable 2.0 flash
            'gemini-2.5-flash',           # 2.5 flash (may be text-only)
            'gemini-1.5-flash-latest',    # 1.5 flash latest
            'gemini-1.5-pro-latest',      # 1.5 pro latest
            'gemini-pro-vision',          # Legacy vision model
        ]
        
        self.model = None
        self.model_name = None
        for model_name in model_candidates:
            try:
                self.model = genai.GenerativeModel(model_name)
                self.model_name = model_name
                print(f"✅ Using Gemini model: {model_name}")
                break
            except Exception as e:
                print(f"⚠️ Model {model_name} not available: {e}")
                continue
        
        if not self.model:
            raise ValueError("No Gemini vision model available. Please check your API key and model access.")
        
        # Map names (Chinese -> English)
        self.map_names = {
            '亚海悬城': 'Ascent',
            '源工重镇': 'Bind',
            '极寒冬港': 'Icebox',
            '隐世修所': 'Haven',
            '霓虹町': 'Split',
            '微风岛屿': 'Breeze',
            '裂变峡谷': 'Fracture',
        }
        
        # Reverse mapping for validation
        self.english_map_names = list(self.map_names.values())
        
        # All Valorant agents (exact spelling)
        self.agent_list = [
            'Astra', 'Breach', 'Brimstone', 'Chamber', 'Clove', 'Cypher',
            'Deadlock', 'Fade', 'Gekko', 'Harbor', 'Iso', 'Jett',
            'KAY/O', 'Killjoy', 'Neon', 'Omen', 'Phoenix', 'Raze',
            'Reyna', 'Sage', 'Skye', 'Sova', 'Viper', 'Vyse', 'Yoru'
        ]
        
        print(f"✅ Gemini Agent Detector initialized with {len(self.agent_list)} agents")
    
    def detect_agents_from_screenshot(self, image_path: str, agent_descriptions: dict = None) -> List[str]:
        """
        Detect agents from a Valorant scoreboard screenshot
        
        Args:
            image_path: Path to the scoreboard screenshot
            agent_descriptions: Optional dict of agent descriptions from JSON file
            
        Returns:
            List of 10 agent names in order from top to bottom
        """
        try:
            # Load image
            img = Image.open(image_path)
            
            # Resize if too large (Gemini has size limits)
            max_size = 2048
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                print(f"📐 Resized image to {new_size} for Gemini API")
            
            print(f"📏 Image size: {img.size}, Mode: {img.mode}")
            
            # Create highly specific prompt for agent detection (with optional extra descriptions)
            prompt = self._create_agent_detection_prompt(agent_descriptions)
            print(f"📝 Prompt length: {len(prompt)} characters")
            print(f"🤖 Using model: {self.model._model_name if hasattr(self.model, '_model_name') else 'unknown'}")
            
            # Generate content with image (with retry)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(
                        [prompt, img],
                        generation_config={
                            'temperature': 0.0,  # Zero temperature for deterministic, accurate results
                            'top_p': 0.9,        # Balanced for consistency
                            'top_k': 40,         # Standard value for balance
                        }
                    )
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Attempt {attempt + 1} failed, retrying... ({e})")
                        import time
                        time.sleep(1)
                    else:
                        raise
            
            print(f"📤 Raw Gemini response length: {len(response.text)} characters")
            print(f"📤 Raw response (first 500 chars):\n{response.text[:500]}\n")
            
            # Parse response
            agents = self._parse_agent_response(response.text)
            
            # Validate and normalize agent names
            agents = self._validate_agents(agents)
            
            # Detect map name from the same screenshot
            map_name = self.detect_map_name(image_path)
            
            print(f"🎯 Detected agents: {agents}")
            print(f"🗺️ Detected map: {map_name}")
            return {'agents': agents, 'map': map_name}
            
        except Exception as e:
            print(f"❌ Error detecting agents with Gemini Vision: {e}")
            import traceback
            traceback.print_exc()
            return {'agents': ['Unknown'] * 10, 'map': 'Unknown'}
    
    def detect_map_name(self, image_path: str) -> str:
        """
        Detect the map name from the scoreboard screenshot
        
        Args:
            image_path: Path to the scoreboard screenshot
            
        Returns:
            Map name in English (e.g., 'Ascent', 'Bind', etc.)
        """
        try:
            img = Image.open(image_path)
            
            # Resize if needed
            max_size = 2048
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Create prompt for map detection
            prompt = f"""Analyze this VALORANT scoreboard screenshot and identify the map name.

**AVAILABLE MAPS** (you may see Chinese or English names):

Chinese Name → English Name:
- 亚海悬城 → Ascent
- 源工重镇 → Bind
- 极寒冬港 → Icebox
- 隐世修所 → Haven
- 霓虹町 → Split
- 微风岛屿 → Breeze
- 裂变峡谷 → Fracture

**TASK**: Look for the map name text on the scoreboard (usually at the top or near the score display).

**OUTPUT**: Return ONLY the English map name from the list above, nothing else.

Map name:"""
            
            response = self.model.generate_content(
                [prompt, img],
                generation_config={
                    'temperature': 0.1,
                    'top_p': 0.7,
                    'top_k': 20,
                }
            )
            
            map_text = response.text.strip()
            print(f"🗺️ Raw map response: {map_text}")
            
            # Try to match Chinese or English name
            map_text_clean = map_text.strip().strip('"').strip("'")
            
            # Check if it's a Chinese name
            if map_text_clean in self.map_names:
                return self.map_names[map_text_clean]
            
            # Check if it's already English
            for eng_name in self.english_map_names:
                if eng_name.lower() in map_text_clean.lower():
                    return eng_name
            
            print(f"⚠️ Unknown map detected: {map_text_clean}")
            return 'Unknown'
            
        except Exception as e:
            print(f"❌ Error detecting map name: {e}")
            return 'Unknown'
    
    def detect_agents_from_screenshot_old(self, image_path: str) -> List[str]:
        """
        OLD METHOD - Returns only agents list (kept for backwards compatibility)
        Use detect_agents_from_screenshot() instead which returns {'agents': [...], 'map': '...'}
        """
        result = self.detect_agents_from_screenshot(image_path)
        if isinstance(result, dict):
            return result['agents']
        return result
    
    def detect_single_agent(self, image_path: str) -> Dict[str, any]:
        """
        Detect a single agent from a cropped portrait image
        Useful for manual correction or verification
        
        Args:
            image_path: Path to cropped agent portrait
            
        Returns:
            Dict with 'agent' name and 'confidence' score
        """
        try:
            img = Image.open(image_path)
            
            prompt = f"""Identify this VALORANT agent from their portrait icon.

**AVAILABLE AGENTS**:
{', '.join(self.agent_list)}

**INSTRUCTIONS**:
Look at the portrait's distinctive features:
- Hair color and style
- Face features and expression
- Color scheme (primary colors)
- Unique visual elements or accessories
- Character ethnicity/appearance

**OUTPUT**: Return ONLY the agent name, nothing else. Choose from the list above.
Agent name:"""
            
            response = self.model.generate_content([prompt, img])
            agent = response.text.strip()
            
            # Validate agent name
            agent = self._normalize_agent_name(agent)
            
            if agent in self.agent_list:
                return {'agent': agent, 'confidence': 0.95}
            else:
                print(f"⚠️ Unknown agent detected: {agent}")
                return {'agent': 'Unknown', 'confidence': 0.0}
                
        except Exception as e:
            print(f"❌ Error detecting single agent: {e}")
            return {'agent': 'Unknown', 'confidence': 0.0}
    
    def _create_agent_detection_prompt(self, agent_descriptions: dict = None) -> str:
        """Create the detailed prompt for agent detection with comprehensive visual descriptions"""
        
        # Add JSON descriptions if provided
        extra_descriptions = ""
        if agent_descriptions:
            extra_descriptions = "\n**ADDITIONAL QUICK REFERENCE (High Priority Identifiers):**\n"
            for agent_name, desc in agent_descriptions.items():
                extra_descriptions += f"- {agent_name}: {desc}\n"
            extra_descriptions += "\n"
        
        return f"""You are analyzing a VALORANT match scoreboard screenshot to identify agents.

**CRITICAL TASK**: Identify the agent each player is using by examining their circular portrait icon on the LEFT side of each player row.

**AVAILABLE AGENTS** (Choose ONLY from these exact names):
{', '.join(self.agent_list)}

{extra_descriptions}**⚠️ MANDATORY VERIFICATION CHECKLIST - CHECK THESE FIRST:**

Before identifying ANY agent, answer these questions for EACH portrait:

1. **FACE CHECK:**
   - ❓ Is there a WHITE HAT visible? → If YES, check for hidden face = CYPHER (NOT Chamber)
   - ❓ Can you see GLASSES on the face? → If YES, face visible = CHAMBER (NOT Cypher)
   - ❓ Is the face completely hidden behind a mask? → Check hat color

2. **ARMS CHECK:**
   - ❓ Are the arms HUGE ROBOTIC PROSTHETICS? → If YES = BREACH (NOT Phoenix, NOT anyone else)
   - ❓ Are the arms normal human-sized? → Check other features

3. **CLOTHING CHECK:**
   - ❓ Is there a CROP TOP showing bare midriff/stomach? → If YES = RAZE (NOT Sage)
   - ❓ Are there long flowing WHITE ROBES covering the body? → If YES = SAGE (NOT Raze)

4. **ETHNICITY/AGE CHECK:**
   - ❓ Is this a young BLACK male with dreadlocks? → If YES = PHOENIX (NOT Breach)
   - ❓ Is this a middle-aged WHITE man with white beard? → Check for robot arms = BREACH

**CRITICAL DISTINCTIONS TO AVOID COMMON MISTAKES:**

🚫 **DO NOT confuse Cypher with Chamber:**
- CYPHER: WHITE FEDORA HAT + NO FACE VISIBLE (completely hidden) + beige/white trench coat
- CHAMBER: GLASSES + FACE FULLY VISIBLE (brown hair showing) + navy blue suit

🚫 **DO NOT confuse Raze with Sage:**
- RAZE: CROP TOP with BELLY/MIDRIFF EXPOSED + orange headset + casual sporty look
- SAGE: WHITE ROBES covering ENTIRE BODY + black hair in buns + formal elegant look

🚫 **DO NOT confuse Breach with Phoenix:**
- BREACH: HUGE ROBOT ARMS (unmissable prosthetics) + middle-aged WHITE man + white beard
- PHOENIX: NORMAL HUMAN ARMS + young BLACK male + fire-tipped dreadlocks

**COMPREHENSIVE VISUAL IDENTIFICATION GUIDE**:

🔹 **Astra** (Controller)
Colors: Deep Purple, Gold, Black, Blue
Face: Black woman, large braided hair with golden beads and rings, golden triangular markings on forehead/cheeks
Key Feature: Solid gold right arm made of cosmic energy (VERY DISTINCTIVE)
Style: Cosmic royalty, astral power theme

🔹 **Breach** (Initiator)
Colors: Orange, Dark Grey, Silver/Titanium, NO BLACK
Face: Middle-aged WHITE MAN, short white/grey hair, white beard and mustache, rugged scarred face, CAUCASIAN
Key Feature: MASSIVE ROBOTIC ARMS - BOTH ARMS are HUGE TITANIUM PROSTHETICS with glowing ORANGE joints, DISPROPORTIONATELY LARGE compared to body, sleeveless outfit showing robot arms (NOT black jacket, NOT fire theme, NOT young Black male, NOT dreadlocks) ⚠️ BREACH = HUGE ROBOT ARMS + WHITE BEARD + MIDDLE-AGED WHITE MAN, NOT PHOENIX
Style: Bionic Swedish powerhouse - THE ARMS ARE UNMISTAKABLE, VERY BULKY appearance

🔹 **Brimstone** (Controller)
Colors: Army Green, Grey, Orange, Black
Face: Older man, grey hair, thick grey mustache and beard
Key Feature: BRIGHT ORANGE BERET on head (signature military cap), tactical vest, device on left forearm, NO ROBOTIC ARMS ⚠️ BRIMSTONE = ORANGE BERET, NOT ROBOT ARMS
Style: Veteran military commander - distinguished older officer look

🔹 **Chamber** (Sentinel)
Colors: Navy Blue, Gold, White, Brown, NO WHITE HAT
Face: Slicked-back brown hair, well-groomed facial hair, STYLISH SQUARE GLASSES on face (VERY DISTINCTIVE), FACE FULLY VISIBLE, human French man
Key Feature: Sharp NAVY BLUE suit vest, white collared shirt with tie, golden chain on vest, GLASSES (NOT hat, NOT mask, NOT hidden face, NOT trench coat) ⚠️ CHAMBER = GLASSES + NAVY SUIT + VISIBLE FACE, NOT CYPHER
Style: Elegant French weapons designer - sophisticated businessman look, GLASSES ALWAYS VISIBLE

🔹 **Clove** (Controller)
Colors: Pink, Purple, Blue, Black
Face: Short wavy pink hair (VERY DISTINCTIVE), youthful face, mischievous expression
Key Feature: Asymmetrical outfit with cropped black top, single pink sleeve, glowing pink/blue butterfly motifs
Style: Rebellious Scottish punk aesthetic

🔹 **Cypher** (Sentinel)
Colors: White/Beige, Black, Glowing Blue, NO NAVY BLUE
Face: COMPLETELY HIDDEN - black face mask with SINGLE HORIZONTAL glowing blue line across eyes, WHITE FEDORA HAT on top (UNMISTAKABLE COMBO), NO FACE VISIBLE, NO EYES VISIBLE, NO GLASSES
Key Feature: WHITE HAT on head (like a spy fedora), white/beige trench coat with high collar, ONE glowing blue line (NOT navy suit, NOT glasses, NOT visible face, NOT brown hair) ⚠️ CYPHER = WHITE HAT + HIDDEN FACE + TRENCH COAT, NOT CHAMBER WITH GLASSES
Style: Mysterious Moroccan information broker - classic spy look with HAT, completely mysterious appearance

🔹 **Deadlock** (Sentinel)
Colors: White, Grey, Silver
Face: White/platinum blonde hair, pale skin, Norwegian, serious expression
Key Feature: Nanowire/wire theme visible, tactical gear, stern appearance
Style: Norwegian tactical agent

🔹 **Fade** (Initiator)
Colors: Black, Dark Grey, Teal/Turquoise
Face: Long dark hair with grey/white streaks, heterochromia (one grey/blue eye, one orange/amber eye - DISTINCTIVE)
Key Feature: Henna-like markings on hands, dark layered clothing
Style: Dark Turkish bounty hunter, gothic appearance

🔹 **Gekko** (Initiator)
Colors: Bright Green, Beige, Purple, Blue
Face: Bright lime-green hair in short spiky cut (VERY DISTINCTIVE), plaster on nose often visible
Key Feature: Beige sleeveless puffer vest over purple t-shirt, small grey beanie, colorful creature companions
Style: Casual LA streetwear

🔹 **Harbor** (Controller)
Colors: Teal, Cyan, Blue, Black
Face: Dark hair tied back, Indian, calm expression
Key Feature: Teal/cyan water theme throughout outfit, bracelet artifact visible
Style: Indian water-themed agent

🔹 **Iso** (Duelist)
Colors: Purple, Black, Dark Grey
Face: Dark hair SLICKED BACK with prominent purple streak on one side (DISTINCTIVE), HUMAN face visible
Key Feature: Black suit with glowing purple energy lines, flowing dark coat/armor, NO ROBOT PARTS ⚠️ ISO = PURPLE STREAK + HUMAN FACE, NOT ROBOT SCREEN
Style: Sleek Chinese fixer, high-tech - fully human agent

🔹 **Jett** (Duelist)
Colors: White, Blue, Black
Face: Korean woman, short spiky white hair (VERY DISTINCTIVE)
Key Feature: Blue poncho-like garment flowing over shoulders (looks like clouds/air), grey/white bodysuit
Style: Agile wind-based theme

🔹 **KAY/O** (Initiator)
Colors: White, Grey, Black, Glowing Blue
Face: NO HUMAN FACE - ROBOTIC HEAD with DIGITAL SCREEN showing lines/circles/X pattern (COMPLETELY NON-HUMAN, NOT a purple-haired man)
Key Feature: FULLY MECHANICAL BODY with NO ORGANIC PARTS, screen for head with glowing display (NOT purple energy lines, NOT human suit) ⚠️ KAY/O = ROBOT WITH SCREEN HEAD, NOT HUMAN WITH PURPLE
Style: Humanoid war machine robot - ONLY non-human looking agent

🔹 **Killjoy** (Sentinel)
Colors: Bright Yellow, Green, Grey
Face: Young woman, dark hair under bright yellow beanie (VERY DISTINCTIVE), large round glasses
Key Feature: Yellow beanie + round spectacles combo, green cropped puffer jacket
Style: Youthful German engineer, nerdy tech aesthetic

🔹 **Neon** (Duelist)
Colors: Bright Blue, Yellow, Black
Face: Filipino woman, blue hair in two high ponytails with yellow lightning-bolt streaks (VERY DISTINCTIVE)
Key Feature: Athletic bodysuit with glowing yellow bio-electric lines, face markings that glow
Style: Speed and electricity theme

🔹 **Omen** (Controller)
Colors: Black, Dark Grey, Glowing Purple/Blue
Face: NO FACE VISIBLE - dark grey hood and mask with three glowing horizontal blue/purple slits (UNMISTAKABLE)
Key Feature: Tattered multi-layered cloak, arms wrapped in bandages, phantom-like
Style: Shadowy spectral entity

🔹 **Phoenix** (Duelist)
Colors: Black, White, Orange/Yellow, NO GREY/SILVER
Face: Young BLACK MALE (African descent), dark DREADLOCKS with glowing fire-like orange/yellow tips (DISTINCTIVE), MALE face visible, youthful confident expression
Key Feature: Black bomber jacket with large white Phoenix bird logo on back, NORMAL-SIZED HUMAN ARMS (NOT robot arms, NOT prosthetics, NOT grey/white beard, NOT middle-aged white man) ⚠️ PHOENIX = YOUNG BLACK MALE + FIRE DREADLOCKS + NORMAL ARMS, NOT BREACH
Style: Flashy confident duelist, fire theme - masculine confident look, YOUTHFUL appearance

🔹 **Raze** (Duelist)
Colors: Orange, Teal, Grey, Green, NO WHITE
Face: Brazilian FEMALE (woman), dark skin, dreadlocks tied up in bun/ponytail, ORANGE HEADSET/BEANIE visible, ENERGETIC youthful expression
Key Feature: Grey MIDRIFF-BARING crop top exposing stomach, orange explosive pack on chest, cluster grenades on strap, CASUAL SPORTY outfit (NOT white robes, NOT formal dress, NOT elegant attire, NOT black hair buns, NOT Chinese) ⚠️ RAZE = FEMALE + ORANGE HEADSET + CROP TOP SHOWING MIDRIFF, NOT SAGE WITH ROBES
Style: Vibrant Brazilian engineer, chaotic practical - feminine athletic CASUAL look, very sporty

🔹 **Reyna** (Duelist)
Colors: Purple, Black, Magenta
Face: Mexican woman, long dark hair with glowing purple streaks, eyes glow purple when abilities active (DISTINCTIVE)
Key Feature: Black/purple tactical bodysuit, glowing purple device on chest
Style: Predatory Mexican Radiant, intimidating

🔹 **Sage** (Sentinel)
Colors: White, Jade Green, Black, NO ORANGE
Face: Chinese woman (East Asian), long BLACK hair in intricate buns/braids with jade hairpins (DISTINCTIVE), calm serene expression
Key Feature: Long flowing WHITE ROBE with jade green accents, high collar, qipao-inspired, VERY FORMAL elegant attire covering entire body (NOT crop top, NOT casual, NOT orange headset, NOT midriff showing, NOT tied-up dreads, NOT Brazilian) ⚠️ SAGE = WHITE ROBES + BLACK HAIR BUNS + FORMAL COVERED, NOT RAZE WITH CROP TOP
Style: Serene Chinese healer, graceful monk-like - very elegant FORMAL appearance, completely covered body

🔹 **Skye** (Initiator)
Colors: Green, Brown, Tan, Reddish-brown
Face: Muscular woman, reddish-brown hair in side-swept braid
Key Feature: Green crop top, animal-tooth necklaces, wooden bracers and trinkets
Style: Australian naturalist, rugged eco-warrior

🔹 **Sova** (Initiator)
Colors: Blue, White, Gold, Brown
Face: Long blonde hair, glowing blue bionic right eye (VERY DISTINCTIVE)
Key Feature: Heavy fur-lined blue and white cloak/poncho, high-tech bow on back
Style: Russian futuristic archer/hunter

🔹 **Viper** (Controller)
Colors: Dark Green, Black, Glowing Pink/Purple
Face: COMPLETELY HIDDEN - full-face BLACK RESPIRATOR MASK with glowing PINK/PURPLE TRIANGULAR visor pattern (DISTINCTIVE), long black braid from back
Key Feature: NO FACE VISIBLE, mask with SIDE CANISTERS for gas, black/green bodysuit (NOT white hat, NOT single blue line, NOT beige trench coat) ⚠️ VIPER = GREEN/BLACK + TRIANGULAR PINK MASK, NOT WHITE HAT
Style: Sleek tactical chemist - chemical warfare specialist look

🔹 **Vyse** (Sentinel)
Colors: Blue, Silver, Metallic
Face: Silver/metallic hair, female, futuristic features, metallic elements
Key Feature: High-tech armor, metallic sheen throughout design
Style: Futuristic tech aesthetic

🔹 **Yoru** (Duelist)
Colors: Dark Blue, Black, Light Blue
Face: Young Japanese man, spiky hair dark blue/black at roots fading to light blue tips (DISTINCTIVE TWO-TONE)
Key Feature: Dark blue high-collared jacket with large white and gold oni (demon) mask graphic on back
Style: Confident Japanese dimension-hopper

**MOST UNMISTAKABLE FEATURES**:
1. **Cypher** - White fedora + black mask with single blue line, NO FACE VISIBLE
2. **KAY/O** - ROBOT with screen head, completely non-human
3. **Omen** - Hooded figure, NO FACE, three glowing slits only
4. **Breach** - MASSIVE robotic arms, disproportionately huge
5. **Viper** - Full-face respirator mask, triangular pink/purple glow
6. **Astra** - Solid GOLD right arm, cosmic theme
7. **Clove** - SHORT PINK HAIR, most colorful agent
8. **Killjoy** - BRIGHT YELLOW beanie + round glasses
9. **Gekko** - LIME-GREEN HAIR, most vibrant green
10. **Neon** - Blue hair in HIGH PONYTAILS with yellow lightning streaks

**DETECTION PRIORITY**:
1. First check for agents with NO VISIBLE FACE (Cypher, Omen, Viper, KAY/O)
2. Then check for DISTINCTIVE COLORS (pink=Clove, yellow=Killjoy, green=Gekko, gold arm=Astra)
3. Then check UNIQUE FEATURES (huge arms=Breach, bionic eye=Sova, heterochromia=Fade)
4. Then check hair style and color combinations
5. If still uncertain after all checks → "Unknown"

**COMMON CONFUSION PAIRS** (PAY EXTREME ATTENTION):
- **Cypher vs Chamber** ⚠️ CRITICAL → Cypher has WHITE HAT + HIDDEN FACE + trench coat (NO FACE VISIBLE), Chamber has GLASSES + VISIBLE FACE + navy suit (face clearly visible)
- **Raze vs Sage** ⚠️ CRITICAL → Raze has ORANGE HEADSET + CROP TOP showing midriff (casual sporty), Sage has WHITE ROBES + BLACK HAIR BUNS (formal elegant, body covered)
- **Breach vs Phoenix** ⚠️ CRITICAL → Breach has HUGE ROBOT ARMS + white beard + middle-aged WHITE man, Phoenix has NORMAL ARMS + fire dreadlocks + young BLACK male
- **Breach vs Brimstone** → Breach has HUGE ROBOT ARMS (unmissable), Brimstone has ORANGE BERET + normal arms
- **KAY/O vs Iso** → KAY/O is ROBOT with SCREEN HEAD (non-human), Iso is HUMAN with purple hair streak
- **Brimstone vs Phoenix** → Brimstone is OLDER with ORANGE BERET + grey beard, Phoenix is YOUNG BLACK MALE with fire dreadlocks
- **Cypher vs Viper** → Cypher has WHITE HAT + black mask with ONE blue line, Viper has GREEN/BLACK + TRIANGULAR pink/purple mask
- Jett vs Neon → Jett has WHITE hair, Neon has BLUE with ponytails + lightning
- Sage vs Skye → Sage has BLACK hair + Chinese buns, Skye has RED-BROWN braid
- Yoru vs Iso → Yoru has TWO-TONE blue spiky hair, Iso has purple streak + slicked back
- Phoenix vs Raze → Phoenix has dreadlocks with FIRE TIPS, Raze has tied-up dreads + orange headset
- Viper vs Fade → Viper has RESPIRATOR MASK (no face), Fade has visible face + heterochromia
- Chamber vs Brimstone → Chamber has GLASSES + suit, Brimstone has ORANGE BERET + beard
- Omen vs Cypher → Omen has HOOD + 3 slits, Cypher has HAT + mask with 1 line

**🔍 FINAL VERIFICATION - Before submitting your answer:**

Go through each agent you identified and verify:

1. ✅ If you said "Cypher" → Did you see a WHITE HAT? Is the face HIDDEN? (If you see GLASSES or VISIBLE FACE, it's CHAMBER not Cypher!)

2. ✅ If you said "Chamber" → Did you see GLASSES? Is the face VISIBLE? (If you see a WHITE HAT or HIDDEN FACE, it's CYPHER not Chamber!)

3. ✅ If you said "Raze" → Did you see a CROP TOP with MIDRIFF EXPOSED? Orange gear? (If you see WHITE ROBES or COVERED BODY, it's SAGE not Raze!)

4. ✅ If you said "Sage" → Did you see WHITE ROBES covering the ENTIRE BODY? Black hair buns? (If you see CROP TOP or MIDRIFF, it's RAZE not Sage!)

5. ✅ If you said "Breach" → Did you see HUGE ROBOT ARMS? White beard? Middle-aged white man? (If you see NORMAL ARMS or young BLACK male, it's PHOENIX not Breach!)

6. ✅ If you said "Phoenix" → Did you see NORMAL HUMAN ARMS? Young BLACK male? Fire dreadlocks? (If you see ROBOT ARMS or white beard, it's BREACH not Phoenix!)

**If ANY verification fails, change your answer to "Unknown" for that player!**

**OUTPUT FORMAT** - Return ONLY a JSON array:
```json
["Agent1", "Agent2", "Agent3", "Agent4", "Agent5", "Agent6", "Agent7", "Agent8", "Agent9", "Agent10"]
```

**STRICT RULES**:
- Return EXACTLY 10 agent names in TOP to BOTTOM order
- Use exact agent names (case-sensitive)
- If portrait unclear → "Unknown"
- If doesn't match descriptions → "Unknown"
- If uncertain between two agents → "Unknown"
- DO NOT guess or make assumptions
- Better "Unknown" than wrong

**CONFIDENCE CHECK before each agent**:
1. Can you clearly see the portrait? NO → "Unknown"
2. Does it match description exactly? NO → "Unknown"
3. Are you 90%+ certain? NO → "Unknown"

Begin detection now:"""
    
    def _parse_agent_response(self, response_text: str) -> List[str]:
        """Parse Gemini's response to extract agent list"""
        try:
            text = response_text.strip()
            
            # Remove markdown code blocks
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            # Try to find JSON array
            # Look for pattern: ["Agent1", "Agent2", ...]
            json_match = re.search(r'\[.*?\]', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
            
            # Parse JSON
            agents = json.loads(text)
            
            if not isinstance(agents, list):
                print(f"⚠️ Response is not a list: {agents}")
                return ['Unknown'] * 10
            
            return agents
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {response_text[:200]}")
            
            # Fallback: try to extract agent names manually
            agents = []
            for agent in self.agent_list:
                if agent in response_text:
                    agents.append(agent)
            
            if len(agents) >= 10:
                return agents[:10]
            
            return ['Unknown'] * 10
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            return ['Unknown'] * 10
    
    def _validate_agents(self, agents: List[str]) -> List[str]:
        """Validate and normalize agent names - allow duplicates (they can happen in real games)"""
        validated = []
        agent_counts = {}
        
        for i, agent in enumerate(agents):
            normalized = self._normalize_agent_name(agent)
            
            # Exact match required - no fuzzy matching to avoid false positives
            if normalized in self.agent_list:
                # Track duplicates but don't reject them (duplicates are possible)
                if normalized in agent_counts:
                    agent_counts[normalized] += 1
                    validated.append(normalized)
                    print(f"   ✅ Player {i+1}: {normalized} (duplicate #{agent_counts[normalized]} - acceptable)")
                else:
                    agent_counts[normalized] = 1
                    validated.append(normalized)
                    print(f"   ✅ Player {i+1}: {normalized}")
                    
            elif normalized.lower() == 'unknown':
                # Explicitly marked as unknown
                validated.append('Unknown')
                print(f"   ❓ Player {i+1}: Unknown (AI uncertain)")
            else:
                # Strict: Only allow exact matches from agent list
                # Try case-insensitive match ONE time only
                found = False
                for valid_agent in self.agent_list:
                    if normalized.lower() == valid_agent.lower():
                        # Track duplicates for case-corrected agents too
                        if valid_agent in agent_counts:
                            agent_counts[valid_agent] += 1
                            validated.append(valid_agent)
                            print(f"   ⚠️ Player {i+1}: {valid_agent} (case corrected, duplicate #{agent_counts[valid_agent]} - acceptable)")
                        else:
                            agent_counts[valid_agent] = 1
                            validated.append(valid_agent)
                            print(f"   ⚠️ Player {i+1}: {valid_agent} (case corrected)")
                        found = True
                        break
                
                if not found:
                    validated.append('Unknown')
                    print(f"   ❌ Player {i+1}: '{agent}' is invalid -> Unknown")
        
        # Ensure we have exactly 10 agents
        while len(validated) < 10:
            validated.append('Unknown')
        
        # Final sanity check: log duplicate summary
        duplicate_agents = {agent: count for agent, count in agent_counts.items() if count >= 2}
        if duplicate_agents:
            print(f"   📊 Duplicate summary: {duplicate_agents}")
        
        return validated[:10]
    
    def _normalize_agent_name(self, agent: str) -> str:
        """Normalize agent name (trim, handle special cases)"""
        agent = agent.strip().strip('"').strip("'")
        
        # Handle common variations
        variations = {
            'kay/o': 'KAY/O',
            'kayo': 'KAY/O',
            'kay-o': 'KAY/O',
        }
        
        agent_lower = agent.lower()
        if agent_lower in variations:
            return variations[agent_lower]
        
        return agent
    
    def get_supported_agents(self) -> List[str]:
        """Get list of all supported agents"""
        return self.agent_list.copy()


# Global instance
_gemini_agent_detector = None

def get_gemini_agent_detector(api_key: Optional[str] = None) -> GeminiAgentDetector:
    """Get or create the global GeminiAgentDetector instance"""
    global _gemini_agent_detector
    if _gemini_agent_detector is None:
        _gemini_agent_detector = GeminiAgentDetector(api_key)
    return _gemini_agent_detector
