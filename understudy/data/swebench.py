"""Loads real SWE-bench Verified instances.

The agent-facing Instance never carries the gold patch — that split exists
at the type level in schemas.py (Instance has no patch field at all), and
this loader is the only place that reads the cached file and produces both
the patch-free Instance and the offline-only ScoringCase from the same row.

Source data is public and fetched without any credentials from the
Hugging Face datasets-server API (princeton-nlp/SWE-bench_Verified), cached
to data/swebench_verified_sample.json so nothing re-fetches on every run.
"""

from __future__ import annotations

import json
from pathlib import Path

from understudy.schemas import Instance, ScoringCase

DEFAULT_CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "swebench_verified_sample.json"


def load_cases(path: Path = DEFAULT_CACHE_PATH) -> list[ScoringCase]:
    """Read the cached sample and return one ScoringCase per row.

    Call .instance on a ScoringCase to get the patch-free view an agent or
    its tools are allowed to see; never pass the ScoringCase itself, or its
    gold_patch, anywhere near the agent.
    """
    raw = json.loads(Path(path).read_text())
    cases = []
    for row in raw:
        instance = Instance(
            instance_id=row["instance_id"],
            repo=row["repo"],
            issue_text=row["issue_text"],
            base_commit=row["base_commit"],
        )
        cases.append(ScoringCase(instance=instance, gold_patch=row["gold_patch"]))
    return cases


def epoch_image_ref(instance_id: str) -> str:
    """The Epoch AI rebuild's naming scheme for an x86_64 evaluation image.

    Double underscores in instance_id (e.g. 'astropy__astropy-12907') are
    kept as-is here; Docker Hub's own official images had to replace them
    with '_1776_' because Docker Hub repo names reject '__', but ghcr.io
    doesn't have that restriction — verified by checking a real manifest,
    not assumed from the writeup.
    """
    return f"ghcr.io/epoch-research/swe-bench.eval.x86_64.{instance_id}"
