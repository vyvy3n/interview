"""
Exercise 04 — Bounded Blocking Queue

Implement a thread-safe FIFO queue with a fixed capacity.
put() blocks when full; get() blocks when empty.

Allowed imports: threading, collections (stdlib only)
"""

import threading
from collections import deque
from typing import Any


class BoundedQueue:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._capacity = capacity
        self._queue: deque = deque()
        # TODO: add a threading.Condition here
        raise NotImplementedError

    def put(self, item: Any) -> None:
        """Enqueue item.  Blocks if the queue is at capacity."""
        raise NotImplementedError

    def get(self) -> Any:
        """Dequeue and return the front item.  Blocks if the queue is empty."""
        raise NotImplementedError
