from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()

OUTPUT_DIR = "audio_files/output"

@router.get("/{job_id}")
async def get_audio(job_id: str):
    # This is a simplified version, should check DB for actual path
    file_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp3")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(file_path)
