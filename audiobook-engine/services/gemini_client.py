import google.generativeai as genai
import os
import json
from config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

def parse_scenes(text: str):
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    # Use absolute path for prompt file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(base_dir, "prompts", "scene_parser.txt")
    
    with open(prompt_path, "r") as f:
        system_prompt = f.read()
        
    prompt = f"{system_prompt}\n\nBOOK TEXT:\n{text}"
    
    response = model.generate_content(prompt)
    
    # Extract JSON from response
    try:
        # Gemini often wraps JSON in backticks
        content = response.text.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        scenes = json.loads(content)
        return scenes
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        print(f"Raw response: {response.text}")
        return None
