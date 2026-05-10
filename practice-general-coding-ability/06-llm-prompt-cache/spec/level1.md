# Level 1 — Basic Prompt Cache: PUT / GET / DELETE

## What you're implementing

You write **one Python function**:

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

- **Input:** a list of "queries". Each query is a list of strings — the first string is a command name (`"CACHE_PUT"`, `"CACHE_GET"`, or `"CACHE_DELETE"`); the rest are arguments.
- **Output:** a list of strings, **exactly one string per query**, in the same order. Each string is the result of running that query against your cache state.

## Mental model

Imagine your function is the caching layer of an LLM API server. Every time a user sends a prompt, the server first checks whether it has already computed the response for that exact prompt. If it has (a cache hit), it returns the cached response instantly — no GPU time needed. If not (a cache miss), it calls the model, gets a response, and stores it for next time.

At Level 1, this is a simple key-value store: `prompt → response`. No expiry, no capacity limits, no hit tracking — just put, get, and delete.

You are not building a CLI or REST API. Just a pure function that loops through `queries`, mutates internal cache state (a dict of `prompt → response`), and emits one response string per query.

## The 3 commands for Level 1

### 1. `["CACHE_PUT", <ts>, <prompt>, <response>]`

Store `response` in the cache keyed by `prompt`.

| Situation | Return |
|-----------|--------|
| `prompt` is new | `""` (empty string, always) |
| `prompt` already in cache (overwrite silently) | `""` (empty string, always) |

CACHE_PUT **always returns `""`**. If the prompt already exists, its value is silently overwritten.

### 2. `["CACHE_GET", <ts>, <prompt>]`

Look up `prompt` in the cache.

| Situation | Return |
|-----------|--------|
| `prompt` is in cache (hit) | the stored response string |
| `prompt` is not in cache (miss) | `""` (empty string) |

### 3. `["CACHE_DELETE", <ts>, <prompt>]`

Remove `prompt` from the cache.

| Situation | Return |
|-----------|--------|
| `prompt` was in cache (deleted) | `"true"` |
| `prompt` was not in cache (no-op) | `"false"` |

## Worked example — trace through it

```python
queries = [
    ["CACHE_PUT",    "1", "What is 2+2?",    "4"],
    ["CACHE_GET",    "2", "What is 2+2?"],
    ["CACHE_GET",    "3", "What is 3+3?"],
    ["CACHE_PUT",    "4", "What is 2+2?",    "Four"],
    ["CACHE_GET",    "5", "What is 2+2?"],
    ["CACHE_DELETE", "6", "What is 2+2?"],
    ["CACHE_DELETE", "7", "What is 2+2?"],
    ["CACHE_GET",    "8", "What is 2+2?"],
]
```

Step by step, watching the internal state and the output collected so far:

| # | Query | Internal state after | Output for this query |
|---|-------|----------------------|-----------------------|
| 1 | `CACHE_PUT "What is 2+2?" "4"` | `{"What is 2+2?": "4"}` | `""` |
| 2 | `CACHE_GET "What is 2+2?"` (hit) | unchanged | `"4"` |
| 3 | `CACHE_GET "What is 3+3?"` (miss) | unchanged | `""` |
| 4 | `CACHE_PUT "What is 2+2?" "Four"` (overwrite) | `{"What is 2+2?": "Four"}` | `""` |
| 5 | `CACHE_GET "What is 2+2?"` (hit, new value) | unchanged | `"Four"` |
| 6 | `CACHE_DELETE "What is 2+2?"` (deleted) | `{}` | `"true"` |
| 7 | `CACHE_DELETE "What is 2+2?"` (not found) | `{}` | `"false"` |
| 8 | `CACHE_GET "What is 2+2?"` (miss, was deleted) | `{}` | `""` |

Final return value:

```python
["", "4", "", "", "Four", "true", "false", ""]
```

## Constraints

- All `<ts>` values are positive integer **strings**, strictly increasing across queries.
- `<prompt>` and `<response>` are arbitrary non-empty strings. They may contain spaces.
- Up to `10^5` queries — aim for `O(1)` per operation.
- **Strings everywhere.** No numeric conversion needed at Level 1.

## Common gotchas

1. **CACHE_PUT always returns `""`** — even if you just overwrote an existing entry. Don't return the old value.
2. **CACHE_GET miss vs DELETE miss return different things** — GET miss is `""`, DELETE miss is `"false"`. Don't confuse them.
3. **Overwrite is silent** — a second CACHE_PUT for the same prompt replaces the response with no error. Level 2 will track hits independently of PUTs.
4. **CACHE_DELETE returns `"true"` / `"false"` as strings** — not Python `True` / `False`. Return `"true"` and `"false"`.

## When you're done

```
cd 06-llm-prompt-cache
python3 test_level1.py
```

All tests must pass before Level 2 is revealed.
