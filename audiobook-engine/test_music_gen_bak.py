from services.musicgen_client import generate
import os

if __name__ == "__main__":
    # Ensure directory exists
    os.makedirs("audio_files/test", exist_ok=True)
    
    prompt = "calm ambient piano, soothing"
    duration = 5 # 5s for fast test
    output_path = "audio_files/test/test_music.wav"
    
    print(f"Testing MusicGen with prompt: {prompt}")
    final_path = generate(prompt, duration, output_path)
    print(f"Test completed. Output: {final_path}")
