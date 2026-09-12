# Understudy

## What this is

An agent that watches a repo and, for each inbound bug report, writes a Python script
intended to reproduce the reported behavior, runs it in a locked-down container,
fixes the script if it fails to run, and reports a verdict. It is allowed to interrupt
the maintainer a limited number of times per day, and that limit is enforced in code.

One sentence: **before you spend time on a bug report, Understudy tries to run it.**

## Non-negotiable rules

1. **Never change `understudy/schemas.py`** without updating every module that depends on
   it. It is the contract that lets the pipeline stages agree on shapes.

2. **Scoring is the gold-patch differential, only.** A reproduction counts as
   `reproduced` if and only if the script **fails at `base_commit`** AND **passes at
   `base_commit` + the dataset's gold patch**. Never score on exit code alone — a script
   that exits non-zero because of an `ImportError` is a broken script, not a reproduced
   bug. Timeouts, setup failures, OOM and unrelated errors cannot establish reproduction.
   Live results are candidates; offline confirmation is a separate result. **The agent
   must never see the gold patch**; only the offline scorer applies it, after the verdict
   is committed.

3. **The agent must never run `git`.** It is blocked in the `BeforeToolCallEvent` hook and
   every attempt is logged. SWE-bench images clone the full repo and reset to
   `base_commit`, so the fix commit is still reachable via `git log --all`, `git show`,
   packed refs and the reflog. If the agent reads it, the affected evaluation is invalid.
   Blocked git is not enough: runtime artifacts must also exclude all readable history,
   patches and scorer files.

4. **Container flags are fixed:** `--network none --memory 512m --cpus 1 --pids-limit 128
   --user nobody`, read-only rootfs with a tmpfs `/tmp`, stdin from `/dev/null` (so
   `input()` hits EOF instead of hanging), and an external `timeout 60` followed by
   SIGKILL. This runs untrusted code from strangers. No exceptions.

5. **Use `/bin/bash -lc`, never `/bin/sh`.** `sh` is dash on these images and `source`
   fails. This is a recurring, documented SWE-bench trap.

6. **Model is local Ollama (`qwen2.5-coder:7b`).** AWS Bedrock access on this account
   returns `ValidationException: Operation not allowed`, confirmed to persist across a
   full Free-to-Paid plan upgrade. Do not switch to Bedrock or any paid API without asking
   first.

7. **Every screen renders from a JSON file.** The UI never calls a model or Docker
   synchronously. The live agent's only job is to write that file.

8. **Every run writes a full cassette** to `runs/<id>.json` — issue text, each generated
   script, each stderr, timings, verdict. `UNDERSTUDY_REPLAY=1` must reproduce any run
   exactly, with the network disabled. The demo video is recorded from replay.

9. **Out of scope, deliberately:** duplicate detection, labelling beyond the verdict, docs
   answers, stale-issue closing, PR review, `git bisect`, PyPI packaging. Depth on one
   capability beats breadth across many.

## Writing

Anything a reader sees — README, video script, issue comments the agent posts — should
sound like a working engineer wrote it. No marketing language, no inflated claims. State
numbers plainly, including the bad ones.

## Interface notes

`Instance` (agent-facing) is patch-free; `ScoringCase` (offline-scorer-only) carries the
gold patch. Live verdicts use `candidate_reproduction`; only a valid gold differential
establishes `Score.reproduced`. The triage result preserves the final script before
scoring. Notifications cost one integer unit, persist across restart, and are never
refunded after delivery. All outbound channels share the same cap.
