import shutil

import redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..dependencies import require_admin
from ..models import AuditLog, BuildJob, BuildStatus, User
from ..schemas import AuditOut

router = APIRouter(tags=["系统"])


@router.get("/health/live")
def live():
    return {"status": "ok"}


@router.get("/health/ready")
def ready(db: Session = Depends(get_db)):
    checks: dict[str, bool] = {}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False
    try:
        checks["redis"] = bool(redis.from_url(get_settings().redis_url).ping())
    except Exception:
        checks["redis"] = False
    settings = get_settings()
    settings.data_root.mkdir(parents=True, exist_ok=True)
    checks["disk"] = (
        shutil.disk_usage(settings.data_root).free >= settings.min_free_disk_gb * 1024**3
    )
    if not all(checks.values()):
        raise HTTPException(status_code=503, detail=checks)
    return {"status": "ready", "checks": checks}


@router.get("/dashboard")
def dashboard(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    builds = list(db.scalars(select(BuildJob).order_by(BuildJob.created_at.desc()).limit(50)))
    return {
        "queued": sum(b.status == BuildStatus.queued for b in builds),
        "running": sum(
            b.status
            in {
                BuildStatus.cloning,
                BuildStatus.installing,
                BuildStatus.building,
                BuildStatus.packaging,
            }
            for b in builds
        ),
        "succeeded": sum(b.status == BuildStatus.succeeded for b in builds),
        "failed": sum(b.status == BuildStatus.failed for b in builds),
    }


@router.get("/audit-logs", response_model=list[AuditOut])
def audit_logs(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(500)))
