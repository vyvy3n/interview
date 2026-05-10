# Level 5 — Concurrent Workers

## What you're implementing

Extend `TaskScheduler` with a real worker pool that processes tasks concurrently using `threading`.

```python
class TaskScheduler:
    # ... (L1-L4 methods) ...
    def start_workers(self, count: int) -> None: ...
    def stop_workers(self) -> None: ...
```

All existing methods (L1–L4) must remain **thread-safe** at this level.

## Mental model

Until now, the scheduler was a passive data store — you had to manually call `complete_task`. Now it becomes active: worker threads continuously pull the next runnable task from the queue, mark it "running", simulate doing work (sleeping for `duration` seconds), and mark it "completed".

This is exactly how Celery workers operate: a pool of workers competing to pull tasks from a shared queue, each independently executing and reporting completion.

The scheduler's internal state is now shared across threads, so every mutation must be protected by a `threading.Lock`.

## The 2 methods for Level 5

### 1. `start_workers(count: int) -> None`

Spawn `count` new worker threads. Each worker loops:

1. Acquire the scheduler lock, call `get_next_runnable()` to find a task.
2. If a task is found, mark it `"running"`, release the lock.
3. Sleep for `task.duration` seconds (simulating work). **Release the lock during sleep.**
4. Re-acquire the lock, mark task `"completed"`, release the lock.
5. If no task was found, release the lock and briefly sleep (e.g., 0.005 s) before retrying.
6. Repeat until a stop signal is set.

| Situation | Behavior |
|-----------|----------|
| `count=2` called once | 2 worker threads running |
| `start_workers` called again with `count=3` | 3 more threads added (5 total) |
| Workers already stopped | new workers start fresh |

### 2. `stop_workers() -> None`

Signal all running workers to stop and block until they have all exited.

| Situation | Behavior |
|-----------|----------|
| Workers are idle (no task) | exit at next loop iteration |
| Worker is mid-task | finish the current task, then exit |
| No workers running | no-op |

After `stop_workers()` returns, all worker threads have been joined.

## get_status additions

`get_status(task_id)` now also returns:

| Status | Meaning |
|--------|---------|
| `"running"` | A worker has claimed the task and is sleeping through its duration |

## Worked example

```python
import time
from solution import TaskScheduler

ts = TaskScheduler()

# Submit tasks with tiny durations (0.01 s each)
ts.submit_task("job1", 0.01)
ts.submit_task("job2", 0.01)
ts.submit_task("job3", 0.01)

ts.start_workers(2)   # 2 workers race to claim tasks

time.sleep(0.2)       # give them time to finish

ts.stop_workers()

assert ts.get_status("job1") == "completed"
assert ts.get_status("job2") == "completed"
assert ts.get_status("job3") == "completed"
assert ts.count_by_status("pending")   == 0
assert ts.count_by_status("running")   == 0
assert ts.count_by_status("completed") == 3
```

## Constraints

- Worker `duration` values in tests are very small floats (e.g., `0.01` seconds). Tests complete in under 2 seconds.
- `submit_task(task_id, duration)` — at this level, `duration` is a float (seconds). The existing tests that used int durations still work fine since workers were not present.
- All state mutations must hold a `threading.Lock` — never mutate shared state without the lock.
- Workers must release the lock while sleeping — holding the lock during sleep blocks other threads.
- `stop_workers()` must join all threads — don't return before threads exit.

## Concurrency notes

### Lock discipline

Use a single `threading.Lock` (e.g., `self._lock`) to protect all reads/writes of the task dict, dependency graph, and submission counter.

**Pattern:**
```python
with self._lock:
    task_id = self.get_next_runnable()
    if task_id:
        self._tasks[task_id]["status"] = "running"
    # lock is released here

if task_id:
    time.sleep(duration)    # <- outside the lock!
    with self._lock:
        self._tasks[task_id]["status"] = "completed"
```

### Stop signal

Use a `threading.Event` for the stop signal:

```python
self._stop_event = threading.Event()

# In worker loop:
while not self._stop_event.is_set():
    ...

# In stop_workers:
self._stop_event.set()
for t in self._threads:
    t.join()
self._threads.clear()
self._stop_event.clear()   # allow future start_workers calls
```

### Thread safety for L1-L4 methods

Wrap every existing method body with `with self._lock:`. This is safe because:
- Reads (get_status, list_by_status, get_next_runnable) are read-only.
- Workers acquire the lock atomically to claim tasks, preventing double-claiming.

## Common gotchas

1. **Never hold the lock during `time.sleep`** — this serializes all workers, defeating concurrency.
2. **`start_workers` is additive** — each call adds more threads; don't reset the thread list.
3. **`get_next_runnable` inside the lock** — claim must be atomic: find-and-mark-running in one critical section, then release before sleeping.
4. **Join all threads in `stop_workers`** — returning early (before join) can cause assertion failures in tests that check post-stop state.
5. **`count_by_status("running")` must work** — the "running" status is real and queryable via the existing L2 methods.

## When you're done

```bash
python3 test_level5.py
```
