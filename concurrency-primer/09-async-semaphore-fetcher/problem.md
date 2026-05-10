# Exercise 09 — Async Semaphore Fetcher

## Goal

Fetch a list of URLs concurrently, but limit how many fetches run at the same
time using an async semaphore.

## What you're implementing

```python
async def fetch_all(urls: list[str], max_concurrent: int) -> list[str]:
    ...
```

## Behavior

- Simulates fetching each URL with `asyncio.sleep(0.1)` (no real HTTP needed).
- Returns a list of result strings, one per URL, in the same order as `urls`.
  Each result is `f"result:{url}"`.
- At most `max_concurrent` fetches run simultaneously.
- All URLs are eventually fetched.

## Concurrency tools

- `asyncio.Semaphore(max_concurrent)` — acquire before starting a fetch, release
  when done.

## Test pressure

- 20 URLs, max_concurrent=5.
- Tests track the peak number of active fetches using a shared async counter.
- Peak must be ≤ max_concurrent (5) and > 1 (parallelism is real).

## Gotchas

1. Use `async with sem:` (context manager) rather than manual acquire/release —
   it's cleaner and exception-safe.
2. Wrap fetch logic in a helper coroutine so the semaphore acquisition is
   per-URL, not per-batch.
3. Use `asyncio.gather` to launch all fetch coroutines at once — the semaphore
   throttles them internally.
4. Order preservation: `asyncio.gather` preserves order when all coroutines are
   passed positionally.
5. The shared peak counter in tests uses an `asyncio.Lock` (not `threading.Lock`)
   since everything runs in one event loop.

## Run

```bash
python3 test_solution.py
```
