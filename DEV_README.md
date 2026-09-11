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

## Kill gate: passed, on real data (Sep 12)

`scripts/verify_kill_gate.py` proves the full pipeline end-to-end on a real
SWE-bench Verified instance (`astropy__astropy-12907`), not a synthetic
fixture:

- 30 real instances fetched from the public `princeton-nlp/SWE-bench_Verified`
  dataset via Hugging Face's datasets-server API — no credentials needed,
  cached at `data/swebench_verified_sample.json`.
- Confirmed the Epoch AI registry images are real and resolve
  (`docker manifest inspect`, no full pull, on several instance IDs).
- Pulled one image for real: 964MB, 78s.
- Confirmed the documented convention exactly: working dir `/testbed`, conda
  env `testbed` — this is the real image, not an assumption from the writeup.
- Hand-authored a reproduction script from the real issue text (a genuine
  astropy bug: nested `CompoundModel` separability). Ran it against the
  unpatched image — **failed, as the bug predicts.** Applied the real gold
  patch through a new offline-only path (`prepare_fixed_image` +
  `run_patched_script_in_container`) and reran the identical script —
  **passed.** `score_differential` correctly reports `reproduced=True`.

This is a hand-authored script proving the infrastructure is honest, not an
agent result — no model call was made, and none of this needed AWS credentials.

One real design bug found and fixed while building this: applying the gold
patch under the same read-only, no-network container used for untrusted
script execution can't work (`git apply` needs to write). Fixed by splitting
into two container lifecycles — a trusted prep step (writable, applies the
patch, commits a new local image, always cleaned up after) and then the
*exact same locked-down execution* used for the buggy run, against that
image. Untrusted-code containment is never weakened; verified no leftover
containers or images after the run.

`understudy/data/swebench.py` is now the loader real evaluation work will
use — `load_cases()` returns real `ScoringCase` objects, with the gold patch
kept out of the agent-facing `Instance` type at the type-system level (the
type has no field for it), not just by convention.

## Agent wiring: one more real finding (Sep 12)

`understudy/agent.py` assembles the three tools and the policy hook into a
real Strands `Agent`. Building this surfaced something worth knowing before
Ashraf ever touches AWS: **`Agent(model=None)` does not defer credential
resolution.** The SDK defaults to `BedrockModel` and tries to load AWS
credentials immediately at construction — even if the agent is never
invoked. On this machine that fails with a botocore dependency error before
any test could even check that tools registered correctly.

Fixed for testing purposes with `tests/fake_model.py` — a minimal `Model`
subclass that satisfies the abstract interface and touches nothing. Proven
against the *real* Strands hook registry (not a standalone hook test):
`git_log` is blocked and the escalation budget is enforced through an actual
constructed `Agent`, not just the hook object in isolation.

Also added `understudy/ingest/github.py` — real, unauthenticated, read-only
fetches of public GitHub issues. No credentials needed for reading. Caught a
real pagination bug against live data: a PR-heavy repo (tested against
python/cpython) can fill an entire page with pull requests, which get
filtered out, silently starving the result — fixed by paginating until
enough real issues are found or the repo genuinely runs out.

64 tests passing. `ARCHITECTURE.md` and `SAFETY.md` are now in the repo,
describing only what's built, with a mermaid diagram of the real trust
boundaries.

## Status: everything buildable without AWS/GitHub credentials is done

What's left needs one of: Ashraf's AWS account (any real model call),
Ashraf's GitHub account (a fork to post to), his decision on evaluation
spend, or a human (video, recruiting reviewers, publishing posts). Nothing
further should be built speculatively past this point — the four UI screens
and the eval-at-scale results depend on having real triage output to render,
which needs a real model call first.
