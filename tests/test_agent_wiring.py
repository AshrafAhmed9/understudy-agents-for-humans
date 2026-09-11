"""Proves the agent assembles correctly WITHOUT a model — tools register,
the policy hook attaches, and its git-blocking / budget-gating behaviour
fires through the real Agent's real hook registry. No Bedrock call, no
AWS credentials, no cost.
"""

import pytest

from understudy.agent import build_agent, build_tools
from tests.fake_model import NullModel
from understudy.policy.ledger import Ledger, local_day


@pytest.fixture()
def repo(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "a.py").write_text("def f():\n    return 1\n")
    return tmp_path


@pytest.fixture()
def ledger(tmp_path):
    return Ledger(tmp_path / "ledger.sqlite3", daily_cap=1)


def test_agent_constructs_without_a_model(repo, ledger):
    agent = build_agent(repo, ledger, tz_name="UTC", model=NullModel())
    assert agent is not None


def test_all_three_tools_are_registered(repo, ledger):
    agent = build_agent(repo, ledger, tz_name="UTC", model=NullModel())
    names = {t.tool_name for t in agent.tool_registry.registry.values()}
    assert {"read_file", "search_source", "escalate_to_human"} <= names


def test_read_file_tool_is_confined_to_the_repo(repo, ledger):
    tools = build_tools(repo)
    read_file = next(t for t in tools if t.tool_name == "read_file")
    result = read_file(relative_path="pkg/a.py")
    assert "return 1" in result


def test_read_file_tool_blocks_traversal(repo, ledger):
    tools = build_tools(repo)
    read_file = next(t for t in tools if t.tool_name == "read_file")
    with pytest.raises(PermissionError):
        read_file(relative_path="../../etc/passwd")


def test_git_is_blocked_through_the_real_agent_hook_registry(repo, ledger):
    from strands.hooks import BeforeToolCallEvent

    agent = build_agent(repo, ledger, tz_name="UTC", model=NullModel())
    event = BeforeToolCallEvent(
        agent=agent,
        selected_tool=None,
        tool_use={"name": "git_log", "toolUseId": "t1", "input": {}},
        invocation_state={},
    )
    result, _ = agent.hooks.invoke_callbacks(event)
    assert result.cancel_tool is not False


def test_escalation_budget_is_enforced_through_the_real_agent_hook_registry(repo, ledger):
    from strands.hooks import BeforeToolCallEvent

    agent = build_agent(repo, ledger, tz_name="UTC", model=NullModel())  # daily_cap=1 from fixture

    def escalate_event(key):
        return BeforeToolCallEvent(
            agent=agent,
            selected_tool=None,
            tool_use={"name": "escalate_to_human", "toolUseId": key, "input": {"issue_key": key}},
            invocation_state={},
        )

    first, _ = agent.hooks.invoke_callbacks(escalate_event("issue-1"))
    assert first.cancel_tool is False

    second, _ = agent.hooks.invoke_callbacks(escalate_event("issue-2"))
    assert second.cancel_tool is not False  # budget of 1 already spent
