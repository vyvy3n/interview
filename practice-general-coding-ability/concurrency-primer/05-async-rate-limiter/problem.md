# Exercise 05 — Async Rate Limiter

## Goal

Implement an async rate limiter that allows at most N requests per second.

## What you're implementing

```python
class RateLimiter:
    def __init__(self, rate: int) -> None: ...
    async def acquire(self) -> None: ...
```

## Behavior

- `rate` — maximum number of `acquire()` calls allowed per second.
- `acquire()` — a coroutine that returns only when the caller is permitted to
  proceed. If the rate would be exceeded, it sleeps until the next available slot.
- Callers should call `await limiter.acquire()` before performing their
  rate-limited work.

## Concurrency tools

- `asyncio.Semaphore` — limit how many coroutines are active at once.
- `asyncio.sleep` — release the semaphore slot after 1 second.

### Recommended pattern (token-bucket via semaphore + background release)

```
acquire semaphore slot
schedule: asyncio.sleep(1.0) then release that slot
return immediately
```

This gives a sliding-window token bucket with `rate` slots replenished each
second.

## Test pressure

- 10 concurrent `acquire()` calls, rate=2/sec.
- Minimum expected elapsed time: ~4 seconds (10 calls ÷ 2/sec = 5 bursts,
  but first burst is free so 4 sleeps of 1s).
- Tests use wall-clock time with a 20% tolerance.

## Gotchas

1. Do NOT use a plain counter + sleep in `acquire()` — that serializes all
   callers. The semaphore release must happen in a background task so the
   caller returns immediately.
2. `asyncio.Semaphore` is not thread-safe — only use it from coroutines.
3. The first `rate` calls should return immediately (tokens available).
4. `asyncio.create_task(asyncio.sleep(1))` won't release the semaphore by
   itself — you need a helper coroutine that sleeps then calls `sem.release()`.
5. Timing tests on slow CI machines may need generous tolerances — the tests
   use ≥ lower_bound, not an exact match.

## Run

```bash
python3 test_solution.py
```
