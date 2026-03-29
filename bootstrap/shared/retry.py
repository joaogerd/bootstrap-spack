from __future__ import annotations

import time
from typing import Callable, TypeVar


T = TypeVar("T")


def retry(func: Callable[[], T], attempts: int = 1, delay: float = 0.1) -> T:
    last_exc: Exception | None = None

    for i in range(attempts):
        try:
            return func()
        except Exception as exc:
            last_exc = exc
            if i < attempts - 1:
                time.sleep(delay)

    if last_exc:
        raise last_exc

    raise RuntimeError("retry failed unexpectedly")
