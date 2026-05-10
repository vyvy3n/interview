# Level 1 — SET, GET, DELETE on (key, field) pairs

## What you're implementing

You write **one Python function**:

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

- **Input:** a list of "queries". Each query is a list of strings — the first string is a command name (`"SET"`, `"GET"`, or `"DELETE"`); the rest are arguments.
- **Output:** a list of strings, **exactly one string per query**, in the same order. Each string is the result of running that query against your database state.

## Mental model

Imagine a small in-memory database shaped like a nested dictionary: `Dict[str, Dict[str, str]]`. The outer key is a "record name" (called **key**). Each key maps to a set of (field → value) pairs.

You receive a stream of commands, mutate this nested dictionary, and emit one response per command. Nothing is persisted; it all lives in memory for the duration of the `solution()` call.

## The 3 commands for Level 1

### 1. `["SET", <ts>, <key>, <field>, <value>]`

Write `value` at the location `(key, field)`. If `(key, field)` already existed, overwrite silently.

| Situation | Return |
|-----------|--------|
| Always | `""` (empty string) |

### 2. `["GET", <ts>, <key>, <field>]`

Read the value stored at `(key, field)`.

| Situation | Return |
|-----------|--------|
| `(key, field)` exists | the stored value string |
| `key` does not exist | `""` (empty string) |
| `key` exists but `field` does not | `""` (empty string) |

### 3. `["DELETE", <ts>, <key>, <field>]`

Remove the entry at `(key, field)` if it exists.

| Situation | Return |
|-----------|--------|
| `(key, field)` existed and was deleted | `"true"` |
| `key` does not exist | `"false"` |
| `key` exists but `field` does not | `"false"` |

## Worked example — trace through it

```python
queries = [
    ["SET",    "1", "user:1", "name",  "alice"],
    ["SET",    "2", "user:1", "email", "alice@example.com"],
    ["GET",    "3", "user:1", "name"],
    ["GET",    "4", "user:1", "phone"],
    ["GET",    "5", "user:2", "name"],
    ["SET",    "6", "user:1", "name",  "ALICE"],
    ["GET",    "7", "user:1", "name"],
    ["DELETE", "8", "user:1", "email"],
    ["DELETE", "9", "user:1", "email"],
    ["DELETE", "10", "ghost", "x"],
]
```

Step by step, watching the internal state and the output:

| # | Query | Internal state after | Output |
|---|-------|----------------------|--------|
| 1 | `SET user:1 name alice` | `{"user:1": {"name": "alice"}}` | `""` |
| 2 | `SET user:1 email alice@example.com` | `{"user:1": {"name": "alice", "email": "alice@example.com"}}` | `""` |
| 3 | `GET user:1 name` | (unchanged) | `"alice"` |
| 4 | `GET user:1 phone` (field missing) | (unchanged) | `""` |
| 5 | `GET user:2 name` (key missing) | (unchanged) | `""` |
| 6 | `SET user:1 name ALICE` (overwrite) | `{"user:1": {"name": "ALICE", "email": "alice@example.com"}}` | `""` |
| 7 | `GET user:1 name` | (unchanged) | `"ALICE"` |
| 8 | `DELETE user:1 email` | `{"user:1": {"name": "ALICE"}}` | `"true"` |
| 9 | `DELETE user:1 email` (already gone) | (unchanged) | `"false"` |
| 10 | `DELETE ghost x` (key missing) | (unchanged) | `"false"` |

Final return value:

```python
["", "", "alice", "", "", "", "ALICE", "true", "false", "false"]
```

## Constraints

- All `<ts>` values are positive integer **strings**, strictly increasing across queries.
- `<key>`, `<field>`, `<value>` are non-empty strings (no spaces within a single argument).
- Up to `10^5` queries total — aim for `O(1)` per operation.
- The state starts empty — no keys, no fields, no values.

## Common gotchas

1. **SET always returns `""`** — not `"true"`, not the old value, not the new value. Always empty string.
2. **DELETE on a missing key vs. missing field** — both return `"false"`. You only return `"true"` when something actually got removed.
3. **Overwriting with SET** — if `(key, field)` already has a value, just replace it. Don't return `"false"` or raise anything.
4. **Nested dict initialization** — when you SET a brand-new key, you need to create the inner dict first before setting the field. A `defaultdict(dict)` or a manual `setdefault` check both work.
5. **GET on a non-existent key** — don't let Python throw a `KeyError`. Guard with `in` or use `.get()`.

## When you're done

```
cd 02-in-memory-db
python3 test_level1.py
```

All tests must pass before moving to Level 2.
