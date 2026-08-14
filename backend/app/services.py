import json
import re
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import AuditLog, User

SCP_GIT_RE = re.compile(r"^[\w.-]+@[\w.-]+:[\w./-]+$")


def validate_git_url(value: str) -> str:
    if SCP_GIT_RE.fullmatch(value):
        return value
    parsed = urlparse(value)
    if parsed.scheme not in {"https", "ssh"} or not parsed.hostname:
        raise HTTPException(status_code=422, detail="Git 地址仅支持 HTTPS 或 SSH")
    if parsed.username and parsed.password:
        raise HTTPException(status_code=422, detail="禁止在 Git URL 中保存密码或 Token")
    return value


def write_audit(
    db: Session,
    user: User | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    detail: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=json.dumps(detail, ensure_ascii=False) if detail else None,
        )
    )
