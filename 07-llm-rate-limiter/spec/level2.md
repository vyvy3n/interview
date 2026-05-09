# Level 2 — Usage Tracking and Top-K Consumers

## What you're implementing

You extend `solution(queries)` with two new commands: `TOTAL_CONSUMED` and `TOP_K_CONSUMERS`.
All Level 1 commands continue to work unchanged.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

## Mental model

Anthropic's usage dashboard lets customers see how many tokens they've burned over time — and
internally, trust-and-safety teams track which API keys are the heaviest consumers. Level 2
adds this accounting layer: every successful `CONSUME` operation records how many tokens were
spent, and you can query the cumulative total for any key or rank all keys by usage.

Think of `total_consumed` as an ever-growing counter that only increases. Unlike the bucket
level (which will eventually refill), the total consumed is a permanent audit log of spend.

## The 2 commands for Level 2

### 1. `["TOTAL_CONSUMED", <timestamp>, <key_id>]`

Return the cumulative number of tokens successfully consumed by this key since registration.

| Situation | Return |
|-----------|--------|
| Key exists | total tokens consumed (as string), e.g. `"1500"` |
| Key does not exist | `""` |

A freshly registered key with no successful CONSUMEs returns `"0"`.

### 2. `["TOP_K_CONSUMERS", <timestamp>, <k>]`

Return the top `k` keys ranked by total tokens consumed (descending).

| Situation | Return |
|-----------|--------|
| At least one key registered | comma-separated list, e.g. `"key-A(5000), key-B(2000), key-C(0)"` |
| No keys registered | `""` |

- **Sort order:** total consumed descending; ties broken by `key_id` **alphabetically ascending**.
- **Format:** `"key1(total1), key2(total2), ..."` — no trailing comma, single space after each comma.
- **If fewer than `k` keys exist,** return all of them (do not pad or error).
- **Keys with 0 consumption are included** in the ranking.

## Worked example — trace through it

```python
queries = [
    ["REGISTER_KEY",    "1",  "key-A", "1000"],
    ["REGISTER_KEY",    "2",  "key-B", "2000"],
    ["CONSUME",         "3",  "key-A", "400"],
    ["CONSUME",         "4",  "key-B", "900"],
    ["CONSUME",         "5",  "key-A", "300"],
    ["CONSUME",         "6",  "key-A", "5000"],
    ["TOTAL_CONSUMED",  "7",  "key-A"],
    ["TOTAL_CONSUMED",  "8",  "ghost"],
    ["TOP_K_CONSUMERS", "9",  "3"],
    ["TOP_K_CONSUMERS", "10", "1"],
]
```

Step by step:

| # | Query | key-A bucket / total | key-B bucket / total | Output |
|---|-------|----------------------|----------------------|--------|
| 1 | `REGISTER_KEY key-A 1000` | 1000 / 0 | — | `"true"` |
| 2 | `REGISTER_KEY key-B 2000` | 1000 / 0 | 2000 / 0 | `"true"` |
| 3 | `CONSUME key-A 400` | 600 / 400 | 2000 / 0 | `"600"` |
| 4 | `CONSUME key-B 900` | 600 / 400 | 1100 / 900 | `"1100"` |
| 5 | `CONSUME key-A 300` | 300 / 700 | 1100 / 900 | `"300"` |
| 6 | `CONSUME key-A 5000` (denied — only 300 left) | 300 / 700 | 1100 / 900 | `""` |
| 7 | `TOTAL_CONSUMED key-A` | unchanged | unchanged | `"700"` |
| 8 | `TOTAL_CONSUMED ghost` | unchanged | unchanged | `""` |
| 9 | `TOP_K_CONSUMERS 3` (only 2 keys) | unchanged | unchanged | `"key-B(900), key-A(700)"` |
| 10 | `TOP_K_CONSUMERS 1` | unchanged | unchanged | `"key-B(900)"` |

Final return value:

```python
["true", "true", "600", "1100", "300", "", "700", "", "key-B(900), key-A(700)", "key-B(900)"]
```

Key trace notes:
- Row 6: `CONSUME key-A 5000` is **denied** because `300 < 5000`. The total stays at 700 (denied calls do NOT add to total_consumed).
- Row 9: only 2 keys exist, so `TOP_K_CONSUMERS 3` returns both, not 3.
- Row 9: key-B leads (900 > 700).

## Constraints

- All Level 1 constraints still apply.
- `k` is a positive integer string (`>= 1`).
- Up to `10^5` queries total.

## Common gotchas

1. **Denied CONSUMEs do NOT count toward total_consumed** — only successful deductions increment the cumulative total.
2. **TOP_K_CONSUMERS includes keys with zero consumption** — every registered key is eligible, even if it has never successfully consumed.
3. **Tie-breaking is alphabetical ASC on key_id** — not by registration order or any other criterion. `"key-A"` beats `"key-B"` alphabetically.
4. **TOP_K_CONSUMERS with k > number of keys returns all keys** — do not return an error or pad with empty entries.
5. **Format is exact:** `"key-A(700), key-B(900)"` is wrong — amounts must be integers with no spaces inside the parens, and the leading key must be the highest consumer.

## When you're done

```
cd 07-llm-rate-limiter
python3 test_level2.py
```

All Level 2 tests must pass before Level 3 is revealed.
