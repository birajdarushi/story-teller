from db.session import SessionLocal
from db.models import Scene, Job
import json

def check_scenes(job_id):
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        print(f"Job: {job.book_title}, Status: {job.status}")
        scenes = db.query(Scene).filter(Scene.job_id == job_id).all()
        print(f"Number of scenes found: {len(scenes)}")
        for scene in scenes:
            print(f"  Scene {scene.order}: {scene.scene_type} (Mood: {scene.mood})")
            print(f"  Narrator Tone: {scene.narrator_tone}")
            print(f"  Music Prompt: {scene.music_prompt}")
            print(f"  Characters: {scene.characters}")
            print(f"  Raw Text: {scene.raw_text[:100]}...")
            print("-" * 20)
    else:
        print("Job not found.")
    db.close()

if __name__ == "__main__":
    check_scenes("39a44fd0-f0e5-4973-afaf-399503287c49")
