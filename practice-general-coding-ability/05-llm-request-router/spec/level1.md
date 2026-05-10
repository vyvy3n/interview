# Level 1 — GPU Registration & Basic Routing

## What you're implementing

You write **one Python function**:

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

- **Input:** a list of "queries". Each query is a list of strings — the first string is a command name (`"REGISTER_GPU"`, `"ROUTE_REQUEST"`, or `"COMPLETE_REQUEST"`); the rest are arguments.
- **Output:** a list of strings, **exactly one string per query**, in the same order. Each string is the result of running that query against your router state.

## Mental model

Imagine your function is a tiny LLM inference scheduler. An LLM inference service runs across a fleet of GPUs. Each GPU can handle only so many requests in parallel — that's its **capacity**. When a new request arrives, you must pick the GPU with the most headroom (fewest active requests relative to its cap) so the fleet stays balanced.

This is the simplest possible routing policy: **least-loaded wins**. No caching, no affinity, no failure handling — just capacity tracking. Nail the bookkeeping here and the later levels slot in cleanly.

Key invariants to maintain:
- A GPU is **available** when `active_requests < capacity`.
- When a request completes (`COMPLETE_REQUEST`), its slot is freed on whatever GPU was assigned.
- You need a `requests` dict mapping `request_id → gpu_id` so completions can be attributed correctly.

## The 3 commands for Level 1

### 1. `["REGISTER_GPU", <ts>, <gpu_id>, <capacity>]`

Register a new GPU with the given concurrent-request capacity.

| Situation | Return |
|-----------|--------|
| `gpu_id` is new | `"true"` |
| `gpu_id` already exists | `"false"` |

`capacity` is a positive integer string — the maximum number of requests that can run simultaneously on this GPU.

### 2. `["ROUTE_REQUEST", <ts>, <request_id>, <token_count>]`

Assign the request to the **least-loaded available GPU** (fewest active requests). `token_count` is informational at this level — store it but you don't need it for routing logic until later levels.

| Situation | Return |
|-----------|--------|
| At least one GPU has spare capacity | assigned `gpu_id` (string) |
| No GPU has spare capacity | `""` (empty string) |
| No GPUs registered at all | `""` (empty string) |

**Tie-breaking:** among GPUs with equal active request counts, pick the one whose `gpu_id` comes first alphabetically (ascending).

### 3. `["COMPLETE_REQUEST", <ts>, <request_id>]`

Mark a request as completed, freeing its slot on the GPU it was routed to.

| Situation | Return |
|-----------|--------|
| `request_id` is known (was successfully routed) | `"true"` |
| `request_id` is unknown | `"false"` |

## Worked example — trace through it

```python
queries = [
    ["REGISTER_GPU",     "1", "gpu-a", "2"],
    ["REGISTER_GPU",     "2", "gpu-b", "1"],
    ["REGISTER_GPU",     "3", "gpu-a", "3"],
    ["ROUTE_REQUEST",    "4", "req-1", "512"],
    ["ROUTE_REQUEST",    "5", "req-2", "256"],
    ["ROUTE_REQUEST",    "6", "req-3", "128"],
    ["ROUTE_REQUEST",    "7", "req-4", "64"],
    ["COMPLETE_REQUEST", "8", "req-1"],
    ["ROUTE_REQUEST",    "9", "req-5", "100"],
    ["COMPLETE_REQUEST", "10", "req-99"],
]
```

Internal state: `gpus` dict mapping `gpu_id → {capacity, active}`. `requests` dict mapping `request_id → gpu_id`.

| # | Query | GPU state after (`active/capacity`) | requests dict | Output |
|---|-------|--------------------------------------|---------------|--------|
| 1 | `REGISTER_GPU gpu-a 2` | `{gpu-a: 0/2}` | `{}` | `"true"` |
| 2 | `REGISTER_GPU gpu-b 1` | `{gpu-a: 0/2, gpu-b: 0/1}` | `{}` | `"true"` |
| 3 | `REGISTER_GPU gpu-a 3` (dup) | unchanged | `{}` | `"false"` |
| 4 | `ROUTE_REQUEST req-1 512` | gpu-a: 1/2, gpu-b: 0/1 | `{req-1: gpu-a}` | `"gpu-a"` |
| 5 | `ROUTE_REQUEST req-2 256` | gpu-a: 1/2, gpu-b: 1/1 | `{req-1: gpu-a, req-2: gpu-b}` | `"gpu-b"` |
| 6 | `ROUTE_REQUEST req-3 128` | gpu-a: 2/2, gpu-b: 1/1 | `{..., req-3: gpu-a}` | `"gpu-a"` |
| 7 | `ROUTE_REQUEST req-4 64` | unchanged | same | `""` |
| 8 | `COMPLETE_REQUEST req-1` | gpu-a: 1/2, gpu-b: 1/1 | `req-1` removed | `"true"` |
| 9 | `ROUTE_REQUEST req-5 100` | gpu-a: 2/2, gpu-b: 1/1 | `{..., req-5: gpu-a}` | `"gpu-a"` |
| 10 | `COMPLETE_REQUEST req-99` (unknown) | unchanged | unchanged | `"false"` |

Trace notes for rows 4-6:
- Row 4: both GPUs are at 0 active. Tie broken alphabetically: `gpu-a` < `gpu-b` → assign `gpu-a`.
- Row 5: `gpu-a` has 1 active, `gpu-b` has 0 active → `gpu-b` is less loaded → assign `gpu-b`.
- Row 6: `gpu-a` has 1 active (still < 2 cap), `gpu-b` is full (1/1) → only `gpu-a` available → assign `gpu-a`.
- Row 7: `gpu-a` is 2/2 (full), `gpu-b` is 1/1 (full) → no capacity → `""`.

Final return value:

```python
["true", "true", "false", "gpu-a", "gpu-b", "gpu-a", "", "true", "gpu-a", "false"]
```

## Constraints

- All `<ts>` values are positive integer **strings**, strictly increasing across queries.
- `<capacity>` is a positive integer string (`>= 1`).
- `<gpu_id>` and `<request_id>` are non-empty strings.
- Up to `10^5` queries total.
- Aim for `O(G)` per `ROUTE_REQUEST` where G = number of GPUs (linear scan over GPUs is fine here).

## Common gotchas

1. **Routing a request to a full fleet returns `""`** — check `active < capacity`, not `active <= capacity`.
2. **Tie-breaking is alphabetical ASC** — `"gpu-a"` beats `"gpu-b"` when both have the same active count. Sort by `(active, gpu_id)`.
3. **COMPLETE_REQUEST for an unknown request_id returns `"false"` not `""`** — both known and unknown are valid inputs, just different outputs.
4. **REGISTER_GPU is idempotent-reject** — a duplicate registration returns `"false"` and keeps the original capacity intact.
5. **token_count is a string** — store it but don't use it for routing at L1. You'll need it later; don't discard it.

## When you're done

```
cd 05-llm-request-router
python3 test_level1.py
```

All tests must pass before Level 2 is revealed.
