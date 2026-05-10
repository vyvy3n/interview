# Exercise 08 — FizzBuzz Multithreaded

## Goal

Print the FizzBuzz sequence from 1 to n using four dedicated threads, each
responsible for exactly one case, in order.

## What you're implementing

```python
class FizzBuzz:
    def __init__(self, n: int) -> None: ...
    def fizz(self,     print_fn: Callable[[str], None]) -> None: ...
    def buzz(self,     print_fn: Callable[[str], None]) -> None: ...
    def fizzbuzz(self, print_fn: Callable[[str], None]) -> None: ...
    def number(self,   print_fn: Callable[[int], None]) -> None: ...
```

## Behavior

- `n` — upper bound (1-indexed, inclusive).
- Thread A calls `fizz(print_fn)` — prints "fizz" for multiples of 3 (not 15).
- Thread B calls `buzz(print_fn)` — prints "buzz" for multiples of 5 (not 15).
- Thread C calls `fizzbuzz(print_fn)` — prints "fizzbuzz" for multiples of 15.
- Thread D calls `number(print_fn)` — prints the integer for all other numbers.
- All four methods run concurrently. Together they output the complete sequence
  in order (1 through n), one token per number.
- `print_fn` is a callable supplied by the caller (used to capture output in tests).

## Concurrency tools

- `threading.Condition` — the canonical tool for "wait until my turn" patterns.
- One shared `Condition` and one shared `current` counter (starting at 1) that
  all four threads inspect and advance.

### Sketch

```
with condition:
    while current <= n:
        if current is my case:
            print_fn(...)
            current += 1
            condition.notify_all()
        else:
            condition.wait()
```

## Test pressure

- n=30: verified against the standard FizzBuzz sequence.
- n=100: verified for correctness at scale.
- Tests run all four methods in separate threads and join within a timeout.

## Gotchas

1. All four methods share the same `current` integer — store it on `self`.
2. `notify_all()` after every increment wakes all three sleeping threads;
   each checks whether the new `current` is theirs.
3. The `while` loop at the top of each method handles spurious wakeups and
   also terminates the loop when `current > n`.
4. Don't use four separate conditions — all four threads must share one so
   that `notify_all()` reaches every thread.
5. `print_fn` for `number()` receives an `int`; the others receive a `str`.

## Run

```bash
python3 test_solution.py
```
