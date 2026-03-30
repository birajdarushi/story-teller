from sqlalchemy import Column, String, Integer, Float, Enum, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .session import Base

class JobStatus(Enum):
    pending = "pending"
    parsing = "parsing"
    generating = "generating"
    mixing = "mixing"
    done = "done"
    failed = "failed"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String, default="pending")  # Simplified for MVP
    book_title = Column(String)
    input_file_path = Column(String)
    output_url = Column(String)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    scenes = relationship("Scene", back_populates="job", cascade="all, delete-orphan")

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    order = Column(Integer)
    chapter = Column(String)
    scene_type = Column(String)
    mood = Column(String)
    characters = Column(JSON)
    music_prompt = Column(String)
    narrator_tone = Column(String)
    estimated_words = Column(Integer)
    raw_text = Column(Text)

    job = relationship("Job", back_populates="scenes")
    audio_tracks = relationship("AudioTrack", back_populates="scene", cascade="all, delete-orphan")

class AudioTrack(Base):
    __tablename__ = "audio_tracks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scene_id = Column(UUID(as_uuid=True), ForeignKey("scenes.id"))
    track_type = Column(String)  # narration, music, sfx
    file_path = Column(String)
    duration_seconds = Column(Float)
    status = Column(String, default="pending")

    scene = relationship("Scene", back_populates="audio_tracks")
