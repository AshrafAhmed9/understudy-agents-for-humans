# Architecture

Status: the execution and safety layer below is built and verified end-to-end
against real data (see DEV_README.md). The agent reasoning loop is wired but
has never made a model call — that needs AWS credentials Ashraf hasn't
provided yet. Nothing in this diagram is aspirational; every box either
exists and is tested, or is explicitly marked not yet built.

```mermaid
flowchart TD
    subgraph Input
        GH[GitHub Issues\nread-only, unauthenticated\nunderstudy/ingest/github.py]
        SWE[SWE-bench Verified\npublic dataset, no auth\nunderstudy/data/swebench.py]
    end

    subgraph Agent["Strands Agent — wired, not yet invoked live"]
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

    subgraph Scoring["understudy/scoring/"]
        DIFF[differential.py\ngold-patch differential\nfails-on-buggy AND passes-on-fixed]
    end

    subgraph Output
        REC[receipts.py\natomic JSON writes\nruns/&lt;id&gt;.json]
        UI["Four screens — NOT YET BUILT\nWatch / Receipt / Evidence / Inbox"]
    end

    GH --> A
    SWE --> SAN
    A --> T1 --> SAN
    A --> T2 --> SAN
    A -->|candidate script| RUN
    RUN -->|ExecResult| DIFF
    PREP -->|fixed image| RUN
    DIFF --> REC
    REC -.->|not yet built| UI
```

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

AWS credentials (nothing above has made a real model call), a decision on
which repo to fork for the live autonomous-posting demo, and everything
downstream: the eval matrix at scale, the four UI screens against real
results, AgentCore deployment, the video, the Builder posts.
