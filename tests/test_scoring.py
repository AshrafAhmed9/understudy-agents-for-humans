"""Hostile-fixture proof: an import error, a timeout, an always-pass script and
an always-fail script must never be scored as a reproduction. This is the
test that must pass before any generated script is trusted.
"""

from understudy.scoring.differential import score_differential
from understudy.schemas import ExecResult


def ok(exit_code: int, timed_out: bool = False) -> ExecResult:
    return ExecResult(exit_code=exit_code, stdout="", stderr="", timed_out=timed_out)


def test_genuine_bug_scores_reproduced():
    # This is the one positive case: fails before the fix, passes after.
    buggy = ok(1)
    fixed = ok(0)
    result = score_differential(buggy, fixed)
    assert result.reproduced is True


def test_always_fail_script_is_not_a_reproduction():
    # A script that exits non-zero unconditionally fails on the fixed commit
    # too, so passes_on_fixed is False.
    buggy = ok(1)
    fixed = ok(1)
    result = score_differential(buggy, fixed)
    assert result.reproduced is False
    assert result.fails_on_buggy is True
    assert result.passes_on_fixed is False


def test_always_pass_script_is_not_a_reproduction():
    buggy = ok(0)
    fixed = ok(0)
    result = score_differential(buggy, fixed)
    assert result.reproduced is False
    assert result.fails_on_buggy is False


def test_import_error_on_both_commits_is_not_a_reproduction():
    # An ImportError is independent of the patch, so it breaks both runs.
    # exit code 1 on both, same as always-fail from the scorer's point of view.
    buggy = ok(1)
    fixed = ok(1)
    result = score_differential(buggy, fixed)
    assert result.reproduced is False


def test_timeout_on_buggy_run_invalidates_the_comparison():
    from understudy.schemas import ExecResult as ER

    buggy = ER(exit_code=137, stdout="", stderr="", timed_out=True)
    fixed = ok(0)
    result = score_differential(buggy, fixed)
    assert result.buggy_execution_valid is False
    assert result.reproduced is False


def test_timeout_on_fixed_run_invalidates_the_comparison():
    from understudy.schemas import ExecResult as ER

    buggy = ok(1)
    fixed = ER(exit_code=137, stdout="", stderr="", timed_out=True)
    result = score_differential(buggy, fixed)
    assert result.fixed_execution_valid is False
    assert result.reproduced is False


def test_infra_failure_invalidates_the_comparison():
    from understudy.sandbox.runner import INFRA_FAILURE_EXIT_CODE

    buggy = ok(INFRA_FAILURE_EXIT_CODE)
    fixed = ok(0)
    result = score_differential(buggy, fixed)
    assert result.buggy_execution_valid is False
    assert result.reproduced is False


def test_a_deliberately_broken_script_cannot_be_forced_to_reproduced():
    # A malformed script (missing fixture, wrong path) that happens to raise
    # a different exit code each run by chance must still not be conflated
    # with a real fail->pass differential unless the SAME behaviour actually
    # flips across the patch.
    buggy = ok(2)  # some unrelated crash
    fixed = ok(2)  # same unrelated crash, patch did nothing to it
    result = score_differential(buggy, fixed)
    assert result.reproduced is False
