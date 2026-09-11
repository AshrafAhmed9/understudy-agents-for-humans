"""The gold-patch differential — the only valid way to score a reproduction.

See CLAUDE.md rule 2. A script that merely exits non-zero on the buggy commit
proves nothing by itself: an ImportError, a wrong path, or a missing fixture
also exits non-zero, and roughly half of model-generated reproduction scripts
are malformed rather than bug-revealing. A broken script fails BOTH before and
after the fix, because the thing breaking it (the import, the path) is
unrelated to the patch. Only a script that captures the specific reported
behaviour will fail on the buggy commit and pass once the gold patch is
applied — that is the only signal this module trusts.

The offline scorer is the only code in the project allowed to see a gold
patch. It runs after the agent's verdict is already persisted (TriageResult),
using only the final candidate script. Nothing here feeds back into the agent.
"""

from __future__ import annotations

from understudy.sandbox.runner import INFRA_FAILURE_EXIT_CODE
from understudy.schemas import ExecResult, Score


def _valid(result: ExecResult) -> bool:
    """An execution is a valid data point only if it actually ran to
    completion inside the container. A timeout or an infra failure (image
    missing, daemon error) tells us nothing about whether the bug is real —
    it must never be read as "fails on buggy"."""
    return not result.timed_out and result.exit_code != INFRA_FAILURE_EXIT_CODE


def score_differential(buggy_run: ExecResult, fixed_run: ExecResult) -> Score:
    """Score one candidate script against its two executions.

    buggy_run: the script executed against the repo at base_commit.
    fixed_run: the same, unmodified, script executed against base_commit with
               the gold patch applied.
    """
    buggy_valid = _valid(buggy_run)
    fixed_valid = _valid(fixed_run)

    return Score(
        fails_on_buggy=buggy_valid and buggy_run.exit_code != 0,
        passes_on_fixed=fixed_valid and fixed_run.exit_code == 0,
        buggy_execution_valid=buggy_valid,
        fixed_execution_valid=fixed_valid,
    )
