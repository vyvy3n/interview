"""
Exercise 10 — Conditional Variable Blocking Cache

Implement BlockingCache: set() stores a value; wait_get() blocks until the key
is available (with optional timeout).

Allowed imports: threading (stdlib only)
"""

import threading
from typing import Any


class BlockingCache:
    def __init__(self) -> None:
        self._cache: dict = {}
        # TODO: add a threading.Condition here
        raise NotImplementedError

    def set(self, key: str, value: Any) -> None:
        """
        Store value under key, then wake all threads waiting for any key.
        Thread-safe.
        """
        raise NotImplementedError

    def wait_get(self, key: str, timeout: float | None = None) -> Any:
        """
        Return cache[key] immediately if present.
        Otherwise block until set() is called for this key.

        Args:
            key:     cache key to retrieve.
            timeout: if given, raise TimeoutError if key not set within timeout seconds.

        Raises:
            TimeoutError: if timeout expires before the key is set.
        """
        raise NotImplementedError
