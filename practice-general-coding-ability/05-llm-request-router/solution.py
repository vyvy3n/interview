"""
LLM Request Router — KV-cache-aware GPU scheduling.

You implement ONE function: solution(queries).

  - Input: a list of queries, each query is a list of strings.
  - Output: a list of strings — exactly one string per query.

Read spec/level1.md for the full spec and a worked example.

Level 1: REGISTER_GPU, ROUTE_REQUEST, COMPLETE_REQUEST   — see spec/level1.md
Level 2: GPU_LOAD, TOP_BUSIEST                           — see spec/level2.md
Level 3: ROUTE_REQUEST_WITH_PREFIX, GET_CACHED_PREFIXES  — see spec/level3.md
Level 4: FAIL_GPU, RECOVER_GPU                           — see spec/level4.md
"""

from collections import OrderedDict


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class GPU:
    """Represents a registered GPU and its current state."""

    def __init__(self, gpu_id: str, capacity: int):
        self.gpu_id = gpu_id
        self.capacity = capacity          # original capacity; restored on RECOVER
        self.active = 0                   # current in-flight request count
        # Per-GPU LRU prefix cache (max 5 entries).
        # OrderedDict: key=prefix, value=None; MRU at the END (move_to_end pushes to back).
        # popitem(last=False) evicts the front = LRU.
        self.prefix_cache: OrderedDict = OrderedDict()

    def has_capacity(self) -> bool:
        return self.active < self.capacity

    def add_prefix(self, prefix: str) -> None:
        """Insert or refresh prefix in LRU cache; evict LRU if over limit."""
        if prefix in self.prefix_cache:
            self.prefix_cache.move_to_end(prefix)   # refresh → MRU (back)
        else:
            self.prefix_cache[prefix] = None
            if len(self.prefix_cache) > 5:
                self.prefix_cache.popitem(last=False)  # evict LRU (front)

    def cached_prefixes_mru_first(self) -> list:
        """Return prefixes ordered most-recently-used first (back of OrderedDict is MRU)."""
        return list(reversed(self.prefix_cache.keys()))

    def reset(self) -> None:
        """Reset state for recovery: zero active, empty cache."""
        self.active = 0
        self.prefix_cache = OrderedDict()


class Request:
    """Tracks an in-flight request."""

    def __init__(self, request_id: str, gpu_id: str, token_count: int, prefix=None):
        self.request_id = request_id
        self.gpu_id = gpu_id
        self.token_count = token_count
        self.prefix = prefix   # None for plain ROUTE_REQUEST; str for WITH_PREFIX


# ---------------------------------------------------------------------------
# Routing helpers
# ---------------------------------------------------------------------------

def _least_loaded_available(gpus: dict) -> "GPU | None":
    """
    Return the GPU with fewest active requests that still has spare capacity.
    Ties broken by gpu_id alphabetically ascending.
    Returns None if no GPU is available.
    """
    candidates = [g for g in gpus.values() if g.has_capacity()]
    if not candidates:
        return None
    return min(candidates, key=lambda g: (g.active, g.gpu_id))


def _route_with_prefix(gpus: dict, prefix: str) -> "GPU | None":
    """
    Return the best GPU for a request with the given prefix:
      1. Among GPUs whose cache contains `prefix` AND has_capacity(), pick least-loaded (ties alpha).
      2. Fallback: _least_loaded_available(gpus).
    Returns None if no GPU has capacity at all.
    """
    # Step 1: prefix-hit candidates (have prefix cached AND have capacity)
    hit_candidates = [
        g for g in gpus.values()
        if prefix in g.prefix_cache and g.has_capacity()
    ]
    if hit_candidates:
        return min(hit_candidates, key=lambda g: (g.active, g.gpu_id))
    # Step 2: fallback to least-loaded
    return _least_loaded_available(gpus)


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------

def solution(queries: list[list[str]]) -> list[str]:
    # --- state ---
    gpus: dict[str, GPU] = {}         # gpu_id → GPU (active GPUs only)
    failed_gpus: dict[str, GPU] = {}  # gpu_id → GPU (failed; capacity preserved for recovery)
    requests: dict[str, Request] = {} # request_id → Request

    out = []

    for q in queries:
        op = q[0]

        # ------------------------------------------------------------------ #
        # Level 1
        # ------------------------------------------------------------------ #

        if op == "REGISTER_GPU":
            # ["REGISTER_GPU", <ts>, <gpu_id>, <capacity>]
            _, ts, gpu_id, capacity = q
            if gpu_id in gpus or gpu_id in failed_gpus:
                out.append("false")
            else:
                gpus[gpu_id] = GPU(gpu_id, int(capacity))
                out.append("true")

        elif op == "ROUTE_REQUEST":
            # ["ROUTE_REQUEST", <ts>, <request_id>, <token_count>]
            _, ts, request_id, token_count = q
            gpu = _least_loaded_available(gpus)
            if gpu is None:
                out.append("")
            else:
                gpu.active += 1
                requests[request_id] = Request(request_id, gpu.gpu_id, int(token_count), prefix=None)
                out.append(gpu.gpu_id)

        elif op == "COMPLETE_REQUEST":
            # ["COMPLETE_REQUEST", <ts>, <request_id>]
            _, ts, request_id = q
            if request_id not in requests:
                out.append("false")
            else:
                req = requests.pop(request_id)
                # Decrement active on the GPU (may have been re-routed; use current gpu_id)
                if req.gpu_id in gpus:
                    gpus[req.gpu_id].active -= 1
                out.append("true")

        # ------------------------------------------------------------------ #
        # Level 2
        # ------------------------------------------------------------------ #

        elif op == "GPU_LOAD":
            # ["GPU_LOAD", <ts>, <gpu_id>]
            _, ts, gpu_id = q
            if gpu_id not in gpus:
                out.append("")
            else:
                g = gpus[gpu_id]
                out.append(f"{g.active}/{g.capacity}")

        elif op == "TOP_BUSIEST":
            # ["TOP_BUSIEST", <ts>, <k>]
            _, ts, k = q
            if not gpus:
                out.append("")
            else:
                k = int(k)
                # Sort descending by active, then ascending by gpu_id for ties
                ranked = sorted(gpus.values(), key=lambda g: (-g.active, g.gpu_id))
                top = ranked[:k]
                out.append(", ".join(f"{g.gpu_id}({g.active}/{g.capacity})" for g in top))

        # ------------------------------------------------------------------ #
        # Level 3
        # ------------------------------------------------------------------ #

        elif op == "ROUTE_REQUEST_WITH_PREFIX":
            # ["ROUTE_REQUEST_WITH_PREFIX", <ts>, <request_id>, <prefix>, <token_count>]
            _, ts, request_id, prefix, token_count = q
            gpu = _route_with_prefix(gpus, prefix)
            if gpu is None:
                out.append("")
            else:
                gpu.active += 1
                gpu.add_prefix(prefix)
                requests[request_id] = Request(request_id, gpu.gpu_id, int(token_count), prefix=prefix)
                out.append(gpu.gpu_id)

        elif op == "GET_CACHED_PREFIXES":
            # ["GET_CACHED_PREFIXES", <ts>, <gpu_id>]
            _, ts, gpu_id = q
            if gpu_id not in gpus:
                out.append("")
            else:
                prefixes = gpus[gpu_id].cached_prefixes_mru_first()
                out.append(", ".join(prefixes) if prefixes else "")

        # ------------------------------------------------------------------ #
        # Level 4
        # ------------------------------------------------------------------ #

        elif op == "FAIL_GPU":
            # ["FAIL_GPU", <ts>, <gpu_id>]
            _, ts, gpu_id = q
            if gpu_id not in gpus:
                # Unknown or already failed
                out.append("")
                continue

            failing_gpu = gpus.pop(gpu_id)

            # Collect all in-flight requests on this GPU, sorted alphabetically
            inflight = sorted(
                [req for req in requests.values() if req.gpu_id == gpu_id],
                key=lambda r: r.request_id
            )

            # Reset the GPU and move to failed state
            failing_gpu.reset()
            failed_gpus[gpu_id] = failing_gpu

            # Re-route each request (gpus dict no longer has the failed GPU)
            success_count = 0
            for req in inflight:
                if req.prefix is not None:
                    new_gpu = _route_with_prefix(gpus, req.prefix)
                else:
                    new_gpu = _least_loaded_available(gpus)

                if new_gpu is None:
                    # No capacity — drop the request
                    del requests[req.request_id]
                else:
                    new_gpu.active += 1
                    if req.prefix is not None:
                        new_gpu.add_prefix(req.prefix)
                    req.gpu_id = new_gpu.gpu_id
                    success_count += 1

            out.append(str(success_count))

        elif op == "RECOVER_GPU":
            # ["RECOVER_GPU", <ts>, <gpu_id>]
            _, ts, gpu_id = q
            if gpu_id in failed_gpus:
                gpu = failed_gpus.pop(gpu_id)
                gpu.reset()  # active=0, empty cache, capacity unchanged
                gpus[gpu_id] = gpu
                out.append("true")
            else:
                # Active GPU or never registered → false
                out.append("false")

        else:
            raise ValueError(f"Unknown op: {op}")

    return out
