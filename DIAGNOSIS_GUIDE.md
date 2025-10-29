# 🔬 Agent Detection Diagnosis Guide

## ⚠️ Problem: Same 3 Errors Keep Happening

Even after multiple enhancements, the AI is **still** making these mistakes:
1. **Cypher → Chamber**
2. **Raze → Sage**
3. **Breach → Phoenix**

---

## 🧪 **Latest Changes Made**

### 1. **Added Mandatory Verification Checklist** (at start of prompt)
Forces AI to check BEFORE identifying:
- Is there a white hat? (Cypher vs Chamber)
- Are arms huge robot prosthetics? (Breach vs Phoenix)
- Is there a crop top showing midriff? (Raze vs Sage)

### 2. **Added Final Double-Check** (at end of prompt)
Verification questions for each problematic agent:
- ✅ If you said "Cypher" → Did you see WHITE HAT + HIDDEN FACE?
- ✅ If you said "Raze" → Did you see CROP TOP + MIDRIFF?
- ✅ If you said "Breach" → Did you see ROBOT ARMS?

### 3. **Increased Temperature to 0.1**
(from 0.0) - Sometimes zero temperature causes the AI to get stuck in wrong patterns

---

## 🔍 **Diagnostic Steps**

### Step 1: Check If Bot Loaded New Prompt
1. Restart your bot completely
2. In the terminal, you should see initialization messages
3. Look for: `✅ Gemini Vision Agent Detector initialized`

### Step 2: Test with Explicit Logging
Let's add detailed logging to see what the AI is actually seeing:

**Add this temporarily to `gemini_agent_detector.py` after the API call:**
```python
# After: response = self.model.generate_content(...)
print(f"🔍 RAW AI RESPONSE:\n{response.text}\n")
```

This will show us the AI's reasoning before validation.

### Step 3: Test Individual Agents
Instead of testing full scoreboards, test these agents individually:

**Priority Test Cases:**
1. Upload a screenshot with **ONLY Cypher** visible
2. Upload a screenshot with **ONLY Chamber** visible  
3. Upload a screenshot with **ONLY Raze** visible
4. Upload a screenshot with **ONLY Sage** visible
5. Upload a screenshot with **ONLY Breach** visible
6. Upload a screenshot with **ONLY Phoenix** visible

**Expected Results:**
- Each should be detected correctly
- If not, the prompt isn't being understood

---

## 🤔 **Possible Root Causes**

### Theory 1: Portrait Quality Issues
**Hypothesis:** The portraits are too small/blurry for the AI to see details

**Test:** 
- Check the image size before it's sent to Gemini
- Look for: `📐 Resized image to...` in logs
- If portraits are < 50px each, they're too small

**Solution:**
- Increase image size or crop individual portraits
- Send higher resolution screenshots

### Theory 2: Color Confusion
**Hypothesis:** The color schemes are confusing the AI

**Test:**
- Does Cypher's white hat look grey in the screenshot?
- Does Raze's outfit look white instead of grey/orange?
- Does Breach's robot arms not look obviously robotic?

**Solution:**
- Adjust contrast descriptions
- Focus on shapes instead of colors

### Theory 3: Model Hallucination
**Hypothesis:** Gemini Vision is "seeing" patterns that aren't there

**Test:**
- Try a different Gemini model (gemini-1.5-pro instead of 2.0-flash-exp)
- Compare results between models

**Solution:**
- Switch model in the model selection order
- Add explicit "DO NOT HALLUCINATE" warnings

### Theory 4: Prompt Too Long
**Hypothesis:** The 600+ line prompt is overwhelming the AI

**Test:**
- Count tokens in the prompt (should be < 2000)
- Try a simplified version with ONLY the 6 problematic agents

**Solution:**
- Create a "short prompt" mode for testing
- Remove less common agents temporarily

---

## 🛠️ **Troubleshooting Actions**

### Action 1: Enable Verbose Logging
Add to `gemini_agent_detector.py`:
```python
def detect_agents_from_screenshot(self, image_path: str):
    # ... existing code ...
    
    print(f"📸 Image path: {image_path}")
    print(f"📏 Image size: {img.size}")
    print(f"📝 Prompt length: {len(prompt)} characters")
    print(f"🤖 Using model: {self.model._model_name}")
    
    # ... rest of code ...
    
    print(f"📤 Raw response text:\n{response.text}")
    print(f"🎯 Parsed agents: {agents}")
```

### Action 2: Test Different Models
Edit `_initialize_model()` priority order:
```python
# Try Pro model first (slower but more accurate)
model_priority = [
    'gemini-1.5-pro',           # MORE ACCURATE
    'gemini-2.0-flash-exp',      # Current
    'gemini-1.5-flash',
    # ... rest
]
```

### Action 3: Simplify for Testing
Create a test version that ONLY checks for these 6 agents:
- Cypher
- Chamber  
- Raze
- Sage
- Breach
- Phoenix

Remove all other agents from the prompt temporarily.

### Action 4: Try Few-Shot Examples
Add example images to the prompt:
```python
# In the prompt:
**EXAMPLE - Cypher:**
[Show example Cypher portrait]
This is Cypher: WHITE HAT, NO FACE VISIBLE

**EXAMPLE - Chamber:**
[Show example Chamber portrait]  
This is Chamber: GLASSES, FACE VISIBLE
```

(Gemini Vision supports multiple images in one prompt)

---

## 📊 **Data Collection Form**

When testing, collect this info:

```
Test #: _____
Date: _____
Screenshot: [describe what agents are visible]

Results:
Player 1: Expected _____, Got _____
Player 2: Expected _____, Got _____
...

Logs:
[Paste relevant logs here]

Notes:
[Any observations]
```

---

## 🎯 **Next Steps**

### Immediate Actions:
1. ✅ Restart bot with new prompt changes
2. 🔬 Add verbose logging (see Action 1)
3. 🧪 Test individual agents (not full teams)
4. 📝 Collect test results

### If Still Failing:
1. Try gemini-1.5-pro model (more accurate but slower)
2. Simplify prompt to only 6 problematic agents
3. Consider using few-shot examples with actual images
4. Check if image quality/size is sufficient

### Alternative Approaches:
1. **Hybrid Approach:** Use YOLO to detect agent positions, then Gemini to identify each one individually
2. **Template Matching:** Pre-process images to enhance contrast before sending to Gemini
3. **Ensemble:** Call the API 3 times and use majority vote
4. **Fine-tuning:** If Gemini supports it, fine-tune on your specific screenshot style

---

## 🚨 **Emergency Fallback**

If nothing works, consider:
1. **Manual Mode:** Flag these 3 pairs for manual verification
2. **Confidence Scores:** Always show these 3 as "Unknown" if confidence < 95%
3. **User Confirmation:** Ask user to confirm when these agents detected
4. **Blacklist Mode:** Temporarily disable auto-detection for these 6 agents

---

## 📞 **Get Help**

If you've tried everything:
1. Share a screenshot with agents labeled (ground truth)
2. Share the bot logs showing what was detected
3. Share the exact Gemini model being used
4. We can debug the raw API response together

Let's systematically diagnose and fix this! 🔧
