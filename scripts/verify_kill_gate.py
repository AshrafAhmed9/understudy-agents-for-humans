"""Manual, one-off proof that the whole pipeline works on real data:
real issue text, real base_commit, real gold patch, real Docker image.

This is a HAND-AUTHORED reproduction script, not agent output — it exists
to prove the runner+sanitizer+scorer are honest before any generated script
is trusted: the runner and scorer must work before requesting generated
scripts.
"""

from pathlib import Path

from understudy.data.swebench import epoch_image_ref, load_cases
from understudy.sandbox.runner import run_patched_script_in_container, run_script_in_container
from understudy.scoring.differential import score_differential

REPRO_SCRIPT = '''
import sys
import numpy as np
from astropy.modeling import models as m
from astropy.modeling.separable import separability_matrix

cm = m.Linear1D(10) & m.Linear1D(5)
result = separability_matrix(m.Pix2Sky_TAN() & cm)
expected_bottom_right = np.array([[True, False], [False, True]])
actual_bottom_right = result[2:, 2:]

if np.array_equal(actual_bottom_right, expected_bottom_right):
    print("separability matrix is correct for nested compound models")
    sys.exit(0)
else:
    print("BUG: nested compound model separability is wrong")
    print("got:\\n", actual_bottom_right)
    sys.exit(1)
'''


def main():
    cases = load_cases()
    case = next(c for c in cases if c.instance.instance_id == "astropy__astropy-12907")
    image = epoch_image_ref(case.instance.instance_id)

    script_path = Path("/tmp/kill_gate_repro.py")
    script_path.write_text(REPRO_SCRIPT)

    print(f"instance: {case.instance.instance_id}")
    print(f"image:    {image}")
    print()

    print("running against base_commit (should FAIL — bug present)...")
    buggy = run_script_in_container(image, script_path, timeout_s=90)
    print(f"  exit_code={buggy.exit_code} timed_out={buggy.timed_out}")
    print(f"  stdout: {buggy.stdout.strip()[:200]}")
    if buggy.stderr.strip():
        print(f"  stderr: {buggy.stderr.strip()[:400]}")
    print()

    print("running against base_commit + gold patch (should PASS — bug fixed)...")
    fixed = run_patched_script_in_container(image, script_path, case.gold_patch, timeout_s=90)
    print(f"  exit_code={fixed.exit_code} timed_out={fixed.timed_out}")
    print(f"  stdout: {fixed.stdout.strip()[:200]}")
    if fixed.stderr.strip():
        print(f"  stderr: {fixed.stderr.strip()[:400]}")
    print()

    result = score_differential(buggy, fixed)
    print(f"Score: {result}")
    print(f"reproduced = {result.reproduced}")

    assert result.reproduced is True, "kill gate FAILED — pipeline is not honest on real data"
    print()
    print("KILL GATE PASSED: real issue -> real bug reproduced -> real fix confirmed.")


if __name__ == "__main__":
    main()
