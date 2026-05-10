# Problem 12: Multi-Tenant File Cache

A constrained file cache shared by multiple tenants. Levels 1–3 build a single-tenant cache with LRU eviction; Level 4 adds multi-tenancy with per-tenant quotas; Levels 5–6 layer on `asyncio` concurrency and atomic compound operations.

This domain combines two recurring Anthropic CodeSignal themes: **constrained file cache** and **cloud database simulation**. Expect questions about LRU correctness, quota accounting, and race-condition safety.

## Files

- `solution.py` — your implementation (`FileCache` class)
- `spec/levelN.md` — the spec for each level (revealed sequentially)
- `test_levelN.py` — standard `unittest` runner; just `python3 test_levelN.py`

## Workflow

1. Read `spec/level1.md`
2. Implement `solution.py`
3. Run `python3 test_level1.py` until all tests pass
4. Move to next level — repeat

## The 6 levels (high-level only — don't think ahead)

1. Basic file ops — store, fetch, remove, size
2. Updates and prefix queries
3. Cache-wide capacity with LRU eviction
4. Multi-tenant namespacing with per-tenant quotas
5. Async concurrent access with `asyncio.Lock`
6. Atomic compound operations (compare-and-update, store-or-update, bulk store)

## Concurrency note

Levels 5–6 use Python's `asyncio` stdlib — no external packages. Use `asyncio.Lock` to protect shared state. Tests use `unittest.IsolatedAsyncioTestCase` (Python 3.8+).

## Running tests

```bash
python3 test_level1.py
python3 test_level2.py
python3 test_level3.py
python3 test_level4.py
python3 test_level5.py
python3 test_level6.py
```
