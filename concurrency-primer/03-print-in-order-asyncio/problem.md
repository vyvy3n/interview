# Exercise 03 — Print in Order (asyncio)

## Goal

Same ordering guarantee as Exercise 02, but using `asyncio` coroutines instead
of threads.

## What you're implementing

```python
class AsyncOrderedPrinter:
    async def first(self,  print_fn: Callable[[], None]) -> None: ...
    async def second(self, print_fn: Callable[[], None]) -> None: ...
    async def third(self,  print_fn: Callable[[], None]) -> None: ...
```

## Behavior

- Each method is a coroutine scheduled concurrently via `asyncio.gather`.
- `print_fn` is a regular (synchronous) callable.
- The methods must guarantee: `first`'s `print_fn` runs before `second`'s, which
  runs before `third`'s.

## Concurrency tools

- `asyncio.Event` — async version of `threading.Event`. `await event.wait()`
  suspends the coroutine without blocking the event loop.

## Test pressure

- Uses `unittest.IsolatedAsyncioTestCase` (Python 3.8+).
- Schedules all three coroutines concurrently and checks output order in all six
  permutations.

## Gotchas

1. `asyncio.Event` is **not** thread-safe — only use it inside the event loop.
2. `await event.wait()` yields control; the event loop can run other coroutines
   while this one waits. That is the whole point.
3. Call `event.set()` **after** `print_fn()` completes.
4. Each `AsyncOrderedPrinter()` instance needs its own fresh `asyncio.Event`
   objects — do not share them across instances.
5. You cannot use `threading.Event` here; the async version must be
   `asyncio.Event`.

## Run

```bash
python3 test_solution.py
```
