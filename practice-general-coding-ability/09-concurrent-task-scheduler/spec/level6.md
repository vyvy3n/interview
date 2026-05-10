# Level 6 — Cancellation & Waiting

## What you're implementing

Extend `TaskScheduler` with task cancellation (including propagation through the dependency graph) and an event-based wait mechanism.

```python
class TaskScheduler:
    # ... (L1-L5 methods) ...
    def cancel_task(self, task_id: str) -> bool: ...
    def wait_for_completion(self, task_id: str, timeout: float = None) -> str: ...
```

## Mental model

Two final production features:

**Cancellation:** When a pending task is cancelled, its downstream dependents (tasks that depend on it) can never run — so they're cancelled too, recursively. This is how build systems handle failures: if "compile" is cancelled, there's no point running "test" or "deploy".

**Waiting:** Instead of polling `get_status` in a loop, callers can block on `wait_for_completion` and be woken up the instant a task reaches a terminal state. This is the `threading.Event` or `threading.Condition` pattern — efficient, not busy-wait.

## The 2 methods for Level 6

### 1. `cancel_task(task_id: str) -> bool`

Cancel a task and propagate cancellation to dependents.

| Situation | Returns | Effect |
|-----------|---------|--------|
| Task is `"pending"` | `True` | status → `"cancelled"`; propagate |
| Task is `"running"` | `True` | mark for cancellation (worker detects and stops early); status → `"cancelled"` when worker sees the flag; propagate |
| Task is `"completed"` | `False` | no change |
| Task is `"cancelled"` | `False` | already cancelled, no further propagation |
| Task does not exist | `False` | no change |

**Propagation:** After cancelling `task_id`, check every other task whose dependency list includes `task_id`. If that task is `"pending"` or `"running"`, cancel it too — and recurse.

`cancel_task` returns `True` if `task_id` itself was successfully cancelled (regardless of how many propagated cancellations occurred).

### 2. `wait_for_completion(task_id: str, timeout: float = None) -> str`

Block the calling thread until the task reaches a terminal state (`"completed"` or `"cancelled"`).

| Situation | Returns |
|-----------|---------|
| Task reaches `"completed"` or `"cancelled"` | that status string |
| `timeout` seconds elapse before terminal state | `""` |
| Task does not exist | `""` |
| `timeout=None` | block indefinitely |

Must use `threading.Condition` or `threading.Event` — **no busy-wait loops**.

## Worked example

```python
import time, threading
from solution import TaskScheduler

ts = TaskScheduler()

# --- Propagation example ---
ts.submit_task("a", 0.01)
ts.submit_task("b", 0.01)
ts.submit_task("c", 0.01)
ts.set_dependencies("b", ["a"])   # b depends on a
ts.set_dependencies("c", ["b"])   # c depends on b

assert ts.cancel_task("a") == True
assert ts.get_status("a") == "cancelled"
assert ts.get_status("b") == "cancelled"   # propagated
assert ts.get_status("c") == "cancelled"   # propagated transitively

# cancel already-cancelled: False
assert ts.cancel_task("a") == False

# --- wait_for_completion example ---
ts2 = TaskScheduler()
ts2.submit_task("job", 0.05)
ts2.start_workers(1)

# Wait up to 1 second — should complete well before that
result = ts2.wait_for_completion("job", timeout=1.0)
assert result == "completed"

ts2.stop_workers()

# Timeout example
ts3 = TaskScheduler()
ts3.submit_task("slow", 10.0)    # won't complete in time (no workers running)
result = ts3.wait_for_completion("slow", timeout=0.05)
assert result == ""              # timed out

# Missing task
ts4 = TaskScheduler()
assert ts4.wait_for_completion("ghost") == ""
```

## Constraints

- Propagation is recursive/transitive — if A's cancellation triggers B's cancellation, B's propagation must also run.
- Workers at L5 must be modified to check for a per-task cancellation flag (or re-check status after waking from sleep) to handle the "running → cancelled" case.
- `wait_for_completion` must be safe to call from multiple threads simultaneously on the same task.
- `timeout=None` means no timeout (block forever until terminal state).

## Concurrency notes

### Per-task completion events

Use a `threading.Condition` (shared with `self._lock`) or a per-task `threading.Event` to notify waiters when a task reaches a terminal state.

**Pattern with per-task Events:**
```python
# At submit time:
self._tasks[task_id]["event"] = threading.Event()

# When task reaches terminal state (completed or cancelled):
self._tasks[task_id]["event"].set()

# In wait_for_completion:
if task_id not in self._tasks:
    return ""
event = self._tasks[task_id]["event"]
if already_terminal:
    return current_status
# release lock, then wait
event.wait(timeout=timeout)
with self._lock:
    status = self._tasks[task_id]["status"]
    return status if status in ("completed", "cancelled") else ""
```

### Cancelling a running task

The cleanest approach: after `time.sleep(duration)` in the worker, re-check the task's status before marking it "completed":

```python
time.sleep(duration)
with self._lock:
    if self._tasks[task_id]["status"] == "running":
        self._tasks[task_id]["status"] = "completed"
        self._tasks[task_id]["event"].set()
    # if it was already "cancelled", leave it; event was already set by cancel_task
```

Alternatively, use a shorter sleep loop with early-exit on a cancellation flag — but the re-check approach is simpler and the tests accept it.

### Propagation implementation

```python
def _propagate_cancel(self, cancelled_id: str):
    # caller holds self._lock
    for tid, info in self._tasks.items():
        if cancelled_id in info.get("deps", set()):
            if info["status"] in ("pending", "running"):
                info["status"] = "cancelled"
                info["event"].set()
                self._propagate_cancel(tid)   # recurse
```

## Common gotchas

1. **Propagation is recursive** — cancelling A must cancel B which must cancel C. A single loop is not enough; recurse or BFS.
2. **`cancel_task` returns False for already-cancelled** — even if there are unvisited downstream tasks; the return value reflects only whether `task_id` itself was newly cancelled.
3. **`wait_for_completion` must check initial state** — if the task is already terminal when called, return immediately without blocking.
4. **Event must be set on every terminal transition** — "completed", "cancelled", and the L6 running→cancelled case all need `event.set()`.
5. **Don't hold the lock while waiting on the Event** — release the lock before calling `event.wait(timeout)` to avoid deadlock with worker threads.

## When you're done

```bash
python3 test_level6.py
```

Congratulations — you've implemented a production-grade concurrent task scheduler with priority queuing, dependency graphs, a worker pool, and robust cancellation.
