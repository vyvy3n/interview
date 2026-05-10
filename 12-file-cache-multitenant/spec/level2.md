# Level 2 — Updates + Queries

## What you're implementing

Add three methods:

```python
def update(self, filename: str, content: str) -> bool: ...
def fetch_by_prefix(self, prefix: str) -> list[str]: ...
def get_total_size(self) -> int: ...
```

All Level 1 methods remain intact.

## Mental model

Now the cache supports **explicit overwrite** (separate from store), **prefix-based directory listing**, and **total bytes used** — the first step toward capacity management.

Think of `fetch_by_prefix` as `ls prefix*` in a shell: it lists matching filenames sorted alphabetically. It does NOT return file contents.

## The 3 methods for Level 2

### A. `update(filename: str, content: str) -> bool`

Overwrite the content of an existing file.

| Situation | Action | Return |
|-----------|--------|--------|
| `filename` exists | Replace content | `True` |
| `filename` missing | Do nothing, do NOT create | `False` |

### B. `fetch_by_prefix(prefix: str) -> list[str]`

Return a **sorted** list of filenames whose names start with `prefix`. Returns `[]` if no match. An empty string prefix `""` matches all files.

**Important:** This is a metadata query — it does NOT update LRU access counters (relevant in Level 3).

### C. `get_total_size() -> int`

Return the sum of `len(content)` over all files in the cache. An empty-content file contributes 0.

## Worked example

```python
cache = FileCache()

cache.store("img_cat.jpg", "cat data")
cache.store("img_dog.jpg", "dog data")
cache.store("img_ant.jpg", "ant data")
cache.store("notes.txt",   "my notes")

cache.fetch_by_prefix("img_")
# ["img_ant.jpg", "img_cat.jpg", "img_dog.jpg"]  — sorted alphabetically

cache.fetch_by_prefix("notes")
# ["notes.txt"]

cache.fetch_by_prefix("xyz")
# []

cache.get_total_size()
# len("cat data") + len("dog data") + len("ant data") + len("my notes") = 8+8+8+8 = 32

cache.update("notes.txt", "revised")  # True
cache.get_total_size()                 # 32 - 8 + 7 = 31

cache.update("ghost.txt", "new")      # False — file doesn't exist
cache.fetch("ghost.txt")              # ""
```

## Constraints

- `prefix` may be an empty string (matches all files).
- `fetch_by_prefix` returns filenames, not contents.
- `update` never creates a new file — use `store` for creation.
- `get_total_size` counts bytes in content strings (`len(content)`).

## Common gotchas

1. **`update` does NOT create** — if the file doesn't exist, return `False` and do nothing.
2. **`fetch_by_prefix` must be sorted** — use `sorted()`.
3. **`fetch_by_prefix` does NOT update LRU** — it's a metadata scan, not a file access.
4. **`get_total_size` reflects updates** — when content changes, the total changes.
5. **`fetch_by_prefix("")` returns ALL filenames sorted** — empty prefix is valid.

## When you're done

```
python3 test_level2.py
```

All tests must pass before moving to Level 3.
