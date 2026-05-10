# Level 1 — Submit & Complete

## What you're implementing

You write a **class** `TaskScheduler` in `solution.py`:

```python
class TaskScheduler:
    def submit_task(self, task_id: str, duration: int) -> bool: ...
    def get_status(self, task_id: str) -> str: ...
    def complete_task(self, task_id: str) -> bool: ...
```

Each test creates a fresh `TaskScheduler()` instance and calls these three methods.

## Mental model

Think of `TaskScheduler` as a whiteboard where you track jobs. When someone calls `submit_task("t1", 5)`, you write "t1: pending, duration=5" on the board. When they call `complete_task("t1")`, you erase "pending" and write "completed". `get_status` lets anyone ask what state a task is in.

Duration is stored but not acted on yet — it will matter in Levels 5 and 6 when real workers run tasks.

## The 3 methods for Level 1

### 1. `submit_task(task_id: str, duration: int) -> bool`

Register a new task with status `"pending"`.

| Situation | Returns |
|-----------|---------|
| `task_id` is new | `True` |
| `task_id` already exists (any status) | `False` |

- `duration` is a positive integer (seconds the task takes to run — stored for later).
- Default priority is `0` (used in Level 3).

### 2. `get_status(task_id: str) -> str`

Read the current status of a task.

| Situation | Returns |
|-----------|---------|
| Task exists | its status string (`"pending"`, `"completed"`) |
| Task does not exist | `""` (empty string) |

### 3. `complete_task(task_id: str) -> bool`

Mark a pending task as completed.

| Situation | Returns |
|-----------|---------|
| Task exists and is `"pending"` | `True`, status → `"completed"` |
| Task does not exist | `False` |
| Task is already `"completed"` | `False` |

## Worked example

```python
ts = TaskScheduler()

# Submit two tasks
assert ts.submit_task("t1", 3) == True    # new task — returns True
assert ts.submit_task("t2", 7) == True    # another new task
assert ts.submit_task("t1", 1) == False   # duplicate — returns False

# Check statuses
assert ts.get_status("t1") == "pending"
assert ts.get_status("t2") == "pending"
assert ts.get_status("t99") == ""         # unknown task

# Complete a task
assert ts.complete_task("t1") == True     # t1 goes pending -> completed
assert ts.get_status("t1") == "completed"

# Can't complete again or complete missing
assert ts.complete_task("t1") == False    # already completed
assert ts.complete_task("t99") == False   # doesn't exist
```

## Constraints

- `task_id` is any non-empty string.
- `duration` is a positive integer.
- Up to 10,000 tasks per test.
- No concurrency at this level — all calls are sequential.

## Common gotchas

1. **Duplicate check spans all statuses** — a task that is already "completed" still blocks a re-submit with the same id.
2. **`complete_task` must check existence first** — don't assume the task exists.
3. **Return types matter** — return Python `bool`, not the strings `"True"/"False"`.
4. **`get_status` returns `""` not `None`** for missing tasks.
5. **Duration is stored, not validated further** — the tests only pass positive ints, so no need to guard against negatives.

## When you're done

```bash
python3 test_level1.py
```

All tests in `TestLevel1` must pass before moving to Level 2.
