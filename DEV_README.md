# Understudy — dev status

Not the submission README (that needs real numbers from an actual eval run).
This is what's built, what's verified, and what needs Ashraf.

## Setup

```
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

48 tests pass, including 7 integration tests against a real Docker daemon
(sandbox/runner.py) and hook tests against the real strands-agents 1.55.1
API (not mocked).

## Built and verified, no AWS credentials needed

- `understudy/sandbox/runner.py` — host-supervised container execution.
  Proven against a real daemon: correct exit codes, stderr capture, an
  infinite loop is actually killed within the timeout (not just abandoned),
  no network reaches out, the root filesystem is genuinely read-only, a
  missing image fails cleanly instead of hanging. One real bug found and
  fixed here: passing `-i` on a `--detach` run left stdin open with nothing
  on the other end, so a generated script calling `input()` hung forever.
- `understudy/scoring/differential.py` — the gold-patch differential. 8
  hostile-fixture tests prove an always-fail, always-pass, import-error, or
  timing-out script can never be scored as a reproduction.
- `understudy/sandbox/sanitize.py` — strips `.git`, packed refs, and
  patch/eval files from a checkout, plus a symlink- and traversal-safe path
  resolver for the agent's read/search tools.
- `understudy/policy/ledger.py` — durable SQLite interruption budget. 10
  tests prove: a 6th request in a 5-cap day is queued, not delivered;
  duplicate keys don't double-spend; state survives closing and reopening
  the ledger; resolving an item never refunds a slot; an ambiguous delivery
  keeps its reservation instead of returning it to the pool.
- `understudy/policy/hooks.py` — the `BeforeToolCallEvent` hook, verified
  against the real SDK (not assumed from docs). Blocks anything that looks
  like a `git` invocation and logs the attempt; gates `escalate_to_human`
  against the ledger. Found and fixed a real regex bug: `\bgit\b` doesn't
  match `run_git` because `_` counts as a word character, so a tool named
  `run_git` or `git_log` would have slipped through.
- `understudy/tools/repo_access.py` — the agent's only two ways to see the
  repo: `read_file` and `search_source`, both confined to the sanitized
  tree and capped so a huge file or a pathological match count can't blow
  up context.
- `understudy/receipts.py` — atomic JSON writes for `runs/<id>.json`, so no
  UI reader ever sees a half-written cassette. Tested under concurrent
  reads while writes are happening.

## Genuinely needs Ashraf next

- **AWS credentials for Nova Lite.** Nothing above calls Bedrock. The actual
  `triage()` reasoning loop (issue text → candidate script) needs his AWS
  account and costs real money, even if small (~$2 budgeted).
- **One SWE-bench instance decision.** Which instance to prove the gold-patch
  differential against end-to-end, and pulling that image (multi-GB, his
  bandwidth/disk).
- **The fork.** A real active Python project to fork, with real open issues
  copied in — needs his GitHub account.
- Everything downstream of those three: the eval matrix, the four screens
  against real data, AgentCore deployment, the video, the Builder posts.

## What's explicitly not built yet

The Strands `Agent(...)` wiring itself — tools are ready, the hook is ready,
but assembling them into a live agent and running it is the first thing that
needs credentials, so it wasn't done speculatively.
