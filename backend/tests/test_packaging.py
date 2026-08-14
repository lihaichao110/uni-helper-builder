import zipfile

from app.models import BuildJob, InstallStrategy, Project
from app.tasks import package_wgt


def test_package_wgt_excludes_existing_wgt(tmp_path, monkeypatch):
    source = tmp_path / "source"
    dist = source / "wgt-dist"
    dist.mkdir(parents=True)
    (dist / "manifest.json").write_text("{}", encoding="utf-8")
    (dist / "old.wgt").write_text("old", encoding="utf-8")
    project = Project(id="project-1", name="demo app", git_url="https://example.com/repo.git")
    build = BuildJob(
        id="build-1",
        project_id=project.id,
        requested_by_id="user-1",
        requested_ref="main",
        commit_sha="abcdef123456",
        vue_version="3",
        install_strategy=InstallStrategy.none,
    )
    monkeypatch.setattr(
        "app.tasks.get_settings", lambda: type("S", (), {"artifact_root": tmp_path / "artifacts"})()
    )
    artifact = package_wgt(project, build, source, lambda _: None)
    with zipfile.ZipFile(artifact.storage_path) as archive:
        assert archive.namelist() == ["manifest.json"]
    assert artifact.sha256 and artifact.size_bytes > 0
