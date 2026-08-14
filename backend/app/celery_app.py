from celery import Celery
from celery.schedules import crontab

from .config import get_settings

settings = get_settings()
celery_app = Celery("uni_builder", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    beat_schedule={
        "cleanup-old-builds": {"task": "app.tasks.cleanup_old_builds", "schedule": crontab(hour=3)},
        "recover-orphaned-builds": {"task": "app.tasks.recover_orphaned_builds", "schedule": 300.0},
    },
)
celery_app.autodiscover_tasks(["app"])
