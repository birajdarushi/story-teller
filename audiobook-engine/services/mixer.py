import os
from pydub import AudioSegment
from config import settings

def mix_audio_outputs(job_id: str, scenes: list):
    """
    Mixes narration and music for all scenes sequentially and exports a final audiobook.
    """
    final_audio = AudioSegment.empty()
    
    narration_dir = os.path.join(settings.LOCAL_STORAGE_PATH, "narration")
    music_dir = os.path.join(settings.LOCAL_STORAGE_PATH, "music")
    final_dir = os.path.join(settings.LOCAL_STORAGE_PATH, "final")
    os.makedirs(final_dir, exist_ok=True)
    
    print(f"[MIXER] Starting mixing for {len(scenes)} scenes...")
    
    for scene in scenes:
        scene_id = scene["id"]
        narration_path = os.path.join(narration_dir, f"{scene_id}_narration.mp3")
        music_path = os.path.join(music_dir, f"{scene_id}_music.wav")
        
        # 1. Load Narration
        if os.path.exists(narration_path):
            narration = AudioSegment.from_file(narration_path)
        else:
            print(f"[MIXER] Warning: Missing narration for scene {scene_id}")
            narration = AudioSegment.silent(duration=2000)
            
        # 2. Load and Process Music (if available)
        if os.path.exists(music_path):
            music = AudioSegment.from_file(music_path)
            
            # Loop music if it is shorter than the narration duration
            if len(music) < len(narration):
                loops = (len(narration) // len(music)) + 1
                music = music * loops
                
            # Trim the music exactly to the length of the narration
            music = music[:len(narration)]
            
            # Reduce music volume by 15 decibels so the narrator can be clearly heard
            # And fade it in and out smoothly
            music = (music - 15).fade_in(2000).fade_out(2000)
            
            # Mix the voice exactly over the background music
            scene_mix = narration.overlay(music)
        else:
            print(f"[MIXER] Warning: Missing music for scene {scene_id}")
            scene_mix = narration
            
        # 3. Concatenate this finished scene to the main audiobook timeline (with 1.5s silent pause between scenes)
        final_audio += scene_mix + AudioSegment.silent(duration=1500)
        
    # Export final MP3
    final_path = os.path.join(final_dir, f"{job_id}_final.mp3")
    print(f"[MIXER] Exporting highly-produced cinematic audiobook to {final_path}...")
    final_audio.export(final_path, format="mp3", bitrate="192k")
    print("[MIXER] Mixing 100% complete!")
    
    return final_path
