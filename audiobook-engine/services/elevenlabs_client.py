import os
import requests
from config import settings
from services.gtts_client import generate_narration_gtts

def generate_narration(text: str, output_path: str):
    """
    Generate narration using ElevenLabs API and save to output_path.
    Falls back to gTTS if ElevenLabs fails.
    Returns path of generated file.
    """
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": settings.ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        print(f"Generating narration for text (length: {len(text)})")
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 200:
            print(f"ElevenLabs API Error: {response.status_code} - {response.text}")
            print("Falling back to gTTS...")
            return generate_narration_gtts(text, output_path)
            
        with open(output_path, 'wb') as f:
            f.write(response.content)
            
        print(f"Narration generated and saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error in ElevenLabs generation: {e}")
        print("Falling back to gTTS...")
        return generate_narration_gtts(text, output_path)
