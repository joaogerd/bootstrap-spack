from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from bootstrap.shared.execution_policy import ExecutionPolicy
from bootstrap.shared.retry import retry


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    command: str
    timed_out: bool
    duration_seconds: float


class CommandRunner:
    def __init__(self, policy: ExecutionPolicy | None = None) -> None:
        self.policy = policy or ExecutionPolicy()

    def _run_once(
        self,
        args: List[str],
        *,
        env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        command = " ".join(shlex.quote(part) for part in args)
        started = time.monotonic()
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                env=env,
                timeout=self.policy.timeout_seconds,
                check=False,
            )
            duration = time.monotonic() - started
            return CommandResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                command=command,
                timed_out=False,
                duration_seconds=duration,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - started
            return CommandResult(
                returncode=124,
                stdout=exc.stdout or "",
                stderr=(exc.stderr or "") + ("\n" if exc.stderr else "") + "timeout",
                command=command,
                timed_out=True,
                duration_seconds=duration,
            )

    def run(
        self,
        args: List[str],
        *,
        env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        return retry(
            lambda: self._run_once(args, env=env),
            attempts=self.policy.retries,
        )

    def run_shell(
        self,
        command: str,
        *,
        env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        return self.run(["bash", "-lc", command], env=env)
