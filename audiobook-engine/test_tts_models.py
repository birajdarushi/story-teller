import requests
import os
from dotenv import load_dotenv

load_dotenv("/Users/rushiraj/Desktop/Home/story-teller/audiobook-engine/.env")
api_key = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
try:
    response = requests.get(url)
    models = response.json().get("models", [])
    tts_models = [m["name"] for m in models if "tts" in m["name"].lower() or "audio" in m["name"].lower() or "2.5" in m["name"].lower()]
    
    print("Found potential TTS / Gemini 2.5 models:")
    for m in tts_models:
        print(m)
        
except Exception as e:
    print(e)
