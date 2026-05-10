# Level 5 — Concurrent Operations (Threading)

## What you're implementing

Make all L1–L4 methods **thread-safe** and add a background scheduler:

```python
class Bank:
    # ... (L1-L4 methods, now thread-safe) ...
    def start_scheduler(self, check_interval: float = 0.05) -> None: ...
    def stop_scheduler(self) -> None: ...
    def advance_time(self, amount: int) -> int: ...
```

## Mental model

Before this level, the Bank was a passive data store — callers drove all state changes synchronously. Now it becomes **active**: a background thread periodically fires `advance_time`, which ticks the internal clock and triggers any due scheduled transfers automatically.

At the same time, multiple external threads may call deposit/withdraw/transfer concurrently. Without proper locking, two threads could both read "balance = $500", both subtract $300, and both store $200 — net $300 disappearing from the bank.

The fix is a single `threading.RLock` (`RLock` because some methods call other methods that also acquire the lock — a regular `Lock` would deadlock). Every method acquires the lock at entry and releases it at exit.

## The 3 methods for Level 5

### 1. `advance_time(amount: int) -> int`

Advance the bank's internal clock by `amount` and execute any newly due scheduled transfers.

| Situation | Behavior |
|-----------|----------|
| Normal | `self._clock += amount`; calls `tick(self._clock)`; returns count of executed transfers |

This method is called both by the background scheduler and by external test code.

### 2. `start_scheduler(check_interval: float = 0.05) -> None`

Start a background thread that periodically calls `advance_time(1)`.

| Situation | Behavior |
|-----------|----------|
| No scheduler running | Start one background thread |
| Scheduler already running | Return immediately (no-op; do NOT start a second thread) |

Background thread loop:
```python
while not self._stop_event.is_set():
    self.advance_time(1)
    time.sleep(check_interval)
```

Use `threading.Event` for the stop signal. Use `daemon=True` so the thread doesn't block interpreter exit.

### 3. `stop_scheduler() -> None`

Signal the scheduler to stop and join the thread.

| Situation | Behavior |
|-----------|----------|
| Scheduler running | Set stop event, join thread, clear state |
| No scheduler running | No-op |

After `stop_scheduler()` returns, the background thread has exited. A subsequent call to `start_scheduler()` must work correctly.

## Thread-safety requirements

- Add `self._lock = threading.RLock()` in `__init__`.
- Wrap every method body with `with self._lock:`.
- Use `RLock` (reentrant lock) — some methods call other methods that also acquire the lock (e.g., `advance_time` calls `tick`).
- The background scheduler thread calls `advance_time` in a loop; `advance_time` acquires the lock internally, so the scheduler loop itself does NOT need to hold the lock.

## Worked example

```python
import time
from solution import Bank

b = Bank()
b.open_account("alice")
b.open_account("bob")
b.deposit("alice", 1000)

# Schedule a transfer at clock tick 5
s = b.schedule_transfer("alice", "bob", 200, execute_at=5)

# Start the background scheduler (ticks once every 0.05 s)
b.start_scheduler(check_interval=0.05)

# After 0.5 s, the clock has advanced >= 5 ticks
time.sleep(0.5)

b.stop_scheduler()

assert b.get_balance("alice") == 800
assert b.get_balance("bob")   == 200

# Concurrent deposits from multiple threads
b2 = Bank()
b2.open_account("shared")
import threading

def add_funds():
    for _ in range(100):
        b2.deposit("shared", 10)

threads = [threading.Thread(target=add_funds) for _ in range(5)]
for t in threads: t.start()
for t in threads: t.join()

assert b2.get_balance("shared") == 5000   # 5 threads × 100 deposits × $10
```

## Constraints

- All L1–L4 methods must be thread-safe.
- Use `threading.RLock`, not `threading.Lock`, to allow reentrant acquisition.
- Only one scheduler thread at a time — `start_scheduler` is idempotent.
- Tests use tiny `check_interval` values (0.01–0.05 s) and short sleeps for fast turnaround.

## Concurrency notes

### Why RLock?

```python
def advance_time(self, amount: int) -> int:
    with self._lock:          # acquires lock (count = 1)
        self._clock += amount
        return self.tick(self._clock)  # tick() also does "with self._lock:" -> count = 2

def tick(self, now: int) -> int:
    with self._lock:          # reentrant: count goes 1->2->1, not deadlock
        ...
```

A regular `Lock` would deadlock at the inner `with self._lock:`. `RLock` tracks the owning thread and allows re-acquisition.

### Stop-then-restart pattern

```python
self._stop_event = threading.Event()

# In stop_scheduler:
self._stop_event.set()
self._scheduler_thread.join()
self._scheduler_thread = None
# Do NOT clear the stop event here — clear it in start_scheduler before starting the new thread
```

## Common gotchas

1. **Use `RLock`, not `Lock`** — methods call other methods that acquire the lock; a `Lock` deadlocks.
2. **`start_scheduler` is idempotent** — guard against starting a second thread if one is already alive.
3. **`stop_scheduler` must join the thread** — returning before join can cause test failures that check post-stop state.
4. **Background thread uses `daemon=True`** — prevents the interpreter from hanging if the test process ends without calling `stop_scheduler`.
5. **`advance_time` returns the tick count** — the return value from `tick` must be propagated.

## When you're done

```bash
python3 test_level5.py
```
