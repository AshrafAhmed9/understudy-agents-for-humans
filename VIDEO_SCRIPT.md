# Video script — 5:00 max

Recorded from the live demo (https://claude.ai/code/artifact/076c03d5-f79f-4e4a-8970-7ee4e46079e4)
and real run data (`results.json`, `runs/*.json`). All numbers below are real, not
placeholders — pulled from the 16-instance run on 2026-09-12. Update them if the eval scales
further before recording.

Still needed before this can be recorded: pick which screen capture to use for the "it acts
on its own" beat (needs the fork + live posting from Stream E, not yet deployed) — if that
isn't ready by freeze, cut 2:10–3:00 down to the architecture point only and redistribute
time to the evidence section, which has the strongest real numbers in the project.

---

**0:00–0:25 — Open on Screen A (the Watch), live cursor idle.**

> "37 issues triaged. You were interrupted twice." — no, say the real one: "16 issues
> triaged. You were interrupted [N]." [fill N from current escalations.length in the demo —
> currently 3, one per reproduced case]
>
> 44% of maintainers who leave open source cite burnout. In March 2024, a backdoor came
> within days of reaching nearly every Linux server on earth — the attack vector was a
> single exhausted maintainer. This isn't a productivity tool. It's triage for the people
> everything else depends on.

**0:25–1:10 — The thesis.**

> The agent has a fixed daily allowance for bothering you. [Point at the pip meter.] Five
> pips. Spending one isn't a vibe — it costs a confirmed reproduction, not a guess. [Click
> into Screen D, show a decision card resolving, pip draining.] When the budget's gone, it
> queues instead of paging you. This is enforced in code — a hook on every tool call, not a
> prompt asking nicely.

**1:10–2:10 — Why its confidence is trustworthy: it runs the bug.**

> [Screen B, pick the astropy-13033 receipt — the one real reproduction.] Issue text in,
> real generated script, real container stdout. [Show the buggy-run output vs. the
> gold-patch run output side by side.] Fails before the fix, passes after — that's the only
> thing this project calls "reproduced."
>
> And here's why that check exists. [Cut to Screen C.] If we'd trusted a script just exiting
> non-zero — which is what naive scoring does — we'd be telling you 88% of these are real
> bugs. They're not. The real number, checked against the dataset's actual fix, is 19%.
> That's not a caveat, that's the headline: an 88%-vs-19% gap is exactly why "the script
> crashed" and "the bug is real" cannot be treated as the same signal.

**2:10–3:00 — It acts on its own.** *(Pending Stream E deployment)*

> [If deployed: real posted comment on the fork, timestamp, nobody watching.] [If not
> deployed by freeze: cut this beat, redirect to a longer walk through the failure taxonomy
> on Screen C instead — false positives, the one semantic inversion, why each happened.]

**3:00–3:40 — Architecture.**

> Strands Agent with a policy hook doing two jobs at once: gating the interruption budget,
> and blocking `git` outright so the agent can never read the fix commit sitting in its own
> checked-out repo. Local inference — qwen2.5-coder, 7 billion parameters, zero cost, because
> the alternative was a cloud model this project explicitly isn't paying for. Full lockdown
> sandbox for anything the agent writes: no network, read-only filesystem, a host-enforced
> kill switch.

**3:40–4:40 — The study.**

> Sixteen real SWE-bench Verified instances. 19% reproduced by the differential, against a
> published GPT-4 zero-shot floor of 3.6%. [Show the baseline comparison bars on Screen C.]
> Failure taxonomy, not a black box: eleven false positives — scripts broken for reasons that
> had nothing to do with the bug, and we know that because they're still broken after the
> real fix. One inverted case, where the script's idea of "correct" was actually the bug.
> One case where nothing detected anything at all. Every one of these is on screen, not
> buried in a log.

**4:40–5:00 — Limits, what's next, close.**

> This is 16 instances, not 500 — a convenience sample, stated as one. It's a local 7B model,
> not a frontier one, by necessity, not preference. What's next: scale the eval, deploy the
> live posting loop, and see if a bigger local model changes the number without changing the
> budget. [Close on Screen D's exhausted-budget state, or the closest real equivalent.]
