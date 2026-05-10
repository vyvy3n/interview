"""
Exercise 07 — Readers-Writers Lock

Multiple concurrent readers are allowed; writers are exclusive.
No readers may be active during a write.

Allowed imports: threading (stdlib only)
"""

import threading


class RWLock:
    def __init__(self) -> None:
        self._reader_count = 0
        # TODO: add threading.Condition (and optionally a separate threading.Lock)
        raise NotImplementedError

    def read_acquire(self) -> None:
        """Acquire the read lock.  Blocks if a writer is active."""
        raise NotImplementedError

    def read_release(self) -> None:
        """Release the read lock.  The last reader notifies waiting writers."""
        raise NotImplementedError

    def write_acquire(self) -> None:
        """Acquire the write lock.  Blocks until all readers have released."""
        raise NotImplementedError

    def write_release(self) -> None:
        """Release the write lock and notify all waiting readers and writers."""
        raise NotImplementedError
