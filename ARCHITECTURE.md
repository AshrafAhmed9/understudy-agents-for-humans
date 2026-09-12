# Architecture

Status (2026-09-12): the execution and safety layer, the real triage loop, and the real
scoring pipeline are built and verified end-to-end against real data — not a mock or a
throwaway script (see DEV_README.md and COMPETITION.md's model-decision note). The model is
local Ollama (`qwen2.5-coder:7b`), not Bedrock — AWS Bedrock access on this account is
broken and Ashraf has ruled out paid APIs. The four UI screens are built and live. Nothing
in this diagram is aspirational; every box either exists and is tested, or is explicitly
marked not yet built.

```mermaid
flowchart TD
    subgraph Input
        GH[GitHub Issues\nread-only, unauthenticated\nunderstudy/ingest/github.py]
        SWE[SWE-bench Verified\npublic dataset, no auth\nunderstudy/data/swebench.py]
    end

    subgraph Triage["understudy/triage.py — real, model-backed"]
        GEN[OllamaGenerator\nqwen2.5-coder:7b, local, $0]
        LOOP[generate -> run -> repair\nup to 3 attempts]
        GEN --> LOOP
    end

    subgraph Agent["Strands Agent — wired, tools available"]
        A[understudy/agent.py]
        T1[read_file]
        T2[search_source]
        T3[escalate_to_human]
        A --> T1
        A --> T2
        A --> T3
    end

    subgraph Policy["understudy/policy/"]
        HOOK[UnderstudyPolicyHook\nBeforeToolCallEvent]
        LEDGER[(Ledger — SQLite\ndurable interruption budget)]
        HOOK -->|gates| T3
        HOOK -->|blocks| GIT[git — never reachable]
        HOOK --> LEDGER
    end

    subgraph Sandbox["understudy/sandbox/ — the trust boundary"]
        SAN[sanitize.py\nstrips .git, packed refs, patches]
        RUN[runner.py\nrun_script_in_container\nnetwork:none, ro rootfs,\nnobody, 512m, 60s host-killed]
        PREP[prepare_fixed_image\noffline-only, trusted,\napplies gold patch]
    end

    subgraph Scoring["understudy/scoring/ + understudy/eval/"]
        DIFF[differential.py\ngold-patch differential\nfails-on-buggy AND passes-on-fixed]
        AGG["run_eval / build_results.py\nresults.json + taxonomy"]
        DIFF --> AGG
    end

    subgraph Output
        REC[receipts.py\natomic JSON writes\nruns/&lt;id&gt;.json]
        UI["ui/index.html — four screens, live\nWatch / Receipts / Evidence / Inbox"]
        AGG --> UI
    end

    GH --> A
    SWE --> LOOP
    A --> T1 --> SAN
    A --> T2 --> SAN
    LOOP -->|candidate script| RUN
    RUN -->|ExecResult| DIFF
    PREP -->|fixed image| RUN
    DIFF --> REC
    REC --> UI
```

**Real result on this pipeline, N=16 real SWE-bench Verified instances (2026-09-12): 3/16
(19%) reproduced by the gold-patch differential**, vs. 14/16 (88%) a naive exit-code check
would have wrongly claimed. See `results.json` and COMPETITION.md for the full breakdown.

## Trust boundaries

1. **The agent never sees a gold patch.** `Instance` (agent-facing) has no
   field for one — it's a type-level guarantee, not a convention. Only
   `ScoringCase`, used exclusively by the offline scorer, carries it.
2. **The agent never runs `git`.** Blocked in `UnderstudyPolicyHook`, and
   the sanitizer separately strips `.git`/packed-refs/patches from the tree
   the agent's tools can see — two independent layers, because blocking the
   `git` executable alone is not sufficient (the fix commit is reachable by
   reading objects directly).
3. **Untrusted code (the generated reproduction script) always runs under
   full lockdown**: no network, read-only root filesystem, capped memory/
   processes/user, host-enforced timeout that actually kills the container
   (not just the CLI process — verified this distinction matters, see
   DEV_README.md).
4. **Applying the gold patch is a separate, trusted lifecycle** from
   executing untrusted code. It happens in a throwaway writable container
   that gets committed to a new image and then discarded; the untrusted
   script only ever runs afterward, under the same lockdown as the buggy
   run, against that image.

## What still needs Ashraf

The video recording, the 3 Builder posts (needs an AWS Builder ID), and final submission on
Devpost. Everything else — the real triage loop, the real scoring pipeline, the eval data,
the four UI screens, the fork (https://github.com/AshrafAhmed9/tqdm) with 3 real issues and
3 real posted verdicts — is built. See `understudy/fork_demo/README.md`.

**AgentCore deployment (Stream E) is confirmed blocked at the account level, not attempted
further.** Verified 2026-09-12: even after attaching a working `bedrock-agentcore:*` IAM
policy directly to the user, every AgentCore control-plane call returns
`AccessDeniedException`. That's the same shape as the Bedrock `ValidationException` — an
account-wide restriction sitting above IAM (an SCP or permissions boundary), not a
permissions gap we can fix from inside the account. Two independent Bedrock-family services
blocked the same way is enough evidence to stop chasing this and disclose it as a known
limitation rather than spend more of the remaining time on it.
