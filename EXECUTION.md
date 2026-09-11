# Understudy — execution plan

Read `COMPETITION.md` and `AGENTS.md`. Use parallel implementation streams with available help. Integrate a
working vertical slice early; do not wait until end of day to discover interface failures.
Model: Nova Lite. Inference ceiling: approximately $2. No Sonnet or paid deployment assumed.

## Critical path and integration order

Build in this order: sanitized execution and offline oracle → one Strands reproduction loop
→ durable interruption queue → JSON receipt/replay → scheduled ingestion → measured study
→ presentation. Ashraf owns the reproduction/scoring decisions. Parallel help can implement
isolated UI, tests or documentation once their actual inputs exist; each stream integrates continuously against versioned fixtures and the real vertical slice.

The full target includes the local execution worker, AgentCore orchestration, GitHub MCP,
four coherent screens, persistent scheduling, paired evaluation, real-issue validation and
three Builder posts. These are dependency stages, not a reduced submission scope. Available
help should build independent components concurrently. Never relax evidence integrity or
sandbox limits to unblock integration. Spending limits still apply: engineering help does
not authorize additional inference or infrastructure charges.

## Next work session: prove feasibility and integrate

Within the first two working hours:

- Pin Python, Pydantic, Strands and one image digest. Verify actual SDK hook behavior on the
  agent instance; a graph is unnecessary for a single bounded repair loop. Do not build
  around an unverified historical issue number or event-name claim.
- Confirm Nova Lite access and measure a bounded call. Track input/output tokens, retries
  and an upper-bound reservation before each call; stop on the inference ceiling. AWS
  alerts do not stop spending. The advertised promotional credits are reportedly exhausted.
- Pull and preflight one compatible image under local emulation. Record download size,
  setup time, memory use and execution time; extrapolate from measurements, not registry
  averages. Begin with one container; increase only if host memory permits.
- Run a hand-written issue-specific failing assertion on a known buggy case and the same
  script on its fixed counterpart. Then prove an import error, timeout, always-pass and
  always-fail script cannot become a scored reproduction.

The runner and scorer must work before requesting generated scripts. Then timebox one real
Strands-generated attempt and repair to the current work session. Record the complete first
cassette and display it in a plain receipt immediately.

If environment setup fails, choose another compatible case or smaller supported repository
without weakening limits. If Nova cannot produce a useful candidate after a bounded pilot,
stop the broad benchmark and diagnose the traces. A hand-authored fixture may demonstrate
infrastructure but cannot be passed off as agent success. Any pivot away from reproduction
needs a fresh product decision; a decorative budget meter is not an equivalent fallback.

## Boundaries and scoring

`schemas.py` is updated with every dependent stream specification in this revision; no
implementation consumers existed. Freeze it after the first vertical slice, not before
checking that it can represent the workflow.

The agent-facing `Instance` contains issue text and pinned repository identity, no answer
key. A separate offline `ScoringCase` contains the gold patch. `triage` returns an immutable
result containing the verdict and final candidate script (if any). Cassettes retain all
attempts. `score(case: ScoringCase, result: TriageResult)` accepts the offline case and the persisted
immutable result, using only its final candidate for execution.

The live status `candidate_reproduction` renders as “Candidate reproduction — review the
assertion.” Never render “this bug is real.” `not_reproduced` is inconclusive; `error` covers
failed setup/execution. Do not show model confidence as calibrated probability. The offline
score is separately labelled “Confirmed by withheld patch” only after valid fail→pass runs.

The assertion must match the reported behavior, not just any exception. Capture setup
success, interpreter invocation, execution completion, exit code, stderr, signal, timeout
and OOM in the cassette. Infrastructure failures are ineligible for a successful differential.
The final script is immutable before scoring; no repair or selection sees fixed-run output.
Preserve the exact script hash and patch/image/input/config hashes in the offline result.

## Sandbox and anti-leakage boundary

Keep all required flags: `--network none --memory 512m --cpus 1 --pids-limit 128 --user nobody`,
read-only rootfs, bounded tmpfs `/tmp`, stdin `/dev/null`, `/bin/bash -lc`, external 60-second
timeout followed by SIGKILL. Add dropped capabilities and no-new-privileges. No credentials,
host directories, Docker socket or scorer artifacts enter the workload. Mount the generated
script read-only outside the tmpfs mount (for example `/repro/repro.py`).

Use a trusted preparation step to construct clean base and fixed runtime artifacts. Agent
and generated Python see only the base artifact. Remove `.git`, packed history, alternate
object stores, gold patches and benchmark answer-bearing eval files from every readable
path; merely rejecting the git executable is insufficient. Fixed artifacts belong solely
to the offline process. Do not give the agent generic shell access. Its read/search tools
resolve canonical paths inside an allowlisted clean tree, reject symlink escapes, and cap
bytes, regex/runtime work and output. Generated Python is untrusted even if these tools are
restricted, so artifact sanitation is essential. Git invocation attempts stay blocked/logged.

Preparation can fetch dependencies with networking; execution cannot. Determine interpreter
and writable-path needs from the image before running it. Set caches and temporary files to
`/tmp`; use preinstalled dependencies. Mark incompatible cases as such before holdout
selection. Do not add network, root access or writable repo mounts to rescue a run.

A host supervisor records the container ID, enforces the deadline, kills/removes that exact
container in `finally`, and verifies it no longer runs. Killing the Docker CLI alone is not
a sufficient timeout implementation. Detect availability of GNU `timeout` on macOS during
preflight. Limit stdout/stderr while preserving truncation metadata. Test infinite loops,
child processes, output flooding and supervisor interruption. Do not claim containers make
arbitrary hostile code perfectly safe; this is a constrained local prototype.

## Agent loop

One Strands agent with narrowly scoped tools: read source, search source, submit a candidate
script for isolated execution, request a maintainer decision. Repository identity, runtime,
paths and notification targets are host-selected, never model-selected shell arguments.

At most three script executions; bounded total tool calls, context bytes and token spend.
Each repair receives only base stderr/stdout and the prior script. Log tool events and
blocked requests. Test a real BeforeToolCallEvent denial. A prompt-injection filter may help
later, but it is not an authorization or filesystem boundary and is not needed to make the
core design safe. Untrusted issue text cannot widen tools or change the budget.

## Attention policy: five means five

Each proactive human interruption costs exactly one integer unit. Remove
`harm × urgency ÷ confidence`: the inputs are uncalibrated and division is undefined at
zero confidence. Remove refunds: dismissing something does not undo the interruption.

Use a durable SQLite ledger and queue outside the sandbox. Scope the cap to the configured
maintainer across watched repos, with an explicit timezone. Atomically reserve a slot and
persist an outbox item under a stable issue/version/action key. Hook denial is visible in the
trace; the actual dispatch function independently enforces the same ledger, including any
non-model path. Queue creation is free. Dispatch reserves a slot; confirmed delivery spends it, while
ambiguous delivery retains the reservation. Clicking “resolve” neither spends nor refunds.
Display queued, reserved and delivered counts separately.

Deduplicate delivery and polling retries. Reconcile uncertain external sends before retrying;
do not release a slot on ambiguous delivery. Show errors and queued items rather than losing
them. Delivered slots are never refunded. Rollover starts a new allowance without deleting
pending work. Order pending decisions by host-configured category (candidate review, then missing context),
then oldest first; age out priority inversions with a documented maximum wait. Allocation is
per scheduled batch, not model-assigned urgency. A cap can still delay valuable work, so show
that tradeoff. Surface queue age, and let a human
inspect the queue at any time. A proactive digest consumes a slot; a pull-only digest does
not send a notification. All proactive channels share the cap.

Acceptance: six concurrent requests yield at most five deliveries; duplicates use one slot;
restart retains spending and queue; midnight uses the configured timezone; resolution does
not refund; uncertain sends do not duplicate; exhausted items remain accessible. Demo this
policy on an explicitly accelerated scenario as well as the recorded agent run.

## Autonomous ingestion and actions

Start with a local scheduled poller on the developer machine, documented as such. Watch an
allowlisted repo/issue set, checkpoint issue IDs and update versions, and persist before
processing. A schedule fires without a person pressing Run. Unsupported repos get an honest
unsupported receipt, not improvised package installation. The host stays awake for the demo.

For real issues record upstream URLs, body snapshots, capture time and pinned source revision.
Do not fetch resolution comments or linked fix PRs into the benchmark agent. Use permitted
excerpts/data with attribution. Replay can ingest a frozen inbox snapshot, clearly labelled.

Default action is a local decision queue and receipt. Actual GitHub comments may themselves
notify people; route any enabled posting through the same policy. Posting requires explicit
user authorization for the destination, uses a scoped token and idempotent marker, and is
never enabled merely because a copied issue is public. This review sends nothing externally.

A fork demonstration is acceptable with visible attribution and “demonstration repository”
disclosure; it is not evidence of adoption by the upstream maintainers. Real outbound posting
is a full-scope integration target conditional on explicit destination authorization. Local
autonomous evidence can proceed while that authorization remains outstanding.

## UI and replay

Build four coherent views: Watch, Receipt, Evidence and Decision Inbox. Share the same
JSON contracts and visual system. Watch links to receipts and pending decisions; Evidence
links every aggregate to individual runs. Each view must answer a distinct maintainer question. Every view renders from JSON snapshots;
use atomic writes so readers never see half a file. Replay controls affect local presentation
state only and are labelled simulation; they must not imply GitHub or ledger mutations.

Show actual issue counts, attempted/unresolved/error totals, interruptions and queue age.
No seeded “37 triaged” or “35 silently handled” unless those receipts exist. Use a recorded
run label, source revision and timestamp. Do not animate a countdown as if polling is live
when displaying replay. Empty, unsupported and stale states are required product states.

The receipt includes source issue, tested revision, script download, issue-specific assertion,
execution logs, attempt diff, runtime, estimated cost and uncertainty. The decision explains
what the maintainer must decide: inspect a candidate or supply missing environment details.
Actions are “Mark reviewed,” “Defer,” and “Inspect script”; no refund or automatic bug label.

`runs/<id>.json` stores original issue, all model/tool outputs, scripts, logs, failures,
timestamps, versions, limits and final decision events. `UNDERSTUDY_REPLAY=1` consumes these
without model, Docker, GitHub or network calls. Record input ordering and clock events so
policy replay is deterministic in a separate sandbox ledger. Public cassettes are sanitized
of tokens/private data without altering the evidence; document any redactions. Do not commit
raw API caches indiscriminately.

Host read-only replay for easy judge inspection and include a cold-runnable test build for
real functionality. AgentCore is part of the full target, integrated after the local vertical slice: do not assume it can run local
Docker images or access a laptop daemon. Any cloud architecture must name and demonstrate a
separate compatible execution worker, its authentication and costs before being claimed.
Use GitHub MCP for scoped issue ingestion and, once authorized, outbound receipt comments.
Its value is a constrained integration exercised in the trace, not the presence of a logo.

## September 12–13: evidence, integration and freeze

September 12 morning: finish policy tests and replay; run unattended ingestion into a real
receipt. By midday, verify a cold setup and make a rough 60-second recording. If any of these
fails, spend the afternoon repairing it before declaring integration complete.

Freeze development/holdout manifests before evaluation. Follow the paired study protocol in
`COMPETITION.md`. Cache with complete keys: issue/source/image/model/prompt/tool/config hashes,
attempt and prior feedback. Never reuse across changed inputs or use scorer output as input.
Run controls and a small holdout first, then increase only from measured time and spend.
Budget runtime for up to three generation executions plus two differential executions per
arm per case; the old 120-execution estimate omitted work. Share the first attempt fairly.

September 13 morning: finalize receipts/results and test the exact demo path. Show all
eligible holdout outcomes, including failures. Verify a new reader can follow setup and
receipt. By 14:00 IST have a rough complete video, submission draft, README, architecture
and license. Publish up to three distinct factual Builder posts when their evidence exists:
attention-policy enforcement, reproduction boundaries, and measured failures/repair cost.

Freeze September 13 at 20:00 IST. September 14 is final recording, link/compliance checks
and submission. Preserve judge access through October 8. The freeze protects the submitted evidence; use available help to finish parallel work beforehand.

## Five-minute video

| Time | Demonstration |
|---|---|
| 0:00–0:30 | Maintainer's concrete task, one real report, actual run totals and uncertainty |
| 0:30–1:45 | Report → relevant code → initial failure → repair diff → candidate receipt |
| 1:45–2:30 | Specific maintainer decision; exhausted budget defers another without losing it |
| 2:30–3:05 | Evidence of unattended schedule; distinguish real recording from replay |
| 3:05–3:45 | Small architecture diagram with trust boundaries and meaningful Strands tool trace |
| 3:45–4:30 | k/N, same-model repair control, one failure, cost and offline gold differential |
| 4:30–5:00 | What remains uncertain, inspect/download receipt, audience and closing outcome |

Record from actual cassettes with replay disclosure and visible original elapsed time.
No fabricated adoption, saved hours, confidence calibration or security prevention claims.
The memorable result must be measured; if reproduction yield is low, say so and show the
useful evidence that actually exists. End with this product, not the out-of-scope bisect idea.


## Full-depth workstreams — user-directed scope

Ashraf explicitly requested depth without reducing scope and has implementation help. Keep
one project. The stages above establish dependency order; this section defines the complete
target and supersedes earlier suggestions to shrink it. The official deadline and existing
spending authorization remain real constraints; neither can be erased by planning.

| Owner / stream | Full deliverable | Demonstrable acceptance |
|---|---|---|
| Ashraf: reproduction reasoning | Source localization, issue-specific assertion generation, bounded repair, final evidence selection without gold | Cases showing localization, a useful repair, and honest abstention; per-attempt traces |
| Execution engineer | Sanitized base/fixed environments, supervised lifecycle, resource enforcement, environment adapters | Hostile fixture suite and repeatable gold differential across supported repositories |
| Policy engineer | Durable scheduling, deduplication, outbox, interruption allocation, deferred queue and digest | Restart/concurrency/ambiguous-delivery tests and no lost decisions |
| Integration engineer | AgentCore orchestrator, authenticated worker bridge, GitHub MCP, least-privilege identities | Scheduled remote orchestration produces a real worker receipt; permitted GitHub write reconciles once |
| Evaluation engineer | Frozen 20–30-case paired study, controls, repeated successes, 30-case real-issue adjudication set | Per-case artifacts, uncertainty, cost, failure taxonomy and no gold leakage |
| Product engineer | Watch, Receipt, Evidence, Inbox; coherent navigation and JSON replay | First-time reader finds issue, assertion, uncertainty and decision without narration |
| Evidence / presentation owner | Maintainer review protocol, README/setup, safety explanation, architecture, video, three Builder posts | Cold setup and independently understandable end-to-end demo with traceable claims |

Agree fixtures and schema version before parallel work. Merge completed slices daily and
run the integrated path after each boundary change; do not defer integration until freeze.

### Cloud execution boundary

AgentCore hosts Strands orchestration; the existing local Docker worker executes untrusted
code. A private authenticated queue carries jobs to the worker through outbound polling;
a private object store holds bounded, versioned artifacts. The worker needs no public
inbound port. Jobs bind an immutable allowed repository revision, script hash, resource
profile and run ID. The worker chooses the approved image from a registry mapping; remote
messages cannot inject shell commands, image names, host paths or runtime flags.

Use short-lived narrowly scoped AWS credentials outside the sandbox. Validate job schema,
lease jobs, renew leases, persist completion before acknowledging, and deduplicate retries.
Store results under run-scoped keys, verify hashes, and publish only sanitized JSON to the
public viewer. A worker outage leaves jobs pending and visibly stale; it must not fabricate
completion. Demonstrate recovery from worker restart and duplicate delivery. Name the actual
schedule invocation target and execution role in deployment instructions.

Before provisioning, estimate AgentCore, queue, storage, logs and model charges using current
AWS pricing; ask for any spending beyond existing authorization only after the deployment
configuration is concrete. If funded deployment is unavailable, mark cloud acceptance as
blocked and present the real local architecture honestly. Do not silently remove this target
or claim a static page satisfies cloud autonomy.

### Evaluation depth

Target 20–30 frozen holdout cases across multiple compatible repositories, separate from
development. Keep the same-model single-attempt versus repair contrast; add an execution-
feedback-disabled arm to isolate feedback from extra inference opportunity, with matched
attempt/token limits where possible and differences disclosed. Distinguish retrieval,
repair and budget effects instead of calling every difference an SDK improvement.

Repeat successful base/fixed differentials at least three times in fresh environments;
report unstable outcomes separately. Include assertion relevance review so a passing patch
differential does not disguise a test of unrelated behavior. Negative controls include
valid no-bug inputs, unrelated exceptions, environment failures, and adversarial issue text.
Report empirical false alerts only on the explicitly adjudicated negative set, with its
size and limitations; never infer population false-positive rate from known bugs.

Retain the 30 real-issue study, with greater rigor: preserve pre-resolution text and pinned
revision, exclude maintainer resolutions from agent context, define labeling criteria before
running, record adjudicator disagreement and unknown cases, and have a second reviewer label
without seeing the agent verdict. Report this as contextual agreement on a selected sample,
not independent definitive bug truth. Do not pool it with the gold-scored benchmark.

The Sonnet comparison remains conditional on explicit model/spend authorization. If it is
not authorized, publish no invented arm. Calculate required tokens and executions for all
arms before launching; the current $2 limit may prevent the full matrix even with more help.
Keep that resource gap visible rather than reducing scope without discussion.

### Product and impact depth

Show candidate review, missing-information decisions, environment failure and deferred queue
recovery as complete workflows. Every decision names the requested action and why the agent
could not complete it. Queue age, provenance and attempted steps prevent silence from hiding
unresolved reports. Confidence remains qualitative/unvalidated unless calibration is measured.

Prepare an observed task comparing raw issue investigation with receipt-assisted review:
record time, correctness, usefulness and whether the reviewer would actually use the script.
Seek several independent maintainer/developer reviewers through Ashraf's contacts; no agent
outreach without authorization. Publish sample size and negative feedback, and avoid claiming
adoption from a fork demonstration. This is a full-scope evidence target, not a prerequisite
for pretending benefit has already been shown.

### One project versus several

Keep one integrated Understudy submission. Multiple substantially different entries are
allowed, but variants of this agent do not qualify as a diversification strategy. Consider a
second project only if an independent team already owns a genuinely different strong idea,
can supply its own complete evidence and demo, and does not consume Understudy's integration
or review capacity. Available help should first deepen this project's accepted workstreams.

## Prelaunch resource worksheet

Populate measured token averages and current prices before running this full matrix. Let H
be 20–30 holdout cases, R=30 real cases and S the observed number of successful final scripts.
These are conservative upper bounds before shared attempts/caching, not a spending estimate.

| Arm | Cases | Maximum generated scripts | Generation executions | Final differential executions | Owner |
|---|---|---|---|---|---|
| Single attempt | H | H | H | 2H | Evaluation |
| Repair | H | 3H | 3H | 2H | Evaluation |
| No feedback, matched attempts | H | 3H | 3H | 2H | Evaluation |
| Source-access contrast | Predeclared subset Q | 3Q | 3Q | 2Q | Evaluation |
| Real contextual study | R | 3R | 3R | Only cases with a legitimate withheld patch | Evaluation |
| Stability confirmation | S | 0 | 0 | 4S additional for three total pairs | Execution |

For each row add measured input/output tokens per attempt, price date, upper-bound dollar
reservation, runtime, cache-sharing rule and actual spend. Record fixed cloud charges and
usage estimates separately. Reserve retries explicitly. Stop launches that exceed current
authorization and present the concrete resource gap; do not silently omit a required arm.

## Judge-objection closure work — J1–J12

COMPETITION.md contains the authoritative objection register. These additions preserve the
full-depth scope and extend existing streams; they do not introduce another project.

1. Evaluation owns a predeclared product comparator: the existing same-model single-attempt
   script output plus a deterministic daily digest. Full Understudy uses the same input cases
   and permitted information. Run an equal-compute comparison where possible and the actual
   full-budget configuration separately; disclose unmatched tokens/attempts. Compare useful
   artifacts and human review outcomes as well as gold yield. Add no new framework or model.
2. Policy owns a separate equal-notification comparison. Give both policies identical candidate
   results so generation quality cannot confound routing. A notification with many items can
   still impose large attention cost: record items read and active review time. An interruption
   is one proactive delivery, not one solved issue or one viewed item. A daily digest is a real
   competing design; the budget policy must earn its complexity through measured benefit.
3. Product owns a receipt handoff test: a helper downloads the immutable script, reproduces its
   execution in the documented environment and identifies the warranted next action without
   author coaching. Persist reviewed/deferred state and issue-version identity. If added
   environment information causes another run, start a separately identified input version;
   never overwrite original evidence. Human resolution is not confirmation by the gold scorer.
4. Evidence owner prepares three independent reviewer sessions with two matched tasks each,
   counterbalanced across baseline and receipt-assisted conditions. Capture correctness,
   accepted script, investigation time, missing information and objections. Record invitations
   and completions separately. Ashraf handles recruitment/authorization; no external messages
   are authorized by this document. Failed recruitment stays an evidence gap.
5. Reproduction owner runs a fresh-input challenge after configuration freeze. Use an authorized
   new issue or a separately authored undisclosed real defect case, and label its provenance.
   Do not imply a seeded issue is organic usage. The agent sees neither the answer nor later
   resolution. Evaluate assertion relevance without pretending a gold patch exists.
6. Execution/integration owners record an unattended multi-issue session with one injected,
   disclosed worker outage, recovery and duplicate delivery. Include all manual interventions,
   environment incompatibilities and pending cases in the session report. A successful queue
   replay alone does not establish that the actual deployed worker recovered.
7. Presentation owner builds an evidence index in the eventual README: claim → video timestamp
   → run/artifact → relevant source/test → limitation. Test the actual video with cold viewers;
   ask them to state the audience, completed work, distinction from a basic agent and one
   limitation. Log misunderstandings and revise the presentation, not just the answer sheet.
8. Before final recording, independent helpers review J1–J12 as PASS/FAIL/UNKNOWN. Link proof
   for every pass. Resolve disagreements in writing. Missing evidence remains visible in the
   submission; no self-awarded readiness score or invented win probability.

Deliverables: `evidence/comparator-protocol.md`, `evidence/reviewer-protocol.md`,
`evidence/reviewer-observations.json`, `evidence/unattended-session.json`,
`evidence/judge-objections.md`, and the README evidence index. These are planned paths,
not files that currently contain study results. Add generation/token costs for the fresh case
and any comparator runs to the resource worksheet before launching them.

### Final review additions: timeliness and stale evidence

Before the equal-notification study, have reviewers label which items require a human
choice and an acceptable response window, without seeing either policy's output. Report
useful decisions delivered late as well as fewer notifications. If arrival volume exceeds
five actionable items per day, no scheduling policy can guarantee prompt delivery for all;
show this backlog condition plainly and keep pull access available.

Bind every receipt to both issue version and source revision. When either changes, show
“Evidence for an earlier revision” on the old receipt and link its successor run. Never
silently retarget an old success to current code. Acceptance: change the watched revision
after a completed run, ingest the update, and verify old/new provenance, stale-state display,
new scheduling and deduplication across repeated polls. Include this in deployed integration
and product checks, not just JSON fixtures.

## Competitive execution assignments

Use the priority list in COMPETITION.md. At the next team handoff assign real names to these
four responsibilities; current role labels must not be mistaken for committed staffing:

| Responsibility | Immediate artifact | Completion evidence |
|---|---|---|
| Integration owner | Shared run command and first integrated receipt | Another helper runs the command; boundary failures recorded |
| Pilot/evidence owner | Compatible maintainer candidate and task protocol | Consented observation; useful artifact and repeat-use decision if obtained |
| Presentation owner | Opening/receipt story and comparative mock-judging packet | Independent preferences, reasons and revisions based on actual materials |
| Publication owner | Three Builder post outlines linked to implemented evidence | Public URLs verified and entered in submission before deadline |

Use existing evidence files for pilot observations and mock-judge findings. A repeat-use
request is stronger demand evidence but does not replace the controlled reviewer study.
Record unsuccessful recruitment and negative feedback. External contact and publication
still require the user's applicable authorization; this planning task sends or publishes
nothing. Submission checks verify the same frozen run IDs and claims across README, video,
Devpost and Builder posts so different surfaces cannot quietly contradict one another.
