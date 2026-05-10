# Level 3 — Priorities

## What you're implementing

Extend `TaskScheduler` with priority-aware submission and a "next task" retrieval method.

```python
class TaskScheduler:
    # ... (L1-L2 methods) ...
    def submit_task_with_priority(self, task_id: str, duration: int, priority: int) -> bool: ...
    def get_next_task(self) -> str: ...
```

## Mental model

Real schedulers don't treat all tasks equally. A "send email" job might have lower priority than a "charge credit card" job. In this level, every task gets a numeric priority — higher number means run first. When you call `get_next_task()`, you get back the highest-priority pending task.

Tie-breaking is by **submission order**: if two tasks share the same priority, the one submitted first wins. This is the classic priority queue semantics (like Python's `heapq` with a sequence counter as a secondary sort key).

Note: `submit_task()` from Level 1 still works — it submits with priority `0`.

## The 2 methods for Level 3

### 1. `submit_task_with_priority(task_id: str, duration: int, priority: int) -> bool`

Like `submit_task` but with an explicit priority.

| Situation | Returns |
|-----------|---------|
| `task_id` is new | `True`, task stored with given priority |
| `task_id` already exists | `False` |

- `priority` can be any integer (positive, zero, or negative).
- `submit_task(task_id, duration)` is equivalent to `submit_task_with_priority(task_id, duration, 0)`.

### 2. `get_next_task() -> str`

Return the task_id of the best pending task to run next.

| Situation | Returns |
|-----------|---------|
| There are pending tasks | task_id with highest priority; ties broken by earliest submission |
| No pending tasks | `""` |

- **Does NOT change task status** — this is a read-only peek, not a claim.
- Only considers tasks with status `"pending"`.

## Worked example

```python
ts = TaskScheduler()

# Submit order: a (pri=5), b (pri=10), c (pri=5), d (pri=1)
ts.submit_task_with_priority("a", 1, 5)
ts.submit_task_with_priority("b", 1, 10)
ts.submit_task_with_priority("c", 1, 5)
ts.submit_task_with_priority("d", 1, 1)

# b has highest priority
assert ts.get_next_task() == "b"

# complete b — now a and c tie at priority 5, a was submitted first
ts.complete_task("b")
assert ts.get_next_task() == "a"

ts.complete_task("a")
assert ts.get_next_task() == "c"

ts.complete_task("c")
assert ts.get_next_task() == "d"

ts.complete_task("d")
assert ts.get_next_task() == ""   # nothing left

# submit_task (no priority) defaults to priority 0
ts2 = TaskScheduler()
ts2.submit_task("x", 2)             # priority 0
ts2.submit_task_with_priority("y", 2, -1)  # lower priority
assert ts2.get_next_task() == "x"   # x wins (priority 0 > -1)
```

## Constraints

- Priority is any integer.
- Submission order is determined by the sequence in which `submit_task` / `submit_task_with_priority` is called.
- `get_next_task()` is read-only — calling it twice in a row returns the same result (as long as no tasks are added/completed between calls).
- Up to 10,000 tasks.

## Common gotchas

1. **get_next_task does NOT claim the task** — the task stays "pending" after the call. Don't change its status.
2. **Tie-breaking by submission order, not alphabetical** — if "z" is submitted before "a" and both have equal priority, "z" wins.
3. **submit_task must keep priority 0** — L1's `submit_task` is a special case of this level's method. Wire them together.
4. **Scanning all tasks is OK at this level** — no explicit performance requirement. A simple loop through pending tasks with `max()` is fine.
5. **Negative priorities are valid** — `priority=-999` is legal. Don't clamp or reject negative values.

## When you're done

```bash
python3 test_level3.py
```
