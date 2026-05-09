# Level 3 — Prefix-Aware Routing with Per-GPU LRU Cache

## What you're implementing

You extend the same `solution(queries)` function from Levels 1-2 with two new commands:
`ROUTE_REQUEST_WITH_PREFIX` and `GET_CACHED_PREFIXES`. All previous commands continue to work unchanged.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

## Mental model

This is the core insight behind real LLM inference routers like vLLM's prefix-aware scheduler.

When an LLM processes a request, it must compute key-value tensors for every input token — this is called **prefill** and it's expensive. The GPU can cache those tensors (the KV cache). If a later request arrives whose input shares a prefix with a previously cached request, the GPU can skip recomputing those tensors, dramatically cutting latency and GPU compute.

The catch: **KV caches are per-GPU**. If you round-robin requests across the fleet, each GPU caches different prefixes and you get almost no reuse. The fix is **prefix-aware routing**: when a request arrives with a known prefix, prefer the GPU that already has that prefix cached. Only fall back to load-balancing when no such GPU exists or all prefix-hit GPUs are at capacity.

Each GPU maintains an **LRU cache** of recently seen prefixes (max 5 entries). When a prefix is used, it moves to the front (most-recently-used). When the cache is full and a new prefix arrives, the least-recently-used prefix is evicted.

**Data model change:** you now need to track which prefix each in-flight request was routed with (so Level 4 can re-route failed requests with their original prefix). Update your request bookkeeping accordingly.

## The 2 commands for Level 3

### 1. `["ROUTE_REQUEST_WITH_PREFIX", <ts>, <request_id>, <prefix>, <token_count>]`

Route the request with prefix-cache awareness.

**Step 1 — find prefix-hit GPUs:** Collect all GPUs whose LRU cache contains `prefix` AND whose `active < capacity`.

**Step 2 — pick best prefix-hit GPU:** From those, pick the one with the fewest active requests. Tie-break alphabetically by `gpu_id` ascending.

**Step 3 — fallback:** If no GPU satisfies Step 1 (no GPU has the prefix cached, or all that do are full), fall back to the standard least-loaded logic from Level 1 (any GPU with `active < capacity`, least-loaded, ties alpha).

**On success (either path):**
- Increment the chosen GPU's active count.
- Update the chosen GPU's LRU cache: if `prefix` is already in the cache, move it to most-recently-used position. If it's not in the cache, add it as most-recently-used; if the cache now has more than 5 entries, evict the least-recently-used entry.
- Record `request_id → (gpu_id, prefix)` in your requests dict (you need the prefix for L4 re-routing).

| Situation | Return |
|-----------|--------|
| Routed to a prefix-hit GPU | assigned `gpu_id` |
| Routed via fallback (no prefix hit or hit GPUs full) | assigned `gpu_id` |
| No GPU with spare capacity | `""` (empty string) |

### 2. `["GET_CACHED_PREFIXES", <ts>, <gpu_id>]`

Return the cached prefixes for a GPU, ordered most-recently-used first.

| Situation | Return |
|-----------|--------|
| GPU exists and has cached prefixes | `"prefix_a, prefix_b, prefix_c"` (comma+space separated, MRU first) |
| GPU exists but cache is empty | `""` (empty string) |
| GPU not registered | `""` (empty string) |

## Worked example — trace through it

```python
queries = [
    ["REGISTER_GPU",              "1",  "gpu-a", "3"],
    ["REGISTER_GPU",              "2",  "gpu-b", "3"],
    ["ROUTE_REQUEST_WITH_PREFIX", "3",  "req-1", "sys:assistant", "512"],
    ["ROUTE_REQUEST_WITH_PREFIX", "4",  "req-2", "sys:assistant", "256"],
    ["ROUTE_REQUEST_WITH_PREFIX", "5",  "req-3", "sys:user",      "128"],
    ["GET_CACHED_PREFIXES",       "6",  "gpu-a"],
    ["GET_CACHED_PREFIXES",       "7",  "gpu-b"],
    ["ROUTE_REQUEST_WITH_PREFIX", "8",  "req-4", "sys:assistant", "64"],
    ["GET_CACHED_PREFIXES",       "9",  "gpu-a"],
    ["COMPLETE_REQUEST",          "10", "req-2"],
    ["ROUTE_REQUEST_WITH_PREFIX", "11", "req-5", "sys:assistant", "64"],
    ["GET_CACHED_PREFIXES",       "12", "gpu-b"],
]
```

LRU cache shown as ordered list `[MRU, ..., LRU]`.

| # | Query | gpu-a (active/cap, cache) | gpu-b (active/cap, cache) | Output |
|---|-------|---------------------------|---------------------------|--------|
| 1 | `REGISTER_GPU gpu-a 3` | 0/3, [] | — | `"true"` |
| 2 | `REGISTER_GPU gpu-b 3` | 0/3, [] | 0/3, [] | `"true"` |
| 3 | `ROUTE_REQUEST_WITH_PREFIX req-1 sys:assistant` | No GPU has prefix. Fallback: both at 0, tie→gpu-a. Add prefix. gpu-a: 1/3, [sys:assistant] | 0/3, [] | `"gpu-a"` |
| 4 | `ROUTE_REQUEST_WITH_PREFIX req-2 sys:assistant` | gpu-a has prefix, gpu-b does not. Only gpu-a hits. gpu-a at 1 active (has cap). Assign gpu-a. MRU update (already there). gpu-a: 2/3, [sys:assistant] | 0/3, [] | `"gpu-a"` |
| 5 | `ROUTE_REQUEST_WITH_PREFIX req-3 sys:user` | No GPU has "sys:user". Fallback: gpu-a at 2, gpu-b at 0. gpu-b is least loaded. Assign gpu-b. Add prefix. gpu-a: 2/3, [sys:assistant] | 1/3, [sys:user] | `"gpu-b"` |
| 6 | `GET_CACHED_PREFIXES gpu-a` | unchanged | unchanged | `"sys:assistant"` |
| 7 | `GET_CACHED_PREFIXES gpu-b` | unchanged | unchanged | `"sys:user"` |
| 8 | `ROUTE_REQUEST_WITH_PREFIX req-4 sys:assistant` | gpu-a has prefix at 2 active (cap=3, has room). gpu-b doesn't have prefix. Assign gpu-a. MRU update. gpu-a: 3/3, [sys:assistant] | 1/3, [sys:user] | `"gpu-a"` |
| 9 | `GET_CACHED_PREFIXES gpu-a` | unchanged | unchanged | `"sys:assistant"` |
| 10 | `COMPLETE_REQUEST req-2` | req-2 was on gpu-a. gpu-a: 2/3 | 1/3, [sys:user] | `"true"` |
| 11 | `ROUTE_REQUEST_WITH_PREFIX req-5 sys:assistant` | gpu-a has prefix at 2 active. gpu-b doesn't. Assign gpu-a. gpu-a: 3/3, [sys:assistant] | 1/3, [sys:user] | `"gpu-a"` |
| 12 | `GET_CACHED_PREFIXES gpu-b` | unchanged | unchanged | `"sys:user"` |

Final return value:

```python
["true", "true", "gpu-a", "gpu-a", "gpu-b", "sys:assistant", "sys:user", "gpu-a", "sys:assistant", "true", "gpu-a", "sys:user"]
```

### LRU eviction example

If a GPU's cache contains `["p5", "p4", "p3", "p2", "p1"]` (MRU→LRU) and a new prefix `"p6"` arrives:
- Cache becomes `["p6", "p5", "p4", "p3", "p2"]` — `"p1"` (LRU) is evicted.

If prefix `"p3"` arrives on that same cache (it's already present):
- Cache becomes `["p3", "p6", "p5", "p4", "p2"]` — `"p3"` moves to MRU, everything else shifts.

## Constraints

- All Level 1-2 constraints still apply.
- Each GPU's prefix cache holds at most **5** entries (fixed, hardcoded).
- Prefix strings are non-empty, can contain any non-whitespace characters.
- Both `ROUTE_REQUEST` (Level 1) and `ROUTE_REQUEST_WITH_PREFIX` (Level 3) may appear in the same query list.
- `ROUTE_REQUEST` does not interact with the prefix cache — it neither reads nor writes it.

## Common gotchas

1. **Cache-hit GPUs must also have capacity** — if gpu-a has the prefix but is full, it doesn't qualify for the prefix-aware path. Fall through to the fallback.
2. **Fallback uses the same least-loaded logic as Level 1** — don't invent a new tie-breaking rule. Among all available GPUs (any prefix or not), pick least active, then alpha.
3. **LRU update happens even on a hit** — if a GPU already has the prefix, move it to MRU position (access refreshes the entry, not just insertion).
4. **GET_CACHED_PREFIXES returns MRU first** — the most recently used prefix is listed first, oldest last.
5. **Plain ROUTE_REQUEST does not touch the cache** — only `ROUTE_REQUEST_WITH_PREFIX` reads and writes the prefix cache. Mixing both in the same test is intentional.

## When you're done

```
cd 05-llm-request-router
python3 test_level3.py
```

All Level 3 tests must pass before moving to Level 4.
