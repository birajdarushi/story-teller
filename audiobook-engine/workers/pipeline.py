from workers.celery_app import app
from workers.scene_parser import parse_scenes_task
from workers.narration import generate_narration_task
from workers.music_gen import generate_music_task
from db.session import SessionLocal
from db.models import Job
from celery import group
import time

def update_job_status(db, job_id, status, error=None):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        job.status = status
        if error:
            job.error_message = error
        db.commit()

@app.task(name='workers.pipeline.run_pipeline')
def run_pipeline(job_id: str, text: str):
    db = SessionLocal()
    try:
        # Phase 2: Parsing
        update_job_status(db, job_id, "parsing")
        # Run parse_scenes_task synchronously in this worker for simplicity or delay().get()
        scenes = parse_scenes_task(job_id, text)
        
        # Phase 3: Generation
        update_job_status(db, job_id, "generating")
        
        # Sequential Execution for M1 8GB Memory Safety
        print(f"Generating Narration sequentially for {len(scenes)} scenes...")
        for scene in scenes:
            generate_narration_task(job_id, scene["id"], scene["raw_text"])
        
        print(f"Generating Music sequentially for {len(scenes)} scenes to protect GPU context...")
        for scene in scenes:
            generate_music_task(job_id, scene["id"], scene["music_prompt"])
        
        # Phase 4: Cinematic Audio Mixing
        update_job_status(db, job_id, "mixing")
        
        from services.mixer import mix_audio_outputs
        final_file = mix_audio_outputs(job_id, scenes)
        
        # Link to DB and Finish
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = "done"
        job.file_path = final_file
        db.commit()
        
    except Exception as e:
        update_job_status(db, job_id, "failed", error=str(e))
        raise e
    finally:
        db.close()
