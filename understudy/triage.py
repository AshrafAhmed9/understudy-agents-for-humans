"""Real implementation of schemas.triage(): patch-free Instance in, an
immutable Verdict + candidate script out.

Model is qwen2.5-coder:7b via local Ollama — not Nova Lite. AWS Bedrock
access on this account returns ValidationException: Operation not allowed,
confirmed persistent across a Free->Paid plan upgrade, and any paid API is
ruled out. Local inference is the only path that
is actually zero-cost. This is a deliberate, disclosed deviation from
CLAUDE.md rule 6, not an oversight.

The agent never receives the gold patch — only Instance (issue_text,
base_commit, repo), never ScoringCase. status is always candidate_reproduction
or not_reproduced or error from this function; only the offline scorer in
scoring/differential.py may declare Score.reproduced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from understudy.data.swebench import epoch_image_ref
from understudy.sandbox.runner import (
    prepare_sanitized_image,
    remove_image,
    run_script_in_container,
)
from understudy.schemas import ExecResult, Instance, ReproSpec, TriageResult, Verdict

MAX_ATTEMPTS = 3

PROMPT_TEMPLATE = """You are given a real bug report for the repository {repo}.

Write a single, self-contained Python script that reproduces the bug: the
script should exit with a non-zero status code if the bug described below is
present, and exit 0 if it is not (i.e. if the code is already correct).

Only use packages already installed in the repository's environment. Do not
attempt to import test frameworks like pytest. Print a short message
explaining what you found before exiting.

This environment may run an old Python (some SWE-bench testbeds pin Python
3.5 or earlier). Do NOT use f-strings, other Python 3.6+ syntax, or
type-annotated variables. Use .format() or % for string formatting instead.

Return ONLY the Python code, no explanation, no markdown fences.

Bug report:
{issue_text}
"""

REPAIR_TEMPLATE = """Your previous script failed to run correctly — this is
about the SCRIPT ITSELF being broken (e.g. an import error, wrong API,
syntax error), not about whether the bug is present. Fix the script so it
runs cleanly, while still correctly detecting the bug described in the
original report. Do not repeat the same mistake.

If the error is a SyntaxError, this environment likely runs an old Python
(3.5 or earlier) that does not support f-strings or other 3.6+ syntax — use
.format() or % instead, and do not repeat the same construct that failed.

Previous script:
{script}

Error output:
{stderr}

Return ONLY the corrected Python code, no explanation, no markdown fences.
"""

_CODE_FENCE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def _extract_code(text: str) -> str:
    match = _CODE_FENCE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def _is_script_crash(stderr: str) -> bool:
    # A SyntaxError has no "Traceback" line, only a File/line pointer, so
    # matching on "Traceback" alone under-detects script-level failures.
    return "Traceback" in stderr or re.search(r'^\s*File "', stderr, re.M) is not None


@dataclass
class OllamaGenerator:
    """Thin wrapper so triage() can be unit-tested with a fake generator
    instead of a real Ollama call."""

    model_id: str = "qwen2.5-coder:7b"
    temperature: float = 0.2

    def generate(self, prompt: str) -> str:
        import ollama

        response = ollama.generate(
            model=self.model_id, prompt=prompt, options={"temperature": self.temperature}
        )
        return response["response"]


def build_triage_fn(generator: OllamaGenerator | None = None):
    """Returns a triage(instance) -> TriageResult callable bound to a model
    generator. Kept as a factory (rather than a bare module function calling
    Ollama directly) so tests can inject a fake generator with no network."""

    gen = generator or OllamaGenerator()

    def triage(instance: Instance) -> TriageResult:
        image = epoch_image_ref(instance.instance_id)
        # The generated script never runs against the raw image: SWE-bench
        # images bake .git into the filesystem, so blocking `git` as a tool
        # call (irrelevant here — no Strands tool call happens in this
        # loop) protects nothing on its own. Every attempt below runs
        # against a one-time-sanitized image instead.
        clean_image = prepare_sanitized_image(image)

        try:
            prompt = PROMPT_TEMPLATE.format(repo=instance.repo, issue_text=instance.issue_text)
            script = _extract_code(gen.generate(prompt))

            attempts = 1
            result: ExecResult = run_script_in_container(clean_image, _write_tmp(script), timeout_s=60)

            while attempts < MAX_ATTEMPTS and _is_script_crash(result.stderr):
                repair_prompt = REPAIR_TEMPLATE.format(script=script, stderr=result.stderr[:2000])
                script = _extract_code(gen.generate(repair_prompt))
                attempts += 1
                result = run_script_in_container(clean_image, _write_tmp(script), timeout_s=60)
        finally:
            remove_image(clean_image)

        spec = ReproSpec(script=script, attempt=attempts)

        if _is_script_crash(result.stderr):
            # Ran out of attempts and the script itself never became valid —
            # we cannot claim any signal about whether the bug is present.
            verdict = Verdict(
                status="error",
                confidence=0.0,
                evidence=f"script failed to execute after {attempts} attempts: {result.stderr[:500]}",
                attempts=attempts,
            )
            return TriageResult(verdict=verdict, final_spec=spec)

        if result.exit_code != 0:
            verdict = Verdict(
                status="candidate_reproduction",
                confidence=0.6,
                evidence=result.stdout[:500] or result.stderr[:500],
                attempts=attempts,
            )
        else:
            verdict = Verdict(
                status="not_reproduced",
                confidence=0.4,
                evidence=result.stdout[:500] or "script ran and exited 0",
                attempts=attempts,
            )

        return TriageResult(verdict=verdict, final_spec=spec)

    return triage


def _write_tmp(script: str):
    from pathlib import Path
    import tempfile

    fd, path = tempfile.mkstemp(suffix=".py")
    import os

    with os.fdopen(fd, "w") as f:
        f.write(script)
    return Path(path)
