# Level 4 — Capacity Cap and LRU Eviction

## What you're implementing

Add a configurable capacity limit with Least-Recently-Used (LRU) eviction. Add one new method and modify the access behavior of existing methods:

```python
def set_capacity(self, max_keys: int) -> int: ...
```

All Level 1-3 methods still work — but `get`, `get_at`, `put`, and `put_with_ttl` now maintain access order.

## Mental model

Real caches can't grow forever. When the cache is full and a new key arrives, the **least-recently-used** entry gets evicted to make room.

"Recently used" means any read *or* write. Track access order with an internal monotonic counter — each access increments the counter and stamps the entry. The entry with the **lowest stamp** is the LRU candidate.

## The 1 new method for Level 4

### A. `set_capacity(max_keys: int) -> int`

Set the maximum number of keys the store may hold.

- If the current store size exceeds `max_keys`, **immediately evict** enough LRU entries (lowest access stamp first) to bring the count down to `max_keys`.
- Returns the number of entries evicted.
- If `max_keys >= current count`, no eviction happens; returns `0`.
- Calling `set_capacity` again with a smaller value may evict again.

## Modified behavior of existing methods

### Access-stamp tracking

Maintain a monotonic integer counter (e.g. `self._tick`). Every time an entry is accessed or written, record the current tick for that key, then increment the tick.

**Events that update the stamp:**

| Method | Updates stamp? |
|--------|---------------|
| `put(key, value)` | Yes (write = access) |
| `put_with_ttl(key, value, ttl, now)` | Yes |
| `get(key)` — on a **hit** | Yes |
| `get_at(key, now)` — on a **hit** (value not expired) | Yes |
| `get(key)` — on a miss | No |
| `get_at(key, now)` — expired or missing | No |
| `delete(key)` | No (entry removed) |

### Eviction on insert

When `put` or `put_with_ttl` would **add a new key** (not overwriting) and the store is at capacity:

1. Evict the entry with the lowest access stamp (the LRU entry).
2. Then insert the new entry.

Overwriting an existing key never triggers eviction (size doesn't change).

If there is **no capacity set**, there is no eviction — the store grows unbounded. Capacity is unset by default.

## Worked example

```python
kv = KVStore()
kv.put("a", "1")   # tick=0 for "a", _tick now 1
kv.put("b", "2")   # tick=1 for "b", _tick now 2
kv.put("c", "3")   # tick=2 for "c", _tick now 3

kv.get("a")        # hit → tick=3 for "a", _tick now 4; returns "1"
# stamps: a=3, b=1, c=2   ← "b" is LRU

kv.set_capacity(2) # store has 3 entries, max is 2 → evict 1 LRU ("b")
                   # returns 1
# store: {a: "1", c: "3"}

kv.put("d", "4")   # store is at capacity (2); new key → evict LRU
                   # stamps: a=3, c=2  → "c" is LRU → evict "c"
                   # insert "d" with tick=4; _tick now 5
# store: {a: "1", d: "4"}

kv.get("a")        # "1"
kv.get("d")        # "4"
kv.get("c")        # "" (evicted)
```

## Constraints

- `max_keys` is a positive integer.
- Ties in access stamp (shouldn't happen with a monotonic counter) can be broken arbitrarily.
- Default state: no capacity limit (the store grows unbounded until `set_capacity` is called).
- `set_capacity` may be called multiple times; the most recent call wins.

## Common gotchas

1. **Misses don't update the stamp.** Only successful reads (and all writes) count as "accesses."
2. **Overwriting a key never evicts.** Eviction only triggers when a *new* key would exceed capacity.
3. **`set_capacity` evicts immediately.** Don't wait for the next `put` — evict right away if over limit.
4. **The tick is monotonically increasing.** Increment it every time any entry's stamp is updated; the exact increment value (by 1 each time) ensures a total order.
5. **LRU = lowest stamp.** When choosing what to evict, pick the entry with the minimum `last_access` value, not the oldest inserted.

## When you're done

```
python3 test_level4.py
```

All Level 1-4 tests must pass before moving to Level 5.
