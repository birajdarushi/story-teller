import torch
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
import os
from config import settings
from pydub import AudioSegment

# Load model ONCE at module level — stays in memory between tasks
_model = None

def get_model():
    global _model
    
    # Determine device ONLY once inside the child process (fixes macOS fork SIGSEGV)
    if _model is None:
        device = 'cpu'  # FORCED CPU: Apple MPS literally corrupts EnCodec mathematics (creates hyper-fast circus noise)
        print(f'MusicGen using device: {device}')
        print(f'MusicGen using device: {device}')
        print(f'Loading MusicGen {settings.MUSICGEN_MODEL} (first load ~30s)...')
        
        _model = MusicGen.get_pretrained(settings.MUSICGEN_MODEL, device=device)
        _model.set_generation_params(duration=30)  # 30s clips default
        
    return _model

def generate(prompt: str, duration: int, output_path: str):
    """
    Generate music clip and save to output_path.
    Returns path of generated .wav file.
    """
    model = get_model()
    # Cap duration at 30s for small model to avoid memory pressure
    gen_duration = min(duration, 30)
    model.set_generation_params(duration=gen_duration)
    
    print(f"Generating music for prompt: {prompt} (duration: {gen_duration}s)")
    wav = model.generate([prompt])  # list of prompts
    
    # Remove .wav extension for audio_write (it adds it automatically)
    base_path = output_path.replace('.wav', '')
    
    audio_write(
        base_path,
        wav[0].cpu(),  # move back to CPU for saving
        model.sample_rate,
        strategy='peak',  # Changed to peak to completely eliminate static clipping distortion
    )
    
    final_wav_path = f"{base_path}.wav"
    print(f"Music generated and saved to: {final_wav_path}")
    return final_wav_path

def loop_to_duration(wav_path: str, target_seconds: int) -> str:
    """
    Loop a wav file to reach target_seconds.
    Adds fade-in/out to mask loop artifacts.
    """
    audio = AudioSegment.from_wav(wav_path)
    target_ms = int(target_seconds * 1000)
    
    if len(audio) < target_ms:
        # Loop with 2s crossfade to mask artifacts
        while len(audio) < target_ms + 2000:
            audio = audio.append(audio, crossfade=2000)
            
    audio = audio[:target_ms].fade_in(2000).fade_out(2000)
    looped_path = wav_path.replace('.wav', '_looped.wav')
    audio.export(looped_path, format='wav')
    return looped_path
