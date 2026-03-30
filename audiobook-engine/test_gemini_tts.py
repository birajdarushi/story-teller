import os
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv("/Users/rushiraj/Desktop/Home/story-teller/audiobook-engine/.env")

def test_tts():
    print("Testing gemini-2.5-pro-preview-tts for quota...")
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.5-pro-preview-tts",
            contents="Hello! This is a test for the audiobook engine.",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Aoede"
                        )
                    )
                )
            )
        )
        
        wrote_audio = False
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    with open("/tmp/gemini_tts_test.wav", "wb") as f:
                        f.write(part.inline_data.data)
                    print(f"Success! Gemini TTS returned {len(part.inline_data.data)} bytes of audio.")
                    wrote_audio = True
                    break
                
        if not wrote_audio:
            print("No audio output found in response parts:", response.text)
            
    except Exception as e:
        print(f"Error during TTS generation: {e}")

if __name__ == "__main__":
    test_tts()
