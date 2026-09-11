"""Strip anything that would let the agent or its generated script peek at the
answer before scoring happens.

Blocking the `git` executable in the tool hook is not enough on its own —
SWE-bench images clone the full upstream repo and reset to base_commit, so the
fix commit is still reachable by reading .git objects directly, without ever
invoking git. This module produces a clean copy of the checkout with all of
that removed, and is the tree the agent and its generated scripts actually see.
"""

from __future__ import annotations

import shutil
from pathlib import Path

# Anything under these names, anywhere in the tree, is removed. Covers the
# ordinary .git directory, git worktrees/submodule gitfiles, packed refs and
# alternate object stores reachable without a git binary.
FORBIDDEN_NAMES = {".git", ".gitmodules"}

# Specific file/dir patterns known to carry benchmark answer material if a
# harness happened to leave them in the checkout.
FORBIDDEN_GLOBS = (
    "**/.git",
    "**/*.patch",
    "**/gold_patch*",
    "**/eval.sh",
    "**/run_tests.sh",
)


def sanitize_repo(src: Path, dst: Path) -> Path:
    """Copy src to dst with forbidden paths excluded, then verify none remain."""
    src = src.resolve()
    dst = dst.resolve()
    if dst.exists():
        shutil.rmtree(dst)

    def _ignore(dirpath: str, names: list[str]) -> set[str]:
        return {n for n in names if n in FORBIDDEN_NAMES}

    shutil.copytree(src, dst, ignore=_ignore, symlinks=False)

    for pattern in FORBIDDEN_GLOBS:
        for path in dst.glob(pattern):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            elif path.exists():
                path.unlink()

    remaining = [p for p in dst.rglob(".git")]
    if remaining:
        raise RuntimeError(f"sanitize_repo left forbidden paths: {remaining}")

    return dst


def resolve_within(root: Path, relative: str) -> Path:
    """Resolve a path the agent asked to read/search, refusing to leave root.

    Used by the read_file / search_source tools. Rejects symlink escapes and
    ../ traversal by comparing resolved absolute paths.
    """
    root = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise PermissionError(f"path escapes sandboxed root: {relative}")
    return candidate
