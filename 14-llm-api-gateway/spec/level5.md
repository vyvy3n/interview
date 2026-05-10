# Level 5 — Async Concurrent Request Handling

## What you're implementing

Add async versions of the four core gateway operations. These use `asyncio.Lock` to protect shared state when many coroutines access the gateway concurrently.

```python
async def aregister_user(self, user_id: str, tier: str) -> bool: ...
async def ahandle_request_at(self, user_id: str, prompt: str, tokens_used: int, now: int) -> str: ...
async def ahandle_cached_request(self, user_id: str, prompt: str, response: str, tokens_used: int, now: int) -> str: ...
async def aget_remaining_tokens_at(self, user_id: str, now: int) -> int: ...
```

**All synchronous methods from L1–L4 remain intact and unchanged.**

## Mental model

Imagine 1,000 clients simultaneously hitting the gateway. In Python's `asyncio`, coroutines run concurrently on a single thread — they interleave at `await` points. Without a lock, two coroutines could both see 500 tokens remaining, both decide the request fits, and both deduct 400 tokens — resulting in -300 tokens (a bug).

`asyncio.Lock` fixes this: only one coroutine holds the lock at a time. The others `await` for their turn. This makes the check-then-act sequence atomic.

## Concurrency notes

### Setting up the lock

Create `asyncio.Lock()` lazily on first use to avoid "no running event loop" errors in `__init__`:

```python
def _get_lock(self) -> asyncio.Lock:
    if self._lock is None:
        self._lock = asyncio.Lock()
    return self._lock
```

### Using the lock

```python
async def ahandle_request_at(self, user_id, prompt, tokens_used, now):
    async with self._get_lock():
        return self._do_handle_request_at(user_id, prompt, tokens_used, now)
```

### Internal helper pattern

Factor the logic into internal `_do_*` helpers that operate without touching the lock. Sync methods call them directly; async methods acquire the lock first:

```python
def handle_request_at(self, ...):
    return self._do_handle_request_at(...)

async def ahandle_request_at(self, ...):
    async with self._get_lock():
        return self._do_handle_request_at(...)
```

### Why sync methods don't need the lock

asyncio is single-threaded. Sync code is never interrupted by another coroutine — interruptions only happen at `await` points. Since sync methods don't `await` anything, they're already atomic from asyncio's perspective.

## Worked example

```python
import asyncio
from solution import LLMGateway

async def main():
    gw = LLMGateway()
    gw.set_tier_limits("free", 10_000, 0)

    # Register 50 users concurrently — all should succeed
    results = await asyncio.gather(*[
        gw.aregister_user(f"user{i}", "free") for i in range(50)
    ])
    assert sum(results) == 50

    # Re-register same users — all should fail
    results2 = await asyncio.gather(*[
        gw.aregister_user(f"user{i}", "free") for i in range(50)
    ])
    assert sum(results2) == 0

    # Concurrent requests that collectively exceed the bucket —
    # only some should succeed (never over-deduct)
    gw.set_tier_limits("limited", 500, 0)
    await gw.aregister_user("limited_user", "limited")
    results3 = await asyncio.gather(*[
        gw.ahandle_request_at("limited_user", f"p{i}", 100, 0)
        for i in range(20)
    ])
    ok_count = sum(1 for r in results3 if r == "ok")
    assert ok_count == 5  # exactly 500 / 100
    remaining = await gw.aget_remaining_tokens_at("limited_user", 0)
    assert remaining == 0

asyncio.run(main())
```

## Constraints

- Use `asyncio.Lock` from the standard library — no external packages.
- The same `LLMGateway` instance is shared across all concurrent coroutines.
- Tests use `unittest.IsolatedAsyncioTestCase` — a fresh event loop per test method.
- Do NOT use `threading.Lock` — this is async, not threaded.

## Common gotchas

1. **Lazy lock creation:** create `asyncio.Lock()` in `_get_lock()`, not in `__init__`. Otherwise Python may warn if there is no running event loop at construction time.
2. **Hold the lock for the FULL operation** — do not release it between the refill step and the deduction step. That window is where race conditions happen.
3. **Sync methods still work** — don't break them. Level 1–4 tests still run.
4. **Concurrent requests to same user with tight bucket:** the lock ensures exactly the right number of requests succeed (no over-deduction, no under-counting).
5. **Cache is also shared state** — `ahandle_cached_request` must hold the lock for the full read-check-write sequence on both the cache and the bucket.

## When you're done

```
python3 test_level5.py
```

All tests must pass before moving to Level 6.
