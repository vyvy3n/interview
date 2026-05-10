# Level 2 — Bulk Operations and Prefix Queries

## What you're implementing

Add three new methods to `KVStore`:

```python
def multi_get(self, keys: list[str]) -> list[str]: ...
def keys_by_prefix(self, prefix: str) -> list[str]: ...
def count(self) -> int: ...
```

All Level 1 methods still work unchanged.

## Mental model

Real caches need batch reads (avoid round-trip overhead) and prefix scans (namespace lookups like `"user:*"`). `multi_get` is the batch read. `keys_by_prefix` is the prefix scan. `count` gives you the current occupancy at a glance.

## The 3 methods for Level 2

### A. `multi_get(keys: list[str]) -> list[str]`

Fetch multiple keys in one call. Returns a list of values **in the same order as the input `keys` list**. For any key that is missing, include `""` at that position.

### B. `keys_by_prefix(prefix: str) -> list[str]`

Return all keys currently in the store that start with `prefix`, sorted **alphabetically** (ascending). If no keys match, return `[]`.

An empty string prefix `""` matches all keys.

### C. `count() -> int`

Return the number of keys currently in the store (i.e. `len` of the underlying dict).

## Worked example

```python
kv = KVStore()
kv.put("user:alice", "30")
kv.put("user:bob", "25")
kv.put("user:carol", "28")
kv.put("session:xyz", "active")

kv.count()                          # 4

kv.multi_get(["user:alice", "missing", "user:bob"])
# ["30", "", "25"]

kv.keys_by_prefix("user:")
# ["user:alice", "user:bob", "user:carol"]

kv.keys_by_prefix("session:")
# ["session:xyz"]

kv.keys_by_prefix("z")
# []

kv.delete("user:bob")
kv.count()                          # 3
kv.keys_by_prefix("user:")
# ["user:alice", "user:carol"]
```

## Constraints

- `multi_get` input list can have duplicate keys — return values for each position independently.
- `keys_by_prefix("")` returns all current keys in sorted order.
- Up to `10^3` keys in the store; up to `10^2` keys in a single `multi_get` call.
- Alphabetical sort means Python's default string sort (`sorted()`).

## Common gotchas

1. **Order matters in `multi_get`.** The output list is 1-to-1 with the input list — don't sort or deduplicate.
2. **`keys_by_prefix` returns *keys*, not values.** It's a key listing, not a key-value dump.
3. **Prefix `""` matches everything.** `"".startswith("")` is `True` in Python, so the empty prefix is valid.
4. **`count()` reflects the live store.** It changes after `put` / `delete` — don't cache it.
5. **`keys_by_prefix` must be sorted.** An unsorted answer will fail the tests even if the set of keys is right.

## When you're done

```
python3 test_level2.py
```

All Level 1 and Level 2 tests must pass before moving to Level 3.
