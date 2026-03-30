from workers.celery_app import app
from services.musicgen_client import generate
from db.session import SessionLocal
from db.models import AudioTrack
import os
from config import settings
import uuid

@app.task(name='workers.music_gen.generate_music_task')
def generate_music_task(job_id: str, scene_id: str, music_prompt: str):
    """
    Celery task to generate music for a scene.
    Generates a 30s clip by default.
    """
    # Ensure directory exists
    output_dir = os.path.join(settings.LOCAL_STORAGE_PATH, "music")
    os.makedirs(output_dir, exist_ok=True)
    
    file_name = f"{scene_id}_music.wav"
    file_path = os.path.join(output_dir, file_name)
    
    # Generate music offline
    try:
        generate(music_prompt, 30, file_path)
    except Exception as e:
        print(f"Error in music_gen task: {e}")
        raise e
        
    # Update database
    db = SessionLocal()
    try:
        audio_track = AudioTrack(
            scene_id=scene_id,
            track_type="music",
            file_path=file_path,
            duration_seconds=30.0,
            status="done"
        )
        db.add(audio_track)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
        
    return file_path
