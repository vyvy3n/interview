# Exercise 04 — Bounded Blocking Queue

## Goal

Implement a thread-safe FIFO queue with a maximum capacity. Producers block when
the queue is full; consumers block when the queue is empty.

## What you're implementing

```python
class BoundedQueue:
    def __init__(self, capacity: int) -> None: ...
    def put(self, item) -> None: ...   # blocks if full
    def get(self) -> Any: ...          # blocks if empty
```

## Behavior

- `put(item)` — enqueues `item`. If the queue is at capacity, blocks the calling
  thread until a consumer calls `get()`.
- `get()` — dequeues and returns the front item. If the queue is empty, blocks
  the calling thread until a producer calls `put()`.
- Order is FIFO.
- Thread-safe: any number of producer and consumer threads may call these methods
  concurrently.

## Concurrency tools

- `threading.Condition` — wraps a lock and provides `wait()` / `notify()`.
  Use a single `Condition` to coordinate both the "not full" and "not empty"
  predicates, or use two separate ones.

## Test pressure

- 5 producer threads + 5 consumer threads, capacity 10, 1000 items total.
- All 1000 items must be consumed exactly once (no duplicates, no drops).
- Tests use a `multiset` comparison to verify correctness.

## Gotchas

1. Always call `wait()` inside a `while` loop, not an `if` — spurious wake-ups
   are real, and another thread may have consumed the slot between when you were
   notified and when you reacquired the lock.
2. `Condition.wait()` atomically releases the lock and blocks. The lock is
   re-acquired before `wait()` returns.
3. Use `notify_all()` rather than `notify()` if you have both producer and
   consumer waiters on the same Condition — `notify()` might wake the wrong kind.
4. `collections.deque` is your friend for the internal buffer (O(1) append/pop).
5. Capacity of 0 should be rejected (raise ValueError) or treated as unbounded —
   pick one and document it. The tests use capacity ≥ 1.

## Run

```bash
python3 test_solution.py
```
