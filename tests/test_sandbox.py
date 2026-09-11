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
