# Video script — second-by-second, 5:00 max

Recorded from the live demo (https://claude.ai/code/artifact/076c03d5-f79f-4e4a-8970-7ee4e46079e4),
real run data (`results.json`, `runs/*.json`), and the real fork demo
(`runs/tqdm_fork_demo.json`, github.com/AshrafAhmed9/tqdm). Every number below is real —
pulled from the 16-instance SWE-bench run and the 3-issue tqdm fork demo, both dated
2026-09-12. If the eval scales further before recording, update the numbers, not the
structure or the timing.

**Format:** timecode, what's on screen, the caption to burn in (bottom-third, small,
non-intrusive), and the exact words to say. Timing was computed from real word counts at
~2.2 words/second — slower than conversational, because technical content needs the room —
and every segment below lands between 1.5 and 2.3 words/second. It sums to exactly 5:00.
Read it once at a natural pace with a stopwatch before recording; if a segment runs long,
that's a sign to cut a word, not to talk faster.

**Recording notes:**
- Screen at 1920×1080, live demo in a browser at 100% zoom, no bookmarks bar visible.
- Cursor moves deliberately — land on what you want the viewer looking at *before* you start
  the sentence about it, don't click-and-talk simultaneously.
- Captions are burned-in overlays, not spoken — add in post, bottom-third, ~28px, high
  contrast. They repeat the single most important phrase of each beat for anyone watching
  muted.
- Two prep items to have open in other tabs before you hit record, so you're not hunting for
  anything live: `github.com/AshrafAhmed9/tqdm/issues/2` scrolled to the posted verdict
  comment, and `diagrams/architecture.png` ready to go full-screen.

---

## 0:00–0:43 — Cold open, the thesis in one screen

| Time | On screen | Caption | Say |
|---|---|---|---|
| 0:00–0:05 | Live demo, Screen A (The Watch), already loaded, cursor still, nothing clicked | **Understudy** | "This is Understudy." |
| 0:05–0:15 | Cursor moves to and underlines the headline stat: "16 issues triaged. You were interrupted 3." | 16 triaged · interrupted 3 | "Sixteen real bug reports went through it. It interrupted a human three times — and only for the ones it could actually prove." |
| 0:15–0:30 | Cut to a plain black slide, white text, or hold on the Watch screen with a text overlay | 44% of maintainers who quit cite burnout | "Forty-four percent of maintainers who leave open source cite burnout. In March 2024 a backdoor came within days of reaching nearly every Linux server on earth — the way in was one exhausted maintainer." |
| 0:30–0:43 | Back to Screen A, cursor hovers the silence bar / quiet timeline rows | Triage for the people everything else depends on | "This isn't a productivity tool. It's triage for the people everything else depends on — before you spend an hour on a report, it tries to actually run the bug." |

## 0:43–1:24 — The interruption budget is enforced in code

| Time | On screen | Caption | Say |
|---|---|---|---|
| 0:43–0:51 | Cursor moves to the pip meter, top-right of the Watch screen | 5 pips/day · enforced in code | "It gets a fixed daily allowance for bothering you. Five pips. Not a suggestion — enforced." |
| 0:51–1:02 | Click into Screen D (Inbox), a real decision card visible (a reproduced case) | Spending a pip costs a confirmed reproduction | "Spending one isn't a vibe. It costs an actual confirmed reproduction, never a guess — you'll see exactly what that means in a second." |
| 1:02–1:16 | Click "Confirm & label" on the card, watch a pip visibly drain in the meter | Budget hook = `BeforeToolCallEvent` | "This is a hook on every tool call the agent makes — `BeforeToolCallEvent` in the Strands SDK. At zero budget, the call is blocked outright and it queues instead of paging you." |
| 1:16–1:24 | Cursor moves back up to the pip meter showing the drained state | Never refunded once delivered | "And once it's spent, it's spent — resolving something later doesn't give the pip back. Five means five." |

## 1:24–2:14 — Why its confidence is trustworthy: it runs the bug

| Time | On screen | Caption | Say |
|---|---|---|---|
| 1:24–1:32 | Click into Screen B (Receipts), select the `astropy__astropy-13033` receipt | Real issue → real script → real execution | "Click into a receipt. This is the one case, out of sixteen, that actually reproduced." |
| 1:32–1:41 | Scroll to the issue text panel, let it sit on screen, fully readable | Issue text only — no repo access used here | "Real GitHub issue text, nothing else — no gold patch, no answer key, no hint at what the fix looks like." |
| 1:41–1:52 | Scroll to the generated script panel, hold on it | The generated reproduction script | "The model wrote this script itself, from that text alone, and it ran inside a locked-down container — no network, read-only filesystem, capped memory." |
| 1:52–2:06 | Scroll to the side-by-side exec output: base_commit run vs. gold-patch run | Fails before the fix. Passes after. | "Run it against the buggy commit — it fails. Run the exact same script again with the real fix applied — it passes. Fail-then-pass is the only thing this project calls 'reproduced.'" |
| 2:06–2:14 | Cut to Screen C (Evidence), headline stat "19%" with the strikethrough "88%" visible | The agent never sees the gold patch | "The agent never sees that patch. Only an offline scorer does, after its verdict is already locked in." |

## 2:14–2:59 — The number that matters: 88% vs. 19%

| Time | On screen | Caption | Say |
|---|---|---|---|
| 2:14–2:24 | Screen C, cursor on the "88%" (naive) figure | Naive scoring: script exited non-zero = 88% | "If you scored this the naive way — did the script exit non-zero — sixteen real bugs would say eighty-eight percent reproduced." |
| 2:24–2:33 | Cursor moves to the "19%" (real gold-patch) figure | Real gold-patch differential = 19% | "The real number, checked properly against the dataset's actual fix, is nineteen percent. That's not a footnote — that's the headline." |
| 2:33–2:47 | Scroll to the taxonomy panel: 11 false positives, 1 semantic inversion, 1 no-signal | 11 of 16 were false positives | "Eleven of those sixteen were scripts broken for reasons that had nothing to do with the bug — and we know that because they're still broken after the real fix is applied." |
| 2:47–2:59 | Cursor on the one `semantic_inversion` row | One inverted the bug's own example | "One inverted the bug entirely — it mistook the buggy output shown in the issue for the correct one. Every failure here is published, not hidden." |

## 2:59–3:47 — It acts on its own, for real

| Time | On screen | Caption | Say |
|---|---|---|---|
| 2:59–3:07 | Switch to browser tab: github.com/AshrafAhmed9/tqdm/issues | A real fork, real open issues | "This is a real fork of tqdm — thirty-one thousand stars, pushed the day before I forked it." |
| 3:07–3:21 | Open issue #2 (the invalid-hex-colour bug), scroll to the posted verdict comment | Real posted verdict, real script, real output | "Three real, unmodified issues copied in from upstream. Understudy read this one, wrote a script, ran it, and posted this comment — with the real script and the real output attached." |
| 3:21–3:39 | Scroll through the comment body: the script, the exit code, the disclosure line at the bottom | Disclosed: manually triggered, not yet scheduled | "It says exactly what it is, right in the comment: a live candidate, not gold-confirmed — there's no fix yet for an open bug. And it says this run was manually triggered, not scheduled, because that's still true." |
| 3:39–3:47 | Cut back to the live demo, brief | Nothing here is asserted without a link to prove it | "Everything in this video links to something you can go check yourself." |

## 3:47–4:35 — Architecture, fast

| Time | On screen | Caption | Say |
|---|---|---|---|
| 3:47–3:59 | Architecture diagram (`diagrams/architecture.png`), full screen | One hook, two jobs | "One hook does two jobs: gates the interruption budget, and blocks `git` outright, so the agent can never read the fix commit in its own checked-out repo." |
| 3:59–4:09 | Cursor on the sandbox section of the diagram (docker flags) | No network · read-only · host-killed | "Everything it writes runs locked down — no network, read-only filesystem, a host-enforced timeout that actually kills the container, not just the process." |
| 4:09–4:25 | Cursor on the "TRIAGE" section, qwen2.5-coder label | Local model, $0, by necessity | "Inference is local — a 7-billion-parameter model on my own machine, genuinely free. Bedrock was broken on this account for the whole build, so I measured what a local model could actually do instead of assuming." |
| 4:25–4:33 | Terminal, real `pytest -q` running fresh, ending on "74 passed" | 74 tests, real Docker + real Ollama | "Seventy-four tests, real Docker integration, real model calls where it matters — nothing mocked out." |

## 4:33–5:00 — Limits, then close

| Time | On screen | Caption | Say |
|---|---|---|---|
| 4:33–4:43 | Screen C, evidence panel, static | 16 instances — a sample, stated as one | "Sixteen instances, not five hundred — a convenience sample, and I'm calling it that on purpose, not a claim about the whole benchmark." |
| 4:43–4:55 | Screen D (Inbox) or the exhausted-budget state if a card has drained all pips | What's next: scale it, deploy it | "What's next: more instances, a real scheduled deployment once AgentCore access clears up, and finding out if a bigger local model changes the number without changing the budget." |
| 4:55–5:00 | Hold on Screen A, the Watch, pip meter visible, static final frame | **Understudy** | "That's Understudy." |

---

## Before recording

- [ ] Live demo confirmed public (done, 2026-09-12).
- [ ] `github.com/AshrafAhmed9/tqdm/issues/2` open in a second tab, pre-scrolled to the posted
      verdict comment.
- [ ] `diagrams/architecture.png` ready to go full-screen or in an image viewer.
- [ ] Terminal ready to run `pytest -q` fresh on cue, not a screenshot.
- [ ] One full silent read-through with a stopwatch before recording — trim words, not speed.
