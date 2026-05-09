# Level 1 — Upload, Get, Copy

## What you're implementing

You write **one Python function**:

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

- **Input:** a list of "queries". Each query is a list of strings — the first string is a command name (`"FILE_UPLOAD"`, `"FILE_GET"`, or `"FILE_COPY"`); the rest are arguments.
- **Output:** a list of strings, **exactly one string per query**, in the same order. Each string is the result of running that query against your file system state.

## Mental model

Imagine your function is a tiny file server. It receives a sequence of commands one at a time, mutates an internal state (a dict of `filename → size`), and emits a one-line response for each command.

File names are global and unique — there is no directory structure, just a flat namespace. A file either exists or it doesn't. Sizes are always positive integers (stored as ints internally, returned as strings in output).

## The 3 commands for Level 1

### 1. `["FILE_UPLOAD", <timestamp>, <name>, <size>]`

Store a file with the given name and size.

| Situation | Return |
|-----------|--------|
| `name` is new | `"true"` |
| `name` already exists | `"false"` (do NOT overwrite) |

### 2. `["FILE_GET", <timestamp>, <name>]`

Look up a file's size.

| Situation | Return |
|-----------|--------|
| File exists | size as a string, e.g. `"200"` |
| File does not exist | `""` (empty string) |

### 3. `["FILE_COPY", <timestamp>, <source>, <dest>]`

Copy an existing file to a new name.

| Situation | Return |
|-----------|--------|
| `source` exists, `dest` is new | `"true"` (dest is created with same size) |
| `source` exists, `dest` already exists | `"true"` (dest is **overwritten** with source's size) |
| `source` does not exist | `""` (empty string — dest is unchanged) |

## Worked example — trace through it

```python
queries = [
    ["FILE_UPLOAD", "1", "report.pdf",   "500"],
    ["FILE_UPLOAD", "2", "report.pdf",   "300"],   # duplicate
    ["FILE_GET",    "3", "report.pdf"],
    ["FILE_GET",    "4", "missing.txt"],
    ["FILE_COPY",   "5", "report.pdf",   "backup.pdf"],
    ["FILE_COPY",   "6", "ghost.txt",    "ghost2.txt"],
    ["FILE_UPLOAD", "7", "notes.txt",    "100"],
    ["FILE_COPY",   "8", "notes.txt",    "backup.pdf"],   # overwrite
    ["FILE_GET",    "9", "backup.pdf"],
]
```

Step by step, watching the internal state and the output collected so far:

| # | Query | Internal state after | Output |
|---|-------|----------------------|--------|
| 1 | `FILE_UPLOAD report.pdf 500` | `{report.pdf: 500}` | `"true"` |
| 2 | `FILE_UPLOAD report.pdf 300` (dup) | `{report.pdf: 500}` | `"false"` |
| 3 | `FILE_GET report.pdf` | unchanged | `"500"` |
| 4 | `FILE_GET missing.txt` (no file) | unchanged | `""` |
| 5 | `FILE_COPY report.pdf → backup.pdf` | `{report.pdf:500, backup.pdf:500}` | `"true"` |
| 6 | `FILE_COPY ghost.txt → ghost2.txt` (no source) | unchanged | `""` |
| 7 | `FILE_UPLOAD notes.txt 100` | `{report.pdf:500, backup.pdf:500, notes.txt:100}` | `"true"` |
| 8 | `FILE_COPY notes.txt → backup.pdf` (overwrite) | `{report.pdf:500, backup.pdf:100, notes.txt:100}` | `"true"` |
| 9 | `FILE_GET backup.pdf` | unchanged | `"100"` |

Final return value:

```python
["true", "false", "500", "", "true", "", "true", "true", "100"]
```

## Constraints

- All `<timestamp>` values are positive integer **strings**, strictly increasing across queries.
- All `<size>` values are positive integer **strings** (`> 0`).
- `<name>` is any non-empty string (no path separators — just a flat name).
- Up to `10^5` queries — aim for `O(1)` per operation.
- **Note:** sizes arrive as strings; store them as `int`, return them as `str`.

## Common gotchas

1. **FILE_UPLOAD does NOT overwrite.** If the file exists, return `"false"` and leave the original untouched.
2. **FILE_COPY DOES overwrite.** Dest already existing is fine — just stomp it.
3. **FILE_COPY returns `""` (not `"false"`) when source is missing.** The return type differs from FILE_UPLOAD's failure.
4. **Timestamps are arguments, not indices.** You don't need to use them at all in Level 1 — just unpack and ignore.
5. **The copy is independent.** After `FILE_COPY a → b`, uploading a new file named `a` again should still return `"false"` (a already exists); changing `b` in later levels won't affect `a`.

## When you're done

```
cd 03-file-system
python3 test_level1.py
```

All tests must pass before Level 2 is revealed.
