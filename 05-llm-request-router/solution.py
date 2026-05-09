"""
LLM Request Router — KV-cache-aware GPU scheduling.

You implement ONE function: solution(queries).

  - Input: a list of queries, each query is a list of strings.
  - Output: a list of strings — exactly one string per query.

Read spec/level1.md for the full spec and a worked example.

The skeleton below has the loop set up for you. You fill in the branch
bodies for each level. Delete the NotImplementedError once you start.

Level 1: REGISTER_GPU, ROUTE_REQUEST, COMPLETE_REQUEST   — see spec/level1.md
Level 2: GPU_LOAD, TOP_BUSIEST                           — see spec/level2.md
Level 3: ROUTE_REQUEST_WITH_PREFIX, GET_CACHED_PREFIXES  — see spec/level3.md
Level 4: FAIL_GPU, RECOVER_GPU                           — see spec/level4.md
"""

from collections import OrderedDict


# ---------------------------------------------------------------------------
# Data structures — extend as you progress through levels
# ---------------------------------------------------------------------------

class GPU:
    """Represents a registered GPU and its current state."""

    def __init__(self, gpu_id: str, capacity: int):
        self.gpu_id = gpu_id
        self.capacity = capacity          # original capacity; restored on RECOVER
        self.active = 0                   # current in-flight request count
        # Level 3: per-GPU LRU prefix cache (max 5 entries).
        # Use an OrderedDict: key=prefix, value=None; MRU at the end (move_to_end).
        self.prefix_cache: OrderedDict = OrderedDict()

    def has_capacity(self) -> bool:
        return self.active < self.capacity

    def add_prefix(self, prefix: str) -> None:
        """Insert or refresh prefix in LRU cache; evict LRU if over limit."""
        if prefix in self.prefix_cache:
            self.prefix_cache.move_to_end(prefix)   # refresh → MRU
        else:
            self.prefix_cache[prefix] = None
            if len(self.prefix_cache) > 5:
                self.prefix_cache.popitem(last=False)  # evict LRU (front)

    def cached_prefixes_mru_first(self) -> list:
        """Return prefixes ordered most-recently-used first."""
        return list(reversed(self.prefix_cache.keys()))


class Request:
    """Tracks an in-flight request."""

    def __init__(self, request_id: str, gpu_id: str, token_count: int, prefix=None):
        self.request_id = request_id
        self.gpu_id = gpu_id
        self.token_count = token_count
        self.prefix = prefix   # None for plain ROUTE_REQUEST; str for WITH_PREFIX


# ---------------------------------------------------------------------------
# Routing helpers — implement once, reuse across levels
# ---------------------------------------------------------------------------

def _least_loaded_available(gpus: dict) -> "GPU | None":
    """
    Return the GPU with fewest active requests that still has spare capacity.
    Ties broken by gpu_id alphabetically ascending.
    Returns None if no GPU is available.
    """
    # TODO: implement — iterate gpus.values(), filter has_capacity(), sort by (active, gpu_id)
    raise NotImplementedError(
        "_least_loaded_available — implement me (used by ROUTE_REQUEST and as fallback in L3/L4)"
    )


def _route_with_prefix(gpus: dict, prefix: str) -> "GPU | None":
    """
    Return the best GPU for a request with the given prefix:
      1. Among GPUs whose cache contains `prefix` AND has_capacity(), pick least-loaded (ties alpha).
      2. Fallback: _least_loaded_available(gpus).
    Returns None if no GPU has capacity at all.
    """
    # TODO: implement — see spec/level3.md routing logic
    raise NotImplementedError(
        "_route_with_prefix — implement me (used by ROUTE_REQUEST_WITH_PREFIX and FAIL_GPU re-routing)"
    )


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------

def solution(queries: list[list[str]]) -> list[str]:
    # --- state ---
    gpus: dict[str, GPU] = {}        # gpu_id → GPU (active GPUs only)
    failed_gpus: dict[str, GPU] = {} # gpu_id → GPU (failed; only capacity preserved)
    requests: dict[str, Request] = {} # request_id → Request

    out = []

    for q in queries:
        op = q[0]

        # ------------------------------------------------------------------ #
        # Level 1
        # ------------------------------------------------------------------ #

        if op == "REGISTER_GPU":
            # q is ["REGISTER_GPU", <ts>, <gpu_id>, <capacity>]
            _, ts, gpu_id, capacity = q
            # TODO: register gpu_id with int(capacity).
            #       Return "true" if new, "false" if already exists.
            raise NotImplementedError("REGISTER_GPU — see spec/level1.md")

        elif op == "ROUTE_REQUEST":
            # q is ["ROUTE_REQUEST", <ts>, <request_id>, <token_count>]
            _, ts, request_id, token_count = q
            # TODO: assign request to least-loaded GPU with spare capacity.
            #       Store Request(request_id, gpu_id, int(token_count), prefix=None).
            #       Return gpu_id or "" if no capacity / no GPUs.
            raise NotImplementedError("ROUTE_REQUEST — see spec/level1.md")

        elif op == "COMPLETE_REQUEST":
            # q is ["COMPLETE_REQUEST", <ts>, <request_id>]
            _, ts, request_id = q
            # TODO: look up request_id in requests dict.
            #       Decrement active on the GPU it was on, remove from requests.
            #       Return "true" if found, "false" if unknown.
            raise NotImplementedError("COMPLETE_REQUEST — see spec/level1.md")

        # ------------------------------------------------------------------ #
        # Level 2
        # ------------------------------------------------------------------ #

        elif op == "GPU_LOAD":
            # q is ["GPU_LOAD", <ts>, <gpu_id>]
            _, ts, gpu_id = q
            # TODO: return "active/capacity" for gpu_id, or "" if not registered.
            raise NotImplementedError("GPU_LOAD — see spec/level2.md")

        elif op == "TOP_BUSIEST":
            # q is ["TOP_BUSIEST", <ts>, <k>]
            _, ts, k = q
            # TODO: sort active GPUs by (-active, gpu_id); take top int(k).
            #       Format each as "gpu_id(active/capacity)"; join with ", ".
            #       Return "" if no GPUs registered.
            raise NotImplementedError("TOP_BUSIEST — see spec/level2.md")

        # ------------------------------------------------------------------ #
        # Level 3
        # ------------------------------------------------------------------ #

        elif op == "ROUTE_REQUEST_WITH_PREFIX":
            # q is ["ROUTE_REQUEST_WITH_PREFIX", <ts>, <request_id>, <prefix>, <token_count>]
            _, ts, request_id, prefix, token_count = q
            # TODO: call _route_with_prefix(gpus, prefix) to pick best GPU.
            #       On success: increment GPU active, call gpu.add_prefix(prefix),
            #       store Request(request_id, gpu_id, int(token_count), prefix=prefix).
            #       Return gpu_id or "" if no GPU has capacity.
            raise NotImplementedError("ROUTE_REQUEST_WITH_PREFIX — see spec/level3.md")

        elif op == "GET_CACHED_PREFIXES":
            # q is ["GET_CACHED_PREFIXES", <ts>, <gpu_id>]
            _, ts, gpu_id = q
            # TODO: return gpu.cached_prefixes_mru_first() joined by ", ".
            #       Return "" if GPU missing or cache is empty.
            raise NotImplementedError("GET_CACHED_PREFIXES — see spec/level3.md")

        # ------------------------------------------------------------------ #
        # Level 4
        # ------------------------------------------------------------------ #

        elif op == "FAIL_GPU":
            # q is ["FAIL_GPU", <ts>, <gpu_id>]
            _, ts, gpu_id = q
            # TODO:
            #   1. Return "" if gpu_id not in gpus (unknown or already failed).
            #   2. Collect all Request objects whose gpu_id == gpu_id; sort by request_id alpha ASC.
            #   3. Remove the failed GPU from gpus, wipe its cache, move to failed_gpus.
            #   4. For each collected request (sorted):
            #      a. If request.prefix is not None: use _route_with_prefix on remaining gpus.
            #      b. If request.prefix is None: use _least_loaded_available on remaining gpus.
            #      c. On success: increment new GPU active, update cache if prefix exists,
            #         update request.gpu_id to new GPU id.
            #      d. On failure (None returned): remove request from requests dict (drop silently).
            #   5. Return count of successfully re-routed requests as a string.
            raise NotImplementedError("FAIL_GPU — see spec/level4.md")

        elif op == "RECOVER_GPU":
            # q is ["RECOVER_GPU", <ts>, <gpu_id>]
            _, ts, gpu_id = q
            # TODO: if gpu_id in failed_gpus: move back to gpus with active=0, empty cache.
            #       Return "true".
            #       Otherwise (active or never registered): return "false".
            raise NotImplementedError("RECOVER_GPU — see spec/level4.md")

        else:
            raise ValueError(f"Unknown op: {op}")

    return out
