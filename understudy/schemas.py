"""Frozen contract between streams.

Every parallel stream builds against these types with stubs. Changing anything here
means updating every stream, so don't — see CLAUDE.md rule 1.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FrozenContract(BaseModel):
    """Reject unexpected fields and prevent mutation after construction."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Instance(FrozenContract):
    """Agent-facing case containing no answer key or scoring artifacts."""

    instance_id: str
    repo: str
    issue_text: str
    base_commit: str


class ScoringCase(FrozenContract):
    """Offline-only answer key; never pass this object to agents or their tools.

    The scorer prepares isolated buggy/fixed environments after triage is persisted.
    Only the patch-free instance crosses into the agent-facing sandbox interface.
    """

    instance: Instance
    gold_patch: str


class ReproSpec(FrozenContract):
    """A candidate reproduction script.

    The script must exit non-zero when the bug is present and zero when it is fixed.
    """

    script: str
    attempt: int = Field(ge=1, le=3)


class ExecResult(FrozenContract):
    """Outcome of running a script inside the sandbox."""

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool


class Verdict(FrozenContract):
    """What the agent concluded, before any scoring happens.

    insufficient_info is declared from the issue text alone, BEFORE any script is
    written. Assigning it after a failed attempt makes the category meaningless and a
    judge will take it apart.
    """

    # A live failure is candidate evidence, never gold-patch confirmation.
    # not_reproduced means this attempt found no reproduction, not that no bug exists.
    status: Literal["candidate_reproduction", "not_reproduced", "insufficient_info", "error"]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str
    attempts: int = Field(ge=0, le=3)


class TriageResult(FrozenContract):
    """Immutable agent output, persisted before the offline scorer starts.

    final_spec is absent when no script was generated. Frozen nested models prevent
    the scorer from replacing the candidate or revising the live verdict in place.
    Persistence and scorer isolation must still be enforced by the orchestrator.
    """

    verdict: Verdict
    final_spec: ReproSpec | None


class Score(FrozenContract):
    """The gold-patch differential — the only valid scoring method.

    reproduced is true iff valid completed runs fail on the buggy commit AND pass
    after the gold patch. Timeouts, OOMs, failed setup/patch application and runner
    failures invalidate the comparison, rather than counting as a buggy failure.
    The scorer sets validity from execution provenance, not model judgment.
    """

    fails_on_buggy: bool
    passes_on_fixed: bool
    buggy_execution_valid: bool
    fixed_execution_valid: bool

    @property
    def reproduced(self) -> bool:
        return (
            self.buggy_execution_valid
            and self.fixed_execution_valid
            and self.fails_on_buggy
            and self.passes_on_fixed
        )


class Escalation(FrozenContract):
    """One notification costs one token; never refund a delivered interruption.

    The controller must reserve tokens atomically in a durable daily ledger and
    deduplicate delivery. Priority may order requests but cannot change their cost.
    """

    verdict: Verdict
    reason: str
    cost: int = Field(default=1, strict=True, ge=1, le=1)


# --- Stream boundaries -------------------------------------------------------
# Stub these to work in parallel; the real implementations land via their streams.

def run_in_sandbox(instance: Instance, spec: ReproSpec) -> ExecResult:
    """Stream A. Runs the script in a locked-down container.

    Flags are non-negotiable, see CLAUDE.md rule 4. Use /bin/bash -lc, never /bin/sh.
    """
    raise NotImplementedError


def triage(instance: Instance) -> TriageResult:
    """Stream CP. Patch-free case in; immutable verdict and final candidate out."""
    raise NotImplementedError


def score(case: ScoringCase, result: TriageResult) -> Score:
    """Stream CP. Offline only, after this exact triage result is persisted.

    No final script means no reproduction: return an invalid comparison with both
    outcome flags false. Never feed fixed-run evidence back into the agent loop.
    """
    raise NotImplementedError
