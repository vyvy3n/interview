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
        self._cond = threading.Condition()

    def put(self, item: Any) -> None:
        """Enqueue item.  Blocks if the queue is at capacity."""
        with self._cond: 
            while len(self._queue) >= self._capacity:
                # atomically release the lock and sleep
                # until someone notifies (typically after a get removed an item).
                self._cond.wait()  
            self._queue.append(item)
            self._cond.notify_all()

    def get(self) -> Any:
        """Dequeue and return the front item.  Blocks if the queue is empty."""
        with self._cond:
            while len(self._queue) == 0:
                self._cond.wait()
            item = self._queue.popleft()
            self._cond.notify_all()
            return item
