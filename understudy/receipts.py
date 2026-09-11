"""Atomic JSON writes for runs/<id>.json.

CLAUDE.md rule 7: every screen renders from a JSON file, never a live call.
That only works if readers never see a half-written file. Write to a temp
file in the same directory, then atomically rename over the target — on a
POSIX filesystem `os.replace` is atomic, so a concurrent reader either sees
the old complete file or the new complete file, never a partial one.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_json(path: Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def read_json(path: Path) -> Any:
    with open(path) as f:
        return json.load(f)
