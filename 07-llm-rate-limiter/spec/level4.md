# Level 4 — Tier Upgrades and Key Merging

## What you're implementing

You extend `solution(queries)` with two new commands: `UPGRADE_TIER` and `MERGE_KEYS`.
All Level 1, Level 2, and Level 3 commands continue to work unchanged.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

## Mental model

Anthropic's API has three tiers: Free, Build, and Scale — each with different `max_tokens`
and `refill_rate` limits. When a customer upgrades their tier, their bucket capacity and
refill rate both change immediately. When a company acquires another company (or an admin
consolidates two API keys), they merge one key into another: capacity, tokens, and usage
history all combine.

**UPGRADE_TIER** is the simpler of the two: refill first, then update the limits. If the
current token count exceeds the new (possibly smaller) cap, trim it. The refill rate changes
atomically with the cap.

**MERGE_KEYS** is the trickier one. Both keys must refill independently up to the current
timestamp (each with its own rate). Then the surviving key absorbs the absorbed key's
capacity, tokens, usage history, and the better of the two refill rates. The absorbed key
disappears permanently.

## The 2 commands for Level 4

### 1. `["UPGRADE_TIER", <timestamp>, <key_id>, <new_max>, <new_rate>]`

Upgrade a key's tier: change its `max_tokens` and `refill_rate`.

**Steps (in order):**
1. Refill the bucket first using the **old** rate up to `ts`.
2. Set `max_tokens = new_max`.
3. If `current_tokens > new_max`, cap it: `current_tokens = new_max`.
4. Set `refill_rate = new_rate`.
5. Set `last_action_ts = ts`.

| Situation | Return |
|-----------|--------|
| Key exists | new `current_tokens` as a string (after refill and possible cap) |
| Key does not exist | `""` |

### 2. `["MERGE_KEYS", <timestamp>, <surviving_key>, <absorbed_key>]`

Merge `absorbed_key` into `surviving_key`. `absorbed_key` ceases to exist.

**Steps (in order):**
1. Refill `surviving_key` using its own rate up to `ts`.
2. Refill `absorbed_key` using its own rate up to `ts`.
3. `surviving_key.max_tokens += absorbed_key.max_tokens`
4. `surviving_key.current_tokens += absorbed_key.current_tokens` — then cap at new max if needed.
5. `surviving_key.total_consumed += absorbed_key.total_consumed`
6. `surviving_key.refill_rate = max(surviving_key.refill_rate, absorbed_key.refill_rate)`
7. `surviving_key.last_action_ts = ts`
8. Delete `absorbed_key` entirely.

| Situation | Return |
|-----------|--------|
| Both keys exist and they are different | `"true"` |
| Either key does not exist | `""` |
| `surviving_key == absorbed_key` | `""` (self-merge is rejected) |

After a successful merge, any subsequent operation on `absorbed_key` returns `""` or `"false"`
(as if the key never existed).

## Worked example — trace through it

```python
queries = [
    ["REGISTER_KEY",  "0",  "key-A", "1000"],
    ["REGISTER_KEY",  "0",  "key-B", "500"],
    ["SET_REFILL_RATE","0", "key-A", "100"],
    ["SET_REFILL_RATE","0", "key-B", "40"],
    ["CONSUME",       "0",  "key-A", "200"],
    ["CONSUME",       "0",  "key-B", "100"],
    ["MERGE_KEYS",    "10", "key-A", "key-B"],
    ["GET_REMAINING", "10", "key-A"],
    ["GET_REMAINING", "10", "key-B"],
    ["UPGRADE_TIER",  "20", "key-A", "3000", "200"],
    ["GET_REMAINING", "25", "key-A"],
]
```

State just before MERGE_KEYS at ts=10:

First, refill each key independently to ts=10.

**key-A** at ts=0 after CONSUME: tokens=800, rate=100, last_ts=0.
- elapsed = 10-0 = 10 seconds, refill = 100*10 = 1000 → 800+1000 = 1800, cap at max=1000 → tokens=1000.

**key-B** at ts=0 after CONSUME: tokens=400, rate=40, last_ts=0.
- elapsed = 10-0 = 10 seconds, refill = 40*10 = 400 → 400+400 = 800, cap at max=500 → tokens=500.

Now merge:
- `surviving (key-A).max_tokens = 1000 + 500 = 1500`
- `surviving (key-A).current_tokens = 1000 + 500 = 1500` → cap at 1500 → `1500`
- `surviving (key-A).total_consumed = 200 + 100 = 300`
- `surviving (key-A).refill_rate = max(100, 40) = 100`
- key-B is deleted.

Trace table:

| # | ts | Query | key-A (tokens/max/rate/total) | key-B (tokens/max/rate/total) | Output |
|---|----|-----------|----|-----|--------|
| 1 | 0 | `REGISTER_KEY key-A 1000` | 1000/1000/0/0 | — | `"true"` |
| 2 | 0 | `REGISTER_KEY key-B 500` | 1000/1000/0/0 | 500/500/0/0 | `"true"` |
| 3 | 0 | `SET_REFILL_RATE key-A 100` | 1000/1000/100/0 | 500/500/0/0 | `"true"` |
| 4 | 0 | `SET_REFILL_RATE key-B 40` | 1000/1000/100/0 | 500/500/40/0 | `"true"` |
| 5 | 0 | `CONSUME key-A 200` | 800/1000/100/200 | 500/500/40/0 | `"800"` |
| 6 | 0 | `CONSUME key-B 100` | 800/1000/100/200 | 400/500/40/100 | `"400"` |
| 7 | 10 | `MERGE_KEYS key-A key-B` | after refill both; key-A: 1500/1500/100/300 | deleted | `"true"` |
| 8 | 10 | `GET_REMAINING key-A` | elapsed=10-10=0, +0 → 1500 | deleted | `"1500"` |
| 9 | 10 | `GET_REMAINING key-B` | — | missing | `""` |
| 10 | 20 | `UPGRADE_TIER key-A 3000 200` | refill first: elapsed=20-10=10, +100*10=1000 → 1500+1000=2500 (cap 1500 currently; new_max=3000 so no post-upgrade cap needed); then max→3000, rate→200, tokens=2500 | deleted | `"2500"` |
| 11 | 25 | `GET_REMAINING key-A` | elapsed=25-20=5, +200*5=1000 → 2500+1000=3500, cap at 3000 → 3000 | deleted | `"3000"` |

Final return value:

```python
["true", "true", "true", "true", "800", "400", "true", "1500", "", "2500", "3000"]
```

Key trace notes:
- Row 7 MERGE: key-A refill: elapsed=10, +100*10=1000 → 800+1000=1800 → capped at 1000 (max=1000). key-B refill: elapsed=10, +40*10=400 → 400+400=800 → capped at 500. Then max: 1000+500=1500. tokens: 1000+500=1500 → no cap needed (1500 ≤ 1500). rate=max(100,40)=100.
- Row 10 UPGRADE_TIER: refill first using OLD rate (100) for elapsed 20-10=10s → 1500+1000=2500 (old max was 1500, so cap at 1500... wait: 1500+1000=2500 > 1500, capped at 1500). Then new_max=3000. current_tokens=1500 ≤ 3000, no capping needed. rate=200. Output: 1500. (Wait — rechecking: at ts=10 after MERGE, tokens=1500, max=1500, last_ts=10. At ts=20, elapsed=10, refill=100*10=1000 → 1500+1000=2500, cap at OLD max 1500 → tokens=1500. Then new max becomes 3000, tokens=1500 ≤ 3000. Output: 1500.)

**CORRECTED** row 10 output: `"1500"` (refill is capped at old max 1500 before the max is changed to 3000).

**CORRECTED** row 11: elapsed=25-20=5, +200*5=1000 → 1500+1000=2500, cap at 3000 → 2500.

Corrected final return value:

```python
["true", "true", "true", "true", "800", "400", "true", "1500", "", "1500", "2500"]
```

## Constraints

- All Level 1, 2, and 3 constraints still apply.
- `<new_max>` and `<new_rate>` are positive integer strings (`>= 1`).
- Timestamps are strictly increasing across queries.
- After MERGE_KEYS, the absorbed key is permanently gone — any op on it returns `""` or `"false"`.

## Common gotchas

1. **Refill happens BEFORE the max changes in UPGRADE_TIER** — refill is computed against the OLD max. Only after the refill step do you update `max_tokens`. Then (and only then) do you check whether `current_tokens > new_max` and cap it.
2. **Refill both keys independently in MERGE_KEYS** — each key refills using its own rate for its own elapsed time (based on its own `last_action_ts`). They don't share a clock.
3. **MERGE refill rate = MAX, not SUM** — the surviving key takes the higher of the two rates. Summing rates would be a classic mistake.
4. **MERGE tokens are capped at the COMBINED max** — after adding `max_tokens`, the combined `current_tokens` might still fit. Don't cap at the old max.
5. **Self-merge is rejected** — `MERGE_KEYS ts key-A key-A` returns `""`. One key that is both surviving and absorbed is a no-op. Check for this before doing any refill.
6. **UPGRADE_TIER with new_max smaller than current tokens** — this is valid; it just caps `current_tokens` to `new_max`. For example, upgrading to a lower tier should reduce the bucket to the new cap if it was above it.

## When you're done

```
cd 07-llm-rate-limiter
python3 test_level4.py
```

All Level 4 tests must pass. Congratulations — you've built Anthropic's token-bucket rate limiter end-to-end.
