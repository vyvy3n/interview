"""
Exercise 10 — Conditional Variable Blocking Cache

Implement BlockingCache: set() stores a value; wait_get() blocks until the key
is available (with optional timeout).

Primary API: ``threading.Condition``. ``time.monotonic`` is used only to
enforce a *total* ``timeout`` across repeated ``wait`` calls after spurious
wakeups (still stdlib, no third-party deps).
"""

import time
import threading
from typing import Any


class BlockingCache:
    """
    A tiny key/value store where readers can block until a key appears.

    One ``threading.Condition`` guards both the dict and all ``wait``/``notify``
    coordination (problem.md). ``notify_all`` is required so every waiter on
    the same condition wakes and re-checks its predicate (gotcha #3).
    """

    def __init__(self) -> None:
        # Shared mapping; must only be read/written while holding ``_cond``.
        self._cache: dict[str, Any] = {}
        self._cond = threading.Condition()

    def set(self, key: str, value: Any) -> None:
        """
        Store value under key, then wake all threads waiting for any key.
        Thread-safe.
        """
        # Lock + update + notify must be atomic w.r.t. waiters re-checking
        # ``key in self._cache`` (problem gotcha #4).
        with self._cond:
            self._cache[key] = value
            # Wake everyone blocked in wait_get; each re-runs its ``while`` and
            # either sees its key and returns, or goes back to wait().
            self._cond.notify_all()

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
        with self._cond:
            # Fast path: no wait if writer already ran.
            if key in self._cache:
                return self._cache[key]

            # -----------------------------------------------------------------
            # Blocking path: Mesa-style condition variable pattern
            # -----------------------------------------------------------------
            # We must re-test ``key not in self._cache`` in a *while* loop:
            #   - Spurious wakeups are allowed.
            #   - notify_all wakes *all* waiters; another thread's key may have
            #     been set — we loop until *our* key appears (gotcha #2).
            # -----------------------------------------------------------------
            if timeout is None:
                while key not in self._cache:
                    self._cond.wait()
                return self._cache[key]

            # Timed wait: ``wait(timeout)`` returns False when the timeout elapses
            # without being notified (gotcha #1) — we must raise TimeoutError.
            #
            # Use a wall deadline so repeated waits after spurious wakeups still
            # respect the *total* budget, not ``timeout`` per iteration.
            deadline = time.monotonic() + timeout
            while key not in self._cache:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError
                if not self._cond.wait(timeout=remaining):
                    # Timed out (or race where we were not notified in time).
                    raise TimeoutError
            return self._cache[key]
