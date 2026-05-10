# Level 1 — Basic File Ops

## What you're implementing

You write a class `FileCache` with four methods:

```python
class FileCache:
    def store(self, filename: str, content: str) -> bool: ...
    def fetch(self, filename: str) -> str: ...
    def remove(self, filename: str) -> bool: ...
    def size(self) -> int: ...
```

No external libraries. The backing store is a plain Python dict.

## Mental model

Imagine a simple in-memory filesystem — like a tiny S3 bucket. Files are stored by name. You can write a new file, read its content, delete it, or count how many files exist.

**Key difference from a key-value store:** `store` does NOT overwrite existing files — that's intentional. Overwriting is a separate `update` method added in Level 2.

## The 4 methods for Level 1

### A. `store(filename: str, content: str) -> bool`

Store a file. If `filename` does not exist, store it and return `True`. If `filename` already exists, do **nothing** and return `False` (no overwrite).

### B. `fetch(filename: str) -> str`

Return the content of `filename`. If `filename` does not exist, return `""` (empty string).

### C. `remove(filename: str) -> bool`

Remove `filename` from the cache.

| Situation | Return |
|-----------|--------|
| `filename` exists | `True` — file removed |
| `filename` does not exist | `False` — nothing changed |

### D. `size() -> int`

Return the count of files currently in the cache.

## Worked example

```python
cache = FileCache()

cache.store("readme.txt", "hello world")  # True
cache.fetch("readme.txt")                  # "hello world"

cache.store("readme.txt", "overwrite?")   # False — no overwrite
cache.fetch("readme.txt")                  # "hello world" (unchanged)

cache.fetch("missing.txt")                 # ""

cache.size()                               # 1

cache.remove("readme.txt")                # True
cache.remove("readme.txt")               # False (already gone)
cache.fetch("readme.txt")                 # ""
cache.size()                              # 0
```

State trace:

| Step | Call | Files | Return |
|------|------|-------|--------|
| 1 | `store("readme.txt", "hello world")` | `{readme.txt}` | `True` |
| 2 | `fetch("readme.txt")` | unchanged | `"hello world"` |
| 3 | `store("readme.txt", "overwrite?")` | unchanged | `False` |
| 4 | `fetch("missing.txt")` | unchanged | `""` |
| 5 | `size()` | unchanged | `1` |
| 6 | `remove("readme.txt")` | `{}` | `True` |
| 7 | `remove("readme.txt")` | `{}` | `False` |
| 8 | `size()` | `{}` | `0` |

## Constraints

- Filenames and content are strings (content may be empty `""`).
- Up to `10^5` operations — aim for O(1) per call.
- No persistence — cache lives only in memory.

## Common gotchas

1. **`store` does NOT overwrite** — unlike a key-value `put`. Return `False` on duplicate.
2. **`fetch` returns `""` not `None`** for missing files. Tests check `assertEqual(result, "")`.
3. **`remove` returns a `bool`**, not a string.
4. **`size` counts distinct files**, not total content bytes.
5. **Storing with empty content `""` is valid** — the file exists; `fetch` returns `""` (not the same as "missing").

## When you're done

```
python3 test_level1.py
```

All tests must pass before moving to Level 2.
