from gtts import gTTS
import os

def generate_narration_gtts(text: str, output_path: str):
    """
    Generate narration using gTTS as a fallback and save to output_path.
    """
    print(f"Generating narration using gTTS (fallback) for text (length: {len(text)})")
    tts = gTTS(text=text, lang='en')
    tts.save(output_path)
    print(f"Narration generated and saved using gTTS to: {output_path}")
    return output_path
