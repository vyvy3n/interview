# Exercise 01 — Thread-Safe Counter

## Goal

Implement a counter that is safe to increment from multiple threads simultaneously.

## What you're implementing

```python
class Counter:
    def increment(self, delta: int = 1) -> None: ...
    def value(self) -> int: ...
```

## Behavior

- `increment(delta=1)` — adds `delta` to the internal count.
- `value()` — returns the current count.
- Both methods must be safe to call from any number of concurrent threads without
  lost updates.

## Concurrency tools

- `threading.Lock` — acquire before read-modify-write, release after.

## Test pressure

- 1000 threads each call `increment()` 1000 times → final value must be exactly
  1,000,000.
- Without a lock the test reliably fails due to race conditions on the
  read-modify-write inside `+=`.

## Gotchas

1. `count += 1` is **not atomic** in CPython — it compiles to LOAD / ADD / STORE,
   and the GIL can release between any bytecode instruction.
2. Use the lock as a context manager (`with self._lock:`) so it is always released,
   even on exceptions.
3. `value()` also needs the lock; a reader racing with a writer can see a
   partially-written int on non-CPython implementations.
4. Do not hold the lock longer than necessary — keep the critical section small.
5. `threading.Lock` is not reentrant; do not call `increment` from inside a block
   that already holds the same lock.

## Run

```bash
python3 test_solution.py
```
