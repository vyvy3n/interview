# Concurrency Primer

10 standalone exercises building muscle memory for `threading` and `asyncio`.
Required prep for the Anthropic Fellows assessment, which tests concurrency
explicitly.

## Exercises

| # | Title | Tool | Difficulty | Time |
|---|-------|------|------------|------|
| 01 | Thread-safe counter | threading.Lock | easy | 5 min |
| 02 | Print in order (threading) | threading.Event | easy | 10 min |
| 03 | Print in order (asyncio) | asyncio.Event | easy | 10 min |
| 04 | Bounded blocking queue | threading.Condition | medium | 15 min |
| 05 | Async rate limiter | asyncio.Semaphore | medium | 15 min |
| 06 | Async gather-with-timeout | asyncio.wait | medium | 15 min |
| 07 | Readers-writers lock | threading.Condition | hard | 20 min |
| 08 | FizzBuzz multithreaded | threading.Condition | hard | 20 min |
| 09 | Async semaphore fetcher | asyncio.Semaphore | medium | 15 min |
| 10 | Conditional variable cache | threading.Condition | hard | 20 min |

## Recommended order

Start with **01-03** to learn lock/event basics. Move to **04-06** for blocking
queues and async patterns. Tackle **07-10** for harder synchronization problems
that require multiple primitives.

## How to use

```bash
cd 01-thread-safe-counter
# read problem.md
# implement solution.py  (remove the NotImplementedError stubs)
python3 test_solution.py
```

Repeat until all tests pass, then move to the next exercise.

## Threading vs asyncio split

| Exercises | Paradigm | Why |
|-----------|----------|-----|
| 01, 02, 04, 07, 08, 10 | `threading` | OS-level threads, shared memory, blocking primitives |
| 03, 05, 06, 09 | `asyncio` | Single-threaded event loop, cooperative multitasking |

The assessment allows either paradigm. Learn both so you can choose the right
tool for the problem on the day.

## Key stdlib imports cheat sheet

```python
# Threading
import threading
threading.Thread(target=fn, args=(...))
threading.Lock()          # mutual exclusion
threading.Event()         # one-shot signal; .set() / .wait()
threading.Condition(lock) # wait/notify; use as context manager
threading.Semaphore(n)    # counting semaphore

# Asyncio
import asyncio
asyncio.create_task(coro())
asyncio.gather(*coros)
asyncio.wait(tasks, timeout=N)
asyncio.Event()           # async version of threading.Event
asyncio.Semaphore(n)      # async counting semaphore
asyncio.sleep(seconds)    # yield control to event loop
```
