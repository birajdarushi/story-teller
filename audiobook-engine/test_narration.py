from services.elevenlabs_client import generate_narration
import os

if __name__ == "__main__":
    # Ensure directory exists
    os.makedirs("audio_files/test", exist_ok=True)
    
    text = "Hello, this is a test of the narration system."
    output_path = "audio_files/test/test_narration.mp3"
    
    print(f"Testing ElevenLabs with text: {text}")
    try:
        final_path = generate_narration(text, output_path)
        print(f"Test completed. Output: {final_path}")
    except Exception as e:
        print(f"Test failed: {e}")
