# Level 2 — Hit Tracking and Popularity Reports

## What you're implementing

You extend `solution(queries)` with two new commands: `HIT_COUNT` and `TOP_K_HOT`. All Level 1 commands continue to work unchanged.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

## Mental model

Real LLM caches track which prompts are requested most often — this data drives decisions like "which entries should we keep in cache when we're under memory pressure?" and "which prompts should we pre-warm at startup?"

At Level 2, you add a hit counter per prompt that increments each time `CACHE_GET` returns a cache hit. You also expose a `TOP_K_HOT` query that returns the most-hit prompts currently in the cache, sorted by popularity.

The key design question: where do you store the hit count? It lives alongside the cached entry — deleting a prompt (via `CACHE_DELETE`) wipes its hit count too. A subsequent re-PUT starts fresh at 0.

## The 2 commands for Level 2

### 1. `["HIT_COUNT", <ts>, <prompt>]`

Return the number of times `CACHE_GET` has returned a hit for this `prompt`.

| Situation | Return |
|-----------|--------|
| `prompt` is in cache, has been hit at least once | hit count as string, e.g. `"3"` |
| `prompt` is in cache, never been hit | `"0"` |
| `prompt` is NOT in cache (missing or deleted) | `""` (empty string) |

- Only counts successful `CACHE_GET` hits — misses do not count.
- `CACHE_PUT` and `CACHE_DELETE` do not affect the hit count (except that DELETE wipes the entry and its count).

### 2. `["TOP_K_HOT", <ts>, <k>]`

Return the top `k` currently-cached prompts by hit count, descending.

| Situation | Return |
|-----------|--------|
| Cache has ≥ 1 entry | `"prompt1(N1), prompt2(N2), ..."` — see format below |
| Cache is empty | `""` (empty string) |

**Format:** comma-space separated, each entry is `prompt(hit_count)`. Example: `"What is 2+2?(5), Tell me a joke(2), Hello(0)"`.

**Sorting:**
- Primary: hit count **descending** (highest hit count first).
- Tiebreak: prompt string **alphabetical ascending** (standard lexicographic order).

**Coverage:**
- Includes prompts with 0 hits.
- Only includes **currently-cached** prompts (not deleted ones).
- If fewer than `k` entries exist, return all of them.

**Important:** `HIT_COUNT` and `TOP_K_HOT` are read-only — they do **not** increment the hit count.

## Worked example — trace through it

```python
queries = [
    ["CACHE_PUT",    "1", "A", "response-A"],
    ["CACHE_PUT",    "2", "B", "response-B"],
    ["CACHE_PUT",    "3", "C", "response-C"],
    ["CACHE_GET",    "4", "A"],
    ["CACHE_GET",    "5", "A"],
    ["CACHE_GET",    "6", "B"],
    ["CACHE_GET",    "7", "Z"],
    ["HIT_COUNT",    "8", "A"],
    ["HIT_COUNT",    "9", "B"],
    ["HIT_COUNT",   "10", "C"],
    ["HIT_COUNT",   "11", "Z"],
    ["TOP_K_HOT",   "12", "2"],
    ["CACHE_DELETE", "13", "A"],
    ["TOP_K_HOT",   "14", "5"],
    ["CACHE_PUT",   "15", "A", "new-response-A"],
    ["HIT_COUNT",   "16", "A"],
    ["TOP_K_HOT",   "17", "3"],
]
```

State at start: cache = `{}`, hits = `{}`

| # | Query | cache keys / hits after | Output |
|---|-------|-------------------------|--------|
| 1 | `CACHE_PUT A` | A:0, B:-, C:- | `""` |
| 2 | `CACHE_PUT B` | A:0, B:0, C:- | `""` |
| 3 | `CACHE_PUT C` | A:0, B:0, C:0 | `""` |
| 4 | `CACHE_GET A` (hit) | A:1, B:0, C:0 | `"response-A"` |
| 5 | `CACHE_GET A` (hit) | A:2, B:0, C:0 | `"response-A"` |
| 6 | `CACHE_GET B` (hit) | A:2, B:1, C:0 | `"response-B"` |
| 7 | `CACHE_GET Z` (miss) | unchanged | `""` |
| 8 | `HIT_COUNT A` | unchanged | `"2"` |
| 9 | `HIT_COUNT B` | unchanged | `"1"` |
| 10 | `HIT_COUNT C` | unchanged | `"0"` |
| 11 | `HIT_COUNT Z` (not in cache) | unchanged | `""` |
| 12 | `TOP_K_HOT 2` | unchanged | `"A(2), B(1)"` |
| 13 | `CACHE_DELETE A` | B:1, C:0 (A gone) | `"true"` |
| 14 | `TOP_K_HOT 5` (only 2 entries) | unchanged | `"B(1), C(0)"` |
| 15 | `CACHE_PUT A` (re-added) | B:1, C:0, A:0 (hit count reset) | `""` |
| 16 | `HIT_COUNT A` (in cache, 0 hits since re-put) | unchanged | `"0"` |
| 17 | `TOP_K_HOT 3` | unchanged | `"B(1), A(0), C(0)"` |

Final return value:

```python
["", "", "", "response-A", "response-A", "response-B", "", "2", "1", "0", "", "A(2), B(1)", "true", "B(1), C(0)", "", "0", "B(1), A(0), C(0)"]
```

Key trace notes:
- Row 7: `CACHE_GET Z` is a miss — Z is not in the cache, count does not increment.
- Row 11: `HIT_COUNT Z` — Z is not in cache, returns `""` not `"0"`.
- Row 13: Deleting A wipes its hit count of 2. It no longer appears in TOP_K_HOT.
- Row 15: Re-adding A resets its hit count to 0. Row 17 tie between A and C (both 0 hits) — A comes before C alphabetically, so A(0) before C(0). But B has 1 hit so B comes first.

## Constraints

- All Level 1 constraints still apply.
- `<k>` is a positive integer string.
- Up to `10^5` queries total.
- Prompt strings may be arbitrarily long. Treat them as opaque string keys.

## Common gotchas

1. **HIT_COUNT on a missing prompt returns `""`, not `"0"`** — `"0"` is only for prompts that are currently cached but haven't been hit yet. This distinction matters.
2. **TOP_K_HOT includes zero-hit prompts** — every cached entry appears, even those with 0 hits. Don't filter them out.
3. **Deleting and re-adding resets the hit count** — a `CACHE_DELETE` followed by `CACHE_PUT` of the same prompt starts the hit count at 0. Don't carry over the old count.
4. **TOP_K_HOT tie-break is alphabetical ASC on the prompt string** — if two prompts have equal hit counts, the lexicographically smaller one comes first.
5. **HIT_COUNT and TOP_K_HOT do not themselves count as hits** — they are read-only diagnostic commands.

## When you're done

```
cd 06-llm-prompt-cache
python3 test_level2.py
```

All Level 2 tests must pass before moving to Level 3.
