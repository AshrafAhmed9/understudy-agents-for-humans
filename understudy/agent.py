"""Wires the three scoped tools and the policy hook into a Strands Agent.

Construction only — this module never invokes the model. One real finding
from doing this without credentials: `Agent(model=None)` in strands-agents
1.55.1 does NOT skip model resolution. Leaving model unset makes the SDK
default to BedrockModel and try to resolve AWS credentials immediately at
construction time, not deferred to the first call — so building an Agent at
all, even just to check that tools and hooks wire up correctly, reaches for
Bedrock on an account with no credentials configured. For structural tests
(tests/fake_model.py: NullModel) we pass a minimal Model subclass instead.
The moment Ashraf has AWS access, running this for real is a one-line
change: pass a real model in place of NullModel.
"""

from __future__ import annotations

from pathlib import Path

from strands import Agent, tool

from understudy.policy.hooks import UnderstudyPolicyHook
from understudy.policy.ledger import Ledger
from understudy.tools import repo_access

SYSTEM_PROMPT = """You are Understudy. You investigate one bug report at a time.

You may read source files and search the repository. You may not run git —
it is blocked. If the report does not give you enough to attempt a
reproduction, say so plainly rather than guessing.

When you have a candidate reproduction script, submit it for isolated
execution. You get at most three attempts: if a run fails to execute
correctly (not because the bug is present, but because the script itself is
broken), you will see the error and may revise once more.

Interrupting a human costs from a small daily budget. Most reports should
resolve without spending it. Escalate only for something that genuinely
needs a person's judgment."""


def build_tools(repo_root: Path):
    """Bind the sanitized-tree tools to a specific checkout, as Strands
    @tool-decorated callables the agent can actually invoke."""

    @tool
    def read_file(relative_path: str) -> str:
        """Read a file from the repository. Paths are relative to the repo root."""
        return repo_access.read_file(repo_root, relative_path)

    @tool
    def search_source(pattern: str, glob: str = "**/*.py") -> list[dict]:
        """Search the repository for a regex pattern, returning matching lines."""
        return repo_access.search_source(repo_root, pattern, glob=glob)

    @tool
    def escalate_to_human(issue_key: str, reason: str) -> str:
        """Ask a human maintainer to look at this. Subject to a daily budget —
        may be refused if the budget is already spent today."""
        # The actual gating happens in UnderstudyPolicyHook.on_before_tool_call,
        # which runs before this body and can cancel the call outright. If we
        # get here, the escalation was allowed.
        return f"escalation recorded for {issue_key}: {reason}"

    return [read_file, search_source, escalate_to_human]


def build_agent(repo_root: Path, ledger: Ledger, tz_name: str, model=None) -> Agent:
    """Construct the agent. Pass a real Model to actually run it, or a
    NullModel (tests/fake_model.py) to build and inspect the wiring without
    touching Bedrock at all. Leaving model=None reaches for AWS credentials
    immediately, even without ever calling the agent — see module docstring."""
    hook = UnderstudyPolicyHook(ledger, tz_name=tz_name)
    return Agent(
        model=model,
        tools=build_tools(repo_root),
        system_prompt=SYSTEM_PROMPT,
        hooks=[hook],
    )
