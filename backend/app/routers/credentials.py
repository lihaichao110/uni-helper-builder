from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_admin
from ..models import Project, RepositoryCredential, User
from ..schemas import CredentialCreate, CredentialOut, CredentialUpdate
from ..security import encrypt_secret
from ..services import write_audit

router = APIRouter(prefix="/credentials", tags=["仓库凭据"])


@router.get("", response_model=list[CredentialOut])
def list_credentials(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return list(db.scalars(select(RepositoryCredential).order_by(RepositoryCredential.name)))


@router.post("", response_model=CredentialOut, status_code=201)
def create_credential(
    payload: CredentialCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    if db.scalar(select(RepositoryCredential.id).where(RepositoryCredential.name == payload.name)):
        raise HTTPException(status_code=409, detail="凭据名称已存在")
    if payload.type.value == "ssh" and not payload.known_hosts:
        raise HTTPException(status_code=422, detail="SSH 凭据必须提供 known_hosts 主机指纹")
    credential = RepositoryCredential(
        name=payload.name,
        type=payload.type,
        username=payload.username,
        encrypted_secret=encrypt_secret(payload.secret),
        known_hosts=payload.known_hosts,
    )
    db.add(credential)
    db.flush()
    write_audit(
        db, admin, "credential.create", "credential", credential.id, {"name": credential.name}
    )
    db.commit()
    db.refresh(credential)
    return credential


@router.patch("/{credential_id}", response_model=CredentialOut)
def update_credential(
    credential_id: str,
    payload: CredentialUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    credential = db.get(RepositoryCredential, credential_id)
    if not credential:
        raise HTTPException(status_code=404, detail="凭据不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(
            credential,
            "encrypted_secret" if key == "secret" else key,
            encrypt_secret(value) if key == "secret" else value,
        )
    if credential.type.value == "ssh" and not credential.known_hosts:
        raise HTTPException(status_code=422, detail="SSH 凭据必须保留 known_hosts 主机指纹")
    write_audit(db, admin, "credential.update", "credential", credential.id)
    db.commit()
    db.refresh(credential)
    return credential


@router.delete("/{credential_id}", status_code=204)
def delete_credential(
    credential_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    credential = db.get(RepositoryCredential, credential_id)
    if not credential:
        raise HTTPException(status_code=404, detail="凭据不存在")
    if db.scalar(select(Project.id).where(Project.credential_id == credential_id)):
        raise HTTPException(status_code=409, detail="凭据仍被项目使用")
    write_audit(
        db, admin, "credential.delete", "credential", credential.id, {"name": credential.name}
    )
    db.delete(credential)
    db.commit()
