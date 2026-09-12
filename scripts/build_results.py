"""Merges the separate eval run files into one canonical results.json that
Stream D's screens render from, plus per-case cassettes for the receipt
screen and replay mode.

Per CLAUDE.md rule 7/8: the UI never calls a model or Docker synchronously,
and every run must be replayable from a committed JSON file. This script is
the one place that reads the raw eval outputs and produces that committed
file — run it after any real eval batch, not as part of the live pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

RUNS_DIR = Path("runs")
OUT_PATH = Path("results.json")

# Which run files contribute, and which of their cases are the "final" record
# for a given instance_id (later files override earlier ones — the django
# retry after the f-string fix supersedes the original django rows).
SOURCE_FILES = [
    "real_pipeline_10.json",
    "django_retry.json",
    "real_pipeline_batch2.json",
    "cassette_refresh.json",  # last: same instances rerun with full cassette fields
]

BASELINES = {
    "gpt4_zero_shot": 0.036,
    "aider": 0.127,
    "swe_agent": 0.159,
    "swe_agent_plus": 0.185,
}


def classify(case: dict) -> str:
    if case["offline_reproduced"]:
        return "reproduced"
    if case["offline_fails_on_buggy"] and not case["offline_passes_on_fixed"]:
        return "false_positive_unrelated_failure"
    if not case["offline_fails_on_buggy"] and case["offline_passes_on_fixed"]:
        return "under_detected_no_signal"
    if not case["offline_fails_on_buggy"] and not case["offline_passes_on_fixed"]:
        # Passes on buggy, fails on fixed: the script's notion of "expected"
        # is backwards - it encoded the buggy output as correct. Distinct
        # from under-detection (which sees nothing either way).
        return "semantic_inversion"
    return "other"


def main():
    by_instance: dict[str, dict] = {}
    for name in SOURCE_FILES:
        path = RUNS_DIR / name
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        for case in data["cases"]:
            case["taxonomy"] = classify(case)
            case["source_run"] = name
            by_instance[case["instance_id"]] = case  # later files win

    cases = sorted(by_instance.values(), key=lambda c: c["instance_id"])
    n = len(cases)
    reproduced = sum(1 for c in cases if c["taxonomy"] == "reproduced")
    naive_reproduced = sum(1 for c in cases if c["offline_fails_on_buggy"])
    errors = sum(1 for c in cases if c["live_status"] == "error")

    taxonomy_counts: dict[str, int] = {}
    for c in cases:
        taxonomy_counts[c["taxonomy"]] = taxonomy_counts.get(c["taxonomy"], 0) + 1

    result = {
        "generated_from": SOURCE_FILES,
        "model": "qwen2.5-coder:7b (local Ollama)",
        "summary": {
            "n": n,
            "reproduced": reproduced,
            "reproduction_rate": reproduced / n if n else 0.0,
            "naive_exit_code_reproduced": naive_reproduced,
            "naive_exit_code_rate": naive_reproduced / n if n else 0.0,
            "script_errors": errors,
        },
        "baselines": BASELINES,
        "taxonomy_counts": taxonomy_counts,
        "cases": cases,
    }

    OUT_PATH.write_text(json.dumps(result, indent=2))
    print(f"wrote {OUT_PATH} — {n} cases, {reproduced} reproduced ({reproduced/n:.0%})")
    print(f"naive exit-code scoring would claim {naive_reproduced}/{n} ({naive_reproduced/n:.0%})")
    print(json.dumps(taxonomy_counts, indent=2))


if __name__ == "__main__":
    main()
