"""The results document schema and aggregation logic for an evaluation run.

Deliberately separate from anything that calls a model: `run_eval` takes a
`triage_fn` as a plain dependency, so this can be tested and used today with
a synthetic or hand-authored triage function, and later pointed at the real
Strands-backed one without changing anything here. See
COMPETITION.md's evidence contract: publish failures alongside wins, and
never let a live candidate result be confused with an offline-confirmed one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from understudy.data.swebench import epoch_image_ref
from understudy.receipts import atomic_write_json
from understudy.sandbox.runner import run_patched_script_in_container, run_script_in_container
from understudy.scoring.differential import score_differential
from understudy.schemas import Instance, ScoringCase, TriageResult

# Instance, never ScoringCase: triage_fn must not be able to reach
# case.gold_patch. See CLAUDE.md rule 2 - the agent must never see the gold
# patch, only the offline scorer below may.
TriageFn = Callable[[Instance], TriageResult]


@dataclass
class CaseResult:
    instance_id: str
    repo: str
    live_status: str
    live_confidence: float
    attempts: int
    offline_reproduced: bool | None  # None means no final_spec was produced
    offline_fails_on_buggy: bool | None
    offline_passes_on_fixed: bool | None
    error: str | None = None
    # Cassette fields (CLAUDE.md rule 8): enough to replay and to render
    # Screen B (the receipt) without calling a model or Docker again.
    issue_text: str | None = None
    final_script: str | None = None
    evidence: str | None = None
    buggy_stdout: str | None = None
    buggy_stderr: str | None = None
    fixed_stdout: str | None = None
    fixed_stderr: str | None = None

    def to_dict(self) -> dict:
        return {
            "instance_id": self.instance_id,
            "repo": self.repo,
            "live_status": self.live_status,
            "live_confidence": self.live_confidence,
            "attempts": self.attempts,
            "offline_reproduced": self.offline_reproduced,
            "offline_fails_on_buggy": self.offline_fails_on_buggy,
            "offline_passes_on_fixed": self.offline_passes_on_fixed,
            "error": self.error,
            "issue_text": self.issue_text,
            "final_script": self.final_script,
            "evidence": self.evidence,
            "buggy_stdout": self.buggy_stdout,
            "buggy_stderr": self.buggy_stderr,
            "fixed_stdout": self.fixed_stdout,
            "fixed_stderr": self.fixed_stderr,
        }


@dataclass
class EvalRun:
    label: str
    cases: list[CaseResult] = field(default_factory=list)

    def summary(self) -> dict:
        total = len(self.cases)
        reproduced = sum(1 for c in self.cases if c.offline_reproduced)
        errored = sum(1 for c in self.cases if c.error is not None)
        no_candidate = sum(1 for c in self.cases if c.offline_reproduced is None and c.error is None)
        return {
            "label": self.label,
            "total_cases": total,
            "reproduced": reproduced,
            "reproduction_rate": (reproduced / total) if total else 0.0,
            "no_candidate_produced": no_candidate,
            "errors": errored,
        }

    def to_dict(self) -> dict:
        return {
            "summary": self.summary(),
            "cases": [c.to_dict() for c in self.cases],
        }

    def write(self, path: Path) -> None:
        atomic_write_json(path, self.to_dict())


def run_eval(
    cases: list[ScoringCase],
    triage_fn: TriageFn,
    *,
    label: str,
    timeout_s: float = 90.0,
) -> EvalRun:
    """Run triage_fn on every case, then score whatever final script it
    produced against the real gold patch. A case that errors doesn't stop
    the run — it's recorded and the run continues, so one bad case can't
    hide every other result (that failure mode is exactly why the eval
    engineer stream exists as a separate concern from the reasoning loop)."""
    run = EvalRun(label=label)

    for case in cases:
        try:
            result = triage_fn(case.instance)
        except Exception as exc:  # noqa: BLE001 - record it, keep going
            run.cases.append(
                CaseResult(
                    instance_id=case.instance.instance_id,
                    repo=case.instance.repo,
                    live_status="error",
                    live_confidence=0.0,
                    attempts=0,
                    offline_reproduced=None,
                    offline_fails_on_buggy=None,
                    offline_passes_on_fixed=None,
                    error=f"triage_fn raised: {exc}",
                )
            )
            continue

        offline_reproduced = None
        offline_fails = None
        offline_passes = None
        error = None
        buggy_stdout = buggy_stderr = fixed_stdout = fixed_stderr = None

        if result.final_spec is not None:
            try:
                image = epoch_image_ref(case.instance.instance_id)
                script_path = Path(f"/tmp/eval-{case.instance.instance_id}.py")
                script_path.write_text(result.final_spec.script)

                buggy = run_script_in_container(image, script_path, timeout_s=timeout_s)
                fixed = run_patched_script_in_container(
                    image, script_path, case.gold_patch, timeout_s=timeout_s
                )
                score = score_differential(buggy, fixed)
                offline_reproduced = score.reproduced
                offline_fails = score.fails_on_buggy
                offline_passes = score.passes_on_fixed
                buggy_stdout, buggy_stderr = buggy.stdout, buggy.stderr
                fixed_stdout, fixed_stderr = fixed.stdout, fixed.stderr
            except Exception as exc:  # noqa: BLE001
                error = f"offline scoring raised: {exc}"

        run.cases.append(
            CaseResult(
                instance_id=case.instance.instance_id,
                repo=case.instance.repo,
                live_status=result.verdict.status,
                live_confidence=result.verdict.confidence,
                attempts=result.verdict.attempts,
                offline_reproduced=offline_reproduced,
                offline_fails_on_buggy=offline_fails,
                offline_passes_on_fixed=offline_passes,
                error=error,
                issue_text=case.instance.issue_text,
                final_script=result.final_spec.script if result.final_spec else None,
                evidence=result.verdict.evidence,
                buggy_stdout=buggy_stdout,
                buggy_stderr=buggy_stderr,
                fixed_stdout=fixed_stdout,
                fixed_stderr=fixed_stderr,
            )
        )

    return run
