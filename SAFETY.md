# Safety

What Understudy will never do autonomously, and what's actually verified
about the boundaries below — not aspirational, checked against real tests
and, for the sandbox, a real Docker daemon.

## What it will never do

- **Never runs `git`**, or anything else that could reach a fix commit,
  a patch, or benchmark answer material. Two independent layers: the
  `git` executable is blocked at the tool-call level
  (`understudy/policy/hooks.py`), and the filesystem the agent can see has
  already had `.git`, packed refs, and patch/eval files stripped out before
  the agent ever gets a look (`understudy/sandbox/sanitize.py`) — verified
  by a test that manufactures a repo with all of that present and confirms
  none of it survives sanitization.
- **Never executes untrusted code outside a locked-down container.**
  No network, a read-only root filesystem, a capped process count, an
  unprivileged user, a memory ceiling, and a host-enforced timeout that
  actually kills the container rather than just abandoning the CLI process
  that started it. All of this is proven against a real Docker daemon, not
  asserted: an infinite loop is genuinely killed within the timeout, a
  socket connection attempt genuinely fails, a write to the root filesystem
  genuinely fails, a script calling `input()` genuinely gets EOF instead of
  hanging forever.
- **Never interrupts past its daily budget.** The interruption ledger is
  durable (SQLite, survives a process restart) and gives no refunds — a
  human resolving a decision, or a notification whose delivery was
  ambiguous, never returns a spent slot to the pool. Proven with a
  concurrency test: six simultaneous requests against a cap of five yield
  exactly five reservations, and the sixth is queued rather than lost.
- **Never claims a bug is confirmed from a single run.** The only valid
  scoring method is the gold-patch differential: a script must fail on the
  buggy commit *and* pass once the real fix is applied. Eight tests prove
  an always-fail, always-pass, import-error, or timed-out script can never
  be scored as a reproduction — this was a real flaw in an earlier version
  of this plan, caught and fixed before any evaluation ran.
- **Never posts anywhere without explicit authorization.** No outbound
  GitHub write path exists yet. Reading public issues is unauthenticated
  and read-only; the only Docker registry access is pulling public images.

## Known limits, stated plainly

- The sandbox is a constrained local prototype, not a claim that arbitrary
  hostile code is perfectly safe to run. Defense in depth (no network, no
  privileges, no persistence, host-supervised kill) is real, but this is
  not a hardened multi-tenant execution service.
- The agent's reasoning has never made a real model call as of this
  writing — everything above is the execution/safety layer, verified
  independently of whether the model behaves well or badly.
- Confidence reported by the agent is not a calibrated probability.
