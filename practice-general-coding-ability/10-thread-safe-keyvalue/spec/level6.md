# Level 6 — Atomic Compound Operations

## What you're implementing

Add three async methods that perform compound read-modify-write operations atomically under a single lock acquisition:

```python
async def acompare_and_set(self, key: str, expected: str, new_value: str) -> bool: ...
async def aget_and_set(self, key: str, new_value: str) -> str: ...
async def aincrement(self, key: str, delta: int) -> int: ...
```

## Mental model

"Atomic" means no other coroutine can observe or modify the key between your read and your write. This is the foundation of lock-free data structures, distributed counters, and optimistic concurrency control.

- **compare-and-set (CAS):** "Only update if the current value matches what I expect." Used for optimistic locking and leader election.
- **get-and-set (swap):** "Replace atomically, give me the old value." Used for token passing.
- **increment:** "Add to a counter without losing any concurrent updates." Used for hit counters, rate limiters, sequence generators.

All three must hold `self._lock` for the **entire** read-compute-write sequence, not just the individual read or write.

## The 3 async methods for Level 6

### A. `async acompare_and_set(key: str, expected: str, new_value: str) -> bool`

Atomically compare the current value to `expected`:

- If current value equals `expected` → set to `new_value`, return `True`.
- If current value does NOT equal `expected` → do nothing, return `False`.

Special cases:

| Situation | `expected` | Result |
|-----------|-----------|--------|
| Key is missing | any non-`""` string | `False` (missing ≠ expected) |
| Key is missing | `""` | `True` — insert-if-absent: set `new_value`, return `True` |
| Key exists | `""` | `False` (value ≠ `""`) |

### B. `async aget_and_set(key: str, new_value: str) -> str`

Atomically read the current value and replace it with `new_value`:

- Returns the **old** value (or `""` if key was missing).
- Always writes `new_value`, regardless of whether the key existed.

### C. `async aincrement(self, key: str, delta: int) -> int`

Atomically:

1. Read current value; parse as `int` (treat missing or non-integer as `0`).
2. Add `delta`.
3. Store result back as a string.
4. Return the **new** integer value.

This is the key atomicity test: 100 concurrent coroutines each calling `aincrement("counter", 1)` must produce a final value of exactly `100` — any race condition would produce a lower number.

## Concurrency notes

All three methods must hold `self._lock` for the whole compound operation:

```python
async def aincrement(self, key: str, delta: int) -> int:
    async with self._lock:           # acquire once
        raw = self._store.get(key, "0")
        try:
            current = int(raw)
        except ValueError:
            current = 0
        new_val = current + delta
        self._store[key] = str(new_val)
        return new_val               # release on exit
```

**Do NOT split the lock into separate aget + aput calls** — that would create a window where another coroutine could slip in between, breaking atomicity.

## Worked example

```python
import asyncio
from solution import KVStore

async def main():
    kv = KVStore()

    # compare_and_set — insert if absent
    ok = await kv.acompare_and_set("x", "", "first")   # True (insert)
    ok = await kv.acompare_and_set("x", "", "second")  # False (exists, "first" != "")
    ok = await kv.acompare_and_set("x", "first", "updated")  # True
    val = await kv.aget("x")    # "updated"

    # get_and_set
    old = await kv.aget_and_set("x", "swapped")   # "updated"
    val = await kv.aget("x")                       # "swapped"
    old2 = await kv.aget_and_set("new_key", "v")  # ""  (was missing)

    # aincrement — the big concurrent test
    await kv.aput("counter", "0")
    await asyncio.gather(*[kv.aincrement("counter", 1) for _ in range(100)])
    result = await kv.aget("counter")
    assert result == "100"   # must be exactly 100 — not 93 or 87

asyncio.run(main())
```

## Constraints

- `delta` for `aincrement` may be negative (decrement) or zero.
- If `aincrement` finds a non-integer string (e.g. `"hello"`), treat it as `0`.
- All three methods must use `async with self._lock:` for the entire compound operation.
- No external libraries.

## Common gotchas

1. **Never release the lock between read and write.** Any `await` between them could let another coroutine run. Use a single `async with` block.
2. **`acompare_and_set` with `expected=""` and missing key is True.** Missing is treated as `""` in this case only.
3. **`aget_and_set` always writes**, even if the key was missing. After the call, the key always exists.
4. **`aincrement` returns an `int`, not a string.** Return the integer result, not `str(result)`.
5. **Re-using `aget`/`aput` inside these methods causes deadlock.** Those methods acquire the same lock — you'd deadlock trying to acquire it twice. Operate on `self._store` directly inside the `async with` block.

## When you're done

```
python3 test_level6.py
```

The atomicity tests will verify that 100 concurrent increments produce exactly 100.
