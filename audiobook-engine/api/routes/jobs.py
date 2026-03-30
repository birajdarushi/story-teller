from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db import models
from pydantic import BaseModel
import os
import glob
from workers.pipeline import run_pipeline

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class JobCreate(BaseModel):
    book_title: str
    file_id: str

@router.post("/")
async def create_job(job: JobCreate, db: Session = Depends(get_db)):
    # Find the uploaded file (look for common extensions)
    upload_dir = "audio_files/uploads"
    search_pattern = os.path.join(upload_dir, f"{job.file_id}.*")
    matching_files = glob.glob(search_pattern)
    
    if not matching_files:
        raise HTTPException(status_code=404, detail="Uploaded file not found")
    
    input_file_path = matching_files[0]
    
    # Create the job in the database
    db_job = models.Job(
        book_title=job.book_title,
        status="pending",
        input_file_path=input_file_path
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    # Read the text content
    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        # If it's not a text file, we might need a PDF parser later
        # For now, let's assume it's text
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    # Trigger Celery task
    run_pipeline.delay(str(db_job.id), text)
    
    return {"job_id": str(db_job.id)}

@router.get("/{job_id}")
async def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
