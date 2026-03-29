from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional

from bootstrap.shared.execution_policy import ExecutionPolicy
from bootstrap.shared.retry import retry


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandRunner:
    def __init__(self, policy: ExecutionPolicy | None = None) -> None:
        self.policy = policy or ExecutionPolicy()

    def _run_once(
        self,
        args: List[str],
        *,
        env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                env=env,
                timeout=self.policy.timeout_seconds,
                check=False,
            )
            return CommandResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired as exc:
            return CommandResult(
                returncode=124,
                stdout=exc.stdout or "",
                stderr=(exc.stderr or "") + ("\n" if exc.stderr else "") + "timeout",
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
