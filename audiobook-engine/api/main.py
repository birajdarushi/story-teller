from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import jobs, upload, audio

app = FastAPI(title="Immersive Audiobook Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(audio.router, prefix="/audio", tags=["audio"])

@app.get("/")
async def root():
    return {"message": "Audiobook Engine API is running"}
