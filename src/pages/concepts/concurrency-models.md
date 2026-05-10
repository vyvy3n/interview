---
layout: ../../layouts/Layout.astro
title: Concurrency — when to use what
---

# Concurrency — when to use what

> Pick the right tool: `asyncio` for I/O wait, `threading` for blocking libs, `multiprocessing` for CPU. Real systems combine them.

## If I can only remember one rule

- **Waiting on the network or async I/O dominates** → `asyncio` (or threads + blocking I/O if the stack is sync).
- **Blocking library, finite workers, overlap waits** → `threading` (often via a pool).
- **Python CPU needs multiple cores** → `multiprocessing` (or vectorize / move hot loop to compiled code).
- **Real systems often combine**: `asyncio` event loop + `asyncio.to_thread` for blocking bits, or a process pool for CPU chunks feeding results back to async code.

## Decision matrix

| Workload | Best tool | Why |
|----------|-----------|-----|
| 1000 HTTP requests with async stack (httpx, aiohttp) | `asyncio` + `gather` | Single thread, cooperative; tens of thousands of concurrent connections at near-zero overhead |
| 50 DB queries via blocking driver (psycopg2, pymysql) | `threading.ThreadPoolExecutor` | Blocking calls release the GIL during I/O; pool bounds memory |
| Image processing, ML inference, NumPy crunch | `multiprocessing.Pool` or compiled code | CPU-bound work needs separate processes to escape the GIL |
| Mostly async + occasional blocking call (requests, file I/O) | `asyncio` + `asyncio.to_thread()` | Don't block the event loop; offload the blocking bit to a thread |
| Mostly CPU-bound with a few I/O steps | `multiprocessing` + `concurrent.futures` | Workers are processes; orchestrate from main with `ProcessPoolExecutor` |
| Real-time stream + heavy CPU per item | `asyncio` event loop + `ProcessPoolExecutor` for CPU stages | Hybrid; event loop coordinates, process pool grinds |

## The three Python concurrency models

### asyncio — cooperative multitasking, one thread

- One OS thread, one event loop.
- Coroutines yield with `await` at suspension points.
- Massively concurrent (~tens of thousands of pending connections) at I/O-bound work.
- Cannot speed up CPU-bound code (still one thread).
- Cannot use blocking libraries safely — must wrap with `asyncio.to_thread()` or `loop.run_in_executor()`.

### threading — preemptive multitasking, GIL-bound

- Multiple OS threads share memory.
- GIL means only one thread executes Python bytecode at a time, BUT...
- ...the GIL releases during I/O system calls and `time.sleep()`. So blocking I/O DOES overlap.
- Good for: blocking libraries (psycopg2, requests, file I/O) and bounded worker pools.
- Bad for: pure-Python CPU-bound work (no parallelism, just lock contention).

### multiprocessing — true parallelism, separate memory

- Multiple OS processes, each with its own Python interpreter and GIL.
- True parallelism across cores.
- Communication is expensive (pickle through pipes / queues).
- Good for: CPU-bound work that's chunkable.
- Bad for: shared mutable state (you'd need `multiprocessing.Manager` and serialization is expensive).

## How to combine them

### asyncio + threading: blocking call inside async code

```python
import asyncio
import requests  # blocking library

async def fetch_blocking(url: str) -> str:
    # Don't call requests.get() directly — it would block the event loop!
    response = await asyncio.to_thread(requests.get, url)
    return response.text

async def main():
    urls = [...]
    return await asyncio.gather(*(fetch_blocking(u) for u in urls))
```

`asyncio.to_thread()` (Python 3.9+) is the clean way to bridge a blocking call into async code. Spawns a thread internally and awaits the result.

### asyncio + multiprocessing: CPU chunks feeding results to async code

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

def cpu_heavy(chunk: bytes) -> int:
    # CPU-bound work: hash, compress, parse, NumPy-style math
    return sum(b * b for b in chunk)

async def main():
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        chunks = [...]
        results = await asyncio.gather(
            *(loop.run_in_executor(pool, cpu_heavy, c) for c in chunks)
        )
    return results
```

`loop.run_in_executor(pool, fn, *args)` dispatches CPU work to a process pool from inside async code.

### threading + multiprocessing: I/O fan-out feeding CPU pool

Less common — usually you'd reach for asyncio at the top instead. But viable if your I/O layer is sync.

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

with ThreadPoolExecutor() as io_pool, ProcessPoolExecutor() as cpu_pool:
    raw_blobs = io_pool.map(fetch_blocking, urls)         # I/O concurrent
    parsed   = cpu_pool.map(cpu_heavy, raw_blobs)         # CPU parallel
```

## Common mistakes

1. **Calling `requests.get()` (or any blocking call) inside `async def`** — freezes the event loop, kills concurrency. Use `httpx` (async client) or `asyncio.to_thread(requests.get, url)`.
2. **Using `threading` for CPU-bound Python** — GIL means no parallelism; net result is often slower than single-threaded due to lock contention.
3. **Using `multiprocessing` for I/O-bound work** — process startup + IPC is overkill; threads or asyncio do the same job with less overhead.
4. **Sharing a Python object between processes without `multiprocessing.Queue` / `Manager`** — each process gets its own copy; mutations don't propagate.
5. **`time.sleep()` inside async code** — blocks the event loop. Always `await asyncio.sleep()`.
6. **Forgetting `await`** — calling an async function without awaiting returns a coroutine object; the work never runs.
7. **`asyncio.run()` inside another coroutine** — creates a nested loop and crashes. Use `await` instead.

## Quick triage flowchart

```
Is the work I/O-bound?
├── YES — Is your stack async-native (httpx, aiohttp, asyncpg)?
│   ├── YES → asyncio
│   └── NO  → threading (ThreadPoolExecutor)
│
└── NO (CPU-bound) — Is the hot loop in pure Python?
    ├── YES → multiprocessing OR rewrite in NumPy / Cython / compiled code
    └── NO  → already parallel via the C extension; no change needed
```

## Practice

- **Concurrency primer (in-repo)** — 10 standalone exercises mixing threading and asyncio. *Insight:* doing both styles of the same problem (e.g. exercises 02 + 03 print-in-order) makes the "when each shines" question concrete. [/Users/vyvyen/code/interview/concurrency-primer/](https://github.com/vyvy3n/interview/tree/main/concurrency-primer)
- **In-repo Problem 09 — concurrent task scheduler (threading)** — bounded worker threads pulling from a job queue. *Insight:* threading + `Lock` is right when you have many bounded blocking calls + shared state — exactly what a job runner looks like. [/Users/vyvyen/code/interview/09-concurrent-task-scheduler/](https://github.com/vyvy3n/interview/tree/main/09-concurrent-task-scheduler)
- **In-repo Problem 10 — async KV store (asyncio)** — atomic compound ops on shared state via `asyncio.Lock`. *Insight:* asyncio.Lock is right when many coroutines mutate the same in-memory state without blocking I/O. [/Users/vyvyen/code/interview/10-thread-safe-keyvalue/](https://github.com/vyvy3n/interview/tree/main/10-thread-safe-keyvalue)
- **Threading deep-dive page** — primitives, deadlock patterns, worker pools. *Insight:* `with lock:` is the universal pattern; everything else is variations. [Concurrency — threading](/concepts/concurrency-threading)
- **asyncio deep-dive page** — async/await, gather, cancellation, IsolatedAsyncioTestCase. *Insight:* every `await` is a potential interleaving point — guard shared state with `asyncio.Lock` even in single-threaded code. [Concurrency — asyncio](/concepts/concurrency-asyncio)
