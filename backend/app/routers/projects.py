from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..dependencies import get_current_user, require_admin
from ..git_service import GitOperationError, list_remote_refs
from ..models import Project, RepositoryCredential, User
from ..schemas import ProjectCreate, ProjectOut, ProjectUpdate
from ..services import validate_git_url, write_audit

router = APIRouter(prefix="/projects", tags=["项目"])


def get_project_or_404(db: Session, project_id: str) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(Project).order_by(Project.created_at.desc())))


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    validate_git_url(payload.git_url)
    if db.scalar(select(Project.id).where(Project.name == payload.name)):
        raise HTTPException(status_code=409, detail="项目名称已存在")
    if payload.credential_id and not db.get(RepositoryCredential, payload.credential_id):
        raise HTTPException(status_code=422, detail="仓库凭据不存在")
    project = Project(**payload.model_dump())
    db.add(project)
    db.flush()
    write_audit(db, admin, "project.create", "project", project.id, {"name": project.name})
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return get_project_or_404(db, project_id)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    project = get_project_or_404(db, project_id)
    data = payload.model_dump(exclude_unset=True)
    if "git_url" in data:
        validate_git_url(data["git_url"])
    if data.get("credential_id") and not db.get(RepositoryCredential, data["credential_id"]):
        raise HTTPException(status_code=422, detail="仓库凭据不存在")
    for key, value in data.items():
        setattr(project, key, value)
    write_audit(db, admin, "project.update", "project", project.id)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    project = get_project_or_404(db, project_id)
    project.is_active = False
    write_audit(db, admin, "project.disable", "project", project.id)
    db.commit()


@router.get("/{project_id}/refs")
def project_refs(
    project_id: str, _: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    project = get_project_or_404(db, project_id)
    settings = get_settings()
    settings.credential_temp_root.mkdir(parents=True, exist_ok=True)
    try:
        return list_remote_refs(project.git_url, project.credential, settings.credential_temp_root)
    except GitOperationError as exc:
        raise HTTPException(status_code=422, detail=f"仓库连接失败：{exc}") from exc


@router.post("/{project_id}/test-repository")
def test_repository(
    project_id: str, _: User = Depends(require_admin), db: Session = Depends(get_db)
):
    refs = project_refs(project_id, _, db)
    return {"ok": True, "ref_count": len(refs)}
