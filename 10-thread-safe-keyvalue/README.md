# Problem 10: Async In-Memory Key-Value Store

A cache system that grows from simple sync operations into a fully async store with TTL, LRU eviction, and concurrent atomic operations.

Mirrors real-world cache design — Redis client patterns, in-memory caches with concurrent readers/writers. Levels 1-4 are synchronous; levels 5-6 introduce `asyncio` for concurrent client simulation.

## Files

- `solution.py` — your implementation (`KVStore` class)
- `spec/levelN.md` — the spec for each level (revealed sequentially)
- `test_levelN.py` — standard `unittest` runner; just `python3 test_levelN.py`

## Workflow

1. Read `spec/level1.md`
2. Implement `solution.py`
3. Run `python3 test_level1.py` until all tests pass
4. Move to next level — repeat

## The 6 levels (high-level only — don't think ahead)

1. Basic put / get / delete
2. Bulk operations and prefix queries
3. TTL / expiration with explicit timestamps
4. Capacity cap and LRU eviction
5. Async concurrent access with `asyncio.Lock`
6. Atomic compound operations (compare-and-set, get-and-set, increment)

## Concurrency note

Levels 5-6 use Python's `asyncio` stdlib — no external packages. Use `asyncio.Lock` to protect shared state. Tests use `unittest.IsolatedAsyncioTestCase` (Python 3.8+).

## Running tests

```bash
# Sync levels
python3 test_level1.py
python3 test_level2.py
python3 test_level3.py
python3 test_level4.py

# Async levels
python3 test_level5.py
python3 test_level6.py
```
