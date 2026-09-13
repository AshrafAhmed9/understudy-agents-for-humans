"""Integration tests against a real Docker daemon. These prove the sandbox
actually enforces what CLAUDE.md rule 4 requires, not just that the code
compiles. Skipped automatically if Docker isn't available.
"""

import shutil
import subprocess
import time

import pytest

from understudy.sandbox.runner import run_script_in_container

IMAGE = "python:3.11-slim"


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(
            ["docker", "info"], capture_output=True, timeout=5
        ).returncode == 0
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _docker_available(), reason="docker not available")


def _write_script(tmp_path, body: str):
    path = tmp_path / "repro.py"
    path.write_text(body)
    return path


def test_normal_exit_code_and_stdout_pass_through(tmp_path):
    script = _write_script(tmp_path, "print('hello from the sandbox')\nimport sys; sys.exit(0)")
    result = run_script_in_container(IMAGE, script, shell_command="python3 /repro/repro.py", timeout_s=30)
    assert result.exit_code == 0
    assert "hello from the sandbox" in result.stdout
    assert result.timed_out is False


def test_nonzero_exit_code_and_stderr_captured(tmp_path):
    script = _write_script(tmp_path, "import sys; print('boom', file=sys.stderr); sys.exit(1)")
    result = run_script_in_container(IMAGE, script, shell_command="python3 /repro/repro.py", timeout_s=30)
    assert result.exit_code == 1
    assert "boom" in result.stderr


def test_infinite_loop_is_killed_by_the_host_supervisor(tmp_path):
    script = _write_script(tmp_path, "while True:\n    pass\n")
    start = time.monotonic()
    result = run_script_in_container(
        IMAGE, script, shell_command="python3 /repro/repro.py", timeout_s=5
    )
    elapsed = time.monotonic() - start
    assert result.timed_out is True
    # Host supervisor must actually kill it, not just give up waiting —
    # this should return shortly after the timeout, not hang indefinitely.
    assert elapsed < 20


def test_stdin_read_hits_eof_instead_of_hanging(tmp_path):
    # A generated script that calls input() must not hang the container
    # forever waiting for a human who will never type anything.
    script = _write_script(
        tmp_path,
        "import sys\n"
        "try:\n"
        "    x = input()\n"
        "    print('got:', repr(x))\n"
        "except EOFError:\n"
        "    print('EOF as expected')\n"
        "sys.exit(0)\n",
    )
    result = run_script_in_container(
        IMAGE, script, shell_command="python3 /repro/repro.py", timeout_s=10
    )
    assert result.timed_out is False
    assert "EOF as expected" in result.stdout or "got:" in result.stdout


def test_no_network_access(tmp_path):
    script = _write_script(
        tmp_path,
        "import socket\n"
        "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
        "s.settimeout(3)\n"
        "try:\n"
        "    s.connect(('8.8.8.8', 53))\n"
        "    print('CONNECTED')\n"
        "except OSError as e:\n"
        "    print('blocked:', e)\n",
    )
    result = run_script_in_container(
        IMAGE, script, shell_command="python3 /repro/repro.py", timeout_s=15
    )
    assert "CONNECTED" not in result.stdout


def test_root_filesystem_is_read_only(tmp_path):
    script = _write_script(
        tmp_path,
        "try:\n"
        "    open('/usr/bin/new_file', 'w').write('x')\n"
        "    print('WROTE')\n"
        "except OSError as e:\n"
        "    print('blocked:', e)\n",
    )
    result = run_script_in_container(
        IMAGE, script, shell_command="python3 /repro/repro.py", timeout_s=15
    )
    assert "WROTE" not in result.stdout


def test_missing_image_reports_infra_failure_not_a_crash(tmp_path):
    from understudy.sandbox.runner import INFRA_FAILURE_EXIT_CODE

    script = _write_script(tmp_path, "print('never runs')")
    result = run_script_in_container(
        "understudy/this-image-does-not-exist:latest",
        script,
        shell_command="python3 /repro/repro.py",
        timeout_s=15,
    )
    assert result.exit_code == INFRA_FAILURE_EXIT_CODE
    assert result.timed_out is False


# --- Offline gold-patch differential path, against a real pulled instance ---
# Skipped unless that specific image is already present locally (it's ~1GB;
# we don't want a routine `pytest` run to pull it). scripts/verify_kill_gate.py
# is the one-off proof this mirrors; this test protects that path from
# silently regressing.

_REAL_IMAGE = "ghcr.io/epoch-research/swe-bench.eval.x86_64.astropy__astropy-12907"


def _real_image_present() -> bool:
    if not _docker_available():
        return False
    try:
        return subprocess.run(
            ["docker", "image", "inspect", _REAL_IMAGE],
            capture_output=True, timeout=10,
        ).returncode == 0
    except Exception:
        return False


@pytest.mark.skipif(not _real_image_present(), reason="real SWE-bench image not pulled locally")
def test_offline_differential_reproduces_a_real_bug(tmp_path):
    import json

    from understudy.data.swebench import load_cases
    from understudy.sandbox.runner import run_patched_script_in_container
    from understudy.scoring.differential import score_differential

    cases = load_cases()
    case = next(c for c in cases if c.instance.instance_id == "astropy__astropy-12907")

    script = _write_script(
        tmp_path,
        "import sys\n"
        "import numpy as np\n"
        "from astropy.modeling import models as m\n"
        "from astropy.modeling.separable import separability_matrix\n"
        "cm = m.Linear1D(10) & m.Linear1D(5)\n"
        "result = separability_matrix(m.Pix2Sky_TAN() & cm)\n"
        "expected = np.array([[True, False], [False, True]])\n"
        "sys.exit(0 if np.array_equal(result[2:, 2:], expected) else 1)\n",
    )

    buggy = run_script_in_container(_REAL_IMAGE, script, timeout_s=90)
    fixed = run_patched_script_in_container(_REAL_IMAGE, script, case.gold_patch, timeout_s=90)

    result = score_differential(buggy, fixed)
    assert result.reproduced is True
    assert result.fails_on_buggy is True
    assert result.passes_on_fixed is True

    # No leftover images from the prepare/commit/rmi lifecycle.
    leftover = subprocess.run(
        ["docker", "images", "--filter", "reference=understudy-fixed-*", "-q"],
        capture_output=True, timeout=10,
    ).stdout.decode().strip()
    assert leftover == ""
    leftover_clean = subprocess.run(
        ["docker", "images", "--filter", "reference=understudy-clean-*", "-q"],
        capture_output=True, timeout=10,
    ).stdout.decode().strip()
    assert leftover_clean == ""


@pytest.mark.skipif(not _real_image_present(), reason="real SWE-bench image not pulled locally")
def test_generated_script_cannot_see_git_history(tmp_path):
    """The whole point of the differential is that the script can't know
    which commit it's running against except by actually testing for the
    bug. If .git were reachable, a script could trivially cheat by checking
    HEAD instead of exercising any real behavior."""
    from understudy.sandbox.runner import prepare_sanitized_image, remove_image

    clean_image = prepare_sanitized_image(_REAL_IMAGE)
    try:
        check = subprocess.run(
            ["docker", "run", "--rm", clean_image, "/bin/bash", "-lc",
             "test -e /testbed/.git && echo PRESENT || echo ABSENT"],
            capture_output=True, timeout=30,
        )
        assert b"ABSENT" in check.stdout
        # The rest of the checkout must still be there and usable.
        setup_check = subprocess.run(
            ["docker", "run", "--rm", clean_image, "/bin/bash", "-lc",
             "test -e /testbed/setup.py && echo PRESENT || echo ABSENT"],
            capture_output=True, timeout=30,
        )
        assert b"PRESENT" in setup_check.stdout
    finally:
        remove_image(clean_image)
