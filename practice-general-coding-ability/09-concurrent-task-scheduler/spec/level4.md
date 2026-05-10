# Level 4 — Dependencies

## What you're implementing

Extend `TaskScheduler` with a dependency graph and a smarter "next task" method that only returns tasks whose dependencies are fully satisfied.

```python
class TaskScheduler:
    # ... (L1-L3 methods) ...
    def set_dependencies(self, task_id: str, dep_ids: list[str]) -> bool: ...
    def get_next_runnable(self) -> str: ...
```

## Mental model

In real pipelines (think CI/CD, data ETL, build systems), tasks have prerequisites. You can't run "deploy" until "build" and "test" both finish. This level adds that DAG (directed acyclic graph) structure to the scheduler.

`set_dependencies(task_id, dep_ids)` wires up the graph. `get_next_runnable()` then applies both the priority ordering from Level 3 AND the constraint that all dependencies must be `"completed"` before a task is eligible.

A task with no dependencies (or an empty `dep_ids` list) is always runnable if it's pending. Cycle detection is required — setting up a cycle must return `False`.

## The 2 methods for Level 4

### 1. `set_dependencies(task_id: str, dep_ids: list[str]) -> bool`

Register the dependency list for a task. This **replaces** any previously set dependencies.

| Situation | Returns |
|-----------|---------|
| `task_id` does not exist | `False` |
| Any `dep_id` in `dep_ids` does not exist | `False` |
| Setting the dependencies would create a cycle | `False` |
| Otherwise | `True`, dependencies updated |

**Cycle definition:** task A depends on task B, and B (directly or transitively) depends on A.

`dep_ids` can be an empty list — this removes all dependencies from `task_id`.

### 2. `get_next_runnable() -> str`

Like `get_next_task()` but only considers tasks that are **runnable**: pending AND all dependencies are `"completed"`.

| Situation | Returns |
|-----------|---------|
| At least one pending task has all deps completed | task_id with highest priority; ties by submission order |
| No runnable tasks exist | `""` |

- Read-only: does not change any task status.
- A task with no dependencies is runnable (if pending).

## Worked example

```python
ts = TaskScheduler()

ts.submit_task("build",  5)
ts.submit_task("test",   3)
ts.submit_task("deploy", 1)
ts.submit_task("notify", 1)

# Wire up: test depends on build; deploy depends on test; notify depends on deploy
assert ts.set_dependencies("test",   ["build"])  == True
assert ts.set_dependencies("deploy", ["test"])   == True
assert ts.set_dependencies("notify", ["deploy"]) == True

# Cycle: build -> test -> deploy -> notify -> build would be a cycle
assert ts.set_dependencies("build", ["notify"]) == False   # cycle detected

# Only "build" has no unmet dependencies
assert ts.get_next_runnable() == "build"
assert ts.get_next_task()     == "build"   # get_next_task still works (ignores deps)

ts.complete_task("build")
assert ts.get_next_runnable() == "test"    # build is done, test is now runnable

ts.complete_task("test")
assert ts.get_next_runnable() == "deploy"

ts.complete_task("deploy")
assert ts.get_next_runnable() == "notify"

ts.complete_task("notify")
assert ts.get_next_runnable() == ""        # all done

# set_dependencies with unknown ids
ts2 = TaskScheduler()
ts2.submit_task("a", 1)
assert ts2.set_dependencies("a",      ["ghost"]) == False  # "ghost" doesn't exist
assert ts2.set_dependencies("ghost",  ["a"])     == False  # "ghost" itself doesn't exist
assert ts2.set_dependencies("a",      [])        == True   # empty list clears deps
```

## Constraints

- Up to 1,000 tasks with up to 1,000 dependency edges total.
- `set_dependencies` fully replaces the dependency list each time it's called.
- No self-dependency in test inputs (a task depending on itself), but cycle detection would catch it anyway.
- `get_next_runnable()` only checks whether deps are `"completed"` — a dep that is "pending" or "running" blocks the dependent task.

## Common gotchas

1. **Cycle detection must be transitive** — DFS or BFS from the dep_ids to check if `task_id` is reachable. A simple direct-link check is not enough.
2. **`set_dependencies` replaces, not appends** — calling it twice on the same task with different lists uses the second list only.
3. **Empty `dep_ids` is valid** — it removes all dependencies. Don't treat `[]` as an error.
4. **`get_next_task` (L3) is unaffected** — it still ignores dependencies. Only `get_next_runnable` enforces them.
5. **A task whose dep is "running" (L5+) is NOT runnable** — only `"completed"` deps count as satisfied.

## When you're done

```bash
python3 test_level4.py
```
