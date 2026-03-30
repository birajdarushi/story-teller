from workers.celery_app import app
from services.elevenlabs_client import generate_narration
from db.session import SessionLocal
from db.models import AudioTrack
import os
from config import settings
import uuid

@app.task(name='workers.narration.generate_narration_task')
def generate_narration_task(job_id: str, scene_id: str, text: str):
    """
    Celery task to generate narration for a scene.
    """
    # Ensure directory exists
    output_dir = os.path.join(settings.LOCAL_STORAGE_PATH, "narration")
    os.makedirs(output_dir, exist_ok=True)
    
    file_name = f"{scene_id}_narration.mp3"
    file_path = os.path.join(output_dir, file_name)
    
    # Generate narration
    try:
        generate_narration(text, file_path)
    except Exception as e:
        print(f"Error in narration task: {e}")
        raise e
        
    # Update database
    db = SessionLocal()
    try:
        audio_track = AudioTrack(
            scene_id=scene_id,
            track_type="narration",
            file_path=file_path,
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
