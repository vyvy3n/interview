"""
LLM Prompt Cache.

You implement ONE function: solution(queries).

  - Input: a list of queries, each query is a list of strings.
  - Output: a list of strings — exactly one string per query.

Read spec/level1.md for the full spec and a worked example.

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
    cache: dict = {}

    # Use a list as a mutable container so nested helpers can update capacity.
    # cap[0] is None (unlimited) until SET_CAPACITY is called.
    cap = [None]  # cap[0]: int | None

    def is_expired(entry: dict, ts: int) -> bool:
        """Return True if this entry's TTL has elapsed at timestamp ts (half-open interval)."""
        return entry["expiry"] is not None and ts >= entry["expiry"]

    def live_prompts(ts: int) -> list:
        """Return list of prompt keys that are currently live (not expired)."""
        return [p for p, e in cache.items() if not is_expired(e, ts)]

    def evict_lru_if_needed(ts: int) -> int:
        """Evict LRU live entries until len(live) <= capacity. Returns count evicted."""
        if cap[0] is None:
            return 0
        live = live_prompts(ts)
        evicted = 0
        while len(live) > cap[0]:
            # LRU: oldest last_access first; tie-break alphabetical ASC on prompt
            victim = min(live, key=lambda p: (cache[p]["last_access"], p))
            del cache[victim]
            live.remove(victim)
            evicted += 1
        return evicted

    out: list[str] = []

    for q in queries:
        op = q[0]

        # ----------------------------- Level 1 -----------------------------

        if op == "CACHE_PUT":
            # ["CACHE_PUT", <ts>, <prompt>, <response>]
            ts = int(q[1])
            prompt = q[2]
            response = q[3]

            # If the prompt is already live we're overwriting; live count stays same.
            already_live = prompt in cache and not is_expired(cache[prompt], ts)

            cache[prompt] = {
                "response": response,
                "hits": 0,
                "last_access": ts,
                "expiry": None,  # plain PUT clears any TTL
            }

            # Only evict if we added a genuinely new live entry.
            if not already_live:
                evict_lru_if_needed(ts)

            out.append("")

        elif op == "CACHE_GET":
            # ["CACHE_GET", <ts>, <prompt>]
            ts = int(q[1])
            prompt = q[2]

            entry = cache.get(prompt)
            if entry is not None and not is_expired(entry, ts):
                entry["hits"] += 1
                entry["last_access"] = ts
                out.append(entry["response"])
            else:
                out.append("")

        elif op == "CACHE_DELETE":
            # ["CACHE_DELETE", <ts>, <prompt>]
            ts = int(q[1])
            prompt = q[2]

            entry = cache.get(prompt)
            if entry is not None and not is_expired(entry, ts):
                del cache[prompt]
                out.append("true")
            else:
                out.append("false")

        # ----------------------------- Level 2 -----------------------------

        elif op == "HIT_COUNT":
            # ["HIT_COUNT", <ts>, <prompt>]
            ts = int(q[1])
            prompt = q[2]

            entry = cache.get(prompt)
            if entry is not None and not is_expired(entry, ts):
                out.append(str(entry["hits"]))
            else:
                out.append("")

        elif op == "TOP_K_HOT":
            # ["TOP_K_HOT", <ts>, <k>]
            ts = int(q[1])
            k = int(q[2])

            live = [(p, e) for p, e in cache.items() if not is_expired(e, ts)]
            if not live:
                out.append("")
            else:
                # Sort: hits DESC, then prompt ASC for ties
                live.sort(key=lambda pe: (-pe[1]["hits"], pe[0]))
                top = live[:k]
                out.append(", ".join(f"{p}({e['hits']})" for p, e in top))

        # ----------------------------- Level 3 -----------------------------

        elif op == "CACHE_PUT_WITH_TTL":
            # ["CACHE_PUT_WITH_TTL", <ts>, <prompt>, <response>, <ttl>]
            ts = int(q[1])
            prompt = q[2]
            response = q[3]
            ttl = int(q[4])

            already_live = prompt in cache and not is_expired(cache[prompt], ts)

            cache[prompt] = {
                "response": response,
                "hits": 0,
                "last_access": ts,
                "expiry": ts + ttl,
            }

            if not already_live:
                evict_lru_if_needed(ts)

            out.append("")

        elif op == "SET_CAPACITY":
            # ["SET_CAPACITY", <ts>, <max_entries>]
            ts = int(q[1])
            cap[0] = int(q[2])

            evicted = evict_lru_if_needed(ts)
            out.append(str(evicted))

        # ----------------------------- Level 4 -----------------------------

        elif op == "PREFIX_LOOKUP":
            # ["PREFIX_LOOKUP", <ts>, <new_prompt>]
            ts = int(q[1])
            new_prompt = q[2]

            best_prompt: str | None = None
            best_len = -1

            for p, e in cache.items():
                if is_expired(e, ts):
                    continue
                if new_prompt.startswith(p):
                    plen = len(p)
                    # Longest wins; tie-break alphabetical ASC
                    if plen > best_len or (plen == best_len and p < best_prompt):
                        best_len = plen
                        best_prompt = p

            if best_prompt is not None:
                cache[best_prompt]["hits"] += 1
                cache[best_prompt]["last_access"] = ts
                out.append(best_prompt)
            else:
                out.append("")

        elif op == "INVALIDATE_PREFIX":
            # ["INVALIDATE_PREFIX", <ts>, <prefix>]
            # Deletes ALL entries (live AND expired) whose prompt starts with prefix.
            prefix = q[2]
            to_delete = [p for p in cache if p.startswith(prefix)]
            for p in to_delete:
                del cache[p]
            out.append(str(len(to_delete)))

        else:
            raise ValueError(f"Unknown operation: {op}")

    return out
