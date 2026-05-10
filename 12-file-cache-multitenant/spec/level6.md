# Level 6 — Atomic Compound Operations

## What you're implementing

Add three async atomic compound operations that read and write state in a single lock acquisition:

```python
async def acompare_and_update(
    self, filename: str, expected_content: str, new_content: str
) -> bool: ...

async def astore_or_update(self, filename: str, content: str) -> str: ...

async def abulk_store(self, items: list[tuple[str, str]]) -> int: ...
```

All previous methods remain intact.

## Mental model

The core problem: without a compound operation, any "read, then decide, then write" sequence has a TOCTOU (Time of Check to Time of Use) window. Even with `asyncio`, two coroutines could:

1. Both read the same file content.
2. Both decide "yes, expected matches".
3. Both write — one wins, one silently overwrites.

By holding the lock for the **entire read + decide + write**, we make these operations truly atomic.

## The 3 new methods

### A. `acompare_and_update(filename, expected_content, new_content) -> bool`

Atomically:
1. If `filename` does not exist → return `False`.
2. If current content != `expected_content` → return `False`, do not modify.
3. If current content == `expected_content` → update to `new_content`, return `True`.

This is the classic Compare-And-Swap (CAS) pattern, used in optimistic concurrency control.

### B. `astore_or_update(filename, content) -> str`

Atomically:
- If `filename` **exists** → update its content, return `"updated"`.
- If `filename` **does not exist** → store it, return `"stored"`.

This is an upsert (insert-or-update) with a meaningful return value indicating what happened.

### C. `abulk_store(items: list[tuple[str, str]]) -> int`

Atomically store multiple `(filename, content)` pairs (global tenant). **All-or-nothing:**
- Check if any filename in `items` already exists in the cache.
- Check for duplicate filenames within `items` itself.
- If ANY conflict detected → store **nothing**, return `0`.
- If no conflicts → store all files, return count stored (= `len(items)`).

## Worked example

```python
import asyncio
from solution import FileCache

async def main():
    cache = FileCache()
    await cache.astore("version.txt", "v1")

    # --- acompare_and_update ---
    ok = await cache.acompare_and_update("version.txt", "v1", "v2")  # True
    ok2 = await cache.acompare_and_update("version.txt", "v1", "v3") # False (stale expected)
    val = await cache.afetch("version.txt")  # "v2"

    # --- astore_or_update ---
    r1 = await cache.astore_or_update("newfile.txt", "created")  # "stored"
    r2 = await cache.astore_or_update("newfile.txt", "revised")  # "updated"
    val2 = await cache.afetch("newfile.txt")  # "revised"

    # --- abulk_store ---
    n = await cache.abulk_store([("a.txt", "A"), ("b.txt", "B")])  # 2
    n2 = await cache.abulk_store([("a.txt", "A2"), ("c.txt", "C")])  # 0 (a.txt exists)
    val3 = await cache.afetch("a.txt")  # "A" — not overwritten
    val4 = await cache.afetch("c.txt")  # "" — c.txt was not stored

asyncio.run(main())
```

## Why these tests would fail without proper locking

### `acompare_and_update`

Without the full lock held across the read+check+write:

```python
# Broken (lock released between steps — hypothetical pseudocode)
val = await cache.afetch("f.txt")       # reads "v1"
# --- another coroutine runs here and updates to "v2" ---
if val == "v1":
    await cache.aupdate("f.txt", "new") # writes "new" on stale data!
    return True  # WRONG — should have failed
```

With the lock: one coroutine holds the lock for the entire check+write. The second coroutine waits, then sees the updated value and correctly returns `False`.

### `abulk_store`

Without atomic all-or-nothing semantics, two concurrent bulk stores that share one filename could both succeed for their non-overlapping files, leaving the cache in a partial state.

## Constraints

- All three methods operate on the **global tenant** only.
- `acompare_and_update` on a missing file returns `False` — it does not create.
- `abulk_store` with an empty list returns `0`.
- `abulk_store` treats duplicate filenames **within the items list** as a conflict (return `0`, store nothing).

## Common gotchas

1. **Hold the lock for the FULL compound op** — acquire once, do all read+check+write inside the `async with` block, release once.
2. **`acompare_and_update` on missing file returns `False`**, not `True`. It is NOT "create if missing" — that's `astore_or_update`.
3. **`abulk_store` is ALL-or-nothing** — even if 9 of 10 filenames are new, if 1 conflicts, store 0.
4. **`abulk_store` must check for internal duplicates** — `[("f.txt", "A"), ("f.txt", "B")]` should return 0.
5. **Don't call `async` methods inside the lock body** — call the synchronous `_do_*` helpers instead, to avoid trying to re-acquire an already-held lock (deadlock).

## When you're done

```
python3 test_level6.py
```

All tests must pass. Congratulations — you've built a production-grade multi-tenant async file cache.
