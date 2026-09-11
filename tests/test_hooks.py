"""Proves BeforeToolCallEvent actually fires and actually blocks a call in
the pinned strands-agents version — not an assumption from a blog post.
Required first-hour check from EXECUTION.md.
"""

import pytest

from strands.hooks import BeforeToolCallEvent, HookRegistry

from understudy.policy.hooks import (
    BUDGET_EXHAUSTED_MESSAGE,
    GIT_BLOCKED_MESSAGE,
    UnderstudyPolicyHook,
)
from understudy.policy.ledger import Ledger, local_day


def _event(tool_name: str, tool_input) -> BeforeToolCallEvent:
    return BeforeToolCallEvent(
        agent=None,
        selected_tool=None,
        tool_use={"name": tool_name, "toolUseId": "t1", "input": tool_input},
        invocation_state={},
    )


@pytest.fixture()
def registry_and_hook(tmp_path):
    ledger = Ledger(tmp_path / "ledger.sqlite3", daily_cap=1)
    hook = UnderstudyPolicyHook(ledger, tz_name="UTC")
    registry = HookRegistry()
    registry.add_hook(hook)
    return registry, hook, ledger


def test_before_tool_call_event_fires_through_the_registry(registry_and_hook):
    registry, hook, ledger = registry_and_hook
    event = _event("read_file", {"path": "a.py"})
    result_event, interrupts = registry.invoke_callbacks(event)
    assert result_event.cancel_tool is False


def test_git_tool_name_is_blocked(registry_and_hook):
    registry, hook, ledger = registry_and_hook
    event = _event("run_git", {})
    result_event, _ = registry.invoke_callbacks(event)
    assert result_event.cancel_tool == GIT_BLOCKED_MESSAGE
    assert hook.blocked_git_attempts


def test_git_inside_shell_input_is_blocked(registry_and_hook):
    registry, hook, ledger = registry_and_hook
    event = _event("shell", {"command": "git log --all"})
    result_event, _ = registry.invoke_callbacks(event)
    assert result_event.cancel_tool == GIT_BLOCKED_MESSAGE


def test_non_git_shell_command_is_not_blocked(registry_and_hook):
    registry, hook, ledger = registry_and_hook
    event = _event("shell", {"command": "grep -r TODO ."})
    result_event, _ = registry.invoke_callbacks(event)
    assert result_event.cancel_tool is False


def test_escalation_within_budget_is_allowed(registry_and_hook):
    registry, hook, ledger = registry_and_hook
    event = _event("escalate_to_human", {"issue_key": "issue-1"})
    result_event, _ = registry.invoke_callbacks(event)
    assert result_event.cancel_tool is False
    day = local_day("UTC")
    assert ledger.counts(day).reserved == 1


def test_escalation_over_budget_is_blocked_and_fed_back_as_steering(registry_and_hook):
    registry, hook, ledger = registry_and_hook
    registry.invoke_callbacks(_event("escalate_to_human", {"issue_key": "issue-1"}))
    event2 = _event("escalate_to_human", {"issue_key": "issue-2"})
    result_event, _ = registry.invoke_callbacks(event2)
    assert result_event.cancel_tool == BUDGET_EXHAUSTED_MESSAGE


def test_duplicate_escalation_for_same_issue_does_not_spend_twice(registry_and_hook):
    registry, hook, ledger = registry_and_hook
    registry.invoke_callbacks(_event("escalate_to_human", {"issue_key": "issue-1"}))
    result_event, _ = registry.invoke_callbacks(
        _event("escalate_to_human", {"issue_key": "issue-1"})
    )
    # Same key, so it's idempotent — cap is 1 but this must still be allowed.
    assert result_event.cancel_tool is False


def test_underscored_git_tool_name_is_blocked(registry_and_hook):
    registry, hook, ledger = registry_and_hook
    event = _event("run_git", {})
    result_event, _ = registry.invoke_callbacks(event)
    assert result_event.cancel_tool == GIT_BLOCKED_MESSAGE


def test_words_containing_git_as_substring_are_not_false_positives(registry_and_hook):
    registry, hook, ledger = registry_and_hook
    event = _event("read_file", {"path": "digit_utils.py", "note": "legitimate change"})
    result_event, _ = registry.invoke_callbacks(event)
    assert result_event.cancel_tool is False
