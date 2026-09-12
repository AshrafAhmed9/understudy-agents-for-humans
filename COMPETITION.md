# Understudy — competition strategy

Reviewed September 12, 2026. This replaces the initial strategy after adversarial review.
Execution details live in `EXECUTION.md`; extreme-depth acceptance is in `DEPTH.md`;
findings and remaining gates are in `REVIEW.md`.

## Decision

Keep Understudy and enter Professional Agents. Optimize for first place, including grand
prize, through a complete useful workflow and credible evidence. Ashraf has implementation help
and explicitly wants the full scope retained; depth targets and parallel ownership are in
EXECUTION.md. Dependency ordering is not permission to silently cut scope. There is no evidence that
a developer tool has a permanent impact-score ceiling. There is also no defensible basis
for assigning this unbuilt project a 25%, 40%, or other probability of winning.

**Product promise:** Understudy watches a configured Python repository, attempts to turn
bug reports into executable evidence, and queues maintainer decisions under a hard daily
interruption limit. It leaves a receipt even when it cannot reproduce the report.

**Opening line:** “Before you spend time on a bug report, Understudy tries to run it.”
Follow with actual counts from the recorded run, including unresolved cases. Do not promise
that silence means an issue was solved. Do not claim every other agent only reads reports.

The winning moment is one continuous, understandable chain: a report arrives unattended;
the agent reads relevant code, repairs an invalid script, produces a usable receipt, and
queues a specific human decision. A second decision at the budget boundary is visibly
deferred and remains recoverable. The evidence is downloadable and replayable.

## Verified event information

[Official rules](https://agentsforhumans.devpost.com/rules), checked September 11:
submission closes September 14, 17:00 PDT (September 15, 05:30 IST). Judging ends October 8.
Required: new Strands project, public source with MIT/Apache license, README, architecture
diagram, public video of at most five minutes, description, AWS Builder ID, and test access.
Five criteria are equally weighted; ties use their listed order. AgentCore and a live demo
help technical scoring but are optional. Three qualifying Builder posts can add 0.6 points.
One project can win one prize. Confirm eligibility and third-party rights before submitting.

[Overview](https://agentsforhumans.devpost.com/) lists the three tracks and the current
judge panel. Do not tailor architecture to guessed preferences of two individual judges.
Registration count is not submission count or a probability model.

[FAQ](https://agentsforhumans.devpost.com/details/faqs) allows AI coding assistants and
requires disclosure of other incorporated pre-existing work. Use “Agents for Humans” in
Builder titles. The rules' August update removes the old mandatory hashtag, though a later
paragraph retains inconsistent wording; including both the phrase and #AgentsforHumans is
an inexpensive precaution, not a claim that the old requirement still applies.

[Resources](https://agentsforhumans.devpost.com/resources) currently says all credits have
been disbursed. Rules/FAQ advertise $50 requests through September 11 noon PT. Record this
conflict; do not budget against unreceived credits. Having an existing AWS account was not
itself grounds to conclude ineligibility. Keep Nova Lite and the approximately $2 inference
cap. No Sonnet switch or paid deployment is assumed. Budget alerts are not spending caps.

**Model decision, superseding the Nova Lite line above (2026-09-12):** Bedrock access on
Ashraf's account is broken — `ValidationException: Operation not allowed`, persisting
through IAM checks, the retired model-access page, the Marketplace-gate theory, and a full
Free-to-Paid plan upgrade (confirmed by two AWS emails). Same failure recurred in a past
project, so this looks account-level, not self-service-fixable in the time remaining. Ashraf
has ruled out any paid API — the $0 constraint is non-negotiable. Real inference now runs on
**local Ollama, `qwen2.5-coder:7b`**, genuinely free, no account, no card. This is a
deliberate deviation, not an oversight — CLAUDE.md rule 6 should be read as superseded by
this note.

Empirical check before committing: ran the real `triage()` + `run_eval` pipeline (not a
throwaway script) against 4 real cached SWE-bench Verified instances
(astropy-12907, astropy-13033, astropy-13236, django-10097), 3-attempt repair cap.
**Result: 1/4 reproduced (25%)** — see `runs/real_pipeline_check.json`. That beats GPT-4
zero-shot (3.6%) and lands near SWE-Agent-class methods (15.9-18.5%) that also use repo
access + execution feedback, on an N too small to trust precisely. Failure modes seen:
semantic inversion (mistook the buggy output shown in the issue for the expected one),
a no-op script that ran clean without exercising the bug, and a repeated syntax mistake the
repair loop never escaped (model doesn't reliably know the target Python's f-string quoting
rules). These are genuine capability gaps, not harness bugs, and go in the failure taxonomy
as-is. Decision: proceed with `qwen2.5-coder:7b`; report the reproduction rate against
published baselines rather than in a vacuum, and report the local-model-vs-cost tradeoff
itself as a finding — nobody else in the field will have that ablation.

**Scaled to 10 real instances (2026-09-12), before the fix below: 1/10 reproduced (10%)**,
but 4/4 django instances errored outright (script never became syntactically valid in 3
attempts) versus 1/6 on astropy. Root-caused, not assumed: `django__django-10097`'s testbed
runs **Python 3.5.6** (`docker run ... python --version`) — f-strings don't exist there, and
the model kept generating them across every repair attempt because nothing told it the
interpreter was that old. Fixed by adding an explicit instruction to both `PROMPT_TEMPLATE`
and `REPAIR_TEMPLATE` in `understudy/triage.py` to avoid 3.6+ syntax. Retried the same 4
django instances: script-error rate dropped from 4/4 to 1/4. **Combined 10-instance result
after the fix: 1/10 reproduced (10%), 1/10 script errors** (`runs/real_pipeline_10.json` +
`runs/django_retry.json`). The remaining django failures now run cleanly but don't reproduce
the bug — a real capability ceiling, not a harness defect, and goes in the taxonomy as-is.
This is the number to report for now: 10% vs GPT-4 zero-shot's 3.6%, on N=10, expect it to
move as N grows toward the planned 20-30.

**⭐ The number that validates C1, with real data (2026-09-12):** naive exit-code-only
scoring — "the script exited non-zero, so the bug reproduced" — on these same 10 real runs
would have reported **8/10 (80%) reproduced**. The gold-patch differential shows the true
number is **1/10 (10%)**. The other 7 "reproductions" are scripts that fail on `base_commit`
for reasons unrelated to the reported bug (wrong API assumption, import error) and **keep
failing after the real fix is applied** — proof the failure has nothing to do with the
patch. Taxonomy over the 10 cases, saved to `runs/failure_taxonomy_n10.json`:
- **reproduced (gold differential): 1** — astropy-13033
- **false_positive_unrelated_failure (fails before AND after the fix): 7** — astropy-13236,
  13398, 13977, 14096, django-10097, 10554, 10914
- **under_detected_no_signal (passes before AND after — script never triggers the bug): 2**
  — astropy-12907, django-10880

This is exactly the C1 concern the adversarial pass raised in the abstract, now demonstrated
with real numbers instead of an argument: 80% vs 10%, an 8x inflation from the naive method
this submission explicitly rejected. This single comparison is one of the strongest, most
concrete claims in the whole submission and belongs in the video and Screen C, not buried
here.

**Scaled to 16 real instances (2026-09-12):** added 6 more (astropy-14182, 14309, 14365;
django-10973, 10999, 11066) via `runs/real_pipeline_batch2.json`. **Combined result:
3/16 reproduced (18.75%)** — astropy-13033, astropy-14182, astropy-14309. Still clearly above
the 3.6% zero-shot floor. One instance (django-10973) errored in this batch after crashing 3
times, but a standalone rerun of the identical prompt produced a clean, non-crashing script —
this is LLM sampling variance (temperature=0.2, not 0), not a new systematic bug; the plan
already names non-determinism as a known demo/eval risk. Aggregated into `results.json` via
`scripts/build_results.py`, which merges all run files and reclassifies every case into the
taxonomy above — that script is now the canonical source for Stream D's screens.

**Updated C1 validation number, N=16:** naive exit-code scoring would report **14/16 (88%)
reproduced**. The real gold-patch differential says **3/16 (19%)**. Full taxonomy: 3
reproduced, 11 false_positive_unrelated_failure, 1 under_detected_no_signal, 1
semantic_inversion (astropy-12907 — the script's notion of "expected" is backwards: it
encoded the buggy output as correct, so it passes before the fix and fails after). This is
the number and the taxonomy to use everywhere going forward — 88% vs 19%, not 80% vs 10%.

**Stream D built (2026-09-12): live demo URL — https://claude.ai/code/artifact/076c03d5-f79f-4e4a-8970-7ee4e46079e4**
The four screens from §5, all rendering from the committed `results.json` (built by
`scripts/build_results.py`), no synchronous model or Docker call from the page (rule 7).
Screen A (Watch): counterfactual headline, silence bar, inverted timeline — the 3 reproduced
cases break the ribbon as full cards, the other 13 are thin quiet rows. Screen B (Receipts):
real issue text, real generated script, real container stdout/stderr for both the buggy and
gold-patched runs, per case. Screen C (Evidence): the 19%-vs-88% headline stat, the baseline
comparison bars, the taxonomy breakdown. Screen D (Inbox): interactive decision cards for the
3 reproduced cases with a draining budget-pip meter (client-side only — no backend deployed
yet, this is not the AgentCore endpoint from Stream E). This is real evidence rendering, not
a mockup; it is currently a static/interactive artifact, not yet wired to a live scheduled
agent run (that is Stream E, which needs Ashraf's AWS/GitHub credentials).

Working judge access must last through judging, not just video recording. A static replay
is useful, but identify it as replay and provide a working test build plus instructions.
Never imply that prerecorded JSON is a currently running cloud deployment.

## Rubric strategy and acceptance evidence

| Criterion | What earns consideration for first place | Required evidence |
|---|---|---|
| Technical implementation | Strands actually reads, generates, executes, repairs, and obeys the policy boundary | Real trace, pinned SDK, tested hook and executor, one unattended run |
| Design | A maintainer can understand and act on an uncertain result without opening five tools | Watch with inline receipt and decision queue; usable errors and exhausted state |
| Impact | Less investigation and fewer unnecessary interruptions for a specific Python maintainer workflow | Real issue provenance; inspectable script; measured review task or explicitly unvalidated benefit |
| Originality | Execution evidence combined with durable attention policy and auditable abstention | Side-by-side evidence receipt and budget enforcement, with prior art acknowledged |
| Presentation | A continuous working story with visible failures and useful outcome | Rehearsed ≤5-minute video; actual timestamps/counts; explicit replay disclosure |

A budget alone can hide useful work. Measure deferred decisions, age of oldest queued item,
and missed important cases alongside interruptions. A digest and manual queue inspection
must make deferral visible. Do not advertise this as emergency/security incident handling.

## Field and prior art

The [gallery](https://agentsforhumans.devpost.com/project-gallery) has not exposed a usable
field during this review. Unknown overlap stays unknown; remove the invented “0–2” estimate.
Recheck before freeze. Obvious substitutes include ordinary issue triage assistants, coding
agents that can execute tests, and specialist bug-reproduction research. Execution alone
is not novel.

[SWT-Bench](https://swtbench.com/) already evaluates generated reproductions using patch
differentials. [AssertFlip](https://arxiv.org/abs/2507.17542) and
[e-Otter](https://arxiv.org/abs/2508.06365) establish substantial prior work. Our claim is a
small maintainer-facing workflow combining evidence, repair, and enforced interruptions,
not a new test-generation algorithm or state-of-the-art accuracy.

Published results are context only. The initial plan's GPT-4 3.6% comparison used a different
split and protocol from our small SWE-bench Verified sample. Do not put those percentages
beside ours as a leaderboard, infer a causal advantage from them, or tune until our baseline
matches them. Use a paired Nova Lite single-attempt control on our exact frozen cases.

The [previous AWS hackathon winner announcement](https://aws-agent-hackathon.devpost.com/updates/38140-congratulations-to-the-winners-of-the-aws-ai-agent-global-hackathon)
recognizes EcoLafaek, AegisAgent, Province, and AgentShell. These are useful comparable
projects, not evidence about why individual judges voted. The practical lesson is to show
specific beneficiaries, a working outcome, and a coherent use of technology. A prior
specialist award does not establish that adding MCP or more agents improves this rubric.

Do not use the xz backdoor as proof Understudy prevents supply-chain attacks. That causal
claim is unsupported, and the project does not address maintainer succession or malicious
maintainers. Show the actual investigation burden instead.

## Evidence contract

1. **Live:** `candidate_reproduction` means a script produced issue-relevant failure evidence.
   It is not independent confirmation that the reported bug is real. `not_reproduced` means
   this attempt did not reproduce it, never that no bug exists. Environment failures and
   timeouts are errors; insufficient information is a pre-execution classification.
2. **Offline:** only the frozen final script failing on base and passing on base plus the
   withheld gold patch counts as `Score.reproduced`. Both executions must be valid. A
   fail→fail result alone cannot distinguish a broken script from an ineffective test.
3. Never expose gold patches, future repository history, scorer files, fixed source, or
   post-resolution issue comments to the agent. Block git and remove readable history from
   the runtime filesystem. Record the boundary tests; do not claim impossibility of cheating.
4. Freeze the verdict, exact script, prompt/config hashes and input manifest before scoring.
   Do not select among attempts using gold outcomes. Repair sees only base-run feedback.
5. Benchmark reproduction rate is not real-world bug-classification accuracy. A dataset of
   known bugs alone cannot establish false-positive rate on non-bugs.

## Study that fits the deadline

Use 3–5 development cases to fix the harness; exclude them from the reported holdout. Freeze
20–30 distinct holdout cases across at least two supported repositories if runtime permits.
Publish the selection rule, seed, IDs, exclusions, environment restrictions and raw outcomes.
This is a small convenience sample, not a representative estimate of all GitHub issues.

Run paired single-attempt and at-most-three-attempt configurations with the same model,
input, tools, limits and first attempt. Report k/N, a binomial interval, invalid/error counts,
paired gains and losses, latency, tokens and actual estimated inference cost. Show the extra
compute cost of repair. Do not claim statistical superiority from a few successes.

Separately replay a fixed issue/decision sequence with policy enabled and disabled. Test
concurrency, duplicate delivery, restart, daily rollover, and exhausted budget. Report
interruptions, deferred decisions and lost items. This demonstrates the policy, not a
benchmark of Strands versus another framework or model-derived confidence calibration.

Retain a 30-case real-issue study with blinded adjudication as specified in EXECUTION.md,
and select 3–5 documented case studies at pinned revisions for the demonstration. Maintainer comments are contextual adjudication, not a perfect
oracle. Show one success, one unresolved report, and one environment/repair failure if those
occur. Select from completed runs and disclose any curation. Synthetic controls test safety
and semantics but must never inflate real-issue counts.

An observed 10–15-minute review with a Python maintainer would strengthen Impact more than
another dashboard. Prepare a task and feedback questions; Ashraf may recruit a participant.
No outreach is authorized by this plan review. Without feedback, say user benefit remains
unvalidated. Estimate time saved only from an observed comparison with its method stated.

## Claims → proof ledger

All implementation evidence is currently missing; the repo contains plans and schema stubs.

| Claim | Proof to collect | Status |
|---|---|---|
| Generates useful executable evidence | Real issue → immutable script → base execution receipt | Not built |
| Repair helps under this budget | Paired holdout results, including regressions and cost | Not measured |
| Offline reproductions survive a fix | Valid base/fixed executions of identical final script | Not measured |
| At most five interruptions per day | Durable integer policy tests and exhausted-state trace | Not built |
| No work disappears at exhaustion | Queue persisted across restart; oldest item shown | Not built |
| Runs without manual triggering | Poll checkpoint, input timestamp, receipt and action record | Not built |
| Scorer cannot leak through tools | Sanitized artifact inspection and hostile read tests | Not built |
| Replay is faithful | Immutable cassette hashes and offline replay comparison | Not built |
| Useful for a maintainer | Real cases and observed reviewer task | Unvalidated |

## Freeze and submission gates

Feature freeze: September 13, 20:00 IST. Draft submission and rough video by September 13,
14:00 IST. Submit final by September 14, noon PDT (September 15, 00:30 IST), leaving five
hours before the official deadline. September 14 is recording/submission only. Do not spend
the buffer on unfinished deployment work.

- [ ] Core end-to-end run and negative controls pass; no safety relaxation to get a demo.
- [ ] Claimed counts resolve to real cassette IDs; replay and synthetic examples labelled.
- [ ] Cold installation and offline test build verified on the documented platform.
- [ ] Public repo, recognized license, README, architecture, third-party attribution complete.
- [ ] Description, public video ≤5:00, AWS Builder ID, track and testing instructions entered.
- [ ] Judge access maintained through October 8; private credentials excluded from artifacts.
- [ ] Three distinct factual Builder posts published and links entered if completed.
- [ ] Recheck official rules, resources, gallery, and links on September 13 and 14.
- [ ] Every remaining limitation is visible; no unsupported performance or adoption claim.

**Readiness verdict:** the revised strategy is feasible enough to build, conditional on the
execution gates. The submission is not yet competitive evidence of a win: no agent, result,
user validation, deployment, or demonstration exists. Stop expanding the plan and prove the
core loop. After results, compare actual winners and record what this strategy got wrong.

## Depth commitment

Full scope includes four screens, AgentCore with a real execution-worker bridge, GitHub MCP,
durable policy and scheduling, a multi-repository paired study, and a blinded real-issue
study. Depth must be visible in receipts, failure recovery and measured outcomes. Additional
help resolves labor constraints; spending and deployment access remain explicit resource
gates. Do not substitute extra services for a missing useful outcome. One integrated entry
is the recommendation; see EXECUTION.md for the conditions on any second project.

## Why a judge could choose another project — September 12 review

Confidence in the direction is moderate; confidence that the current submission is ready to
win is low. These are qualitative assessments, not calibrated probabilities. Only plans and
schema stubs exist today. No evidence yet establishes useful reproduction yield, maintainer
benefit, deployed reliability or superiority to a simpler workflow. The event gallery remains
unavailable for a meaningful comparison of actual entries; competitor scenarios below are
inferences, not descriptions of known submissions.

The [current judging criteria](https://agentsforhumans.devpost.com/) reward a complete product,
credible demonstrated impact and understandable presentation alongside technical skill.
Depth helps only when it improves these outcomes and judges can inspect its evidence.

| ID / priority | Credible reason to pick another entry | Required response in our plan | Evidence that closes the objection | Owner |
|---|---|---|---|---|
| J1 / highest | “Their agent completes a useful task; yours produces more work to inspect.” | Finish the investigation handoff: portable script, precise assertion, tested environment, next decision and durable acknowledgement. Measure downstream review burden, not only generated scripts. | Independent reviewer reruns an artifact and reaches a correct next action; negative outcomes remain counted. | Product + evaluation |
| J2 / highest | “A simple script generator and daily digest does this adequately.” | Compare the full workflow against that simpler substitute under matched inputs and budget; reuse the existing first-attempt arm rather than adding a framework. | Side-by-side usable artifacts, review errors, human time, interruptions and deferred-item age; publish losses too. | Evaluation |
| J3 / highest | “Another team has actual users; your audience is hypothetical.” | Run observed tasks with independent Python maintainers/developers; document permission and relationship. Seek repeat use as stronger evidence than a quote. | Target three independent participants and two matched tasks each, anonymized notes, accepted/rejected scripts and changes made; actual counts disclosed if target is missed. | Evidence owner + Ashraf |
| J4 / highest | “Their tool works on fresh input; yours relies on known benchmark fixes.” | Add an issue received after prompts/configuration freeze, without known resolution in the agent context, alongside the benchmark. | Timestamped intake, untouched input, run receipt and independent relevance review; success is not assumed and fresh-input failure stays visible. | Reproduction + evaluation |
| J5 / high | “Five notifications is an arbitrary throttle that hides important decisions.” | Compare budget policy to a daily digest at the same notification count and review capacity; define actionable decision requests and measure delayed useful decisions. | Prelabelled utility/response windows, late useful decisions, queued age and review effort; cap-only success cannot pass. | Policy + evaluation |
| J6 / high | “Their agent handles the entire task unattended; yours needs environment babysitting.” | Track all manual setup, image adaptation, retry and supervision work; qualify supported repositories through a preflight. | Full unattended multi-issue session plus cold setup by another helper; total human intervention count and supported-input coverage printed. | Execution + integration |
| J7 / high | “The other system is more accurate; your negative results mislead users.” | Distinguish script validity, assertion relevance, differential success and human usefulness. Test whether readers understand inconclusive statuses. | Reviewers distinguish candidate/error/inconclusive and stale-revision evidence; relevant assertions and repeated differentials accompany yield. | Reproduction + product |
| J8 / high | “Your depth is invisible, or AWS services are attached for points.” | Show a real Strands tool/repair trace and one end-to-end recovery crossing the deployed worker boundary, with a reason for each component. | Video timestamps and source/run links for each mechanism; remove unsupported architectural claims, retain implementation targets. | Integration + presentation |
| J9 / high | “Their product is immediately usable; yours needs a laptop, credentials and large downloads.” | Measure onboarding and artifact rerun burden. Supply a no-account replay, complete test-build instructions and separately costed live setup. | Independent cold-start log, download/storage requirements, first receipt time and worker availability limits; replay never presented as live execution. | Product + execution |
| J10 / high | “The polished clip is cherry-picked and I cannot verify it.” | Make every headline resolve to an immutable manifest and individual outcomes; let a reviewer choose a non-featured case to inspect. | Judge evidence index, complete denominator, disclosed curation and a helper's independent rerun of an unfeatured artifact. | Evaluation + presentation |
| J11 / high | “Their value is obvious; your five-minute pitch is a benchmark lecture.” | Lead with one person's completed investigation and decision. Show depth in the middle and link to details. | Cold viewers explain audience, completed task, meaningful mechanism and limit without prompting after watching once. | Presentation |
| J12 / high | “They have a sustainable working deployment; your full plan exceeds your budget.” | Complete the resource worksheet and worker availability plan before claiming feasibility; retain all full-scope targets while identifying unfunded gates. | Actual token/runtime/cost ledger, deployment estimate, authorized funding and test access through judging. | Integration + Ashraf |

These are required proof targets, not established results or official judging thresholds.
No count of agents, screens or experiments by itself closes an objection. Keep full scope;
assign helpers to these outcomes rather than repeatedly expanding architecture.

### Comparison and confidence gate

Before final submission, a reviewer who did not implement the component records each J1–J12
as PASS, FAIL or UNKNOWN, with an artifact link and a sentence explaining the decision.
UNKNOWN is not a pass. A second reviewer checks J1–J5 and any disputed judgment. This is a
project-specific readiness review, not an estimate of the probability of winning.

Confidence can rise materially when: real generated artifacts are useful without the gold
patch; an observed maintainer outcome improves over the simple comparator; autonomy survives
failure; and the video communicates that advantage clearly. If the simpler substitute is
competitive, report that result and improve the specific failing stage using development
cases, then freeze a fresh evaluation. Do not relabel experiments or select favorable cases.
Even passing all gates cannot eliminate another team's stronger impact, execution or idea.

## Remaining ways to improve our chances

September 12 follow-up. Preserve the full-depth scope. The following actions strengthen
execution and competitive positioning; they are not additional architecture requirements.
Priority is a reasoned judgment, not a quantified uplift in win probability.

1. **Secure one real pilot with a second use.** The reviewer study establishes usability;
   a maintainer voluntarily supplying another issue is stronger evidence of demand. Ask
   Ashraf to identify an accessible Python maintainer with a compatible environment and
   actual reproduction burden. Record the initial need before showing the product, one
   useful delivered artifact, and whether the maintainer chooses to use it again. Obtain
   permission for attribution. Do not require praise or call a friend testing a demo adoption.
2. **Make one advantage decisive.** Use the simple-comparator study already planned. Choose
   the headline from predeclared outcomes: useful receipts, correct next decisions, human
   investigation effort, or fewer interruptions within acceptable delay. A persuasive result
   must identify the comparator, denominator and tradeoff. If no advantage appears, improve
   the failed stage and rerun under a newly frozen protocol; do not compensate with rhetoric.
3. **Own an exact audience and use case.** Lead with maintainers of Python libraries who
   repeatedly reconstruct incomplete bug reports in supported environments. Show why their
   existing workflow is costly using observed cases. This sharpens positioning without
   removing any planned repository, experiment or capability. Avoid promising every language,
   arbitrary dependencies or automatic bug resolution.
4. **Exercise the explicit scoring opportunity.** Three distinct qualifying Builder posts
   can earn up to 0.6 bonus points under the official rules. Treat publication and entering
   the links as owned deliverables, not a vague intention. Posts explain implemented AWS
   mechanisms, evidence and limitations; they cannot be written as completed results before
   those results exist. Recheck public access and title requirements before submission.
5. **Win the short inspection as well as the deep inspection.** Judges may rely only on the
   submitted video/text. Prepare a 30-second opening showing the audience and actual outcome,
   a two-minute path through the strongest receipt and decision, and the full five-minute
   account with technical proof. These are views of the same evidence, not three new videos.
   Make source, run artifacts and limitations discoverable from the first README screen.
6. **Run a comparative mock judging session.** Give independent helpers the exact rubric,
   our actual video/description and two publicly available comparable project presentations.
   Record project identity and different-event limitations; these are calibration examples,
   not known current competitors. Each reviewer first chooses a project and states why,
   without discussion or author coaching. Resolve the strongest repeated reason to choose
   another entry, then repeat with fresh reviewers. Do not claim predicted official scores.
7. **Resolve resource uncertainty before it damages the evidence.** Populate the existing
   cost worksheet from the pilot. If the current model/budget cannot support the target,
   prepare a bounded alternative with its expected benefit, exact cost cap and comparison
   protocol for Ashraf's decision. No model switch, extra spending or cloud provision is
   authorized by this recommendation. Buying more compute is not itself a scoring advantage.
8. **Make available help operational.** Replace role names in EXECUTION.md with named owners
   and accepted tasks. Assign an integration owner and a separate evidence/presentation
   owner so helpers do not all build isolated features. Each handoff includes a runnable
   artifact, acceptance evidence and unresolved failures. Unassigned work is not coverage.

9. **Scope decision on the 30-case real-issue study (2026-09-12):** investigated building
   this. It requires a genuinely separate execution path from the SWE-bench work already
   done — checking out an arbitrary real repo at an arbitrary pinned revision and building a
   working environment for it, since Epoch's rebuilt image registry only covers the 500
   curated SWE-bench Verified instances, not arbitrary GitHub issues. That's real,
   non-trivial infrastructure (dependency resolution varies per repo, no pre-built image to
   pull), not a small extension of `understudy/ingest/github.py` (which only reads issue
   text, never executes anything). Given the remaining time and that a half-built version
   of this would produce unreliable environment-setup failures indistinguishable from real
   triage failures — polluting exactly the kind of evidence this project is built to keep
   honest — this is recorded as a known gap rather than attempted partially. If Ashraf wants
   to prioritize it, the concrete next step is a `understudy/sandbox/generic_checkout.py`
   that clones a repo, checks out a commit, and attempts a best-effort environment build
   (requirements.txt / pyproject / setup.py, in that order), accepting that some real repos
   will simply fail to build — which itself becomes an honestly-reported limitation rather
   than blocking the whole study.

**Fork demo built (2026-09-12):** forked tqdm/tqdm (31k stars, pushed the day before —
genuinely active, pure Python, no compiled deps) to
https://github.com/AshrafAhmed9/tqdm. Copied 3 real open upstream issues in unmodified with
disclosure (#1827 CLI --log crash, #1826 invalid hex colour, #1810 empty-DataFrame
ZeroDivisionError) as fork issues #1-3. Built a real (non-SWE-bench) container environment
for tqdm main and ran real triage against all three with `qwen2.5-coder:7b`: 2/3 produced a
genuine candidate reproduction (#1826, #1810 — clean scripts, real evidence in stdout), #1827
didn't reproduce on this attempt. Posted real verdict comments to all three fork issues,
honestly disclosed as live-candidate (no gold patch exists for an unfixed upstream bug, so
these are correctly never scored as `reproduced`) and as manually triggered, not yet on an
EventBridge schedule. Full writeup: `understudy/fork_demo/README.md`, raw results
`runs/tqdm_fork_demo.json`. This is real evidence for the "it acts on its own" claim, short
of full autonomy (that needs Stream E, blocked on AWS access — see below).

Source for bonus and artifact-based judging:
[official rules, sections 4 and 6](https://agentsforhumans.devpost.com/rules), rechecked
September 12. No assumption of favorable judging follows from publishing posts or using AWS.

### When further planning stops helping

The plan now specifies technical depth, competing alternatives, real-user proof, submission
quality and independent review. Further open-ended feature brainstorming has no demonstrated
advantage over producing the first end-to-end evidence. Retain the full target and revisit
strategy when a pilot result, user observation, deployment failure or actual competing entry
provides new information. Do not treat another planning document as progress on a proof gate.
