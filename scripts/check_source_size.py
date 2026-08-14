"""检查手写 Python 与 TypeScript 源码是否超过企业级文件规模上限。"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

LIMITS = {".py": 500, ".ts": 300, ".tsx": 300}
EXCLUDED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "alembic",
    "build",
    "dist",
    "node_modules",
    "outputs",
    "venv",
    "work",
}


@dataclass(frozen=True)
class Violation:
    """描述一个超过文件规模上限的源码文件。"""

    path: Path
    line_count: int
    limit: int


def is_excluded(path: Path) -> bool:
    """判断路径是否属于生成内容、依赖、迁移或运行产物。"""

    return any(part in EXCLUDED_DIRECTORIES for part in path.parts) or path.name.endswith(".d.ts")


def iter_source_files(paths: Iterable[Path]) -> Iterable[Path]:
    """遍历输入路径中的受控源码文件。"""

    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix in LIMITS and not is_excluded(path):
                yield path
            continue
        for current_root, directory_names, file_names in os.walk(path):
            directory_names[:] = [
                name for name in directory_names if name not in EXCLUDED_DIRECTORIES
            ]
            current_path = Path(current_root)
            for file_name in file_names:
                candidate = current_path / file_name
                if candidate.suffix in LIMITS and not is_excluded(candidate):
                    yield candidate


def count_lines(path: Path) -> int:
    """按物理行统计 UTF-8 源码行数。"""

    with path.open(encoding="utf-8") as source:
        return sum(1 for _ in source)


def find_violations(paths: Iterable[Path]) -> list[Violation]:
    """返回所有超过对应语言硬限制的文件。"""

    violations: list[Violation] = []
    for path in sorted(set(iter_source_files(paths))):
        line_count = count_lines(path)
        limit = LIMITS[path.suffix]
        if line_count > limit:
            violations.append(Violation(path=path, line_count=line_count, limit=limit))
    return violations


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。"""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="待检查文件或目录；默认检查整个仓库并应用排除规则",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """执行检查并返回适合 CI 使用的退出码。"""

    args = parse_args(argv)
    repository_root = Path(__file__).resolve().parent.parent
    paths = args.paths or [repository_root]
    violations = find_violations(paths)
    if not violations:
        print("源码文件行数检查通过。")
        return 0

    print("以下源码文件超过企业级规模硬限制：", file=sys.stderr)
    for violation in violations:
        try:
            display_path = violation.path.resolve().relative_to(repository_root)
        except ValueError:
            display_path = violation.path
        print(
            f"- {display_path}: {violation.line_count} 行，限制 {violation.limit} 行",
            file=sys.stderr,
        )
    print("请按独立职责拆分模块，禁止通过压缩格式规避限制。", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
