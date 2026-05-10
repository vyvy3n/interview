# Exercise 02 — Print in Order (Threading)

## Goal

Guarantee that three threads execute in a fixed order — first, second, third —
regardless of which thread the OS schedules first.

## What you're implementing

```python
class OrderedPrinter:
    def first(self,  print_fn: Callable[[], None]) -> None: ...
    def second(self, print_fn: Callable[[], None]) -> None: ...
    def third(self,  print_fn: Callable[[], None]) -> None: ...
```

## Behavior

- Each method is called from a different thread (potentially in any order).
- `print_fn` is a zero-argument callable supplied by the caller.
- The methods must guarantee: `first`'s `print_fn` runs before `second`'s, which
  runs before `third`'s.
- No busy-waiting (spinning in a loop checking a flag) — use blocking primitives.

## Concurrency tools

- `threading.Event` — one-shot signal. `event.wait()` blocks until `event.set()`
  is called from another thread.

## Test pressure

- Tests run the three methods in all six possible thread-start orderings and
  verify the recorded output sequence is always `["first", "second", "third"]`.

## Gotchas

1. Two events are needed: one to signal that `first` finished, one to signal that
   `second` finished.
2. `threading.Event` starts in the **unset** state — `wait()` blocks immediately.
3. Call `event.set()` **after** running `print_fn`, not before.
4. `threading.Event` is not reusable across test runs if you share instances —
   each `OrderedPrinter()` instance should create fresh events.
5. Don't confuse `threading.Event` (one-shot flag) with `threading.Condition`
   (notify/wait loop). Either works, but Event is simpler here.

## Run

```bash
python3 test_solution.py
```
