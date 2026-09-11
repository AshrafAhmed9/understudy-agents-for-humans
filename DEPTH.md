# Understudy — depth specification and proof plan

This is the full target requested by Ashraf, not a claim about completed implementation.
Read with EXECUTION.md. Keep the product boundary: repo watching, executable bug evidence,
maintainer decisions and enforced interruptions. Do not add unrelated agent features.

## The hard question

A strong coding agent can already read an issue and run tests. Why use Understudy?

Because a maintainer needs an unattended, repeatable workflow with inspectable evidence,
known environment identity, explicit uncertainty, durable decisions and bounded interruption.
The project must demonstrate that entire chain, including failure recovery. Neither a novel
prompt nor a large stack establishes this advantage.

## Reproduction reasoning

Use a documented sequence: extract claimed behavior and required inputs; locate the relevant
entry point; inspect current tests and API usage; formulate an assertion connecting expected
and observed behavior; execute; classify failure; repair only from permitted base feedback;
freeze a final candidate and communicate its limits. The trace should expose these artifacts,
not private model reasoning or a fabricated narrative.

A useful script includes minimal input/setup, the relevant call, and an assertion whose
failure means the reported behavior was observed. Avoid checks of version strings, hardcoded
source text, implementation line numbers or incidental exception wording unless the issue
specifically concerns that behavior. These can exploit a patch differential without testing
the report. Review assertion relevance independently of the final score.

Cap all source retrieval and loop budgets. Record whether each repair fixes environment/API
usage, strengthens assertion relevance, or changes the test hypothesis. Do not optimize only
for a nonzero exit. Keep unresolved hypotheses visible; inability to reproduce is not a
resolution. Confidence is not a routing probability unless a calibration study supports it.

## Experiments and what they establish

| Experiment | Controlled contrast | Valid conclusion |
|---|---|---|
| Repair | One attempt versus three, same first attempt and inputs | Incremental yield and cost of the repair policy on this sample |
| Feedback | Three candidates with versus without execution feedback | Contribution of feedback, with sampling and token differences disclosed |
| Source access | Issue-only versus allowlisted source access on a predeclared subset | Sensitivity to retrieval, not proof about all repository agents |
| Attention policy | Identical decision requests, hook/dispatcher enforcement on versus off | Delivered/deferred counts and durable cap behavior |
| Stability | Fresh repeated base/fixed runs of successful candidates | Observed nondeterminism and reproducibility limits |
| Real-issue adjudication | Blinded agent output versus independent contextual labels | Agreement and disagreement on a selected messy sample |
| Maintainer task | Raw report versus receipt-assisted investigation | Observed task performance and usefulness for participating reviewers |

Freeze dataset manifests, prompts, model identity, sampling settings, tool bounds, environment
adapters and primary outcome before final runs. Revisions after seeing holdout results create
a new exploratory version; retain and report the earlier result. Share first attempts where
appropriate, not cached responses that alter an arm's intended information access.

Use all eligible scheduled cases in the primary denominator; show infrastructure failures
separately. Report valid-run-only yield as a secondary metric, with both denominators printed.
For each arm publish successes, errors, abstentions, unstable cases, median and tail latency,
input/output tokens and measured cost. Small N produces wide uncertainty: print k/N alongside
intervals. Avoid multiple-comparison superiority claims from exploratory ablations.

The current inference authorization is approximately $2. Build a cost worksheet with number
of cases, arms, attempts, retrieval tokens, output tokens, retries and scoring repetitions.
Use a small measured pilot to populate it. More helpers do not solve a funding gap. Complete
the experimental design now; launch additional funded arms only within explicit authorization.

## Evidence and artifact model

The minimal schema is not the entire cassette format. Version a JSON envelope with:

- Run identity, ingestion source, source revision, capture time, issue-body hash and consent/
  destination configuration where applicable.
- Model/provider configuration, prompt/tool hashes, image digest, environment adapter and
  every enforced limit.
- Ordered attempts with source references, exact script, content hash, execution provenance,
  setup result, exit/signal/timeout/OOM, bounded logs and truncation markers.
- Frozen live verdict and final candidate hash; independent scorer references only in offline
  results, never in the agent-visible record.
- Decision request, policy reason, queue position, reservation and delivery state, deduplication
  key, original timestamps, and recovery events.
- Estimated cost with pricing date and actual token counts; replay redaction information.

Store a content hash for each artifact and publish a manifest so a judge can trace an aggregate
to a script and execution. Hashes establish internal consistency, not independent attestation
that execution occurred. Supply runnable commands and a cold verification path for that.

## Reliability state machine

Jobs progress through discovered → queued → leased → executing → completed or failed.
Lease expiry permits retry of unfinished work, keyed to the same job identity. A completed
artifact wins over a duplicate worker result only under a deterministic reconciliation rule;
conflicting results are recorded, not overwritten silently. Issue edits create a new version.

Decisions progress through pending → reserved → dispatched → acknowledged/reviewed, or
pending → deferred when no slot exists. Delivery failure is distinct from a negative verdict.
An ambiguous dispatch remains reserved until reconciliation; never blindly retry an external
write. Exactly-once external delivery cannot be promised without destination support.

Test crashes immediately before/after artifact persistence, reservation, external dispatch
and acknowledgement. Verify the queue can recover without inventing a result or bypassing
the daily cap. Show stale worker status and the oldest unresolved decision in the product.

## Security acceptance matrix

| Attack or failure | Required behavior | Evidence |
|---|---|---|
| Issue asks to read a patch or ignore the cap | Tools remain scoped, action denied | Real blocked-tool trace |
| Source symlink traverses outside clean tree | Canonical-path read rejected | Fixture and tool test |
| Script reads git objects or scorer files | Artifacts absent/inaccessible | Runtime filesystem inspection and hostile script |
| Script accesses credentials or Docker socket | Neither mounted nor inherited | Environment/mount test with harmless sentinels |
| Script loops, forks or floods logs | Runtime, PID and output limits hold; container removed | Supervisor integration tests |
| Worker job alters image/flags/path | Schema/allowlist rejects it | Authenticated malformed-job test |
| Duplicate schedule or queue delivery | One logical run/action under idempotency key | Concurrent replay and ledger state |
| GitHub destination changes via prompt | Host allowlist prevents write | Tool authorization test |
| Public replay attempts live execution | No credentialed action path exists | Network-disabled playback and static deployment inspection |

Adversarial fixtures must be harmless bounded tests. Do not publish operational exploit
payloads as demonstration assets. Document the local-container threat model and residual
host-kernel risk without claiming perfect isolation or using a model guardrail as a boundary.

## Four product views

**Watch:** what arrived, what was attempted, what remains unresolved, worker freshness,
interruption usage and pending age. Distinguish completed investigation from solved bug.

**Receipt:** exact report and source revision, assertion, script, execution environment,
attempt diff and uncertainty. A maintainer can download and understand the artifact.

**Evidence:** inspectable experiment manifest, raw outcomes, controls, ablation cost and
limitations. Every chart/filter resolves to recorded rows; no decorative aggregate numbers.

**Decision Inbox:** a specific action requested, why automation stopped, delivery history,
and review/defer controls. Reviewing does not refund attention. In replay these controls
are explicitly local simulation; in the real application they persist through the worker.

Use a shared layout, typography and state vocabulary. Verify keyboard navigation, readable
tracebacks, long issue titles, empty/error/stale states, and a small screen. Coherence comes
from shared behavior as well as styling.

## Human-value study

Recruit through Ashraf, not unsolicited agent messages. Prepare matched tasks and counter-
balance ordering so familiarity with the same bug does not create fake time savings. Ask
reviewers to identify the next action and evaluate assertion relevance. Record task time,
correctness, confidence in the receipt, missing information and whether the script is useful.

Keep the raw task protocol and anonymized observations with consent. Report participant
experience, task count and selection limitations. A positive quote is not adoption. If nobody
participates, the study stays incomplete; replace the claim, not the missing evidence.

## Depth checkpoints

1. **Mechanism:** one generated script with legitimate issue relevance and a valid differential.
2. **Generalization:** held-out cases across more than one supported repository, with failures.
3. **Causality:** controlled experiments identify what retrieval and feedback contribute.
4. **Reliability:** restart, duplicate and resource-failure behavior demonstrated end to end.
5. **Integration:** deployed orchestration reaches the actual execution worker and produces a
   receipt under scoped credentials; any enabled external action is authorized and reconciled.
6. **Usefulness:** a maintainer can make a better-informed decision from the receipt.
7. **Communication:** five minutes shows the outcome; repo and evidence support deeper inspection.

An entry with several checked mechanisms but no useful maintainer outcome can still lose to
a stronger product. An attractive product with an invalid oracle can fail technical review.
First-place readiness requires both, not an arbitrary count of services, agents or pages.

## Competitive depth, beyond internal ablations

Use the J1–J12 register in COMPETITION.md as the final acceptance layer. Internal experiments
can explain how a system works while leaving unanswered whether anybody should use it.
The product comparator and equal-notification digest comparison are therefore separate from
repair/source-access ablations. A winning argument must connect implementation depth to
useful work completed, attention required and credible deployment behavior.

The following definitions prevent favorable but misleading aggregates:

- **Executable artifact:** the documented setup and script run; execution may legitimately fail.
- **Relevant candidate:** independent review finds the assertion tests the reported behavior.
- **Differential reproduction:** valid frozen-script fail→pass under the withheld patch protocol.
- **Useful receipt:** a reviewer can use the artifact to make a warranted next decision, with
  acceptance/rejection recorded independently of the differential result.
- **Completed investigation:** the scoped reproduction attempt and receipt are delivered; this
  does not imply the issue is fixed, closed, or a bug conclusively ruled out.
- **Human effort:** setup, supervision, receipt review and follow-up time, not just notification
  count. Report recurring and one-time costs separately.

Report these stages as a funnel with actual denominators, not interchangeable success labels.
Show supported-input coverage before the funnel so environment exclusions do not disappear.
A greater number of tests or stricter cap cannot compensate for worse useful-receipt yield.

Cold review acceptance includes correct interpretation of candidate/not-reproduced/error,
rerunning an unfeatured artifact, understanding the next action, and finding a failure outcome
from the results page. Collect observations rather than claiming usability from screenshots.
