"""Proves the sanitizer actually removes what would let a script find the
fix without ever calling git — CLAUDE.md rule 3 depends on this, not just on
blocking the git executable.
"""

import pytest

from understudy.sandbox.sanitize import resolve_within, sanitize_repo


@pytest.fixture()
def dirty_repo(tmp_path):
    src = tmp_path / "src"
    (src / ".git" / "objects").mkdir(parents=True)
    (src / ".git" / "objects" / "somehash").write_text("pretend git object")
    (src / ".git" / "packed-refs").write_text("pretend packed refs")
    (src / "pkg").mkdir()
    (src / "pkg" / "module.py").write_text("def f():\n    return 1\n")
    (src / "gold_patch.diff").write_text("--- the answer ---")
    (src / "eval.sh").write_text("#!/bin/bash\necho run the hidden tests")
    return src


def test_git_directory_is_removed(dirty_repo, tmp_path):
    dst = sanitize_repo(dirty_repo, tmp_path / "clean")
    assert not (dst / ".git").exists()
    assert not any(dst.rglob(".git"))


def test_answer_bearing_files_are_removed(dirty_repo, tmp_path):
    dst = sanitize_repo(dirty_repo, tmp_path / "clean")
    assert not (dst / "gold_patch.diff").exists()
    assert not (dst / "eval.sh").exists()


def test_ordinary_source_survives(dirty_repo, tmp_path):
    dst = sanitize_repo(dirty_repo, tmp_path / "clean")
    assert (dst / "pkg" / "module.py").read_text() == "def f():\n    return 1\n"


def test_resolve_within_blocks_traversal(tmp_path):
    root = tmp_path / "clean"
    root.mkdir()
    (root / "inside.py").write_text("ok")

    resolved = resolve_within(root, "inside.py")
    assert resolved == (root / "inside.py").resolve()

    with pytest.raises(PermissionError):
        resolve_within(root, "../outside.py")


def test_resolve_within_blocks_symlink_escape(tmp_path):
    root = tmp_path / "clean"
    root.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("gold patch material")
    (root / "escape.py").symlink_to(outside)

    with pytest.raises(PermissionError):
        resolve_within(root, "escape.py")
