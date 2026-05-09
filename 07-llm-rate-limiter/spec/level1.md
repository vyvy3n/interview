# Level 1 — Register Keys, Consume Tokens, Check Remaining

## What you're implementing

You write **one Python function**:

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

- **Input:** a list of "queries". Each query is a list of strings — the first string is a command name (`"REGISTER_KEY"`, `"CONSUME"`, or `"GET_REMAINING"`); the rest are arguments.
- **Output:** a list of strings, **exactly one string per query**, in the same order. Each string is the result of running that query against your rate-limiter state.

## Mental model

Imagine your function is Anthropic's API gateway. Each API key gets a **token bucket**: a
container that starts full (holding `max_tokens` tokens), and shrinks as the key makes API
calls. Each call costs some number of tokens (proportional to request size). If the bucket
is too empty to cover a call's cost, the call is denied — the API returns a 429.

At Level 1, buckets don't refill — a key that burns through its quota stays empty until you
add refill logic in Level 3. For now, focus on the accounting: track how many tokens remain
in each bucket, deduct on successful calls, deny on insufficient capacity.

You're not building a REST API or a CLI. Just a pure function that loops through `queries`
and returns one response per query.

## The 3 commands for Level 1

### 1. `["REGISTER_KEY", <timestamp>, <key_id>, <max_tokens>]`

Register a new API key. Its bucket starts **full** at `max_tokens`.

| Situation | Return |
|-----------|--------|
| `key_id` is new | `"true"` |
| `key_id` already exists | `"false"` |

### 2. `["CONSUME", <timestamp>, <key_id>, <tokens>]`

Attempt to consume `tokens` from the key's bucket (representing an API call of that cost).

| Situation | Return |
|-----------|--------|
| Key exists AND bucket has `>= tokens` available | remaining tokens after deduction, e.g. `"800"` |
| Key does not exist | `""` (denied — no consumption) |
| Key exists but bucket has `< tokens` available | `""` (denied — no consumption, bucket unchanged) |

### 3. `["GET_REMAINING", <timestamp>, <key_id>]`

Return the current bucket level without consuming anything.

| Situation | Return |
|-----------|--------|
| Key exists | current token count as a string, e.g. `"500"` |
| Key does not exist | `""` |

## Worked example — trace through it

```python
queries = [
    ["REGISTER_KEY",  "1", "key-A", "1000"],
    ["REGISTER_KEY",  "2", "key-A", "500"],
    ["CONSUME",       "3", "key-A", "300"],
    ["CONSUME",       "4", "key-B", "100"],
    ["GET_REMAINING", "5", "key-A"],
    ["CONSUME",       "6", "key-A", "800"],
    ["GET_REMAINING", "7", "key-A"],
]
```

Step by step, watching the internal state and the output collected so far:

| # | Query | Internal state after | Output for this query |
|---|-------|----------------------|-----------------------|
| 1 | `REGISTER_KEY key-A 1000` | `{"key-A": {tokens: 1000, max: 1000}}` | `"true"` |
| 2 | `REGISTER_KEY key-A 500` (dup) | unchanged | `"false"` |
| 3 | `CONSUME key-A 300` | `{"key-A": {tokens: 700, max: 1000}}` | `"700"` |
| 4 | `CONSUME key-B 100` (missing) | unchanged | `""` |
| 5 | `GET_REMAINING key-A` | unchanged | `"700"` |
| 6 | `CONSUME key-A 800` (only 700 left) | unchanged | `""` |
| 7 | `GET_REMAINING key-A` | unchanged | `"700"` |

Final return value:

```python
["true", "false", "700", "", "700", "", "700"]
```

That's it. You return that list. The test harness compares your list to the expected list.

## Constraints

- All `<timestamp>` values are positive integer **strings**, strictly increasing across queries.
- All `<tokens>` and `<max_tokens>` values are positive integer **strings** (`> 0`).
- `<key_id>` is any non-empty string.
- Up to `10^5` queries — aim for `O(1)` per operation.
- **Note:** strings everywhere. You must convert with `int(tokens)` to do math, and `str(remaining)` to return.

## Common gotchas

1. **Bucket starts FULL at `max_tokens`** — not at 0. A newly registered key can immediately consume up to its max.
2. **Denied CONSUME must NOT modify the bucket** — if there are insufficient tokens, the bucket is completely unchanged. No partial consumption.
3. **REGISTER_KEY on duplicate returns `"false"` and leaves the existing key untouched** — do not reset its bucket or max.
4. **GET_REMAINING on a missing key returns `""`** — not `"0"`. Missing and empty are different.
5. **`tokens` can equal the full bucket exactly** — consuming exactly what's left leaves `"0"` remaining (not denied). Zero remaining is a valid, successful consumption.

## When you're done

```
cd 07-llm-rate-limiter
python3 test_level1.py
```

All tests must pass before Level 2 is revealed.
