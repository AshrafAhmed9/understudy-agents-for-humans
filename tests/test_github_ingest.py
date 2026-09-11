"""Integration test against the real, live, public GitHub API. Skipped if
the network isn't reachable or the API is rate-limited (no auth => 60/hr,
shared across whatever else is hitting it from this machine)."""

import pytest

from understudy.ingest.github import fetch_recent_issues


def _api_reachable() -> bool:
    try:
        fetch_recent_issues("python", "cpython", state="all", limit=1)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _api_reachable(), reason="GitHub API unreachable or rate-limited")


def test_fetches_real_issues_not_pull_requests():
    issues = fetch_recent_issues("python", "cpython", state="all", limit=5)
    assert len(issues) == 5
    for issue in issues:
        assert issue.repo == "python/cpython"
        assert issue.number > 0
        assert issue.title
        assert issue.url.startswith("https://github.com/python/cpython/issues/")
        assert issue.captured_at


def test_respects_the_limit():
    issues = fetch_recent_issues("python", "cpython", state="all", limit=3)
    assert len(issues) <= 3
