# Level 4 — GPU Failure & Request Rebalancing

## What you're implementing

You extend the same `solution(queries)` function from Levels 1-3 with two new commands:
`FAIL_GPU` and `RECOVER_GPU`. All previous commands continue to work unchanged.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

## Mental model

Real GPU clusters fail. A GPU can crash mid-inference, leaving in-flight requests dangling. A production router must detect failure, evict the lost requests from the failed GPU, and attempt to re-route them to remaining healthy GPUs — ideally preserving prefix affinity so re-routed requests can still benefit from cached KV tensors on the new GPU.

This is the hardest part of the problem. Two tensions to manage:

1. **Re-routing order matters** — requests are re-routed in `request_id` alphabetical order. Earlier requests in sort order claim capacity first; later ones might get dropped if the fleet fills up.
2. **Re-routing uses prefix-aware logic** — use the same priority as `ROUTE_REQUEST_WITH_PREFIX`: prefer GPUs with the prefix cached, fall back to least-loaded. A re-routed request updates the new GPU's cache exactly like a fresh `ROUTE_REQUEST_WITH_PREFIX` would.

After a GPU fails, it enters a **failed** state (distinct from registered). A failed GPU cannot receive new requests. It can be recovered with `RECOVER_GPU`, which brings it back online with empty cache and its original capacity.

## The 2 commands for Level 4

### 1. `["FAIL_GPU", <ts>, <gpu_id>]`

Fail a currently-active GPU.

**Procedure:**
1. If `gpu_id` doesn't exist (never registered, or already failed), return `""`.
2. Collect all in-flight requests on this GPU. Sort them by `request_id` alphabetically ascending.
3. For each request in that sorted order: attempt to re-route it to another available GPU using prefix-aware logic (same as `ROUTE_REQUEST_WITH_PREFIX` — prefer GPU with the prefix cached and spare capacity; fallback to least-loaded with spare capacity).
   - The re-routing prefix is the prefix that was originally used when the request was first routed (stored in your request dict from Level 3). Requests originally routed without a prefix (via plain `ROUTE_REQUEST`) have no prefix — treat them as prefix-less and use the plain fallback (least-loaded with spare capacity).
   - On successful re-route: update the new GPU's active count and cache (if the request had a prefix).
   - On failed re-route (no capacity anywhere): drop the request silently (remove from the requests dict entirely).
4. The failed GPU's active count drops to 0, cache is wiped, and it enters **failed** state. Remove it from the pool of routable GPUs.
5. Return the count of successfully re-routed requests as a string (e.g. `"3"`).

| Situation | Return |
|-----------|--------|
| GPU exists and is active | count of successfully re-routed requests (string) |
| GPU doesn't exist or is already failed | `""` |

### 2. `["RECOVER_GPU", <ts>, <gpu_id>]`

Bring a previously-failed GPU back online.

| Situation | Return |
|-----------|--------|
| `gpu_id` is in the failed state | `"true"` — GPU re-enters active pool with empty cache and original capacity |
| `gpu_id` is currently active (not failed) | `"false"` |
| `gpu_id` was never registered | `"false"` |

A recovered GPU starts with `active = 0`, `cache = []`, and the same `capacity` it had when originally registered. It is immediately eligible to receive new requests.

## Worked example — trace through it

```python
queries = [
    ["REGISTER_GPU",              "1",  "gpu-a", "2"],
    ["REGISTER_GPU",              "2",  "gpu-b", "2"],
    ["REGISTER_GPU",              "3",  "gpu-c", "1"],
    ["ROUTE_REQUEST_WITH_PREFIX", "4",  "req-a", "pfx:chat", "100"],
    ["ROUTE_REQUEST_WITH_PREFIX", "5",  "req-b", "pfx:chat", "100"],
    ["ROUTE_REQUEST_WITH_PREFIX", "6",  "req-c", "pfx:chat", "100"],
    ["ROUTE_REQUEST_WITH_PREFIX", "7",  "req-d", "pfx:chat", "100"],
    ["FAIL_GPU",                  "8",  "gpu-a"],
    ["RECOVER_GPU",               "9",  "gpu-a"],
    ["RECOVER_GPU",               "10", "gpu-a"],
    ["GPU_LOAD",                  "11", "gpu-a"],
]
```

State after rows 1-3: `gpu-a: 0/2 []`, `gpu-b: 0/2 []`, `gpu-c: 0/1 []`.

| # | Query | Routing result / state | Output |
|---|-------|------------------------|--------|
| 1-3 | `REGISTER_GPU` x3 | as above | `"true","true","true"` |
| 4 | `ROUTE_REQUEST_WITH_PREFIX req-a pfx:chat` | No prefix hit. Fallback: all at 0. gpu-a (alpha). gpu-a: 1/2 [pfx:chat] | `"gpu-a"` |
| 5 | `ROUTE_REQUEST_WITH_PREFIX req-b pfx:chat` | gpu-a has prefix (1 active, cap 2, room). Assign gpu-a. gpu-a: 2/2 [pfx:chat] | `"gpu-a"` |
| 6 | `ROUTE_REQUEST_WITH_PREFIX req-c pfx:chat` | gpu-a has prefix but FULL (2/2). gpu-b and gpu-c don't have prefix. Fallback: gpu-b at 0, gpu-c at 0. gpu-b (alpha). gpu-b: 1/2 [pfx:chat] | `"gpu-b"` |
| 7 | `ROUTE_REQUEST_WITH_PREFIX req-d pfx:chat` | gpu-a full, gpu-b has prefix (1 active, cap 2, room). Assign gpu-b. gpu-b: 2/2 [pfx:chat] | `"gpu-b"` |
| 8 | `FAIL_GPU gpu-a` | gpu-a had req-a, req-b. Sort: [req-a, req-b]. Re-route req-a: gpu-a failed, gpu-b full (2/2), gpu-c at 0/1 → assign gpu-c (fallback, gpu-b has prefix but full; gpu-c doesn't have prefix but has capacity). gpu-c: 1/1 [pfx:chat]. Re-route req-b: gpu-b full, gpu-c now full (1/1) → no capacity → drop req-b. Success count: 1. gpu-a enters failed state. | `"1"` |
| 9 | `RECOVER_GPU gpu-a` | gpu-a was failed → recover. gpu-a: 0/2 [] (active pool) | `"true"` |
| 10 | `RECOVER_GPU gpu-a` | gpu-a is now active (not failed) → return false | `"false"` |
| 11 | `GPU_LOAD gpu-a` | gpu-a: 0/2 | `"0/2"` |

Final return value:

```python
["true", "true", "true", "gpu-a", "gpu-a", "gpu-b", "gpu-b", "1", "true", "false", "0/2"]
```

## Constraints

- All Level 1-3 constraints still apply.
- A GPU can fail and recover multiple times (each recovery resets to original capacity with empty cache).
- Re-routing is attempted for ALL in-flight requests on the failed GPU, in `request_id` alpha ASC order.
- Re-routed requests that had no prefix (originally via `ROUTE_REQUEST`) use plain fallback logic only.
- At most `10^4` GPUs and `10^5` requests total.

## Common gotchas

1. **Re-routing order determines who gets capacity** — requests sorted alphabetically claim slots first. A later request might get dropped even if an earlier one succeeds. Don't process in arbitrary order.
2. **Re-routing re-uses prefix from original route** — if `req-x` was originally routed with prefix `"pfx:A"`, its re-route attempt also uses `"pfx:A"`. This may now land on a different GPU and update that GPU's cache.
3. **Failed GPU is not "missing"** — `FAIL_GPU` on an already-failed gpu returns `""`. `RECOVER_GPU` on an active gpu also returns `"false"`. These are distinct states: `{active, failed, never_registered}`.
4. **RECOVER resets cache to empty** — do NOT carry over the cache from before the failure. The GPU comes back clean.
5. **Requests originally routed via plain ROUTE_REQUEST have no prefix** — they stored `prefix=None` (or similar sentinel). Re-routing them uses plain least-loaded fallback; they do not update any cache on the new GPU.

## When you're done

```
cd 05-llm-request-router
python3 test_level4.py
```

All Level 4 tests must pass. Congratulations — you've built a KV-cache-aware LLM request router with failure recovery.
