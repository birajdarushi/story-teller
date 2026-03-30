from workers.celery_app import app
from services.gemini_client import parse_scenes
from db.session import SessionLocal
from db.models import Scene
import uuid

@app.task(name='workers.scene_parser.parse_scenes_task')
def parse_scenes_task(job_id: str, text: str):
    scenes_json = parse_scenes(text)
    if not scenes_json:
        raise Exception("Failed to parse scenes from Gemini")
    
    db = SessionLocal()
    try:
        scenes = []
        for i, scene_data in enumerate(scenes_json):
            db_scene = Scene(
                job_id=job_id,
                order=scene_data.get("order", i+1),
                chapter=scene_data.get("chapter", "Chapter 1"),
                scene_type=scene_data.get("scene_type"),
                mood=scene_data.get("mood"),
                characters=scene_data.get("characters"),
                music_prompt=scene_data.get("music_prompt"),
                narrator_tone=scene_data.get("narrator_tone"),
                estimated_words=scene_data.get("estimated_words"),
                raw_text=scene_data.get("raw_text")
            )
            db.add(db_scene)
            db.flush() # To get the id
            scene_data["id"] = str(db_scene.id)
            scenes.append(scene_data)
        
        db.commit()
        return scenes
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
