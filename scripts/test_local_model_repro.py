"""Capability probe: can a local model actually produce a working
reproduction script for real bugs, given only the issue text? Not part of
the production pipeline — a fast signal before committing to a local model
for real.

For each instance: single-shot attempt, one self-correction round if the
script crashes (matches production design), scored with the real gold-patch
differential against the real image.
"""

import re
import sys
from pathlib import Path

import ollama

from understudy.data.swebench import epoch_image_ref, load_cases
from understudy.sandbox.runner import run_patched_script_in_container, run_script_in_container
from understudy.scoring.differential import score_differential

MODEL = "qwen2.5-coder:7b"

PROMPT_TEMPLATE = """You are given a real bug report for the repository {repo}.

Write a single, self-contained Python script that reproduces the bug: the
script should exit with a non-zero status code if the bug described below is
present, and exit 0 if it is not (i.e. if the code is already correct).

Only use packages already installed in the repository's environment. Do not
attempt to import test frameworks like pytest. Print a short message
explaining what you found before exiting.

Return ONLY the Python code, no explanation, no markdown fences.

Bug report:
{issue_text}
"""

REPAIR_TEMPLATE = """Your previous script failed to run correctly — this is
about the SCRIPT ITSELF being broken (e.g. an import error, wrong API), not
about whether the bug is present. Fix the script so it runs cleanly, while
still correctly detecting the bug described in the original report.

Previous script:
{script}

Error output:
{stderr}

Return ONLY the corrected Python code, no explanation, no markdown fences.
"""


def extract_code(text: str) -> str:
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def ask(prompt: str) -> str:
    response = ollama.generate(model=MODEL, prompt=prompt, options={"temperature": 0.2})
    return response["response"]


def probe_instance(instance_id: str, script_path: str = "/tmp/local_model_repro.py") -> dict:
    cases = load_cases()
    case = next(c for c in cases if c.instance.instance_id == instance_id)
    image = epoch_image_ref(instance_id)

    print(f"\n{'=' * 60}\n{instance_id} ({case.instance.repo})\n{'=' * 60}")

    prompt = PROMPT_TEMPLATE.format(repo=case.instance.repo, issue_text=case.instance.issue_text)
    raw = ask(prompt)
    script = extract_code(raw)

    Path(script_path).write_text(script)
    result1 = run_script_in_container(image, Path(script_path), timeout_s=60)
    print(f"attempt 1: exit_code={result1.exit_code} timed_out={result1.timed_out}")
    if result1.stderr.strip():
        print(f"  stderr: {result1.stderr.strip()[:200]}")

    final_script = script
    final_result = result1
    attempts = 1
    def is_script_crash(stderr: str) -> bool:
        # SyntaxError has no "Traceback" line, only a File/line pointer, so
        # matching on that alone under-detects script-level failures.
        return "Traceback" in stderr or re.search(r'^\s*File "', stderr, re.M) is not None

    first_crashed = is_script_crash(result1.stderr)

    # MAX_ATTEMPTS = 3 total: the repro loop's repair cap.
    while attempts < 3 and is_script_crash(final_result.stderr):
        repair_prompt = REPAIR_TEMPLATE.format(script=final_script, stderr=final_result.stderr[:2000])
        raw_n = ask(repair_prompt)
        script_n = extract_code(raw_n)
        Path(script_path).write_text(script_n)
        result_n = run_script_in_container(image, Path(script_path), timeout_s=60)
        attempts += 1
        print(f"attempt {attempts}: exit_code={result_n.exit_code} timed_out={result_n.timed_out}")
        if result_n.stderr.strip():
            print(f"  stderr: {result_n.stderr.strip()[:200]}")
        final_script = script_n
        final_result = result_n

    script_crashed = first_crashed

    Path(script_path).write_text(final_script)
    try:
        fixed_result = run_patched_script_in_container(
            image, Path(script_path), case.gold_patch, timeout_s=90
        )
        score = score_differential(final_result, fixed_result)
        reproduced = score.reproduced
        error = None
    except Exception as exc:  # noqa: BLE001
        reproduced = False
        error = str(exc)

    print(f"attempts={attempts} reproduced={reproduced}" + (f" error={error}" if error else ""))

    return {
        "instance_id": instance_id,
        "attempts": attempts,
        "script_crashed_first": script_crashed,
        "reproduced": reproduced,
        "error": error,
    }


def main():
    instance_ids = [
        "astropy__astropy-12907",
        "astropy__astropy-13033",
        "astropy__astropy-13236",
        "django__django-10097",
    ]
    results = [probe_instance(iid) for iid in instance_ids]

    print(f"\n{'=' * 60}\nSUMMARY\n{'=' * 60}")
    n_reproduced = sum(1 for r in results if r["reproduced"])
    for r in results:
        status = "REPRODUCED" if r["reproduced"] else "not reproduced"
        print(f"  {r['instance_id']}: {status} (attempts={r['attempts']})" + (f" [error: {r['error']}]" if r["error"] else ""))
    print(f"\n{n_reproduced}/{len(results)} reproduced with {MODEL}")


if __name__ == "__main__":
    main()
