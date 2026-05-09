# Level 3 — Time-Based Token Refill

## What you're implementing

You extend `solution(queries)` with one new command: `SET_REFILL_RATE`. More importantly,
you add **time-based bucket refill** semantics that affect ALL existing commands. All Level 1
and Level 2 commands continue to work, but their behavior changes when a refill rate is set.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

## Mental model

Real token buckets don't just drain — they continuously replenish. Anthropic's rate limiter
refills each key's bucket at a steady rate (tokens per second) up to its maximum capacity.
A key on the free tier might refill at 100 tokens/second with a 10,000-token cap; a scale-tier
key might refill at 10,000 tokens/second with a 1,000,000-token cap.

The implementation trick: rather than a background timer, you compute refill **lazily** — only
when a key is touched. When any operation accesses a key, you first compute how many seconds
have elapsed since the last time that key was touched, multiply by the refill rate, add that
to the bucket (capped at max), then proceed with the operation.

This is the "lazy token bucket" pattern — it's the correct implementation for single-threaded
systems (and for this interview).

## The 1 command for Level 3

### 1. `["SET_REFILL_RATE", <timestamp>, <key_id>, <tokens_per_second>]`

Set or update the refill rate for a key.

| Situation | Return |
|-----------|--------|
| Key exists | `"true"` |
| Key does not exist | `"false"` |

**Critically:** before applying the new rate, first refill the bucket up to `ts` using the
**old rate** (if one existed). Then set the new rate. Then update `last_action_ts = ts`.

If the key had no prior rate (i.e., this is the first `SET_REFILL_RATE`), there is nothing
to refill before setting — just apply the new rate and set `last_action_ts = ts`.

## Refill semantics (the heart of Level 3)

Every key now tracks these fields in addition to Level 1 data:

- `refill_rate`: tokens added per second (default `0` — no refill until set)
- `last_action_ts`: timestamp of the last operation that touched this key (initialized to
  the timestamp of `REGISTER_KEY`)

**Rule:** Before ANY operation reads or writes a key's bucket, apply this refill step first:

```
elapsed = current_ts - last_action_ts
current_tokens = min(max_tokens, current_tokens + refill_rate * elapsed)
last_action_ts = current_ts
```

This applies to: `CONSUME`, `GET_REMAINING`, `SET_REFILL_RATE`, and `TOTAL_CONSUMED`.

Notes:
- All arithmetic is **integer** — `refill_rate * elapsed` is exact (no floats).
- `TOTAL_CONSUMED` also triggers refill (because `last_action_ts` must advance).
- Keys with `refill_rate == 0` never refill (0 * elapsed = 0).
- The refill cap is `max_tokens` — you can never exceed the maximum.

## Worked example — trace through it

```python
queries = [
    ["REGISTER_KEY",   "0",   "key-A", "1000"],
    ["CONSUME",        "0",   "key-A", "600"],
    ["SET_REFILL_RATE","5",   "key-A", "50"],
    ["GET_REMAINING",  "7",   "key-A"],
    ["CONSUME",        "10",  "key-A", "500"],
    ["SET_REFILL_RATE","10",  "key-A", "100"],
    ["GET_REMAINING",  "15",  "key-A"],
    ["CONSUME",        "20",  "key-A", "2000"],
    ["GET_REMAINING",  "20",  "key-A"],
]
```

Trace (key-A: max=1000, rate=0 initially, last_ts=0):

| # | ts | Refill step (before op) | Operation | tokens after | last_ts | Output |
|---|----|--------------------------|-----------|--------------|---------|----|
| 1 | 0 | first op, no refill | REGISTER_KEY: tokens=1000, rate=0, last_ts=0 | 1000 | 0 | `"true"` |
| 2 | 0 | elapsed=0-0=0, +0*0=0 → 1000 | CONSUME 600: 1000-600=400 | 400 | 0 | `"400"` |
| 3 | 5 | elapsed=5-0=5, +0*5=0 → 400 (rate still 0) | SET_REFILL_RATE 50: now rate=50 | 400 | 5 | `"true"` |
| 4 | 7 | elapsed=7-5=2, +50*2=100 → 500 | GET_REMAINING | 500 | 7 | `"500"` |
| 5 | 10 | elapsed=10-7=3, +50*3=150 → 650 | CONSUME 500: 650-500=150 | 150 | 10 | `"150"` |
| 6 | 10 | elapsed=10-10=0, +50*0=0 → 150 (old rate=50) | SET_REFILL_RATE 100: rate=100 | 150 | 10 | `"true"` |
| 7 | 15 | elapsed=15-10=5, +100*5=500 → 650 | GET_REMAINING | 650 | 15 | `"650"` |
| 8 | 20 | elapsed=20-15=5, +100*5=500 → min(1000,1150)=1000 | CONSUME 2000: 1000 < 2000, denied | 1000 | 20 | `""` |
| 9 | 20 | elapsed=20-20=0, +100*0=0 → 1000 | GET_REMAINING | 1000 | 20 | `"1000"` |

Final return value:

```python
["true", "400", "true", "500", "150", "true", "650", "", "1000"]
```

Key trace notes:
- Row 3: At ts=5, elapsed = 5-0 = 5 seconds. But rate is still 0 (we're applying the OLD rate before setting the new one). 0 * 5 = 0, so no refill. Then rate becomes 50.
- Row 8: At ts=20, elapsed=5, refill = 100*5 = 500. tokens = 150+500 = 650 (wait — that's from row 7). At ts=20 after row 7, last_ts=15, tokens=650. elapsed=20-15=5, refill=100*5=500 → 650+500=1150, capped at max=1000. Then CONSUME 2000 is denied (1000 < 2000). tokens stay at 1000.
- Row 9: elapsed=20-20=0, no refill, GET_REMAINING returns 1000.

## Constraints

- All Level 1 and Level 2 constraints still apply.
- `<tokens_per_second>` is a positive integer string (`>= 1`).
- Timestamps are strictly increasing **across queries** — but two queries at the same timestamp
  can occur (elapsed = 0 → zero refill).
- All refill math uses integer arithmetic. No floats.

## Common gotchas

1. **Refill uses the OLD rate before applying the new one** — in `SET_REFILL_RATE`, the refill step runs with the current (old) rate, then the rate is updated. Getting this order wrong corrupts the bucket.
2. **Refill is lazy — it only happens when a key is touched** — do not try to refill all keys on every query. Only refill the specific key being operated on.
3. **Cap at `max_tokens` after refill** — `current_tokens + refill * elapsed` can exceed `max_tokens`. Always apply `min(max_tokens, ...)`.
4. **`TOTAL_CONSUMED` also triggers the refill step** — even though it doesn't change the bucket. This is necessary to keep `last_action_ts` current.
5. **`REGISTER_KEY` initializes `last_action_ts` to the registration timestamp** — not 0. If ts=100 for REGISTER_KEY and ts=110 for the next CONSUME, elapsed = 10 (times rate).

## When you're done

```
cd 07-llm-rate-limiter
python3 test_level3.py
```

All Level 3 tests must pass before Level 4 is revealed.
