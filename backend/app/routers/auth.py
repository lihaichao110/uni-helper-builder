from datetime import UTC, datetime
from typing import Literal, TypedDict

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..dependencies import get_current_user
from ..models import User
from ..schemas import LoginRequest, TokenResponse, UserOut
from ..security import create_access_token, create_refresh_token, decode_token, verify_password
from ..services import write_audit

router = APIRouter(prefix="/auth", tags=["认证"])


class _CookieAttrs(TypedDict):
    secure: bool
    samesite: Literal["lax", "strict"]


def _cookie_attrs() -> _CookieAttrs:
    """构造 refresh_token Cookie 属性；secure/samesite 按环境区分，保证开发与生产都能被浏览器保存并回传。

    - development：secure=False、samesite=lax，兼容本地 HTTP 与跨端口同站直连；
    - production：secure=True（可用 COOKIE_SECURE=false 覆盖以适配纯 HTTP 部署）、samesite=strict，
      前端与 /api 同源经 nginx 反代，strict 不影响回传。
    """
    settings = get_settings()
    production = settings.environment == "production"
    secure = production if settings.cookie_secure is None else settings.cookie_secure
    return {"secure": secure, "samesite": "strict" if production else "lax"}


def set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        "refresh_token",
        token,
        httponly=True,
        max_age=settings.refresh_token_days * 86400,
        path="/api/auth",
        **_cookie_attrs(),
    )


def clear_refresh_cookie(response: Response) -> None:
    """删除 refresh_token Cookie；属性需与下发时一致才能命中同一条 Cookie。"""
    response.delete_cookie("refresh_token", httponly=True, path="/api/auth", **_cookie_attrs())


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    user.last_login_at = datetime.now(UTC)
    write_audit(db, user, "auth.login", "user", user.id)
    db.commit()
    set_refresh_cookie(response, create_refresh_token(user.id))
    return TokenResponse(
        access_token=create_access_token(user.id), user=UserOut.model_validate(user)
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="缺少刷新令牌")
    try:
        user_id = decode_token(refresh_token, "refresh")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="刷新令牌无效") from exc
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不可用")
    set_refresh_cookie(response, create_refresh_token(user.id))
    return TokenResponse(
        access_token=create_access_token(user.id), user=UserOut.model_validate(user)
    )


@router.post("/logout", status_code=204)
def logout(
    response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    clear_refresh_cookie(response)
    write_audit(db, user, "auth.logout", "user", user.id)
    db.commit()


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
