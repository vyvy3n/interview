# Level 4 — Per-Prompt Response Caching

## What you're implementing

Add a shared prompt-response cache. When the gateway receives a prompt it has seen before, it returns the cached response immediately — skipping token deduction entirely. This mirrors how Anthropic's API uses prompt caching to reduce cost and latency.

```python
def handle_cached_request(self, user_id: str, prompt: str, response: str, tokens_used: int, now: int) -> str: ...
def get_cache_size(self) -> int: ...
def get_cache_hits(self, user_id: str) -> int: ...
def invalidate_cache(self, prefix: str) -> int: ...
def get_cache_hit_rate(self) -> str: ...
```

**All Level 1–3 methods still work unchanged.**

## Mental model

The cache maps `prompt -> response`. It is **global** — any user's cached prompt can be served to any other user. This is fine for this problem (pretend all users query the same LLM with deterministic responses).

When a request comes in:
1. Look up the prompt in cache.
2. **Cache hit:** return the cached response (no token deduction, user's `cache_hits` counter incremented).
3. **Cache miss:** run normal rate-limit check. If accepted, store the response in cache, return `"ok"`. If rate-limited, return `"rate_limited"` (do NOT write to cache).

## The 5 methods

### 1. `handle_cached_request(user_id, prompt, response, tokens_used, now) -> str`

The main cached-request entry point. Combines caching with rate limiting.

| Situation | Return |
|-----------|--------|
| `user_id` missing | `""` |
| Cache hit (any user cached this prompt) | cached response string (NOT `"ok"`) |
| Cache miss + accepted (tokens available) | `"ok"` (and response stored in cache) |
| Cache miss + rate_limited | `"rate_limited"` |

**Important:** Every call to this method is counted in the global attempt counter used by `get_cache_hit_rate`, regardless of outcome.

### 2. `get_cache_size() -> int`

Return the total number of distinct prompts currently in cache.

### 3. `get_cache_hits(user_id: str) -> int`

Return the number of cache hits attributed to this user. Returns `-1` if user missing.

A "hit" is when a call to `handle_cached_request` finds the prompt in cache.

### 4. `invalidate_cache(prefix: str) -> int`

Delete all cached entries whose prompt starts with `prefix`. Returns the count of deleted entries.

- If `prefix = ""`, all entries are deleted.
- Order of deletion doesn't matter.

### 5. `get_cache_hit_rate() -> str`

Return the global cache hit rate as the string `"X/Y"` where:
- `X` = total cache hits across all calls to `handle_cached_request`
- `Y` = total calls to `handle_cached_request` (regardless of hit/miss/user-missing)

Return `"0/0"` if no calls have been made yet.

## Worked example

```python
gw = LLMGateway()
gw.set_tier_limits("free", 1000, 100)
gw.register_user("alice", "free")
gw.register_user("bob",   "free")

# alice sends a prompt — cache miss, token deduction
gw.handle_cached_request("alice", "What is AI?", "AI is...", 50, now=0)
# → "ok"  (cache now has "What is AI?" -> "AI is...")

# bob sends the SAME prompt — cache hit, no tokens deducted
gw.handle_cached_request("bob", "What is AI?", "different", 999, now=0)
# → "AI is..."  (cached response, tokens NOT deducted)

gw.get_cache_hits("alice")   # 0
gw.get_cache_hits("bob")     # 1
gw.get_cache_size()          # 1
gw.get_cache_hit_rate()      # "1/2"

# invalidate anything starting with "What"
gw.invalidate_cache("What")  # 1 (deleted "What is AI?")
gw.get_cache_size()          # 0

# cache miss again, but alice is rate-limited (only has ~1000 tokens)
gw.handle_cached_request("alice", "What is AI?", "AI is...", 2000, now=0)
# → "rate_limited"  (not written to cache)
gw.get_cache_size()          # 0

gw.get_cache_hit_rate()      # "1/3"
```

## Constraints

- The cache is global — it persists until invalidated.
- Cache hit check is based on exact prompt string match (no normalization).
- `invalidate_cache("")` deletes the entire cache.
- A user-missing call (returns `""`) **does** count toward the attempt counter.

## Common gotchas

1. **Cache hit returns the cached response string, NOT `"ok"`** — this is intentional. The caller can distinguish "freshly computed" from "served from cache" by checking if the return value is `"ok"`.
2. **Cache miss + rate_limited does NOT write to cache** — only accepted requests populate the cache.
3. **Cache is shared — any user's miss populates for all** — if alice caches a response, bob gets it for free.
4. **`handle_cached_request` calls count toward the hit rate even if the user is missing** — track attempts before the user check, or restructure to count unconditionally.
5. **`invalidate_cache("")` deletes ALL entries** — the empty string is a prefix of every string.

## When you're done

```
python3 test_level4.py
```

All tests must pass before moving to Level 5.
