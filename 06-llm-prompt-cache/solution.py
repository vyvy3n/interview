"""
LLM Prompt Cache.

You implement ONE function: solution(queries).

  - Input: a list of queries, each query is a list of strings.
  - Output: a list of strings — exactly one string per query.

Read spec/level1.md for the full spec and a worked example.

The skeleton below has the loop set up for you. You fill in the branch
bodies for each level. Delete the NotImplementedError once you start.

Level 1: CACHE_PUT, CACHE_GET, CACHE_DELETE       — see spec/level1.md
Level 2: HIT_COUNT, TOP_K_HOT                     — see spec/level2.md
Level 3: CACHE_PUT_WITH_TTL, SET_CAPACITY         — see spec/level3.md
Level 4: PREFIX_LOOKUP, INVALIDATE_PREFIX         — see spec/level4.md
"""


def solution(queries: list[list[str]]) -> list[str]:
    # --- Internal state ---
    # cache: prompt (str) -> {
    #   "response": str,
    #   "hits": int,
    #   "last_access": int,   # timestamp of last PUT or CACHE_GET hit
    #   "expiry": int | None, # None means never expires; otherwise expires at this ts (half-open)
    # }
    cache = {}
    capacity = None  # None = unlimited; set by SET_CAPACITY

    def is_expired(entry, ts):
        """Return True if this entry's TTL has elapsed at timestamp ts."""
        return entry["expiry"] is not None and ts >= entry["expiry"]

    def evict_lru_if_needed(ts):
        """Evict LRU live entries until len(live) <= capacity. Returns count evicted."""
        if capacity is None:
            return 0
        live = [p for p, e in cache.items() if not is_expired(e, ts)]
        evicted = 0
        while len(live) > capacity:
            # LRU: oldest last_access first; tie-break alphabetical ASC on prompt
            victim = min(live, key=lambda p: (cache[p]["last_access"], p))
            del cache[victim]
            live.remove(victim)
            evicted += 1
        return evicted

    out = []

    for q in queries:
        op = q[0]

        # --- Level 1 ---

        if op == "CACHE_PUT":
            # q is ["CACHE_PUT", <ts>, <prompt>, <response>]
            _, ts, prompt, response = q
            # TODO: Store response at prompt. Overwrite silently if already exists.
            #       A plain CACHE_PUT clears any existing TTL (entry becomes never-expiring).
            #       last_access = int(ts). Evict LRU if over capacity after insert.
            #       Always returns "".
            raise NotImplementedError("CACHE_PUT — see spec/level1.md")

        elif op == "CACHE_GET":
            # q is ["CACHE_GET", <ts>, <prompt>]
            _, ts, prompt = q
            # TODO: Return cached response if present and not expired.
            #       On hit: increment hits, update last_access = int(ts).
            #       On miss (absent or expired): return "".
            raise NotImplementedError("CACHE_GET — see spec/level1.md")

        elif op == "CACHE_DELETE":
            # q is ["CACHE_DELETE", <ts>, <prompt>]
            _, ts, prompt = q
            # TODO: Delete the entry if present and not expired.
            #       Return "true" if deleted, "false" if not in cache (or expired).
            raise NotImplementedError("CACHE_DELETE — see spec/level1.md")

        # --- Level 2 ---

        elif op == "HIT_COUNT":
            # q is ["HIT_COUNT", <ts>, <prompt>]
            _, ts, prompt = q
            # TODO: Return hits for prompt as a string if it's in cache and not expired.
            #       Return "" if not in cache or expired (even if hits exist internally).
            raise NotImplementedError("HIT_COUNT — see spec/level2.md")

        elif op == "TOP_K_HOT":
            # q is ["TOP_K_HOT", <ts>, <k>]
            _, ts, k = q
            # TODO: Return top int(k) live (non-expired) entries sorted by hits DESC,
            #       then prompt ASC for ties.
            #       Format: "promptA(N), promptB(N), ..."
            #       Return "" if no live entries exist.
            #       Include entries with 0 hits. Return all if fewer than k live entries.
            raise NotImplementedError("TOP_K_HOT — see spec/level2.md")

        # --- Level 3 ---

        elif op == "CACHE_PUT_WITH_TTL":
            # q is ["CACHE_PUT_WITH_TTL", <ts>, <prompt>, <response>, <ttl>]
            _, ts, prompt, response, ttl = q
            # TODO: Store response at prompt with expiry = int(ts) + int(ttl).
            #       Overwrite existing entries (with or without TTL) silently.
            #       last_access = int(ts). Evict LRU if over capacity after insert.
            #       Always returns "".
            raise NotImplementedError("CACHE_PUT_WITH_TTL — see spec/level3.md")

        elif op == "SET_CAPACITY":
            # q is ["SET_CAPACITY", <ts>, <max_entries>]
            _, ts, max_entries = q
            # TODO: Set capacity = int(max_entries).
            #       Immediately evict LRU live entries until live count <= capacity.
            #       Expired entries are invisible (don't count, don't evict).
            #       Return count of evicted entries as string.
            raise NotImplementedError("SET_CAPACITY — see spec/level3.md")

        # --- Level 4 ---

        elif op == "PREFIX_LOOKUP":
            # q is ["PREFIX_LOOKUP", <ts>, <new_prompt>]
            _, ts, new_prompt = q
            # TODO: Find the longest live (non-expired) cached prompt P such that
            #       new_prompt.startswith(P). Tie-break by prompt alphabetical ASC.
            #       On match: increment its hit count, update its last_access = int(ts).
            #       Return the matched prompt string, or "" if no match.
            raise NotImplementedError("PREFIX_LOOKUP — see spec/level4.md")

        elif op == "INVALIDATE_PREFIX":
            # q is ["INVALIDATE_PREFIX", <ts>, <prefix>]
            _, ts, prefix = q
            # TODO: Delete ALL entries (live AND expired) whose prompt starts with prefix.
            #       Return count of deleted entries as string (e.g. "0" if none matched).
            raise NotImplementedError("INVALIDATE_PREFIX — see spec/level4.md")

        else:
            raise ValueError(f"Unknown operation: {op}")

    return out
