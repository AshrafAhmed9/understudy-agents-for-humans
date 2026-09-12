# Understudy

**It watches a repo, verifies bug reports by actually running them, and is only allowed to
interrupt you five times a day.**

Live demo (four screens, real data): https://claude.ai/code/artifact/076c03d5-f79f-4e4a-8970-7ee4e46079e4

## What it does

A maintainer gets a bug report. Before anyone spends time on it, Understudy tries to run it.

For each inbound issue, it reads the issue text and the checked-out repo (no `git` — that's
blocked, see Safety below), writes a Python script meant to reproduce the reported bug, and
executes it in a locked-down container. If the script itself is broken — not the bug, the
script — it reads the error back and tries again, up to three times. It reports one of four
verdicts: `candidate_reproduction`, `not_reproduced`, `insufficient_info`, or `error`.

It can act on that without asking: post a comment, request the one missing detail. But
interrupting a person costs from a daily budget that's enforced in code, not requested
politely. Most triaged issues shouldn't need it at all.

## Why the number can't just be "it crashed"

A script that exits non-zero doesn't mean the bug is real — an `ImportError` or a wrong API
call also exits non-zero. So the only check this project trusts is the **gold-patch
differential**: run the candidate script at the issue's `base_commit` (must fail), then run
the identical script again with the dataset's answer-key patch applied (must pass). Only
fail-then-pass counts as `reproduced`. The agent never sees the gold patch — only the
offline scorer does, after the verdict is already committed.

Ran both checks side by side on the same 16 real SWE-bench Verified instances:

| Scoring method | Result |
|---|---|
| Naive (script exited non-zero on the buggy commit) | **14/16 — 88%** |
| Real (gold-patch differential) | **3/16 — 19%** |

The naive number is what you'd publish if you didn't check. It's wrong by 4.6x. Eleven of
those sixteen "reproductions" were scripts that failed for reasons unrelated to the reported
bug and kept failing after the real fix — proof the failure had nothing to do with the
patch. One inverted the bug's own example, mistaking the buggy output shown in the issue for
the correct one. Full taxonomy, and every underlying run, is in `results.json` and on Screen
C of the live demo.

19% still clears the published zero-shot floor (GPT-4, issue text alone: 3.6%), on a model
that costs nothing to run.

## The model, and why it isn't what the plan originally said

Inference is local — **`qwen2.5-coder:7b` via Ollama**, not a cloud model. AWS Bedrock
access on this account returns `ValidationException: Operation not allowed`, confirmed to
persist across a full Free-to-Paid plan upgrade, and it's the second project where this
exact failure has shown up. Deploying via Bedrock AgentCore hit the same wall from a
different angle: a working `bedrock-agentcore:*` IAM policy attached directly to the user
still gets `AccessDeniedException` on every call. Two Bedrock-family services blocked the
same way, from above the IAM-user level, reads as an account-wide restriction, not something
fixable from inside the account.

This project has a hard $0 budget, so the fallback wasn't a paid API — it was local
inference. The honest cost of that: a 7B local model underperforms a frontier model on this
task. That wasn't assumed away; it was measured (the table above), and it's the finding this
project leads with instead of hiding. Full decision history is in `COMPETITION.md`.

## Architecture

`diagrams/understudy_architecture.excalidraw` has the full picture, including where the two
real numbers above come from and what the hook actually blocks. `ARCHITECTURE.md` has the
mermaid version and the trust-boundary writeup in text. Short version:

```
issue text ──► triage (Ollama, repo-read tools, git BLOCKED) ──► candidate script
                                                                        │
                                                          locked-down container
                                                     (--network none, ro rootfs, nobody,
                                                      512m/1cpu, host-enforced timeout)
                                                                        │
                                                          offline gold-patch differential
                                                          (agent never sees the gold patch)
                                                                        │
                                                          results.json ──► four UI screens
```

Built with the Strands Agents SDK (`Agent`, `@tool`, `HookProvider`/`BeforeToolCallEvent`),
Pydantic-frozen schemas as the contract between every stage, and Docker for isolated
execution. Sandbox images are Epoch AI's rebuilt SWE-bench registry
(`ghcr.io/epoch-research/swe-bench.eval.x86_64.<instance_id>`), pulled directly — no
network access at execution time.

## Safety

- **The agent never sees a gold patch.** `Instance` (agent-facing) has no field for one —
  it's a type-level guarantee. Only `ScoringCase`, used exclusively by the offline scorer,
  carries it.
- **The agent never runs `git`.** Blocked in `UnderstudyPolicyHook`'s `BeforeToolCallEvent`
  handler, and separately the sandbox sanitizer strips `.git`/packed-refs/patches from
  anything the agent's tools can read — two independent layers, because blocking the `git`
  executable alone isn't enough (the fix commit is still reachable by reading objects
  directly).
- **Untrusted code always runs under full lockdown**: `--network none`, read-only rootfs
  with a tmpfs `/tmp`, capped memory/CPU/processes, `--user nobody`, stdin from `/dev/null`
  (so a script calling `input()` hits EOF instead of hanging forever), and a host-enforced
  timeout that actually kills and removes the container, not just the CLI process.
- **Applying the gold patch is a separate, trusted lifecycle** from executing untrusted
  code — a throwaway writable container commits to a new local image and is discarded; the
  untrusted script only ever runs afterward, under the same lockdown as the buggy run.

Full writeup: `SAFETY.md`.

## Running it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
ollama pull qwen2.5-coder:7b   # local inference, one-time
pytest -q                       # 74 tests, real Docker + real Ollama integration where marked
```

`scripts/test_local_model_repro.py` is a standalone capability probe against real cached
instances. `scripts/build_results.py` regenerates `results.json` from the raw run files in
`runs/`, which the UI (`ui/index.html`) renders from directly — the page never calls a model
or Docker itself.

## What's real vs. what's still a demo

Built and verified against real data: the sandbox, the sanitizer, the interruption-budget
ledger, the anti-cheat hook, the real triage loop against a real local model, the gold-patch
differential scorer, the four UI screens rendering real results, and a real fork
(https://github.com/AshrafAhmed9/tqdm) carrying 3 real, unmodified upstream issues with 3
real posted verdict comments — see `understudy/fork_demo/`.

Not yet done: those verdicts were posted by a manually-triggered script, not a scheduled
AgentCore + EventBridge deployment — that's blocked at the account level, same story as the
Bedrock access issue above. The SWE-bench eval also hasn't scaled past 16 instances. Both
tracked in `COMPETITION.md`.

## Competition

Built for the AWS "Agents for Humans" hackathon, Professional Agents track. See
`COMPETITION.md` for the rubric, the field analysis, and the full claims-to-proof table.
