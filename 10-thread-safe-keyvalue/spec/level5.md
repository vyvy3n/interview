# Level 5 — Async Concurrent Access

## What you're implementing

Add async versions of the three core read/write methods. These use `asyncio.Lock` to protect shared state when many coroutines run concurrently:

```python
async def aget(self, key: str) -> str: ...
async def aput(self, key: str, value: str) -> None: ...
async def adelete(self, key: str) -> bool: ...
```

The synchronous methods from L1-L4 remain intact and unchanged.

## Mental model

Imagine 100 web-request handlers all hitting the same in-memory cache simultaneously. In Python's asyncio, coroutines run concurrently on a single thread — they interleave at `await` points. Without a lock, two coroutines could read-then-write the same key and one update could be silently lost.

`asyncio.Lock` fixes this: only one coroutine holds the lock at a time. The others `await` for it. This is analogous to a mutex but cooperative (yields at `await lock.acquire()`).

## The 3 async methods for Level 5

### A. `async aget(key: str) -> str`

Async version of `get`. Acquires the lock, reads the value, releases the lock, returns value or `""`.

### B. `async aput(key: str, value: str) -> None`

Async version of `put`. Acquires the lock, writes the value, releases the lock.

### C. `async adelete(key: str) -> bool`

Async version of `delete`. Acquires the lock, removes the key if present, releases the lock. Returns `True` if deleted, `False` if missing.

## Concurrency notes

### Setting up the lock

Initialize `asyncio.Lock()` in `__init__`:

```python
def __init__(self):
    self._store = {}
    self._lock = asyncio.Lock()
    # ... other state
```

### Using the lock

Always use `async with self._lock:` — it's cleaner than manual `acquire`/`release` and correctly releases on exceptions:

```python
async def aput(self, key: str, value: str) -> None:
    async with self._lock:
        self._store[key] = value
```

### Why sync methods don't need the lock

The sync methods (`get`, `put`, `delete`) don't acquire `self._lock` because:

1. asyncio is single-threaded — sync code can't be interrupted mid-operation by another coroutine.
2. Only at `await` points can another coroutine run.
3. The async methods use the lock to protect the critical section that includes the `await lock.acquire()`.

**Do not add lock acquisition to sync methods** — calling `await` from a sync context would be a syntax error anyway.

### The test strategy

Tests spawn 100+ concurrent coroutines via `asyncio.gather`. A naive implementation without the lock would pass most of the time (asyncio is single-threaded) — but the concurrent `aincrement` test at Level 6 is specifically designed to expose race conditions. At L5 we verify basic safety properties.

## Worked example

```python
import asyncio
from solution import KVStore

async def main():
    kv = KVStore()

    # Sequential async calls
    await kv.aput("name", "alice")
    val = await kv.aget("name")   # "alice"
    deleted = await kv.adelete("name")   # True
    val2 = await kv.aget("name")  # ""

    # Concurrent puts — all 100 should land
    await asyncio.gather(*[kv.aput(f"k{i}", str(i)) for i in range(100)])
    # every key k0..k99 must be present
    for i in range(100):
        assert await kv.aget(f"k{i}") == str(i)

asyncio.run(main())
```

## Constraints

- Use `asyncio.Lock` from the standard library — no external packages.
- The same `KVStore` instance is shared across all concurrent coroutines.
- Tests use `unittest.IsolatedAsyncioTestCase` which creates a fresh event loop per test method.
- Do NOT use `threading.Lock` at this level — use `asyncio.Lock`.

## Common gotchas

1. **`asyncio.Lock()` must be created inside an event loop or in `__init__`.** In modern Python (3.10+), creating it in `__init__` is fine. If you see "no running event loop" errors, move lock creation to the first async call or use `asyncio.get_event_loop()`.
2. **Always use `async with`**, not manual `acquire`/`release` — the latter leaks the lock on exceptions.
3. **The sync methods still work** — don't break them. Tests for L1-L4 still run.
4. **`asyncio.gather` runs coroutines concurrently, not in parallel.** They interleave at `await` points, which is all the concurrency asyncio provides.
5. **Don't hold the lock across unrelated awaits.** Grab it, do the work, release it. Don't `await` something unrelated while holding the lock.

## When you're done

```
python3 test_level5.py
```

All Level 5 tests must pass before moving to Level 6.
