"""The agent's only two ways to look at the repository: read a file, or
search for a pattern. Both are confined to the sanitized clean tree by
resolve_within (understudy/sandbox/sanitize.py) and capped so a pathological
regex or a huge file can't blow up context or runtime.

No general shell access is given to the agent for a reason: a shell is one
more way to reach git, environment variables, or the network. These two
tools are all the "give the agent read_file and grep" correction (C3 in the
plan) actually needs.
"""

from __future__ import annotations

import re
from pathlib import Path

from understudy.sandbox.sanitize import resolve_within

MAX_FILE_BYTES = 50_000
MAX_MATCHES = 200
MAX_SEARCH_FILES = 2_000


def read_file(root: Path, relative_path: str) -> str:
    """Read a file inside the sanitized tree, truncated if it's large."""
    path = resolve_within(root, relative_path)
    if not path.is_file():
        raise FileNotFoundError(relative_path)
    data = path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    if len(data) > MAX_FILE_BYTES:
        text = text[:MAX_FILE_BYTES] + f"\n...[truncated, file is {len(data)} bytes]..."
    return text


def search_source(root: Path, pattern: str, *, glob: str = "**/*.py") -> list[dict]:
    """Grep-like search over the sanitized tree. Returns at most MAX_MATCHES
    hits as {path, line_number, line} so results stay bounded regardless of
    repo size or how common the pattern is."""
    root = root.resolve()
    try:
        regex = re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"invalid search pattern: {exc}") from exc

    hits: list[dict] = []
    files_scanned = 0
    for path in root.glob(glob):
        if not path.is_file():
            continue
        files_scanned += 1
        if files_scanned > MAX_SEARCH_FILES:
            break
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if regex.search(line):
                hits.append(
                    {
                        "path": str(path.relative_to(root)),
                        "line_number": lineno,
                        "line": line.strip()[:500],
                    }
                )
                if len(hits) >= MAX_MATCHES:
                    return hits
    return hits
