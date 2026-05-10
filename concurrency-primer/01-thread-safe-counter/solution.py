"""
Exercise 01 — Thread-Safe Counter

Implement Counter so that concurrent calls to increment() never lose updates.

Allowed imports: threading (stdlib only)
"""

import threading


class Counter:
    def __init__(self) -> None:
        self._count = 0
        # TODO: add a threading.Lock here
        self._lock = threading.Lock()

    def increment(self, delta: int = 1) -> None:
        """Add delta to the counter.  Thread-safe."""
        with self._lock:
            self._count += delta

    def value(self) -> int:
        """Return the current count.  Thread-safe."""
        with self._lock:
            return self._count
