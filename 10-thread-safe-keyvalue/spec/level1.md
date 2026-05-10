# Level 1 — Basic Put / Get / Delete

## What you're implementing

You write a class `KVStore` with three methods:

```python
class KVStore:
    def put(self, key: str, value: str) -> None: ...
    def get(self, key: str) -> str: ...
    def delete(self, key: str) -> bool: ...
```

No external libraries. The backing store is a plain Python dict.

## Mental model

Imagine a tiny in-memory database — like a stripped-down Redis. Every `put` writes a record. Every `get` fetches it (or says "not there"). Every `delete` removes it and tells you whether it existed.

All keys and values are strings. There is no persistence — the store lives only in memory for the lifetime of the `KVStore` object.

## The 3 methods for Level 1

### A. `put(key: str, value: str) -> None`

Store `value` under `key`. If `key` already exists, overwrite its value. Returns nothing.

### B. `get(key: str) -> str`

Return the value stored under `key`. If `key` does not exist, return `""` (empty string).

### C. `delete(key: str) -> bool`

Remove `key` (and its value) from the store.

| Situation | Return |
|-----------|--------|
| `key` exists | `True` — entry removed |
| `key` does not exist | `False` — nothing changed |

## Worked example

```python
kv = KVStore()

kv.put("name", "alice")
kv.get("name")        # "alice"

kv.put("name", "bob") # overwrite
kv.get("name")        # "bob"

kv.get("missing")     # ""

kv.delete("name")     # True
kv.delete("name")     # False  (already gone)
kv.get("name")        # ""
```

Trace through the internal state:

| Step | Call | Store state after | Return |
|------|------|-------------------|--------|
| 1 | `put("name", "alice")` | `{"name": "alice"}` | — |
| 2 | `get("name")` | unchanged | `"alice"` |
| 3 | `put("name", "bob")` | `{"name": "bob"}` | — |
| 4 | `get("name")` | unchanged | `"bob"` |
| 5 | `get("missing")` | unchanged | `""` |
| 6 | `delete("name")` | `{}` | `True` |
| 7 | `delete("name")` | `{}` | `False` |
| 8 | `get("name")` | `{}` | `""` |

## Constraints

- Keys and values are non-empty strings.
- Up to `10^5` operations — aim for O(1) per call.
- No need to handle `None` keys or values at this level.

## Common gotchas

1. **Return `""` not `None` for missing keys.** The tests check `assertEqual(result, "")`.
2. **`delete` returns a `bool`, not a string.** Return `True`/`False`, not `"true"`/`"false"`.
3. **`put` on an existing key is a silent overwrite** — don't raise an exception or return an error.
4. **`put` returns `None`** — no need to return anything meaningful.
5. **`get` after a `delete` must return `""`**, not raise a KeyError.

## When you're done

```
python3 test_level1.py
```

All tests must pass before moving to Level 2.
