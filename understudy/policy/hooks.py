"""The one hook that does two jobs: gates the interruption budget, and blocks
`git`. See CLAUDE.md rules 2, 3.

Verified against strands-agents==1.55.1: BeforeToolCallEvent.cancel_tool
accepts a string, which becomes the reason fed back to the agent as steering
("resolve autonomously or queue for the digest" / "git is not available") —
not a silent failure the model has to guess about.
"""

from __future__ import annotations

import re

from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry

from understudy.policy.ledger import Ledger, local_day

# Any tool invocation whose name or input plausibly shells out to git is
# blocked. This is deliberately broad — blocking too much costs nothing here
# (the agent has read_file/search_source instead), and SWE-bench images clone
# the full repo, so `git log --all`, `git show`, and reading packed refs
# directly can all reach the fix commit. See understudy/sandbox/sanitize.py
# for the complementary filesystem-level defense; this hook alone is not
# sufficient by itself, which is exactly why both exist.
# Non-letter boundary on both sides, so "run_git" and "git_log" match
# (underscore is not a letter) but "digit" and "legitimate" do not.
_GIT_PATTERN = re.compile(r"(?:^|[^a-zA-Z])git(?:[^a-zA-Z]|$)", re.IGNORECASE)

GIT_BLOCKED_MESSAGE = (
    "git is not available in this environment. Use read_file or search_source "
    "instead — repository history and any patch information are deliberately "
    "excluded from what you can see."
)

BUDGET_EXHAUSTED_MESSAGE = (
    "Today's interruption budget is spent. Resolve this yourself if you can, "
    "or leave your verdict for tomorrow's digest — do not keep retrying to "
    "reach a human right now."
)


def _looks_like_git(tool_name: str, tool_input: object) -> bool:
    if _GIT_PATTERN.search(tool_name):
        return True
    if isinstance(tool_input, dict):
        for value in tool_input.values():
            if isinstance(value, str) and _GIT_PATTERN.search(value):
                return True
    elif isinstance(tool_input, str):
        return bool(_GIT_PATTERN.search(tool_input))
    return False


class UnderstudyPolicyHook(HookProvider):
    """Registered on the agent. Fires before every tool call."""

    def __init__(
        self,
        ledger: Ledger,
        tz_name: str,
        escalation_tool_name: str = "escalate_to_human",
    ) -> None:
        self._ledger = ledger
        self._tz_name = tz_name
        self._escalation_tool_name = escalation_tool_name
        self.blocked_git_attempts: list[dict] = []  # logged, per CLAUDE.md rule 3

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)

    def _on_before_tool_call(self, event: BeforeToolCallEvent) -> None:
        tool_use = event.tool_use
        tool_name = tool_use.get("name", "")
        tool_input = tool_use.get("input")

        if _looks_like_git(tool_name, tool_input):
            self.blocked_git_attempts.append(
                {"tool_name": tool_name, "input": tool_input}
            )
            event.cancel_tool = GIT_BLOCKED_MESSAGE
            return

        if tool_name == self._escalation_tool_name:
            issue_key = None
            if isinstance(tool_input, dict):
                issue_key = tool_input.get("issue_key") or tool_input.get("key")
            issue_key = issue_key or tool_use.get("toolUseId", "unknown")

            day = local_day(self._tz_name)
            granted = self._ledger.try_reserve(day, str(issue_key), category="escalation")
            if not granted:
                event.cancel_tool = BUDGET_EXHAUSTED_MESSAGE
