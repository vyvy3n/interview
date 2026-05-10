# Problem 11: Bank Account System

Build a bank progressively — from basic account lifecycle through concurrent, atomic operations — mirroring real-world financial system design patterns.

## Files

- `solution.py` — your implementation (`Bank` class)
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
| 1 | Account Lifecycle | ~10 min | open, balance, deposit, withdraw |
| 2 | Transfers + History | ~10 min | atomic transfers, per-account audit log |
| 3 | Scheduled Transfers | ~15 min | post-dated transfers, tick-based clock |
| 4 | Interest + Merge | ~15 min | basis-point interest, account consolidation |
| 5 | Concurrent Operations | ~20 min | RLock thread-safety, background scheduler |
| 6 | Atomic Compound Ops | ~20 min | CAS, all-or-nothing batch, condition-var waiting |

Levels 1–4 are fully sequential. Levels 5–6 introduce `threading` — no external libraries.

## Running tests

```bash
cd 11-bank-account-system
python3 test_level1.py   # run after implementing L1
python3 test_level2.py   # run after implementing L2
python3 test_level3.py   # run after implementing L3
python3 test_level4.py   # run after implementing L4
python3 test_level5.py   # run after implementing L5
python3 test_level6.py   # run after implementing L6
```

Each file uses Python's standard `unittest` library and is self-contained.

## Notes for the assessment

- You will not be evaluated on code quality or readability.
- Execution speed only matters when explicitly mentioned.
- Don't worry about edge cases not covered by tests.
- Tests are the final word on requirements — read them freely and run them often.
- For threading (Levels 5–6): use `threading.RLock` (reentrant, not plain `Lock`) to avoid deadlocks when methods call other methods.
