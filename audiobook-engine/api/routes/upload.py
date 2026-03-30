from fastapi import APIRouter, UploadFile, File
import os
import uuid

router = APIRouter()

UPLOAD_DIR = "audio_files/uploads"

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{extension}")
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    return {"file_id": file_id, "filename": file.filename}
