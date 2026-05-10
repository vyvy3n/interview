# Level 2 — Load Reporting

## What you're implementing

You extend the same `solution(queries)` function from Level 1 with two new commands:
`GPU_LOAD` and `TOP_BUSIEST`. All Level 1 commands continue to work unchanged.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

The function signature does not change. You're adding two new `elif` branches inside the same loop.

## Mental model

Level 2 adds **fleet observability**. In a real LLM serving system, operations teams need to see where load is concentrating — which GPUs are saturated, which are idle, and which are the hot spots right now.

`GPU_LOAD` is a per-GPU point-in-time probe. `TOP_BUSIEST` is a fleet-wide snapshot ranking, ordered by how many requests each GPU is currently handling.

The key insight: you already track `active_requests` per GPU for routing. These two commands just expose that state in different shapes. No new bookkeeping is needed — it's a view problem, not a state problem.

## The 2 commands for Level 2

### 1. `["GPU_LOAD", <ts>, <gpu_id>]`

Return the current load of a specific GPU as a fraction string.

| Situation | Return |
|-----------|--------|
| `gpu_id` exists | `"active/capacity"` e.g. `"2/4"` |
| `gpu_id` not registered | `""` (empty string) |

The numbers are the raw integers — no rounding, no percentages.

### 2. `["TOP_BUSIEST", <ts>, <k>]`

Return the top-K GPUs ranked by current active request count, descending. `k` is a positive integer string.

| Situation | Return |
|-----------|--------|
| GPUs are registered | formatted string of up to k GPUs |
| No GPUs registered | `""` (empty string) |

**Tie-breaking:** GPUs with equal active counts are sorted by `gpu_id` alphabetically ascending.

**Output format:** `"gpu-a(3/4), gpu-b(2/4), gpu-c(0/4)"`
- Each entry is `gpu_id(active/capacity)`.
- Entries separated by `", "` (comma followed by a single space).
- If fewer than `k` GPUs exist, return all of them (never pad).
- Idle GPUs (active=0) are included in the ranking.

## Worked example — trace through it

```python
queries = [
    ["REGISTER_GPU",  "1", "gpu-a", "4"],
    ["REGISTER_GPU",  "2", "gpu-b", "4"],
    ["REGISTER_GPU",  "3", "gpu-c", "4"],
    ["ROUTE_REQUEST", "4", "req-1", "100"],
    ["ROUTE_REQUEST", "5", "req-2", "100"],
    ["ROUTE_REQUEST", "6", "req-3", "100"],
    ["ROUTE_REQUEST", "7", "req-4", "100"],
    ["GPU_LOAD",      "8", "gpu-a"],
    ["GPU_LOAD",      "9", "gpu-z"],
    ["TOP_BUSIEST",   "10", "2"],
    ["COMPLETE_REQUEST", "11", "req-1"],
    ["TOP_BUSIEST",   "12", "5"],
    ["TOP_BUSIEST",   "13", "1"],
]
```

Tracking: `gpus = {gpu_id: {active, capacity}}`.

| # | Query | GPU state (`active/cap`) | Output |
|---|-------|--------------------------|--------|
| 1 | `REGISTER_GPU gpu-a 4` | `gpu-a: 0/4` | `"true"` |
| 2 | `REGISTER_GPU gpu-b 4` | `gpu-a: 0/4, gpu-b: 0/4` | `"true"` |
| 3 | `REGISTER_GPU gpu-c 4` | `gpu-a: 0/4, gpu-b: 0/4, gpu-c: 0/4` | `"true"` |
| 4 | `ROUTE_REQUEST req-1` | gpu-a: 1/4 (tie→gpu-a first alpha) | `"gpu-a"` |
| 5 | `ROUTE_REQUEST req-2` | gpu-b: 1/4 (gpu-a at 1, gpu-b/gpu-c at 0→gpu-b) | `"gpu-b"` |
| 6 | `ROUTE_REQUEST req-3` | gpu-c: 1/4 | `"gpu-c"` |
| 7 | `ROUTE_REQUEST req-4` | gpu-a: 2/4 (all at 1, tie→gpu-a) | `"gpu-a"` |
| 8 | `GPU_LOAD gpu-a` | unchanged | `"2/4"` |
| 9 | `GPU_LOAD gpu-z` | unchanged | `""` |
| 10 | `TOP_BUSIEST 2` | gpu-a: 2/4, gpu-b: 1/4, gpu-c: 1/4 → top 2: gpu-a(2), then gpu-b(1) ties gpu-c(1) alpha→gpu-b | `"gpu-a(2/4), gpu-b(1/4)"` |
| 11 | `COMPLETE_REQUEST req-1` | gpu-a: 1/4 | `"true"` |
| 12 | `TOP_BUSIEST 5` | gpu-a: 1/4, gpu-b: 1/4, gpu-c: 1/4 — all tied at 1, alpha order → gpu-a, gpu-b, gpu-c; only 3 GPUs so return all 3 | `"gpu-a(1/4), gpu-b(1/4), gpu-c(1/4)"` |
| 13 | `TOP_BUSIEST 1` | same state → just top 1 | `"gpu-a(1/4)"` |

Final return value:

```python
["true", "true", "true", "gpu-a", "gpu-b", "gpu-c", "gpu-a", "2/4", "", "gpu-a(2/4), gpu-b(1/4)", "true", "gpu-a(1/4), gpu-b(1/4), gpu-c(1/4)", "gpu-a(1/4)"]
```

## Constraints

- All Level 1 constraints still apply.
- `<k>` is a positive integer string (`>= 1`).
- Up to `10^5` queries total.
- Aim for `O(G log G)` for `TOP_BUSIEST` where G = number of GPUs (sort on demand).

## Common gotchas

1. **TOP_BUSIEST includes idle GPUs** — a GPU with `active=0` still appears in the ranking. It just ends up near the bottom.
2. **k > number of GPUs** — return all GPUs, not an error. Never emit empty entries.
3. **The format includes capacity** — `gpu-a(2/4)` not `gpu-a(2)`. Don't forget the `/capacity` part.
4. **GPU_LOAD on unknown gpu_id returns `""`** — same as other "missing resource" responses in this problem.
5. **Ties in TOP_BUSIEST are broken alphabetically ASC** — sort by `(-active, gpu_id)` to get this for free.

## When you're done

```
cd 05-llm-request-router
python3 test_level2.py
```

All Level 2 tests must pass before moving to Level 3.
