from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_admin
from ..models import User
from ..schemas import UserCreate, UserOut, UserUpdate
from ..security import hash_password
from ..services import write_audit

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("", response_model=list[UserOut])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return list(db.scalars(select(User).order_by(User.created_at.desc())))


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=409, detail="用户名已存在")
    user = User(
        username=payload.username, password_hash=hash_password(payload.password), role=payload.role
    )
    db.add(user)
    db.flush()
    write_audit(
        db,
        admin,
        "user.create",
        "user",
        user.id,
        {"username": user.username, "role": user.role.value},
    )
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    data = payload.model_dump(exclude_unset=True)
    if user.id == admin.id and data.get("is_active") is False:
        raise HTTPException(status_code=409, detail="不能停用当前登录管理员")
    if "password" in data:
        user.password_hash = hash_password(data.pop("password"))
    for key, value in data.items():
        setattr(user, key, value)
    write_audit(
        db, admin, "user.update", "user", user.id, {"fields": list(payload.model_fields_set)}
    )
    db.commit()
    db.refresh(user)
    return user
