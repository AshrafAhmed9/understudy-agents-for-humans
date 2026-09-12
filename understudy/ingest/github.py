"""Read-only ingestion of real public GitHub issues.

Unauthenticated (60 requests/hour, fine for a demo-sized poll) — reading a
public repo's issues needs no credentials. Posting a comment does, and that
path is intentionally not built here: it needs an explicit destination
authorization (a token, a repo the operator controls) before it exists.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

API_ROOT = "https://api.github.com"
USER_AGENT = "understudy-hackathon-project (read-only ingestion)"


@dataclass(frozen=True)
class RealIssue:
    """A real, unmodified public issue, captured with provenance.

    Evidence contract: preserve the pre-resolution text, the source URL,
    and the capture time, so nothing here can later be confused with a
    seeded or fabricated case.
    """

    repo: str
    number: int
    title: str
    body: str
    url: str
    state: str
    created_at: str
    captured_at: str


def _get(path: str) -> object:
    req = urllib.request.Request(
        f"{API_ROOT}{path}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub API error {exc.code} for {path}: {exc.read()[:300]}") from exc


MAX_PAGES = 10  # a hard stop so a PR-heavy repo can't spin this forever


def fetch_recent_issues(owner: str, repo: str, *, state: str = "open", limit: int = 10) -> list[RealIssue]:
    """Real issues, unmodified, most recently updated first. Pull requests
    are excluded (GitHub's issues endpoint returns both; PRs carry a
    'pull_request' key we filter out) — which means one page is not enough
    for a PR-heavy repo, so this paginates until it has `limit` real issues,
    runs out, or hits MAX_PAGES."""
    captured_at = datetime.now(timezone.utc).isoformat()
    per_page = 100
    issues: list[RealIssue] = []

    for page in range(1, MAX_PAGES + 1):
        raw = _get(
            f"/repos/{owner}/{repo}/issues"
            f"?state={state}&per_page={per_page}&sort=updated&page={page}"
        )
        if not raw:
            break

        for item in raw:
            if "pull_request" in item:
                continue
            issues.append(
                RealIssue(
                    repo=f"{owner}/{repo}",
                    number=item["number"],
                    title=item["title"],
                    body=item.get("body") or "",
                    url=item["html_url"],
                    state=item["state"],
                    created_at=item["created_at"],
                    captured_at=captured_at,
                )
            )
            if len(issues) >= limit:
                return issues

        if len(raw) < per_page:
            break  # last page

    return issues
