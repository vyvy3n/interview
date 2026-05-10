# Level 1 — User Accounts & File Uploads

## What you're implementing

You write **one Python function**:

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

- **Input:** a list of "queries". Each query is a list of strings — the first string is a command name (`"CREATE_USER"`, `"UPLOAD"`, or `"DELETE"`); the rest are arguments.
- **Output:** a list of strings, **exactly one string per query**, in the same order. Each string is the result of running that query against your cloud storage state.

## Mental model

Imagine your function is a cloud storage server. It manages user accounts, each with a fixed storage quota (in bytes). Users can upload files; each file has an ID and a size. The server tracks how many bytes each user has used, and refuses uploads that would push them over quota.

Each user has their **own file namespace**: `alice` and `bob` can both have a file called `"doc"` without conflicting — they are completely separate objects.

## The 3 commands for Level 1

### 1. `["CREATE_USER", <timestamp>, <user_id>, <quota>]`

Register a new user with the given storage quota (a positive integer, in bytes).

| Situation | Return |
|-----------|--------|
| `user_id` is new | `"true"` |
| `user_id` already exists | `"false"` |

### 2. `["UPLOAD", <timestamp>, <user_id>, <file_id>, <size>]`

Upload a file owned by `user_id`. The file has identifier `file_id` and occupies `size` bytes.

- If `user_id` already owns a file with this `file_id`, **overwrite** it. The quota check uses the **net difference**: `new_size - old_size` must not push `used` past `quota`.
- If the user does **not** already have this file, quota check is simply `used + new_size <= quota`.

| Situation | Return |
|-----------|--------|
| Upload succeeds | user's total used bytes after upload, e.g. `"500"` |
| User does not exist | `""` (empty string) |
| Upload would exceed quota | `""` — do **not** modify state |

### 3. `["DELETE", <timestamp>, <user_id>, <file_id>]`

Delete the file `file_id` owned by `user_id`. Frees the bytes it occupied.

| Situation | Return |
|-----------|--------|
| File exists and is deleted | `"true"` |
| User does not exist | `"false"` |
| File does not exist for that user | `"false"` |

## Worked example — trace through it

```python
queries = [
    ["CREATE_USER", "1", "alice", "1000"],
    ["CREATE_USER", "2", "alice", "500"],
    ["CREATE_USER", "3", "bob",   "400"],
    ["UPLOAD",      "4", "alice", "report", "300"],
    ["UPLOAD",      "5", "alice", "photo",  "500"],
    ["UPLOAD",      "6", "alice", "video",  "400"],
    ["UPLOAD",      "7", "alice", "report", "100"],
    ["UPLOAD",      "8", "bob",   "report", "300"],
    ["DELETE",      "9", "alice", "photo"],
    ["DELETE",      "10","bob",   "missing"],
    ["UPLOAD",      "11","alice", "video",  "400"],
]
```

Step by step:

| # | Query | alice used / quota | bob used / quota | Output |
|---|-------|--------------------|------------------|--------|
| 1 | CREATE_USER alice 1000 | — / 1000 | — | `"true"` |
| 2 | CREATE_USER alice 500 (dup) | 0 / 1000 | — | `"false"` |
| 3 | CREATE_USER bob 400 | 0 / 1000 | 0 / 400 | `"true"` |
| 4 | UPLOAD alice report 300 | 300 / 1000 | 0 / 400 | `"300"` |
| 5 | UPLOAD alice photo 500 | 800 / 1000 | 0 / 400 | `"800"` |
| 6 | UPLOAD alice video 400 | 800+400=1200 > 1000 — reject | 0 / 400 | `""` |
| 7 | UPLOAD alice report 100 (overwrite, diff = 100-300 = -200) | 800-200=600 / 1000 | 0 / 400 | `"600"` |
| 8 | UPLOAD bob report 300 | 600 / 1000 | 300 / 400 | `"300"` |
| 9 | DELETE alice photo | 600-500=100 / 1000 | 300 / 400 | `"true"` |
| 10 | DELETE bob missing | 100 / 1000 | 300 / 400 | `"false"` |
| 11 | UPLOAD alice video 400 | 100+400=500 / 1000 | 300 / 400 | `"500"` |

Final return value:

```python
["true", "false", "true", "300", "800", "", "600", "300", "true", "false", "500"]
```

## Constraints

- All `<timestamp>` values are positive integer **strings**, strictly increasing across all queries.
- All numeric arguments (`<quota>`, `<size>`) are positive integer **strings** (`>= 1`).
- `<user_id>` and `<file_id>` are non-empty strings with no spaces.
- Up to `10^5` queries — aim for `O(1)` per operation.
- **Strings everywhere**: use `int(size)` to do math, `str(used)` to return.

## Common gotchas

1. **Overwrite quota math**: when a file already exists, the delta is `new_size - old_size`, which can be **negative** (file got smaller — that's fine, and should always succeed if it frees space). Only reject if `used + delta > quota`.
2. **Separate file namespaces**: `alice`'s file `"report"` and `bob`'s file `"report"` are completely independent. Don't store files in a global dict keyed only by `file_id`.
3. **DELETE both-false cases**: return `"false"` whether the user doesn't exist OR the file doesn't exist. Don't try to distinguish them in the return value.
4. **Quota-exact is allowed**: `used + size == quota` is a valid upload (returns the used bytes string, not an error).
5. **State immutability on failure**: if an UPLOAD fails (exceeds quota), leave the user's `used` and file table completely unchanged.

## When you're done

```
cd 04-cloud-storage
python3 test_level1.py
```

All tests must pass before moving to Level 2.
