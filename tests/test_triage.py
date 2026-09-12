"""Unit tests for understudy.triage using a fake generator (no network, no
Ollama). Real-model behavior is separately probed in
scripts/test_local_model_repro.py against real cached instances."""

from understudy.schemas import Instance
from understudy.triage import OllamaGenerator, build_triage_fn

INSTANCE = Instance(
    instance_id="astropy__astropy-12907",
    repo="astropy/astropy",
    issue_text="Nested CompoundModels do not correctly compute separability.",
    base_commit="d16bfe05a744909de4b27f5875fe0d4ed41ce607",
)


class FakeGenerator(OllamaGenerator):
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self.responses.pop(0)


class FakeRunner:
    """Swaps in for run_script_in_container: returns queued ExecResults in
    order regardless of image/path, so triage logic can be tested without
    Docker."""

    def __init__(self, results):
        self.results = list(results)
        self.calls = 0

    def __call__(self, image, path, timeout_s=60):
        self.calls += 1
        return self.results.pop(0)


def test_triage_one_shot_success(monkeypatch):
    from understudy.schemas import ExecResult

    monkeypatch.setattr(
        "understudy.triage.run_script_in_container",
        FakeRunner([ExecResult(exit_code=1, stdout="bug found", stderr="", timed_out=False)]),
    )
    gen = FakeGenerator(["print('bug found'); exit(1)"])
    triage = build_triage_fn(gen)

    result = triage(INSTANCE)

    assert result.verdict.status == "candidate_reproduction"
    assert result.verdict.attempts == 1
    assert result.final_spec is not None
    assert result.final_spec.attempt == 1
    assert len(gen.calls) == 1


def test_triage_repairs_a_crashing_script(monkeypatch):
    from understudy.schemas import ExecResult

    runner = FakeRunner(
        [
            ExecResult(
                exit_code=1,
                stdout="",
                stderr='Traceback (most recent call last):\nNameError: name \'array\' is not defined',
                timed_out=False,
            ),
            ExecResult(exit_code=1, stdout="bug found", stderr="", timed_out=False),
        ]
    )
    monkeypatch.setattr("understudy.triage.run_script_in_container", runner)
    gen = FakeGenerator(["broken script", "fixed script"])
    triage = build_triage_fn(gen)

    result = triage(INSTANCE)

    assert result.verdict.status == "candidate_reproduction"
    assert result.verdict.attempts == 2
    assert len(gen.calls) == 2  # initial + one repair prompt


def test_triage_exhausts_attempts_and_reports_error(monkeypatch):
    from understudy.schemas import ExecResult

    crash = ExecResult(
        exit_code=1,
        stdout="",
        stderr='Traceback (most recent call last):\nNameError: still broken',
        timed_out=False,
    )
    runner = FakeRunner([crash, crash, crash])
    monkeypatch.setattr("understudy.triage.run_script_in_container", runner)
    gen = FakeGenerator(["v1", "v2", "v3"])
    triage = build_triage_fn(gen)

    result = triage(INSTANCE)

    assert result.verdict.status == "error"
    assert result.verdict.attempts == 3
    assert result.verdict.confidence == 0.0


def test_triage_never_reads_gold_patch():
    # Instance has no patch field at all — the schema itself enforces this,
    # but assert the attribute doesn't exist as a regression guard.
    assert not hasattr(INSTANCE, "gold_patch")


def test_syntax_error_detected_as_script_crash():
    from understudy.triage import _is_script_crash

    syntax_err = '  File "/repro/repro.py", line 22\n    print(f"..)\n           ^\nSyntaxError: invalid syntax'
    assert _is_script_crash(syntax_err) is True


def test_prompts_warn_about_old_python():
    # Regression guard: django__django-10097's testbed runs Python 3.5.6, and
    # the model kept generating f-strings across every repair attempt because
    # nothing told it the interpreter was that old (found 2026-09-12).
    # Losing this instruction silently reintroduces a 4/4
    # systematic failure on old-Python instances.
    from understudy.triage import PROMPT_TEMPLATE, REPAIR_TEMPLATE

    assert "f-string" in PROMPT_TEMPLATE.lower()
    assert "f-string" in REPAIR_TEMPLATE.lower()
