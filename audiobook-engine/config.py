import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # LLM — scene parsing
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

    # TTS — narration
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    # MusicGen — LOCAL model
    MUSICGEN_MODEL = os.getenv("MUSICGEN_MODEL", "facebook/musicgen-small")
    MUSICGEN_DEVICE = os.getenv("MUSICGEN_DEVICE", "mps")

    # Storage
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
    LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", "./audio_files")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://app:secret@localhost:5432/audiobook")

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # App
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    API_PORT = int(os.getenv("API_PORT", 8000))

settings = Settings()
