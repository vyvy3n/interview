# Exercise 07 — Readers-Writers Lock

## Goal

Implement a lock that allows multiple concurrent readers but only one exclusive
writer, with no readers active during a write.

## What you're implementing

```python
class RWLock:
    def read_acquire(self)  -> None: ...
    def read_release(self)  -> None: ...
    def write_acquire(self) -> None: ...
    def write_release(self) -> None: ...
```

## Behavior

- Multiple threads may hold the read lock simultaneously.
- Only one thread may hold the write lock at a time.
- No thread may hold the read lock while any thread holds the write lock.
- If readers are continuously arriving, writers must not starve indefinitely.
  (A basic readers-preferred implementation is acceptable for this exercise.)
- Methods must not raise when called in the correct acquire/release sequence.

## Concurrency tools

- `threading.Lock` — the underlying mutex.
- `threading.Condition` — `wait()` for writers blocked by active readers;
  `notify_all()` to wake writers after the last reader exits.

## Test pressure

- 10 reader threads + 2 writer threads, all running concurrently.
- Tests verify:
  1. At some point, 2+ readers are active simultaneously (parallelism).
  2. Whenever a writer is active, zero readers are active (exclusion).
  3. No deadlock — all threads finish within the timeout.

## Gotchas

1. Track `_reader_count` (int). The first reader acquires the write-lock; the
   last reader releases it. This is the classic "first reader-writer" pattern.
2. Alternatively: use a Condition and check `_reader_count == 0` before a
   writer proceeds. This avoids the nested-lock pattern.
3. The `Condition` object wraps a `Lock`. Only one Condition per RWLock is
   needed.
4. Writers must `notify_all()` (not `notify()`) when they finish, in case
   multiple readers are waiting.
5. Use `with self._condition:` as the outer guard, then `wait()` inside a
   `while` loop checking the predicate.

## Run

```bash
python3 test_solution.py
```
