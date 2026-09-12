# Live fork demo

Real, disclosed autonomous-posting proof for the hackathon (COMPETITION.md's C6). Fork:
https://github.com/AshrafAhmed9/tqdm

Three real open tqdm issues (unmodified, copied with disclosure) were posted to the fork's
tracker as https://github.com/AshrafAhmed9/tqdm/issues/1-3. `Dockerfile` here builds a plain
pip-installed checkout of `tqdm/tqdm` main (no conda, unlike the SWE-bench images —
`understudy.sandbox.runner.plain_command()` is the non-conda shell command for this case).

Real triage ran against all three with `qwen2.5-coder:7b` (issue text only, no repo-read
tools used for this pass), inside the same locked-down container flags as everything else
(--network none, read-only rootfs, nobody, capped memory/cpus, host-enforced timeout).
Results: `runs/tqdm_fork_demo.json`. Verdicts posted as real comments on the three fork
issues.

**What this proves:** the full loop — real issue text in, real generated script, real
container execution, real posted verdict — works end to end against a real, unmodified
GitHub issue outside the SWE-bench benchmark, where there's no gold patch to score against
(these are still open upstream). Verdicts here are correctly `candidate_reproduction` /
`not_reproduced`, never `reproduced` — that status only exists after gold-patch
confirmation, and there is no gold patch for a bug nobody has fixed yet.

**What this does not prove:** it was triggered manually, once, by a script — not on an
EventBridge schedule via a deployed AgentCore runtime (that's Stream E, blocked on AWS
access). The posted comments say so explicitly. Don't imply otherwise in the video.
