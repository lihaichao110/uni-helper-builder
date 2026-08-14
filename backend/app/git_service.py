import os
import shlex
import stat
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .models import CredentialType, RepositoryCredential
from .security import decrypt_secret


class GitOperationError(RuntimeError):
    pass


@contextmanager
def git_environment(credential: RepositoryCredential | None, temp_root: Path):
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    with tempfile.TemporaryDirectory(dir=temp_root) as temp_dir:
        root = Path(temp_dir)
        if credential:
            secret = decrypt_secret(credential.encrypted_secret)
            if credential.type == CredentialType.ssh:
                key_path = root / "deploy_key"
                hosts_path = root / "known_hosts"
                key_path.write_text(secret, encoding="utf-8")
                hosts_path.write_text(credential.known_hosts or "", encoding="utf-8")
                key_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
                env["GIT_SSH_COMMAND"] = (
                    f"ssh -i {shlex.quote(str(key_path))} -o IdentitiesOnly=yes "
                    f"-o UserKnownHostsFile={shlex.quote(str(hosts_path))} -o StrictHostKeyChecking=yes"
                )
            else:
                askpass = root / "git-askpass.sh"
                username = credential.username or "oauth2"
                askpass.write_text(
                    '#!/bin/sh\ncase "$1" in *Username*) printf \'%s\' "$GIT_AUTH_USER";; *) printf \'%s\' "$GIT_AUTH_TOKEN";; esac\n',
                    encoding="utf-8",
                )
                askpass.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                env.update(
                    {
                        "GIT_ASKPASS": str(askpass),
                        "GIT_AUTH_USER": username,
                        "GIT_AUTH_TOKEN": secret,
                    }
                )
        yield env


def run_git(
    args: list[str], env: dict[str, str], cwd: Path | None = None, timeout: int = 120
) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode:
        message = (result.stderr or result.stdout or "Git 操作失败").strip()
        raise GitOperationError(message[-2000:])
    return result.stdout.strip()


def list_remote_refs(
    git_url: str, credential: RepositoryCredential | None, temp_root: Path
) -> list[dict]:
    with git_environment(credential, temp_root) as env:
        output = run_git(["ls-remote", "--heads", "--tags", git_url], env)
    refs: list[dict] = []
    for line in output.splitlines():
        if not line.strip() or "\t" not in line:
            continue
        sha, ref = line.split("\t", 1)
        if ref.endswith("^{}"):
            continue
        if ref.startswith("refs/heads/"):
            refs.append({"type": "branch", "name": ref.removeprefix("refs/heads/"), "sha": sha})
        elif ref.startswith("refs/tags/"):
            refs.append({"type": "tag", "name": ref.removeprefix("refs/tags/"), "sha": sha})
    return sorted(refs, key=lambda item: (item["type"], item["name"]))


def clone_ref(
    git_url: str,
    ref: str,
    destination: Path,
    credential: RepositoryCredential | None,
    temp_root: Path,
    log,
) -> str:
    destination.mkdir(parents=True, exist_ok=False)
    with git_environment(credential, temp_root) as env:
        run_git(["init", "--quiet"], env, destination)
        run_git(["remote", "add", "origin", git_url], env, destination)
        log(f"正在拉取 Ref: {ref}")
        run_git(["fetch", "--quiet", "--depth", "1", "origin", ref], env, destination, timeout=600)
        run_git(["checkout", "--quiet", "--detach", "FETCH_HEAD"], env, destination)
        sha = run_git(["rev-parse", "HEAD"], env, destination)
        run_git(["remote", "set-url", "origin", "disabled://credential-redacted"], env, destination)
        return sha
