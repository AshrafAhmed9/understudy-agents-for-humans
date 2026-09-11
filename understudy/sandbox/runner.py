"""Host-supervised container execution.

Every script from a bug report is untrusted code from a stranger. This module is
the only place that is allowed to invoke Docker. See CLAUDE.md rule 4.

Timeout enforcement is done host-side, not by relying on a `timeout` binary
inside the container image (some SWE-bench images don't have one, and macOS
doesn't ship GNU timeout by default either). Killing the `docker run` CLI
process on the host does NOT stop the container — the daemon keeps it running
detached. So: run detached, poll, and on timeout explicitly `docker kill` +
`docker rm -f` the exact container ID, then verify it is actually gone.
"""

from __future__ import annotations

import subprocess
import time
import uuid
from pathlib import Path

from understudy.schemas import ExecResult

# Exit code the runner reports when Docker itself failed to run the workload
# (missing image, daemon unreachable, bad invocation) — distinct from any code
# the *script* could produce. The scorer treats this as an invalid execution,
# never as "fails on buggy" evidence.
INFRA_FAILURE_EXIT_CODE = -1

MAX_CAPTURE_BYTES = 200_000  # cap stdout/stderr we keep, to avoid output flooding


def _truncate(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace")
    if len(text) > MAX_CAPTURE_BYTES:
        cut = len(text) - MAX_CAPTURE_BYTES
        text = text[:MAX_CAPTURE_BYTES] + f"\n...[truncated {cut} chars]..."
    return text


def _docker(*args: str, timeout: float | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", *args],
        capture_output=True,
        timeout=timeout,
    )


def _container_exists(name: str) -> bool:
    result = _docker("inspect", name, timeout=10)
    return result.returncode == 0


def _force_kill(name: str) -> None:
    """Kill and remove a container, verifying it is actually gone."""
    _docker("kill", name, timeout=10)
    _docker("rm", "-f", name, timeout=10)
    for _ in range(10):
        if not _container_exists(name):
            return
        time.sleep(0.2)
    # If it's still there after this, something is badly wrong with the host
    # Docker daemon; surface it loudly rather than pretending cleanup worked.
    if _container_exists(name):
        raise RuntimeError(f"container {name} could not be removed")


def swebench_command(workdir: str = "/testbed", conda_env: str = "testbed") -> str:
    """The verified SWE-bench container convention: bash -lc (never sh, which
    is dash on these images and breaks `source`), activate the named conda
    env, cd into the checkout, run the mounted script."""
    return (
        f"source /opt/miniconda3/bin/activate && conda activate {conda_env} "
        f"&& cd {workdir} && exec python /repro/repro.py"
    )


def run_script_in_container(
    image: str,
    script_path: Path,
    *,
    workdir: str = "/testbed",
    conda_env: str = "testbed",
    shell_command: str | None = None,
    timeout_s: float = 60.0,
) -> ExecResult:
    """Run a single untrusted Python script inside a locked-down container.

    The script is mounted read-only OUTSIDE the tmpfs mount, at /repro/repro.py,
    so the script itself cannot be modified by the process it starts. The
    container gets no network, a small memory ceiling, a capped process count,
    an unprivileged user, a read-only root filesystem with only /tmp writable
    (and that as tmpfs, so nothing persists), stdin wired to /dev/null so a
    stray input() call hits EOF instead of hanging forever, and every Linux
    capability dropped.
    """
    return _run_locked_down(
        image,
        {script_path.resolve(): "/repro/repro.py"},
        shell_command or swebench_command(workdir, conda_env),
        timeout_s,
    )


def prepare_fixed_image(
    base_image: str,
    gold_patch_text: str,
    *,
    workdir: str = "/testbed",
) -> str:
    """Trusted, offline, one-time preparation step: apply the gold patch to
    a writable copy of the base image and commit the result as a new local
    image. This is deliberately a SEPARATE container lifecycle from the one
    that later executes the untrusted script — the patched checkout is
    produced here with full write access (git needs to write the tree), and
    the untrusted script is only ever run afterward, against the resulting
    image, under the same full lockdown as the buggy run. Containment for
    untrusted code is never weakened by this step.

    Trusted content only: the gold patch is our own offline data, not
    anything the agent or a generated script ever supplies.
    """
    import tempfile

    prep_name = f"understudy-prep-{uuid.uuid4().hex[:12]}"
    fixed_tag = f"understudy-fixed-{uuid.uuid4().hex[:12]}"

    with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False) as f:
        f.write(gold_patch_text)
        patch_path = Path(f.name).resolve()

    try:
        create = _docker(
            "create", "--name", prep_name,
            "-v", f"{patch_path}:/tmp/gold.patch:ro",
            base_image,
            "/bin/bash", "-lc",
            f"cd {workdir} && git apply --whitespace=nowarn /tmp/gold.patch",
            timeout=30,
        )
        if create.returncode != 0:
            raise RuntimeError(f"prepare_fixed_image: create failed: {create.stderr.decode()}")

        start = _docker("start", "-a", prep_name, timeout=60)
        if start.returncode != 0:
            raise RuntimeError(
                f"prepare_fixed_image: git apply failed: {start.stdout.decode()} {start.stderr.decode()}"
            )

        commit = _docker("commit", prep_name, fixed_tag, timeout=60)
        if commit.returncode != 0:
            raise RuntimeError(f"prepare_fixed_image: commit failed: {commit.stderr.decode()}")

        return fixed_tag
    finally:
        _docker("rm", "-f", prep_name, timeout=10)
        patch_path.unlink(missing_ok=True)


def run_patched_script_in_container(
    image: str,
    script_path: Path,
    gold_patch_text: str,
    *,
    workdir: str = "/testbed",
    conda_env: str = "testbed",
    timeout_s: float = 90.0,
) -> ExecResult:
    """Offline-scorer-only: build the patched image, then run the same
    script under the exact same lockdown as the buggy run. Never reachable
    from any agent tool — the agent's tools have no way to call this, and
    git is blocked for the agent in understudy/policy/hooks.py.
    """
    fixed_image = prepare_fixed_image(image, gold_patch_text, workdir=workdir)
    try:
        return run_script_in_container(
            fixed_image,
            script_path,
            workdir=workdir,
            conda_env=conda_env,
            timeout_s=timeout_s,
        )
    finally:
        _docker("rmi", "-f", fixed_image, timeout=30)


def _run_locked_down(
    image: str,
    mounts: dict[Path, str],
    shell_command: str,
    timeout_s: float,
) -> ExecResult:
    name = f"understudy-{uuid.uuid4().hex[:12]}"

    cmd = ["run", "--detach", "--name", name]
    for host_path, container_path in mounts.items():
        cmd += ["-v", f"{host_path}:{container_path}:ro"]
    cmd += [
        "--network", "none",
        "--memory", "512m",
        "--cpus", "1",
        "--pids-limit", "128",
        "--user", "nobody",
        "--read-only",
        "--tmpfs", "/tmp:rw,size=64m",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        image,
        "/bin/bash", "-lc",
        shell_command,
    ]

    start = _docker(*cmd, timeout=30)
    if start.returncode != 0:
        # Container never started at all — e.g. image missing locally.
        return ExecResult(
            exit_code=INFRA_FAILURE_EXIT_CODE,
            stdout="",
            stderr=_truncate(start.stderr),
            timed_out=False,
        )

    container_id = start.stdout.decode().strip()
    if not container_id:
        return ExecResult(
            exit_code=INFRA_FAILURE_EXIT_CODE,
            stdout="",
            stderr="docker run produced no container id",
            timed_out=False,
        )

    # No -i flag was passed, so Docker never allocates an attached stdin for
    # this container: the process's stdin is closed from the start, and a
    # generated script calling input() hits EOF immediately instead of
    # hanging forever. (Passing -i on a --detach run was the earlier bug
    # here — it keeps stdin open with nothing on the other end.)
    try:
        wait = _docker("wait", name, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        _force_kill(name)
        logs = _docker("logs", name, timeout=10)
        return ExecResult(
            exit_code=INFRA_FAILURE_EXIT_CODE,
            stdout=_truncate(logs.stdout) if logs.returncode == 0 else "",
            stderr=_truncate(logs.stderr) if logs.returncode == 0 else "",
            timed_out=True,
        )

    logs = _docker("logs", name, timeout=10)
    stdout = _truncate(logs.stdout) if logs.returncode == 0 else ""
    stderr = _truncate(logs.stderr) if logs.returncode == 0 else ""

    exit_code = INFRA_FAILURE_EXIT_CODE
    if wait.returncode == 0:
        try:
            exit_code = int(wait.stdout.decode().strip())
        except ValueError:
            pass

    _docker("rm", "-f", name, timeout=10)

    return ExecResult(
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        timed_out=False,
    )
