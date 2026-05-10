# Level 5 — Async Concurrent Access

## What you're implementing

Add async versions of the core read/write methods. These use `asyncio.Lock` to protect shared state when many coroutines access the cache concurrently:

```python
async def astore(self, filename: str, content: str) -> bool: ...
async def afetch(self, filename: str) -> str: ...
async def aremove(self, filename: str) -> bool: ...
async def aupdate(self, filename: str, content: str) -> bool: ...
async def atenant_store(self, tenant_id: str, filename: str, content: str) -> bool: ...
async def atenant_fetch(self, tenant_id: str, filename: str) -> str: ...
async def atenant_remove(self, tenant_id: str, filename: str) -> bool: ...
async def atenant_update(self, tenant_id: str, filename: str, content: str) -> bool: ...
```

**All synchronous methods from L1–L4 remain intact and unchanged.**

## Mental model

Imagine 100 microservices all sharing the same in-memory file cache simultaneously. In Python's `asyncio`, coroutines run concurrently on a single thread — they interleave at `await` points. Without a lock, two coroutines could both see "file not found", both decide to store it, and one would return `True` even though the file already exists (corrupting the quota count).

`asyncio.Lock` fixes this: only one coroutine holds the lock at a time. The others `await` for it. This is analogous to a mutex but cooperative.

## Concurrency notes

### Setting up the lock

Initialize `asyncio.Lock()` lazily on first use, or in `__init__`. If you create it in `__init__`, it may need to be created lazily in environments where no event loop is running yet:

```python
def _get_lock(self) -> asyncio.Lock:
    if self._lock is None:
        self._lock = asyncio.Lock()
    return self._lock
```

### Using the lock

Always use `async with self._get_lock():` — it correctly releases on exceptions and is cleaner than manual `acquire`/`release`:

```python
async def astore(self, filename: str, content: str) -> bool:
    async with self._get_lock():
        # call the same internal helper that sync store() uses
        return self._do_store(filename, content)
```

### Internal helper pattern

The cleanest implementation shares logic via internal `_do_*` helpers that do the work without touching the lock. The sync methods call these directly; the async methods acquire the lock first:

```python
def store(self, filename: str, content: str) -> bool:
    return self._do_store(filename, content)

async def astore(self, filename: str, content: str) -> bool:
    async with self._get_lock():
        return self._do_store(filename, content)
```

### Why sync methods don't need the lock

asyncio is single-threaded. Sync code cannot be interrupted by another coroutine — interruptions only happen at `await` points. The sync methods don't `await` anything, so they're already atomic from asyncio's perspective.

**Do not add lock acquisition to sync methods** — calling `await` from sync context is a syntax error.

## Worked example

```python
import asyncio
from solution import FileCache

async def main():
    cache = FileCache()

    # Sequential async calls
    await cache.astore("readme.txt", "hello")
    val = await cache.afetch("readme.txt")   # "hello"
    removed = await cache.aremove("readme.txt")  # True
    val2 = await cache.afetch("readme.txt")  # ""

    # Concurrent stores to different files — all 50 must land
    await asyncio.gather(*[cache.astore(f"f{i}.txt", f"v{i}") for i in range(50)])
    for i in range(50):
        assert await cache.afetch(f"f{i}.txt") == f"v{i}"

    # Concurrent stores to SAME file — exactly 1 must succeed
    results = await asyncio.gather(*[cache.astore("shared.txt", str(i)) for i in range(50)])
    assert sum(results) == 1  # exactly one True

asyncio.run(main())
```

## Constraints

- Use `asyncio.Lock` from the standard library — no external packages.
- The same `FileCache` instance is shared across all concurrent coroutines.
- Tests use `unittest.IsolatedAsyncioTestCase` — a fresh event loop per test method.
- Do NOT use `threading.Lock` — this is async, not threading.

## Common gotchas

1. **Lazy lock creation:** if you create `asyncio.Lock()` in `__init__`, some Python versions warn if there's no running event loop. Use a `_get_lock()` helper that creates it on first use.
2. **Always use `async with`**, not manual `acquire`/`release` — the `with` form releases correctly even on exceptions.
3. **The sync methods still work** — don't break them. Tests for L1–L4 still run.
4. **Concurrent stores to the same file:** exactly one coroutine acquires the lock, sees the file is absent, stores it, and returns `True`. All others acquire the lock sequentially and see the file already exists, returning `False`.
5. **Quota accounting must be correct under concurrency** — with the lock, each coroutine's check-then-act is atomic, so quota cannot be exceeded.

## When you're done

```
python3 test_level5.py
```

All tests must pass before moving to Level 6.
