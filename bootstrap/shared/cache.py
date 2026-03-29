from __future__ import annotations

from typing import Dict, Generic, Optional, TypeVar


K = TypeVar("K")
V = TypeVar("V")


class SimpleCache(Generic[K, V]):
    """
    Cache simples em memória.
    """

    def __init__(self) -> None:
        self._data: Dict[K, V] = {}

    def get(self, key: K) -> Optional[V]:
        return self._data.get(key)

    def set(self, key: K, value: V) -> None:
        self._data[key] = value

    def has(self, key: K) -> bool:
        return key in self._data

    def clear(self) -> None:
        self._data.clear()
