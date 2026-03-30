from celery import Celery
from config import settings

app = Celery(
    'audiobook',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['workers.scene_parser', 'workers.narration',
             'workers.music_gen', 'workers.pipeline']
)

app.conf.update(
    # M1 8GB: 2 concurrent tasks max to avoid memory pressure
    worker_concurrency=2,
    # Use prefork (default) — better for CPU-bound tasks on M1
    worker_pool='prefork',
    # Prevent task pile-up — one at a time per worker
    worker_prefetch_multiplier=1,
    # Longer timeout for MusicGen on CPU fallback
    task_soft_time_limit=300,   # 5 min soft
    task_time_limit=600,         # 10 min hard
    # Results expire after 1 hour
    result_expires=3600,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
)
