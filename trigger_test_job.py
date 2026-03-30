import uuid
import sys
import os

# Add audiobook-engine to path
sys.path.append(os.path.join(os.getcwd(), "audiobook-engine"))

from db.session import SessionLocal
from db.models import Job
from workers.pipeline import run_pipeline

def trigger_test():
    db = SessionLocal()
    job_id = str(uuid.uuid4())
    
    text = """
    To Sherlock Holmes she is always the woman. I have seldom heard him mention her under any other name. 
    In his eyes she eclipses and predominates the whole of her sex. It was not that he felt any emotion 
    akin to love for Irene Adler. All emotions, and that one particularly, were abhorrent to his cold, 
    precise but admirably balanced mind. He was, I take it, the most perfect reasoning and observing 
    machine that the world has seen, but as a lover he would have placed himself in a false position. 
    He never spoke of the softer passions, save with a gibe and a sneer. They were admirable things 
    for the observer—excellent for drawing the veil from men’s motives and actions.
    """
    
    try:
        # 1. Create Job in DB
        job = Job(id=job_id, book_title="Sherlock Holmes Test", status="pending")
        db.add(job)
        db.commit()
        print(f"Created Job: {job_id}")
        
        # 2. Trigger Pipeline (directly calling task for monitoring in this script)
        # Using .delay() would run it in worker, but we can call it here or monitor log
        print("Triggering pipeline...")
        run_pipeline.delay(job_id, text)
        print("Pipeline triggered in Celery worker. Monitor 'audiobook-engine/celery_test.log' for progress.")
        
    finally:
        db.close()

if __name__ == "__main__":
    trigger_test()
