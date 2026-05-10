# Exercise 10 — Conditional Variable Blocking Cache

## Goal

Implement a cache where readers can block until a key they need is set by a
writer, with optional timeout support.

## What you're implementing

```python
class BlockingCache:
    def set(self, key: str, value) -> None: ...
    def wait_get(self, key: str, timeout: float | None = None) -> Any: ...
```

## Behavior

- `set(key, value)` — stores the value and wakes all threads waiting for `key`.
- `wait_get(key, timeout=None)` — returns the value immediately if already set.
  If not yet set, blocks until a writer calls `set(key, ...)`.
  - If `timeout` is given and expires before the key is set, raises
    `TimeoutError`.
- Multiple threads may call `wait_get` for the same key concurrently — all are
  unblocked when the key is set.
- Values may be overwritten with a new `set`; readers that unblock after a
  re-set get the latest value.

## Concurrency tools

- `threading.Condition` — `wait(timeout)` blocks and returns `True` if notified
  (or `False` if timeout expired). `notify_all()` wakes all waiters.

## Test pressure

- 3 reader threads call `wait_get("k")` before the writer sets `"k"`.
- All 3 readers must unblock with the same value.
- Timeout test: `wait_get` with a short timeout raises `TimeoutError` when no
  writer comes.

## Gotchas

1. `Condition.wait(timeout)` returns `False` on timeout — check the return value
   and raise `TimeoutError` yourself.
2. Use a single `Condition` for all keys, or one per key. Single is simpler
   (spurious wakeups on other keys are handled by the `while key not in cache`
   predicate).
3. `notify_all()` is required — `notify()` might not wake all waiting threads.
4. `set()` must acquire the condition lock before modifying the dict, so that
   `notify_all()` is atomic with respect to readers checking the predicate.
5. Don't hold the condition lock during long-running work — here `set` is fast,
   so it's fine to hold it for the whole operation.

## Run

```bash
python3 test_solution.py
```
