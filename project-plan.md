# IMMERSIVE AUDIOBOOK ENGINE
## MVP Build Document — Apple M1 8GB Edition

> Text → Narration + Music + SFX, fully automated
>
> **Configured for: Apple M1 | 8 GB RAM | 256 GB SSD | No GPU**


# 1. Your Machine — Apple M1 8GB

This document is written specifically for your hardware. Every performance estimate, memory limit, Docker setting, and model choice below is calibrated for the M1 8GB. Read this section before you start.


| Component | Spec | Impact on this project |
| --- | --- | --- |
| Chip | Apple M1 | ARM64 — some Python packages need special builds |
| CPU cores | 8 total (4 performance + 4 efficiency) | Celery workers: max 4 concurrent tasks recommended |
| CPU clock | Performance cores ~3.2 GHz | MusicGen on CPU: ~2-4 min per 30s clip |
| RAM | 8 GB unified memory | Shared between CPU and GPU — biggest constraint |
| RAM bandwidth | 68.25 GB/s | Fast for model inference vs discrete RAM |
| Neural Engine | 16-core, 11 TOPS | NOT used by PyTorch by default — see MPS section |
| Metal GPU | 7-core GPU (integrated) | MPS backend available — faster than CPU for inference |
| Storage | 256 GB NVMe SSD | Fast I/O, but watch disk space — models are large |
| SSD speed | ~3.4 GB/s read | Model loading is fast once cached |
| OS | macOS (Apple Silicon) | Use arm64 Docker images, brew for deps |


## The unified memory reality
The most important thing to understand about M1 8GB: the CPU and GPU share the same 8GB pool. There is no separate VRAM. This means:

- macOS itself uses ~2-3 GB at idle
- Docker Desktop uses another ~1-2 GB
- Your Python workers + models will have ~3-4 GB left to work with
- Running MusicGen (small model = ~1.5 GB) + Postgres + Redis + the API server simultaneously will push you close to the edge

If your Mac starts swapping to SSD, generation speed will drop 10-50x. Watch Activity Monitor > Memory Pressure. Keep it green.

### Memory allocation strategy

| Process | Approx RAM usage |
| --- | --- |
| macOS system | 2.0 - 2.5 GB |
| Docker Desktop | 1.0 - 1.5 GB (cap it — see below) |
| Redis container | 50 - 100 MB |
| Postgres container | 100 - 200 MB |
| FastAPI server | 200 - 400 MB |
| Celery worker (idle) | 300 - 500 MB |
| MusicGen small (loaded) | 1.3 - 1.6 GB |
| ElevenLabs TTS call | negligible (API call) |
| TOTAL peak | ~6.5 - 7.5 GB |


This is tight but workable. The key is: load MusicGen once and keep it in memory between tasks. Do NOT reload the model per task — that kills performance.

## Docker Desktop memory cap
By default Docker Desktop on Mac takes as much memory as it wants. Cap it explicitly:

- Open Docker Desktop → Settings → Resources → Advanced
- Set Memory limit to 3 GB (leaves headroom for macOS + your Python process)
- Set CPUs to 4 (the 4 performance cores — leave efficiency cores for macOS)
- Set Swap to 512 MB
- Click Apply & Restart

With this cap, Redis + Postgres + the API container will run comfortably inside 3 GB. MusicGen runs outside Docker in your local Python env — not inside a container.

## MPS vs CPU — what to use
Apple M1 has a Metal GPU (7 cores) accessible via PyTorch's MPS (Metal Performance Shaders) backend. This is faster than CPU for model inference, but it is NOT the same as CUDA and has some quirks.


| Backend | MusicGen speed (30s clip) | Notes |
| --- | --- | --- |
| CPU (8 cores) | 3 - 5 minutes | Stable, always works, uses more RAM |
| MPS (M1 GPU) | 45 - 90 seconds | 3-4x faster, shares unified RAM |
| CUDA (GPU) | 5 - 15 seconds | Not available on M1 |


Use MPS. It is 3-4x faster and the audiocraft/MusicGen library supports it. Set MUSICGEN_DEVICE=mps in your .env. See Section 7 for the exact code.


# 2. What We Are Building

The Immersive Audiobook Engine converts a raw book (PDF or plain text) into a full cinematic audio experience — narration with character voices, adaptive background music, and contextual sound effects — all automatically generated from the text.

The gap this fills: every existing tool (ElevenLabs, NarrationBox) does narration only. Nobody has built the unified pipeline — narration + music + SFX — context-aware from a book input. That is the moat.

### Core user flow
Upload book  →  Pick chapter range  →  Wait  →  Download MP3

### The key insight
We treat a book as a scene graph, not a flat text dump. Each scene has a type (battle, dialogue, discovery), a mood, characters, and events. Once we have that graph, every generation task becomes targeted and composable.


# 3. MVP Scope


| Feature | MVP | V2 |
| --- | --- | --- |
| Input | Plain text / PDF, one chapter | Full ePub, chapter selection UI |
| Narration | Single narrator voice | Per-character voice profiles |
| Music | One background track per scene | Adaptive transitions |
| SFX | Skip for MVP | Scene-triggered sound events |
| Mixing | Basic volume blend | Ducking + mastering (-23 LUFS) |
| Output | MP3 file download | Streaming player |
| UI | Upload + progress + download | Full web app |


# 4. Local Dev Setup — Mac M1

Complete setup sequence. Do this once before writing any code.

## Step 1 — Homebrew + system deps

```
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Follow the post-install instructions to add brew to PATH
# Then install system dependencies
brew install ffmpeg          # audio mixing — REQUIRED
brew install postgresql@15   # only needed if running Postgres locally
brew install redis           # only needed if running Redis locally

# Verify ffmpeg works
ffmpeg -version
```

## Step 2 — Python environment
Use Python 3.11. It has the best arm64 support and is the most stable for audiocraft on M1.


```
# Install pyenv to manage Python versions
brew install pyenv
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc

# Install Python 3.11 (arm64 native)
pyenv install 3.11.9
pyenv global 3.11.9
python --version  # should print Python 3.11.9

# Create virtual env for the project
cd audiobook-engine
python -m venv venv
source venv/bin/activate
```

## Step 3 — Python packages
Install order matters. PyTorch must be installed before audiocraft.


```
# Install PyTorch with MPS support (arm64 native build)
pip install torch torchvision torchaudio
# NOTE: on M1, pip installs the arm64 native build automatically
# Do NOT use conda for this — it installs x86 via Rosetta on some configs

# Verify MPS is available
python -c "import torch; print(torch.backends.mps.is_available())"
# Should print: True

# Install audiocraft (MusicGen)
pip install audiocraft

# Install the rest
pip install fastapi uvicorn celery redis sqlalchemy alembic
pip install pydub elevenlabs anthropic python-multipart
pip install psycopg2-binary python-dotenv pytest httpx

# Freeze
pip freeze > requirements.txt
```

Do NOT run pip install audiocraft before torch. It will pull in a CPU-only torch build and MPS will not work.

## Step 4 — Docker Desktop
We use Docker only for Redis and Postgres. All Python workers run natively on your M1 — not in Docker — so MPS works.


```
# Install Docker Desktop for Apple Silicon
# Download from: https://www.docker.com/products/docker-desktop/
# Make sure you download the Apple Silicon version

# After install, cap memory (Settings > Resources > Advanced):
# Memory: 3 GB
# CPUs: 4
# Swap: 512 MB

# Start only the infra services (not the API — that runs natively)
docker compose up redis postgres -d

# Verify both are up
docker compose ps
```

## Step 5 — Run the stack locally
Run API + Celery worker natively (not in Docker) so they can access MPS. Redis and Postgres stay in Docker.


```
# Terminal 1 — start infra
docker compose up redis postgres -d

# Terminal 2 — start FastAPI
source venv/bin/activate
uvicorn api.main:app --reload --port 8000

# Terminal 3 — start Celery worker
source venv/bin/activate
celery -A workers.celery_app worker --loglevel=info --concurrency=2
# concurrency=2 on M1 8GB — keeps memory pressure manageable

# Terminal 4 — frontend
cd audiobook-ui
npm run dev
```

--concurrency=2 means 2 Celery tasks run in parallel. On 8GB this is the safe limit. If you set it to 4 and MusicGen is loaded, you will hit memory pressure.


# 5. System Architecture

Four layers: Next.js frontend, FastAPI gateway, async Celery workers, and storage (Postgres + local files for MVP, S3 for V2).

### Why async workers?
Generation is slow. On your M1 with MPS, TTS via ElevenLabs API takes 5-15 seconds per scene (network bound). MusicGen locally takes 45-90 seconds per 30s clip. You cannot hold an HTTP connection open that long. The async pattern:

- User uploads → API creates job in Postgres, pushes task to Redis → returns job_id immediately
- Frontend polls GET /jobs/:id every 3 seconds for status updates
- Celery worker picks up the task, updates job status at each stage
- When done, MP3 path is written to the job record → frontend shows the player

### Worker chain — with M1 timing estimates

| Worker | What it does | Time on M1 8GB (per scene) |
| --- | --- | --- |
| scene_parser | Claude API call, parse JSON | 3 - 8 seconds (network) |
| narration | ElevenLabs API TTS call | 5 - 15 seconds (network) |
| music_gen | MusicGen local inference (MPS) | 45 - 90 seconds |
| mixer | pydub blend + FFmpeg export | 5 - 20 seconds |
| Total per scene |  | ~1 - 2.5 minutes |
| Full chapter (5 scenes, parallel) |  | ~3 - 6 minutes |


narration and music_gen run in parallel via Celery group(). On M1 the bottleneck is music_gen. Narration finishes first, then waits for music before mixing.


# 6. File Structure


## Backend — audiobook-engine/


> audiobook-engine/
>   api/  # FastAPI app
>     main.py  # app init, CORS, router mount
>     routes/
>       jobs.py  # POST /jobs  GET /jobs/:id  GET /jobs/:id/status
>       upload.py  # POST /upload — accept PDF or plain text
>       audio.py  # GET /audio/:job_id — serve local MP3 file
>     schemas.py  # Pydantic models — Job, Scene, AudioTrack, JobStatus
>     deps.py  # DB session injection, optional API key auth
>   workers/  # Celery tasks — run natively on M1 (not Docker)
>     celery_app.py  # broker=redis://localhost:6379 config
>     pipeline.py  # MAIN orchestrator — chains all tasks in order
>     scene_parser.py  # task: calls Claude API, validates JSON output
>     narration.py  # task: ElevenLabs TTS per scene, saves .wav
>     music_gen.py  # task: MusicGen MPS inference, saves .wav
>     mixer.py  # task: pydub mix + FFmpeg export to .mp3
>   services/  # Thin wrappers around external APIs + models
>     claude_client.py  # scene parse prompt builder + JSON validator
>     elevenlabs_client.py  # voice map, TTS API call, .wav save
>     musicgen_client.py  # model loader (MPS), generate(), loop utility
>     storage.py  # local file save/read (S3 swap-in for V2)
>   db/
>     models.py  # SQLAlchemy — Job, Scene, AudioTrack tables
>     session.py  # engine + SessionLocal factory
>     migrations/  # Alembic migration files
>   prompts/  # LLM prompt templates (plain .txt files)
>     scene_parser.txt  # System prompt for scene extraction — most critical file
>     music_prompt.txt  # Mood-to-MusicGen prompt template
>   audio_files/  # Local audio output — gitignored
>     uploads/  # Uploaded book files
>     narration/  # Per-scene narration .wav files
>     music/  # Per-scene music .wav files
>     output/  # Final mixed .mp3 files
>   config.py  # All env vars — API keys, paths, model config
>   requirements.txt
>   .env  # Your actual secrets — never commit this
>   .env.example  # Template for .env
>   .gitignore  # Include: .env, audio_files/, venv/, __pycache__/


## Frontend — audiobook-ui/


> audiobook-ui/  # Next.js 14 app
>   app/
>     page.tsx  # Home — upload form + book title input
>     jobs/[id]/page.tsx  # Job status polling + audio player
>     layout.tsx  # Root layout, fonts, global styles
>   components/
>     UploadForm.tsx  # Drag-drop file input, book title, submit
>     JobStatus.tsx  # Polls /jobs/:id every 3s, shows stage progress
>     AudioPlayer.tsx  # wavesurfer.js waveform + play/pause/download
>     SceneTimeline.tsx  # Chapter list with timestamps (V2)
>   lib/
>     api.ts  # Typed fetch wrappers for all backend routes
>     types.ts  # Job, Scene, AudioTrack TypeScript interfaces
>   package.json
>   next.config.ts


## Infra files


> docker-compose.yml  # Redis + Postgres ONLY — workers run natively
> .github/workflows/
>   ci.yml  # Lint + pytest on push


# 7. Key File Implementations


## musicgen_client.py — MPS configuration
This is the most M1-specific file. Load the model once at module level so it stays in memory between Celery tasks. Use MPS backend for 3-4x speedup over CPU.


> import torch
> from audiocraft.models import MusicGen
> from audiocraft.data.audio import audio_write
> import os
> # Determine device — MPS on M1, CPU fallback
> def get_device():
>     if torch.backends.mps.is_available():
>         return 'mps'
>     return 'cpu'
> DEVICE = get_device()
> print(f'MusicGen using device: {DEVICE}')
> # Load model ONCE at module level — stays in memory between tasks
> # musicgen-small: ~1.3 GB RAM — safe on M1 8GB
> # musicgen-medium: ~3.3 GB RAM — risky on 8GB, do not use
> _model = None
> def get_model():
>     global _model
>     if _model is None:
>         print('Loading MusicGen small (first load ~30s)...')
>         _model = MusicGen.get_pretrained('facebook/musicgen-small')
>         _model.set_generation_params(duration=30)  # 30s clips
>         if DEVICE == 'mps':
>             _model = _model.to(DEVICE)
>     return _model
> def generate(prompt: str, duration: int, output_path: str):
>     model = get_model()
>     model.set_generation_params(duration=min(duration, 30))
>     wav = model.generate([prompt])  # list of prompts
>     # wav shape: [batch, channels, samples]
>     audio_write(
>         output_path.replace('.wav', ''),
>         wav[0].cpu(),  # move back to CPU for saving
>         model.sample_rate,
>         strategy='loudness',
>     )
> def loop_to_duration(wav_path: str, target_seconds: int) -> str:
>     from pydub import AudioSegment
>     audio = AudioSegment.from_wav(wav_path)
>     target_ms = target_seconds * 1000
>     while len(audio) < target_ms:
>         audio = audio + audio
>     audio = audio[:target_ms].fade_in(2000).fade_out(2000)
>     looped_path = wav_path.replace('.wav', '_looped.wav')
>     audio.export(looped_path, format='wav')
>     return looped_path


Never use musicgen-medium on M1 8GB. It needs 3.3 GB just for the model, and with macOS + Docker + the worker process, you will swap. Use musicgen-small only.

## docker-compose.yml — infra only
On M1, we run ONLY Redis and Postgres in Docker. The API, Celery worker, and MusicGen all run natively so they can use MPS.


> version: '3.8'
> # M1 8GB NOTE: Only infra runs in Docker.
> # API + Celery + MusicGen run natively (venv) for MPS access.
> services:
>   redis:
>     image: redis:7-alpine
>     platform: linux/arm64   # native M1 image
>     ports:
>       - '6379:6379'
>     command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
>   postgres:
>     image: postgres:15
>     platform: linux/arm64   # native M1 image
>     environment:
>       POSTGRES_DB: audiobook
>       POSTGRES_USER: app
>       POSTGRES_PASSWORD: secret
>     ports:
>       - '5432:5432'
>     volumes:
>       - pgdata:/var/lib/postgresql/data
>     deploy:
>       resources:
>         limits:
>           memory: 512m
> volumes:
>   pgdata:


## celery_app.py — M1 concurrency config


> from celery import Celery
> from config import settings
> app = Celery(
>     'audiobook',
>     broker=settings.REDIS_URL,
>     backend=settings.REDIS_URL,
>     include=['workers.scene_parser', 'workers.narration',
>              'workers.music_gen', 'workers.mixer', 'workers.pipeline']
> )
> app.conf.update(
>     # M1 8GB: 2 concurrent tasks max to avoid memory pressure
>     worker_concurrency=2,
>     # Use prefork (default) — better for CPU-bound tasks on M1
>     worker_pool='prefork',
>     # Prevent task pile-up — one at a time per worker
>     worker_prefetch_multiplier=1,
>     # Longer timeout for MusicGen on CPU fallback
>     task_soft_time_limit=300,   # 5 min soft
>     task_time_limit=600,         # 10 min hard
>     # Results expire after 1 hour
>     result_expires=3600,
>     task_serializer='json',
>     result_serializer='json',
>     accept_content=['json'],
> )


## pipeline.py — orchestrator


> from celery import group
> from workers.celery_app import app
> from workers import scene_parser, narration, music_gen, mixer
> from db.session import SessionLocal
> from db.models import Job
> @app.task(bind=True)
> def run_pipeline(self, job_id: str, text: str):
>     db = SessionLocal()
>     try:
>         # Step 1 — parse scenes (must complete before anything else)
>         _update_status(db, job_id, 'parsing')
>         scenes = scene_parser.parse_scenes.delay(job_id, text).get(timeout=120)
>         # Step 2 — generate narration + music in parallel per scene
>         # On M1 8GB: concurrency=2, so 2 scenes generate simultaneously
>         _update_status(db, job_id, 'generating')
>         gen_tasks = group(
>             narration.generate.s(job_id, scene) for scene in scenes
>         ) | group(
>             music_gen.generate.s(job_id, scene) for scene in scenes
>         )
>         gen_tasks.apply_async().get(timeout=600)
>         # Step 3 — mix everything into final MP3
>         _update_status(db, job_id, 'mixing')
>         output_path = mixer.mix_and_export.delay(job_id).get(timeout=180)
>         _update_status(db, job_id, 'done', output_url=output_path)
>     except Exception as e:
>         _update_status(db, job_id, 'failed', error=str(e))
>         raise
>     finally:
>         db.close()
> def _update_status(db, job_id, status, output_url=None, error=None):
>     job = db.query(Job).filter(Job.id == job_id).first()
>     job.status = status
>     if output_url: job.output_url = output_url
>     if error: job.error_message = error
>     db.commit()


## mixer.py — pydub + FFmpeg


> from pydub import AudioSegment
> import os
> def mix_scene(narration_path: str, music_path: str, output_path: str):
>     narration = AudioSegment.from_wav(narration_path)
>     music = AudioSegment.from_wav(music_path)
>     # Loop music to match narration length
>     while len(music) < len(narration):
>         music = music + music
>     music = music[:len(narration)]
>     # Duck music under narration by 12 dB
>     music = music - 12
>     # Fade in/out music
>     music = music.fade_in(2000).fade_out(3000)
>     # Overlay and export
>     mixed = narration.overlay(music)
>     mixed.export(output_path, format='mp3', bitrate='192k')
>     return output_path
> def concat_scenes(scene_paths: list, final_path: str):
>     combined = AudioSegment.empty()
>     silence = AudioSegment.silent(duration=1500)  # 1.5s gap between scenes
>     for i, path in enumerate(scene_paths):
>         segment = AudioSegment.from_mp3(path)
>         combined += segment
>         if i < len(scene_paths) - 1:
>             combined += silence
>     combined.export(final_path, format='mp3', bitrate='192k')
>     return final_path


# 8. Environment Variables


> # .env  (copy from .env.example and fill in your keys)
> # LLM — scene parsing
> ANTHROPIC_API_KEY=sk-ant-...
> # TTS — narration
> ELEVENLABS_API_KEY=...
> ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM   # Rachel — neutral narrator
> # MusicGen — LOCAL model (no API key needed)
> MUSICGEN_MODEL=facebook/musicgen-small      # DO NOT use medium on 8GB
> MUSICGEN_DEVICE=mps                         # MPS for M1 — 3-4x faster than cpu
> # Storage — local for MVP (swap to s3 for V2)
> STORAGE_BACKEND=local
> LOCAL_STORAGE_PATH=./audio_files
> # Database
> DATABASE_URL=postgresql://app:secret@localhost:5432/audiobook
> # Redis (running in Docker on default port)
> REDIS_URL=redis://localhost:6379/0
> # App
> DEBUG=true
> API_PORT=8000


# 9. Database Schema

Three tables. Everything else is derived from these.

### jobs

| Column | Type + notes |
| --- | --- |
| id | UUID primary key |
| status | enum: pending \| parsing \| generating \| mixing \| done \| failed |
| book_title | String — user-provided |
| input_file_path | String — local path to uploaded file |
| output_url | String — local path to final MP3, null until done |
| error_message | String — set on failure |
| created_at | Timestamp |
| updated_at | Timestamp — auto-updated on status change |


### scenes

| Column | Type + notes |
| --- | --- |
| id | UUID primary key |
| job_id | UUID foreign key → jobs |
| order | Integer — playback order |
| chapter | String — e.g. Chapter 3 |
| scene_type | String — action \| dialogue \| description \| battle \| discovery |
| mood | String — comma-separated e.g. tense, melancholic |
| characters | JSON array of character name strings |
| music_prompt | String — 10 words max, for MusicGen |
| narrator_tone | String — e.g. urgent, quiet and reflective |
| estimated_words | Integer — used to estimate audio duration |
| raw_text | Text — the actual scene text from the book |


### audio_tracks

| Column | Type + notes |
| --- | --- |
| id | UUID primary key |
| scene_id | UUID foreign key → scenes |
| track_type | enum: narration \| music \| sfx |
| file_path | String — local path to .wav file |
| duration_seconds | Float — actual audio length after generation |
| status | enum: pending \| done \| failed |


# 10. The Scene Parser Prompt

This is the most critical file in the project. Everything downstream depends on the quality of this JSON. Iterate on this before building anything else.

File: prompts/scene_parser.txt — paste this as the system prompt in claude_client.py


> You are a literary analyst specializing in audio production.
> Given a book excerpt, extract scenes as a JSON array.
> Each scene object must contain:
>   scene_id        - string, format: ch{N}_scene{M}
>   order           - integer, 1-indexed, sequential
>   chapter         - string e.g. 'Chapter 1'
>   scene_type      - one of: action, dialogue, description, battle, discovery
>   mood            - comma-separated string e.g. 'tense, melancholic'
>   characters      - array of character name strings present in scene
>   sound_events    - array of 1-3 short strings e.g. ['sword clash', 'wind']
>   music_prompt    - string, max 10 words, for music generation
>                     e.g. 'dark orchestral battle, brass, urgent drums'
>   narrator_tone   - string e.g. 'urgent', 'quiet and reflective'
>   estimated_words - integer, approximate word count of this scene
>   raw_text        - the full text of this scene verbatim
> Rules:
> - Split at natural breaks: location change, time skip, POV shift
> - Each scene: 200-800 words. Merge very short micro-scenes.
> - Return ONLY valid JSON array. No prose. No markdown. No backticks.
> - If unclear scene breaks, return single-element array.
> - music_prompt must describe instrumentation, not just mood.


# 11. API Routes


| Route | Description |
| --- | --- |
| POST /upload | Multipart file (PDF or .txt). Saves to audio_files/uploads/. Returns { file_id } |
| POST /jobs | Body: { file_id, book_title }. Creates job, starts pipeline. Returns { job_id } |
| GET /jobs/:id | Full job object: status, scene count, output_url, error_message |
| GET /jobs/:id/status | Lightweight: { status, progress_pct, current_stage } — for polling |
| GET /audio/:job_id | Streams the final MP3 from audio_files/output/ |


# 12. Disk Space Plan (256 GB SSD)

256 GB is enough but you need to be intentional. MusicGen downloads a model cache, and audio files accumulate.


| Item | Size |
| --- | --- |
| macOS + system | ~20 GB |
| Xcode CLI tools | ~2 GB |
| Homebrew + packages (ffmpeg etc.) | ~2 GB |
| Python 3.11 + venv | ~1 GB |
| audiocraft + torch dependencies | ~4-5 GB (pip cache + installed) |
| MusicGen small model cache | ~1.3 GB (downloads to ~/.cache/huggingface) |
| MusicGen medium model (DO NOT download) | ~3.3 GB — skip on 256GB |
| Docker images (redis + postgres arm64) | ~400 MB |
| Your project code | ~50 MB |
| Audio files (per full chapter processed) | ~50-200 MB per job |
| TOTAL for setup | ~30-35 GB |
| Free headroom | ~220 GB for audio output and other apps |


MusicGen caches to ~/.cache/huggingface/. If you ever need to free space: rm -rf ~/.cache/huggingface/ and it re-downloads on next run.


# 13. Build Order

Follow this sequence. Each phase validates the previous one. Do not skip ahead.


> Phase 1 — Foundation (Day 1-3)
> 1. brew install ffmpeg   # verify: ffmpeg -version
> 2. Set up Python 3.11 venv, install torch, verify MPS: python -c 'import torch; print(torch.backends.mps.is_available())'
> 3. docker compose up redis postgres -d
> 4. db/models.py + alembic init + alembic upgrade head
> 5. api/routes/jobs.py — basic CRUD
> 6. Smoke test: curl -X POST http://localhost:8000/jobs -d '{"book_title":"test"}' returns a job_id


> Phase 2 — Scene Parsing (Day 4-6)
> 1. Write prompts/scene_parser.txt
> 2. services/claude_client.py — call Anthropic API with the prompt
> 3. workers/scene_parser.py — Celery task wrapping the client
> 4. Test manually: paste a short chapter, verify JSON comes back clean
> 5. Iterate on the prompt until JSON is always valid and well-structured


> Phase 3 — Audio Generation (Day 7-14)
> 1. services/musicgen_client.py — load model with MPS, test generate() for one prompt
> 2. Time it: should be 45-90s on MPS for a 30s clip
> 3. services/elevenlabs_client.py — TTS one scene, save .wav, verify audio
> 4. workers/narration.py + workers/music_gen.py — wrap in Celery tasks
> 5. workers/pipeline.py — wire scene_parser -> parallel narration + music
> 6. Run full pipeline on a short chapter, check all tracks are saved


> Phase 4 — Mixing + Output (Day 15-18)
> 1. workers/mixer.py — mix one scene with pydub, listen to the output
> 2. Tune music volume (-12dB duck is a starting point — adjust by ear)
> 3. concat_scenes() — join all scenes into final MP3
> 4. api/routes/audio.py — serve the file, test download in browser
> 5. Full end-to-end: upload text -> poll -> download MP3 -> listen


> Phase 5 — Frontend (Day 19-28)
> 1. npx create-next-app@latest audiobook-ui
> 2. npm install wavesurfer.js
> 3. UploadForm.tsx + lib/api.ts
> 4. JobStatus.tsx — polling loop with progress bar
> 5. AudioPlayer.tsx — wavesurfer waveform + download
> 6. Wire everything, test full flow in browser


# 14. Known Hard Parts on M1 8GB


### Memory pressure during generation
When MusicGen is loaded (~1.5 GB) and a Celery task is running, your system may show yellow memory pressure in Activity Monitor. This is normal. If it goes red and you hear the fan spin up, reduce concurrency to 1 in celery_app.py.

### MPS not available after wake from sleep
Occasionally after sleep, torch.backends.mps.is_available() returns False. Fix: kill the Celery worker and restart it. This is a known PyTorch/macOS issue. Add a fallback in musicgen_client.py that catches the MPS error and retries on CPU.

### audiocraft install on arm64
audiocraft pulls in a lot of dependencies. If pip install audiocraft fails, try: pip install --no-build-isolation audiocraft. If it still fails, install from source: pip install git+https://github.com/facebookresearch/audiocraft.

### FFmpeg not found by pydub
pydub needs to find ffmpeg on PATH. If you get 'AudioSegment.converter not found': export PATH=/opt/homebrew/bin:$PATH in your shell profile. Homebrew installs to /opt/homebrew on Apple Silicon (not /usr/local).

### Scene parser JSON consistency
Claude will occasionally return malformed JSON, extra commentary, or miss required fields. Add retry logic in claude_client.py: if JSON parse fails, send the error back to Claude with 'Your response was invalid JSON. The error was: {error}. Return only the JSON array.'

### Music looping artifacts
When you loop a 30s MusicGen clip, the loop point is audible. Fix: generate slightly longer than needed (35s), then crossfade the loop point with a 2-second overlap. pydub's append() with crossfade parameter handles this.


# 15. External Dependencies


| Dependency | Used for | M1 note |
| --- | --- | --- |
| Anthropic Claude API | Scene parsing | API call — no local install |
| ElevenLabs API | TTS narration | API call — free tier: 10k chars/month |
| MusicGen (audiocraft) | Background music | Runs locally on MPS — use small model only |
| PyTorch | ML backend for MusicGen | arm64 native via pip — do NOT use conda |
| pydub | Audio mixing + looping | pip install pydub — needs ffmpeg on PATH |
| FFmpeg | Audio encoding + export | brew install ffmpeg — install in Homebrew |
| Redis | Celery job queue | Docker linux/arm64 image |
| PostgreSQL | Job + scene storage | Docker linux/arm64 image |
| wavesurfer.js | Frontend waveform player | npm install wavesurfer.js |
| Next.js | Frontend framework | npm — no M1-specific config needed |


# 16. Copyright Note


> Use public domain books for demos and testing
> Game of Thrones, Harry Potter, and other published books are copyrighted.
> They are great for local testing but cannot be used commercially.
> Best sources for building your content library:
>   - Project Gutenberg (gutenberg.org) — 70,000+ free public domain books
>     Sherlock Holmes, Dracula, Pride & Prejudice, Frankenstein, War and Peace
>   - Standard Ebooks (standardebooks.org) — clean formatted versions
>   - Indie / self-published authors — they will love this tool
>   - Allow users to upload their own writing
> For your MVP demo, use a Sherlock Holmes story from Gutenberg.
> It has clear scenes, strong mood variation, and it is completely free to use.


Immersive Audiobook Engine — MVP Build Document — Apple M1 8GB Edition

