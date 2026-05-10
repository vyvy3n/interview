---
layout: ../../layouts/Layout.astro
title: Concurrency — asyncio
---

# Concurrency — asyncio

> Single-threaded cooperative multitasking: one event loop, many suspended coroutines, zero GIL fights.

## When to use

- **Use asyncio** when work is I/O-bound (network, disk, DB queries) and you control the code with `async/await`
- **Use asyncio** when you need thousands of concurrent connections — threads don't scale to 10k
- **Use threading** when you must call blocking third-party libraries that can't be made async
- **Use multiprocessing** when work is CPU-bound (compute, numpy crunching) — asyncio won't help
- **Hybrid**: run blocking code inside asyncio via `asyncio.to_thread(fn, *args)` (3.9+) or `loop.run_in_executor(None, fn)`

## The async/await mental model

- A **coroutine** (`async def f()`) is a function that can pause itself at `await` points and yield control back to the event loop
- The **event loop** is a single-threaded scheduler: it runs one coroutine at a time, picks the next ready one whenever the current one awaits
- `await expr` means "I'm blocked until `expr` resolves — run something else in the meantime"
- No true parallelism (one CPU core), but overlap of waiting: while one coroutine waits on a socket, another can compute
- Shared mutable state is safer than with threads — only one coroutine runs at a time — but interleaving at `await` points still causes races

## The core primitives

| Primitive | Purpose |
|---|---|
| `async def` | Define a coroutine function |
| `await` | Suspend current coroutine until the awaitable completes |
| `asyncio.run(coro)` | Entry point: create loop, run coro, teardown loop |
| `asyncio.create_task(coro)` | Schedule coro concurrently; returns a `Task` (starts immediately) |
| `asyncio.gather(*coros)` | Run coros concurrently, collect results in order |
| `asyncio.wait(tasks, timeout)` | Returns `(done, pending)` sets; fine-grained control |
| `asyncio.wait_for(coro, timeout)` | Run single coro; raise `TimeoutError` if too slow |
| `asyncio.sleep(n)` | Async sleep — yields control to event loop |
| `asyncio.Lock` | Mutual exclusion between coroutines |
| `asyncio.Event` | Signal one or more waiting coroutines |
| `asyncio.Condition` | `Lock` + `Event` combined; notify/wait on a condition |
| `asyncio.Semaphore(n)` | Allow at most N coroutines past the gate at once |
| `asyncio.Queue` | Thread-safe-for-coroutines FIFO; `put`/`get` block when full/empty |

## Template: basic coroutine + run

```python
import asyncio

async def greet(name: str) -> str:
    await asyncio.sleep(0.1)   # simulate I/O
    return f"Hello, {name}!"

async def main():
    result = await greet("world")
    print(result)              # Hello, world!

asyncio.run(main())            # creates loop, runs main, tears down loop
```

## Template: parallel tasks with gather

```python
import asyncio

async def fetch(url: str) -> str:
    await asyncio.sleep(0.5)   # simulate network delay
    return f"data from {url}"

async def main():
    urls = ["https://a.com", "https://b.com", "https://c.com"]
    # gather schedules all coroutines concurrently; results are in input order
    results = await asyncio.gather(*[fetch(u) for u in urls])
    for url, data in zip(urls, results):
        print(url, "->", data)

    # collect exceptions instead of raising — use return_exceptions=True
    results = await asyncio.gather(*[fetch(u) for u in urls], return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            print("failed:", r)

asyncio.run(main())
```

## Template: concurrent with limit (Semaphore)

```python
import asyncio

async def fetch(sem: asyncio.Semaphore, url: str) -> str:
    async with sem:            # blocks if N coroutines already inside
        await asyncio.sleep(0.1)
        return f"result:{url}"

async def fetch_all(urls: list[str], max_concurrent: int = 5) -> list[str]:
    sem = asyncio.Semaphore(max_concurrent)
    # gather launches all at once; semaphore throttles internally
    return await asyncio.gather(*[fetch(sem, u) for u in urls])

asyncio.run(fetch_all([f"url-{i}" for i in range(20)], max_concurrent=5))
```

## Template: producer-consumer (asyncio.Queue)

```python
import asyncio

async def producer(q: asyncio.Queue, items: list) -> None:
    for item in items:
        await q.put(item)      # blocks if queue is full
    await q.put(None)          # sentinel: signal consumer to stop

async def consumer(q: asyncio.Queue) -> None:
    while True:
        item = await q.get()   # blocks if queue is empty
        if item is None:
            q.task_done()
            break
        print("consumed:", item)
        q.task_done()

async def main():
    q = asyncio.Queue(maxsize=3)   # bounded buffer
    await asyncio.gather(
        producer(q, list(range(10))),
        consumer(q),
    )
    await q.join()             # wait until all task_done() calls match puts

asyncio.run(main())
```

## Template: timeout (wait_for)

```python
import asyncio

async def slow_op() -> str:
    await asyncio.sleep(5)
    return "done"

async def main():
    try:
        result = await asyncio.wait_for(slow_op(), timeout=1.0)
    except asyncio.TimeoutError:
        print("timed out — op was cancelled automatically")

    # Multi-coroutine variant: asyncio.wait returns (done, pending) sets
    tasks = [asyncio.create_task(slow_op()) for _ in range(3)]
    done, pending = await asyncio.wait(tasks, timeout=1.0)
    for t in pending:
        t.cancel()
    # drain cancelled tasks so their cleanup runs before we exit
    await asyncio.gather(*pending, return_exceptions=True)
    print(f"{len(done)} finished, {len(pending)} cancelled")

asyncio.run(main())
```

## Template: cancellation (Task.cancel)

```python
import asyncio

async def worker() -> None:
    try:
        while True:
            await asyncio.sleep(1)
            print("tick")
    except asyncio.CancelledError:
        print("cleaning up…")
        raise        # MUST re-raise — swallowing CancelledError breaks cancellation

async def main():
    task = asyncio.create_task(worker())
    await asyncio.sleep(2.5)   # let it tick twice
    task.cancel()
    try:
        await task             # propagate the CancelledError
    except asyncio.CancelledError:
        print("task is gone")

asyncio.run(main())
```

## Template: mutex over shared async resource (Lock)

```python
import asyncio

shared_counter = 0

async def increment(lock: asyncio.Lock, n: int) -> None:
    global shared_counter
    for _ in range(n):
        async with lock:       # only one coroutine inside at a time
            tmp = shared_counter
            await asyncio.sleep(0)   # yield — without lock this would race
            shared_counter = tmp + 1

async def main():
    lock = asyncio.Lock()
    await asyncio.gather(increment(lock, 1000), increment(lock, 1000))
    print(shared_counter)     # always 2000

asyncio.run(main())
```

## Template: testing async code (IsolatedAsyncioTestCase)

```python
import asyncio
import unittest

async def add(a: int, b: int) -> int:
    await asyncio.sleep(0)    # yield once to prove it's truly async
    return a + b

class TestAsync(unittest.IsolatedAsyncioTestCase):
    # Python 3.8+ — each async test method gets its own fresh event loop

    async def test_add(self):
        result = await add(2, 3)
        self.assertEqual(result, 5)

    async def test_gather(self):
        results = await asyncio.gather(add(1, 1), add(2, 2))
        self.assertEqual(results, [2, 4])

    async def test_timeout(self):
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(asyncio.sleep(10), timeout=0.01)

if __name__ == "__main__":
    unittest.main()
```

## Variants / Gotchas

- **Forgetting `await`** returns a coroutine object silently — `greet("x")` is an unawaited object, not a result; Python 3.11+ warns, older versions don't
- **`asyncio.gather` fail-fast by default** — if any coroutine raises, the exception propagates and remaining coroutines are cancelled; pass `return_exceptions=True` to collect all results including exceptions
- **Blocking the event loop** — `time.sleep(1)` inside a coroutine freezes *everything*; always use `await asyncio.sleep(1)`; offload CPU work with `await asyncio.to_thread(fn)` or `loop.run_in_executor(None, fn)`
- **`asyncio.Lock` is not thread-safe** — it only coordinates coroutines within one event loop; use `threading.Lock` if mixing threads and asyncio
- **`asyncio.run()` is not reentrant** — creates and destroys the loop; calling it a second time in the same process is fine, but calling it from *inside* a running coroutine raises `RuntimeError`; use `await coro` instead
- **Tasks silently vanish if not referenced** — `asyncio.create_task(coro)` must be held in a variable or collected; the GC can cancel it before it runs
- **`asyncio.wait` takes Tasks, not coroutines** — wrap with `asyncio.create_task()` first; `asyncio.gather` accepts raw coroutines and wraps them for you
- **`CancelledError` is not `Exception` in Python 3.8+** — it derives from `BaseException`; a bare `except Exception` won't catch it, so cleanup inside `except asyncio.CancelledError: raise` is the correct pattern

## Async vs Sync mistakes to avoid

**Using `time.sleep` instead of `await asyncio.sleep`:**
```python
# BAD — blocks the entire event loop for 1 second
import time
async def bad(): time.sleep(1)

# GOOD — suspends only this coroutine; others keep running
async def good(): await asyncio.sleep(1)
```

**Calling `asyncio.run` from inside a coroutine:**
```python
# BAD — raises RuntimeError: this event loop is already running
async def bad():
    asyncio.run(other_coro())   # wrong

# GOOD — just await it
async def good():
    await other_coro()
```

**Swallowing `CancelledError`:**
```python
# BAD — task appears to finish normally; cancellation is silently lost
async def bad():
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        pass   # swallowed!

# GOOD — clean up, then re-raise
async def good():
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("cleaning up")
        raise   # propagate
```

**Mutating shared state at await points without a lock:**
```python
# BAD — interleaving at await corrupts counter even in single thread
shared = 0
async def bad_increment():
    global shared
    tmp = shared
    await asyncio.sleep(0)   # another coroutine can run here and mutate shared
    shared = tmp + 1

# GOOD — guard the read-modify-write with asyncio.Lock
lock = asyncio.Lock()
async def good_increment():
    global shared
    async with lock:
        tmp = shared
        await asyncio.sleep(0)
        shared = tmp + 1
```

## Practice

- **Print in Order (asyncio)** — enforce `first → second → third` execution order when all three coroutines are scheduled concurrently via `asyncio.gather`. *Insight:* use two `asyncio.Event` objects; `first` calls `event1.set()` after printing, `second` awaits `event1`, then sets `event2`, and `third` awaits `event2` — chain of events enforces the order. [concurrency-primer/03](/concurrency-primer/03-print-in-order-asyncio/)

- **Async Rate Limiter** — implement `RateLimiter(rate)` where `await limiter.acquire()` allows at most `rate` callers per second. *Insight:* token-bucket via `asyncio.Semaphore(rate)`; `acquire()` grabs a slot then schedules a background task (`asyncio.create_task`) that sleeps 1 second and calls `sem.release()` — the caller returns immediately while the slot is held open for exactly 1 second. [concurrency-primer/05](/concurrency-primer/05-async-rate-limiter/)

- **Async Gather with Timeout** — implement `gather_with_timeout(coros, timeout)` that runs all coroutines concurrently but replaces any that exceed `timeout` with a sentinel value instead of raising. *Insight:* wrap each coroutine in `asyncio.create_task`, then call `asyncio.wait(tasks, timeout=timeout)` which returns `(done, pending)` sets; cancel every task in `pending`, drain them with `asyncio.gather(*pending, return_exceptions=True)`, then reassemble results in input order. [concurrency-primer/06](/concurrency-primer/06-async-gather-with-timeout/)

- **Async Semaphore Fetcher** — fetch a list of URLs concurrently but bound the in-flight count to `max_concurrent`. *Insight:* `async with sem:` inside each per-URL coroutine naturally throttles concurrency; pass all coroutines to `asyncio.gather` at once — the semaphore gates entry while `gather` preserves result order. Mirrors the real-world pattern for rate-limited HTTP clients. [concurrency-primer/09](/concurrency-primer/09-async-semaphore-fetcher/)

- **Web Crawler Multithreaded (asyncio variant)** — given a start URL and `HtmlParser.getUrls(url)`, crawl all pages on the same hostname concurrently. *Insight:* replace `ThreadPoolExecutor` with `asyncio.gather`; track visited URLs with a `set` guarded by `asyncio.Lock`; bound concurrency with `asyncio.Semaphore`. The asyncio version avoids thread overhead while matching the threaded solution's logic exactly. [LC 1242](https://leetcode.com/problems/web-crawler-multithreaded/)
