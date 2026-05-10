# Level 3 — Capacity + LRU Eviction

## What you're implementing

Add one method and integrate a monotonic LRU access counter into existing methods:

```python
def set_capacity(self, max_files: int) -> int: ...
```

All Level 1–2 methods remain intact.

## Mental model

The cache now has a **size limit**. When the cache is full and a new file needs to be stored, the **Least Recently Used** (LRU) file is evicted to make room. LRU is determined by a monotonic access counter that's updated on every meaningful file access.

Think of it like a CPU cache with an LRU replacement policy: the file you accessed longest ago is the first to go.

## The 1 new method for Level 3

### `set_capacity(max_files: int) -> int`

Set the maximum number of files the cache may hold. If the current count exceeds `max_files`, **immediately evict LRU files** until `count <= max_files`. Return the total number of files evicted.

Before `set_capacity` is called, the cache is unbounded.

## LRU tracking rules

Maintain a monotonic integer tick counter. On every "access" operation, stamp the file with the current tick (then increment the tick). The file with the **lowest tick** is the LRU and is evicted first.

### Which operations update the LRU stamp?

| Method | Updates LRU? |
|--------|:---:|
| `store` (new file) | Yes |
| `fetch` (on hit only) | Yes |
| `update` (on hit only) | Yes |
| `remove` | No (file is gone) |
| `fetch_by_prefix` | **No** — metadata query |

### What happens at capacity?

- **`store`**: if `count == max_files`, evict LRU **before** inserting the new file.
- **`update`**: does not change file count — no eviction needed.
- **`set_capacity`**: evict LRU repeatedly until `count <= max_files`.

## Worked example

```python
cache = FileCache()

# Store 3 files in order: a, b, c
# LRU order (oldest first): a, b, c
cache.store("a.txt", "A")   # tick 0
cache.store("b.txt", "B")   # tick 1
cache.store("c.txt", "C")   # tick 2

# Touch "a.txt" — it's now the MRU
cache.fetch("a.txt")         # tick 3 assigned to a.txt

# LRU order: b (tick=1), c (tick=2), a (tick=3)

cache.set_capacity(2)        # evict 1 → evicts "b.txt" (lowest tick)
# Returns 1

cache.fetch("b.txt")         # "" — evicted
cache.fetch("a.txt")         # "A" — still present
cache.fetch("c.txt")         # "C" — still present

# fetch_by_prefix does NOT refresh LRU:
cache.store("x.txt", "X")   # evicts whichever has lowest tick now
cache.store("y.txt", "Y")   # evicts next LRU
cache.fetch_by_prefix("x")  # ["x.txt"] — does NOT refresh x.txt's tick!
cache.store("z.txt", "Z")   # evicts x.txt (it was not refreshed by fetch_by_prefix)
```

## Constraints

- Evict the file with the **single lowest tick** at a time.
- Tie-breaking (two files with the same tick): implementation-defined; tests don't rely on it.
- `max_files` may be 0 — evict everything.
- Capacity only limits `store` (new files), not `update`.

## Common gotchas

1. **`fetch_by_prefix` does NOT update LRU** — a common mistake. If you refresh ticks during prefix scans, files that are "only searched" will never be evicted.
2. **Evict before inserting**, not after — if at capacity, evict LRU first, then add the new file.
3. **`update` doesn't add a file** — no eviction triggered by `update` even if at capacity.
4. **`set_capacity` evicts immediately** — loop until `count <= max_files`.
5. **A `fetch` miss does NOT update LRU** — only hits count (the file must exist).

## When you're done

```
python3 test_level3.py
```

All tests must pass before moving to Level 4.
