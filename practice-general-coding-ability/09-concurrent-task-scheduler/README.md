# Problem 09: Concurrent Task Scheduler

Build a task scheduler that grows from a simple status tracker into a full concurrent worker system — mirroring real production schedulers like Celery, RQ, and Sidekiq.

## Files

- `solution.py` — your implementation (`TaskScheduler` class)
- `spec/levelN.md` — spec for each level
- `test_levelN.py` — unittest test suite; run with `python3 test_levelN.py`

## Workflow

1. Read `spec/level1.md`
2. Implement the required methods in `solution.py`
3. Run `python3 test_level1.py` until all tests pass
4. Move to the next level — repeat

## The 6 levels (high-level only)

| Level | Title | Time | Key idea |
|-------|-------|------|----------|
| 1 | Submit & Complete | ~10 min | Basic task lifecycle |
| 2 | Status Reports | ~10 min | Listing and counting by status |
| 3 | Priorities | ~15 min | Priority queue with tie-breaking |
| 4 | Dependencies | ~15 min | DAG-based runnable detection |
| 5 | Concurrent Workers | ~20 min | Threading, locks, worker pool |
| 6 | Cancellation & Waiting | ~20 min | Cancellation propagation, Event-based blocking |

Levels 1–4 are fully sequential. Levels 5–6 introduce `threading` — no external libraries.

## Running tests

```bash
cd 09-concurrent-task-scheduler
python3 test_level1.py   # run after implementing L1
python3 test_level2.py   # run after implementing L2
# ...
python3 test_level6.py
```

Each file uses Python's standard `unittest` library and is self-contained.

## Notes for the assessment

- You will not be evaluated on code quality or readability.
- Execution speed only matters when explicitly mentioned.
- Don't worry about edge cases not covered by tests.
- Tests are the final word on requirements — read them freely and run them often.
