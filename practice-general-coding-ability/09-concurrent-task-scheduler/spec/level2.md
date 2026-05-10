# Level 2 — Status Reports

## What you're implementing

Extend `TaskScheduler` with two new methods. All Level 1 methods continue to work unchanged.

```python
class TaskScheduler:
    # ... (L1 methods) ...
    def list_by_status(self, status: str) -> list[str]: ...
    def count_by_status(self, status: str) -> int: ...
```

## Mental model

Now that you can track individual tasks, you want aggregate views: "show me everything that's pending" and "how many tasks are done?" These are common dashboard queries in any real scheduler — think Celery's `inspect().reserved()` or a Redis queue length check.

The key design point: `list_by_status` returns results **alphabetically sorted by task_id**. This makes test output deterministic regardless of the order tasks were submitted.

## The 2 methods for Level 2

### 1. `list_by_status(status: str) -> list[str]`

Return all task IDs currently in the given status.

| Situation | Returns |
|-----------|---------|
| Tasks exist with that status | sorted list of task_ids (alphabetical ascending) |
| No tasks have that status | `[]` |
| `status` is a string not in use | `[]` |

Sorting is **lexicographic** (standard Python `sort()`).

### 2. `count_by_status(status: str) -> int`

Return how many tasks have the given status.

| Situation | Returns |
|-----------|---------|
| Tasks exist with that status | count as `int` |
| No tasks have that status | `0` |

`count_by_status(s)` should always equal `len(list_by_status(s))`.

## Worked example

```python
ts = TaskScheduler()

ts.submit_task("banana", 2)
ts.submit_task("apple", 1)
ts.submit_task("cherry", 3)
ts.submit_task("date", 4)

# All pending
assert ts.count_by_status("pending") == 4
assert ts.list_by_status("pending") == ["apple", "banana", "cherry", "date"]
assert ts.count_by_status("completed") == 0
assert ts.list_by_status("completed") == []

ts.complete_task("banana")
ts.complete_task("date")

assert ts.count_by_status("pending") == 2
assert ts.list_by_status("pending") == ["apple", "cherry"]
assert ts.count_by_status("completed") == 2
assert ts.list_by_status("completed") == ["banana", "date"]
```

## Constraints

- Status strings passed in may be anything — if no tasks have that status, return `[]` / `0`.
- Sorting is standard Python lexicographic (uppercase comes before lowercase in ASCII, but tests use lowercase IDs).
- Up to 10,000 tasks.

## Common gotchas

1. **Sort on output, not on insert** — maintaining a sorted structure at insert time is harder than sorting at query time. Just call `sorted()` on the list when returning.
2. **count_by_status must be consistent with list_by_status** — derive one from the other or keep a single source of truth.
3. **Unknown status returns 0 / []** — don't raise KeyError if the status isn't in your internal dict.
4. **Alphabetical is case-sensitive in Python** — `"Apple" < "banana"` in ASCII, but tests use lowercase only.
5. **Don't mutate your internal state** when building the return list — return a new list, not a reference to internal storage.

## When you're done

```bash
python3 test_level2.py
```
