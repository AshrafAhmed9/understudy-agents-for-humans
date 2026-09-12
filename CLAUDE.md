# Understudy

## Competition

This project is a judged hackathon submission. Read `COMPETITION.md` and `EXECUTION.md`
before doing anything else. `COMPETITION.md` holds the rubric, the field, the prize
buckets, the claims and their proofs, and the freeze checklist. Keep it current — update
it in the same turn anything in it changes.

**Deadline: Sep 14, 2026, 5:00pm PDT. Feature freeze: end of Sep 13.**

## What this is

An agent that watches a repo and, for each inbound bug report, writes a Python script
intended to reproduce the reported behavior, runs it in a locked-down container,
fixes the script if it fails to run, and reports a verdict. It is allowed to interrupt
the maintainer a limited number of times per day, and that limit is enforced in code.

One sentence: **before you spend time on a bug report, Understudy tries to run it.**

## Non-negotiable rules

1. **Never change `schemas.py`** without updating every stream that depends on it. It is
   the contract that lets parallel work happen.

2. **Scoring is the gold-patch differential, only.** A reproduction counts as
   `reproduced` if and only if the script **fails at `base_commit`** AND **passes at
   `base_commit` + the dataset's gold patch**. Never score on exit code alone — a script
   that exits non-zero because of an `ImportError` is a broken script, not a reproduced
   bug. Timeouts, setup failures, OOM and unrelated errors cannot establish reproduction.
   Live results are candidates; offline confirmation is a separate result. **The agent must never see the gold patch**; only
   the offline scorer applies it, after the verdict is committed.

3. **The agent must never run `git`.** It is blocked in the `BeforeToolCallEvent` hook and
   every attempt is logged. SWE-bench images clone the full repo and reset to
   `base_commit`, so the fix commit is still reachable via `git log --all`, `git show`,
   packed refs and the reflog. If the agent reads it, the affected evaluation is invalid. Blocked git is not enough:
   runtime artifacts must also exclude all readable history, patches and scorer files.

4. **Container flags are fixed:** `--network none --memory 512m --cpus 1 --pids-limit 128
   --user nobody`, read-only rootfs with a tmpfs `/tmp`, stdin from `/dev/null` (so
   `input()` hits EOF instead of hanging), and an external `timeout 60` followed by
   SIGKILL. We execute untrusted code from strangers. No exceptions.

5. **Use `/bin/bash -lc`, never `/bin/sh`.** `sh` is dash on these images and `source`
   fails. This is a recurring, documented SWE-bench trap.

6. **Model is local Ollama (`qwen2.5-coder:7b`), not Nova Lite.** Superseded 2026-09-12:
   Bedrock access is broken on this account (`ValidationException: Operation not allowed`,
   persisted through a full Free-to-Paid upgrade) and Ashraf will not spend money on a paid
   API. See COMPETITION.md's model-decision note for the empirical check that justified
   this. Do not switch to Bedrock, Nova Lite, or any paid API without asking Ashraf first.

7. **Every screen renders from a JSON file.** The UI never calls a model or Docker
   synchronously. The live agent's only job is to write that file.

8. **Every run writes a full cassette** to `runs/<id>.json` — issue text, each generated
   script, each stderr, timings, verdict. `UNDERSTUDY_REPLAY=1` must reproduce any run
   exactly, with the network disabled. The demo video is recorded from replay.

9. **Do not build:** duplicate detection, labelling beyond the verdict, docs answers,
   stale-issue closing, PR review, `git bisect`, PyPI packaging. Out of scope on purpose —
   Dosu already does several of them free across 50,000+ projects, and breadth is how this
   submission loses.

10. **Freeze is end of Sep 13.** Sep 14 is video and submission only, not a build day.

## Writing

Anything a judge reads — README, video script, blog posts, issue comments the agent
posts — should sound like a working engineer wrote it. No marketing language, no
inflated claims. State numbers plainly, including the bad ones.

## Reviewed plan and interface correction

Follow the September 11–12 review in COMPETITION.md and EXECUTION.md. Instance is
agent-facing and patch-free; ScoringCase belongs only to the offline scorer. Live verdicts
use candidate_reproduction; only valid gold differentials establish Score.reproduced.
The triage result preserves the final script before scoring. Notifications cost one integer
unit, persist across restart, and are never refunded after delivery. All outbound channels
share the same cap. Full scope is retained per Ashraf: use the workstream acceptance gates.
