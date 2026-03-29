from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionPolicy:
    timeout_seconds: int = 30
    retries: int = 1
