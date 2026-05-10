# Level 3 — TTL Expiry and LRU Eviction

## What you're implementing

You extend `solution(queries)` with two new commands: `CACHE_PUT_WITH_TTL` and `SET_CAPACITY`. All Level 1 and Level 2 commands continue to work, but they must now respect TTL expiry.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

## Mental model

Production LLM caches have two constraints that this level adds: **time** and **space**.

**Time (TTL):** Some responses should only be cached for a limited window — e.g., a "current weather" answer is stale after 60 seconds. `CACHE_PUT_WITH_TTL` tags entries with an absolute expiry timestamp. Once that timestamp is reached, the entry behaves as if it were never in the cache.

**Space (LRU eviction):** The cache can't grow forever. `SET_CAPACITY` imposes a limit. When adding a new entry would exceed that limit, you evict the Least Recently Used entry — the one whose `last_access` timestamp is oldest. "Last access" is updated either when you PUT an entry (set to the PUT timestamp) or when a `CACHE_GET` returns a hit (set to the GET timestamp).

These two mechanisms work together: expired entries are invisible to all operations, and LRU eviction only considers live (non-expired) entries.

## The 2 commands for Level 3

### 1. `["CACHE_PUT_WITH_TTL", <ts>, <prompt>, <response>, <ttl>]`

Store `response` at `prompt` with an absolute expiry at `ts + int(ttl)`.

| Situation | Return |
|-----------|--------|
| Always | `""` (empty string, always) |

**Expiry semantics (half-open interval):** An entry stored at timestamp `ts` with TTL `ttl` is valid for the interval `[ts, ts + ttl)`. At exactly `ts + ttl`, it is **expired** and treated as absent.

- If `prompt` is already in the cache (with or without TTL), the new value and TTL replace it entirely.
- Overwriting a `CACHE_PUT_WITH_TTL` entry with a plain `CACHE_PUT` clears the TTL — the entry becomes never-expiring.
- Overwriting a plain `CACHE_PUT` entry with `CACHE_PUT_WITH_TTL` adds a TTL.
- The PUT timestamp (`ts`) is the initial `last_access` for LRU purposes.

### 2. `["SET_CAPACITY", <ts>, <max_entries>]`

Set the maximum number of entries the cache may hold simultaneously.

| Situation | Return |
|-----------|--------|
| Always | count of entries evicted as string, e.g. `"3"` or `"0"` |

**Eviction procedure:**
1. First, treat all expired entries as absent (they don't count toward capacity or eviction candidates).
2. If the count of live (non-expired) entries exceeds `max_entries`, evict the LRU entries — those with the oldest `last_access` timestamp — one by one until `size <= max_entries`.
3. Return the number of entries evicted.

**Eviction on new PUT:** When a `CACHE_PUT` or `CACHE_PUT_WITH_TTL` would bring the live entry count above capacity, evict the single LRU live entry before inserting the new one. (Repeat until there is room — but in practice, capacity ≥ 1 so one eviction suffices per PUT.)

**LRU last_access rules:**
- `CACHE_PUT` / `CACHE_PUT_WITH_TTL`: `last_access = ts` of the PUT.
- `CACHE_GET` hit: `last_access = ts` of the GET (updated to current time).
- `CACHE_GET` miss, `CACHE_DELETE`, `HIT_COUNT`, `TOP_K_HOT`: do NOT update `last_access`.

**TTL semantics apply to ALL existing operations:**
- `CACHE_GET` on an expired entry → `""` (miss; hit count NOT incremented).
- `CACHE_DELETE` on an expired entry → `"false"` (not in cache).
- `HIT_COUNT` on an expired entry → `""`.
- `TOP_K_HOT` excludes expired entries.

**Tie-breaking in LRU eviction:** if two entries have the same `last_access`, evict the one whose prompt is lexicographically smaller (alphabetical ASC).

## Worked example — trace through it

```python
queries = [
    ["CACHE_PUT_WITH_TTL", "1",  "A", "resp-A", "10"],
    ["CACHE_PUT_WITH_TTL", "2",  "B", "resp-B", "5"],
    ["CACHE_PUT",          "3",  "C", "resp-C"],
    ["SET_CAPACITY",       "4",  "2"],
    ["CACHE_GET",          "5",  "A"],
    ["CACHE_GET",          "7",  "B"],
    ["CACHE_GET",          "9",  "A"],
    ["CACHE_PUT",          "10", "D", "resp-D"],
    ["CACHE_GET",          "11", "A"],
    ["CACHE_GET",          "12", "C"],
]
```

Internal state tracks: `{prompt: (response, expiry, last_access, hit_count)}`

Initial state: `{}`, capacity = unlimited

| # | ts | Query | Live entries (prompt: expiry/last_access) | Evicted | Output |
|---|----|----|---|---|---|
| 1 | 1 | `CACHE_PUT_WITH_TTL A resp-A ttl=10` | A(exp=11,la=1) | — | `""` |
| 2 | 2 | `CACHE_PUT_WITH_TTL B resp-B ttl=5` | A(exp=11,la=1), B(exp=7,la=2) | — | `""` |
| 3 | 3 | `CACHE_PUT C resp-C` | A(la=1), B(la=2), C(la=3, no expiry) | — | `""` |
| 4 | 4 | `SET_CAPACITY 2` | All 3 are live at ts=4. Evict LRU (oldest la): A(la=1) evicted. Result: B(la=2), C(la=3) | A | `"1"` |
| 5 | 5 | `CACHE_GET A` | A is gone → miss | — | `""` |
| 6 | 7 | `CACHE_GET B` | B expires at ts=7 (half-open: ts=7 is expired). → miss | — | `""` |
| 7 | 9 | `CACHE_GET A` | A not in cache → miss | — | `""` |
| 8 | 10 | `CACHE_PUT D resp-D` | Live entries: C only (B expired). Adding D: size=1 < cap=2. No eviction. C(la=3), D(la=10) | — | `""` |
| 9 | 11 | `CACHE_GET A` | Not in cache → miss | — | `""` |
| 10 | 12 | `CACHE_GET C` (hit) | C(la=12), D(la=10). Hit count C→1 | — | `"resp-C"` |

Final return value:

```python
["", "", "", "1", "", "", "", "", "", "resp-C"]
```

Key trace notes:
- Row 4: All 3 entries are live at ts=4 (B expires at 2+5=7, which is > 4). Capacity is 2, so 1 must be evicted. A has the oldest last_access (la=1) → A is evicted. Returns `"1"`.
- Row 6: B was stored at ts=2 with TTL=5, so expiry = 2+5 = 7. At ts=7, `7 >= 7` means expired (half-open `[2,7)` — ts=7 is NOT in the valid window). CACHE_GET returns `""`.
- Row 8: At ts=10, B is already expired (exp=7 ≤ 10). Only C is live. Adding D brings size to 2, which equals capacity=2, so no eviction needed.

## Constraints

- All Level 1 and Level 2 constraints still apply.
- `<ttl>` is a positive integer string (`> 0`).
- `<max_entries>` is a positive integer string (`≥ 1`).
- Timestamps are strictly increasing across queries.
- Capacity is unlimited until the first `SET_CAPACITY` is issued.
- `SET_CAPACITY` may be called multiple times; the latest value takes effect.
- Up to `10^5` queries total.

## Common gotchas

1. **Half-open TTL interval — at exactly `ts + ttl` the entry is expired.** An entry with `ttl=5` stored at `ts=10` expires at `ts=15`. A `CACHE_GET` at `ts=15` returns `""`.
2. **`CACHE_GET` hit updates `last_access` — this affects future LRU eviction order.** If you access an entry just before a SET_CAPACITY call, it becomes harder to evict.
3. **Plain `CACHE_PUT` overwrites `CACHE_PUT_WITH_TTL` and clears the TTL** — the entry becomes permanent (never expires). Don't carry over the old TTL.
4. **Expired entries are invisible — they don't count toward capacity.** When checking if a new PUT exceeds capacity, count only live (non-expired) entries.
5. **LRU eviction tie-break: oldest `last_access` first; ties broken alphabetically by prompt ASC.** Don't use insertion order or any other ordering.

## When you're done

```
cd 06-llm-prompt-cache
python3 test_level3.py
```

All Level 3 tests must pass before moving to Level 4.
