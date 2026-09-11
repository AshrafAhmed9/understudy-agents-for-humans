"""Proves the harness plumbing is correct, independent of any model:
- a synthetic triage_fn that always declares "insufficient_info" produces
  a run with no offline scoring attempted (no final_spec => no sandbox call)
- a synthetic triage_fn that raises doesn't stop the whole run
- results are written atomically and round-trip through JSON
- one REAL end-to-end case against the actual pulled SWE-bench image,
  reusing the same hand-authored script from scripts/verify_kill_gate.py,
  proving the harness's sandbox/scoring wiring (not just its bookkeeping)
"""

import json
import subprocess

import pytest

from understudy.data.swebench import load_cases
from understudy.eval.results import run_eval
from understudy.schemas import ReproSpec, ScoringCase, TriageResult, Verdict


def _insufficient_info(case: ScoringCase) -> TriageResult:
    return TriageResult(
        verdict=Verdict(status="insufficient_info", confidence=0.0, evidence="not enough context", attempts=0),
        final_spec=None,
    )


def _always_raises(case: ScoringCase) -> TriageResult:
    raise RuntimeError("simulated triage failure")


def test_no_final_spec_means_no_offline_scoring_attempted():
    cases = load_cases()[:3]
    run = run_eval(cases, _insufficient_info, label="synthetic-insufficient-info")
    assert len(run.cases) == 3
    for c in run.cases:
        assert c.offline_reproduced is None
        assert c.error is None
    assert run.summary()["no_candidate_produced"] == 3
    assert run.summary()["reproduced"] == 0


def test_one_failing_case_does_not_stop_the_run():
    cases = load_cases()[:3]
    run = run_eval(cases, _always_raises, label="synthetic-error")
    assert len(run.cases) == 3
    assert all(c.error is not None for c in run.cases)
    assert run.summary()["errors"] == 3


def test_results_write_and_round_trip(tmp_path):
    cases = load_cases()[:2]
    run = run_eval(cases, _insufficient_info, label="roundtrip")
    path = tmp_path / "results.json"
    run.write(path)
    loaded = json.loads(path.read_text())
    assert loaded["summary"]["total_cases"] == 2
    assert len(loaded["cases"]) == 2


REAL_IMAGE = "ghcr.io/epoch-research/swe-bench.eval.x86_64.astropy__astropy-12907"

REAL_REPRO_SCRIPT = '''
import sys
import numpy as np
from astropy.modeling import models as m
from astropy.modeling.separable import separability_matrix

cm = m.Linear1D(10) & m.Linear1D(5)
result = separability_matrix(m.Pix2Sky_TAN() & cm)
expected = np.array([[True, False], [False, True]])
sys.exit(0 if np.array_equal(result[2:, 2:], expected) else 1)
'''


def _real_image_present() -> bool:
    try:
        return subprocess.run(
            ["docker", "image", "inspect", REAL_IMAGE], capture_output=True, timeout=10
        ).returncode == 0
    except Exception:
        return False


@pytest.mark.skipif(not _real_image_present(), reason="real SWE-bench image not pulled locally")
def test_harness_end_to_end_against_a_real_image():
    def hand_authored_triage(case: ScoringCase) -> TriageResult:
        return TriageResult(
            verdict=Verdict(status="candidate_reproduction", confidence=0.9, evidence="hand-authored", attempts=1),
            final_spec=ReproSpec(script=REAL_REPRO_SCRIPT, attempt=1),
        )

    cases = [c for c in load_cases() if c.instance.instance_id == "astropy__astropy-12907"]
    run = run_eval(cases, hand_authored_triage, label="real-end-to-end")
    assert run.summary()["reproduced"] == 1
    assert run.cases[0].error is None
