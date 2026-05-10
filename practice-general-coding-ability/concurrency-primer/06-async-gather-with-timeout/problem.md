# Exercise 06 — Async Gather with Timeout

## Goal

Implement a version of `asyncio.gather` that imposes a per-coroutine timeout —
cancelling slow coroutines and returning a sentinel for their results.

## What you're implementing

```python
TIMEOUT_SENTINEL = object()   # module-level sentinel, already defined

async def gather_with_timeout(
    coros: list,
    timeout: float,
) -> list:
    ...
```

## Behavior

- Runs all coroutines in `coros` concurrently.
- Each coroutine that completes within `timeout` seconds contributes its return
  value at the corresponding index in the result list.
- Each coroutine that does **not** complete within `timeout` seconds is cancelled
  and contributes `TIMEOUT_SENTINEL` at its index.
- The result list preserves the input order of `coros`.
- Does **not** raise an exception — timed-out coroutines are silently replaced
  with the sentinel.

## Concurrency tools

- `asyncio.wait` with `timeout` argument — returns `(done, pending)` sets.
- `task.cancel()` — send a cancellation to a pending task.
- `asyncio.gather(*pending, return_exceptions=True)` — await cancellation to
  propagate cleanly.

## Test pressure

- Mix of fast coroutines (sleep 0.1s) and slow coroutines (sleep 5s) with a 1s
  timeout.
- Fast ones should return their value; slow ones should return the sentinel.
- Order of results must match order of input.

## Gotchas

1. `asyncio.wait` takes an iterable of **Tasks**, not raw coroutines — wrap with
   `asyncio.create_task()` first.
2. After `asyncio.wait` returns, call `task.cancel()` on every task in `pending`.
3. Await the cancelled tasks (e.g., `asyncio.gather(*pending, return_exceptions=True)`)
   so they have a chance to clean up before the test exits.
4. Preserve input order by mapping tasks back to their original index.
5. `asyncio.wait_for` raises `TimeoutError` for a single coroutine — use
   `asyncio.wait` (different function) for the multi-coroutine case.

## Run

```bash
python3 test_solution.py
```
