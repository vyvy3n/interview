# Level 6 — Cached batch resolution

## What you're building

```python
def resolve_all(
    domains: list[str],
    max_workers: int = 5,
    max_queries: int = 15,
) -> dict[str, str | None]:
    """Resolve every domain in `domains`, return {input_domain: ip_or_None}.

    The input domains are NOT necessarily normalized — keys in the result must
    match the inputs exactly (e.g. {'Anthropic.COM': '160.79.104.10'}).

    Cache the result of every send_query call so that no (name, server_ip) pair
    is queried twice across the entire resolve_all() invocation. The cache must
    be **scoped to this call** — each invocation of resolve_all() starts fresh
    (no module-level state).

    max_workers is unused until Level 7.
    """
```

## Why caching matters

Resolving `www.example.com`, `api.example.com`, and `cdn.example.com` all hit the same root server first (querying for different names), then the same `.com` TLD server (querying for different names), then the same `example.com.` authoritative server. Without caching, that's 9 server hits; with caching, it's still 9 (different (name, server) pairs each time). But resolving `www.example.com` and `www.example.com` (duplicate input) should only do the work once.

More importantly: a single CNAME chain or NS-fallback path inside one resolve might re-ask the same server about the same name multiple times if your code is naive — caching `(name, server)` makes that free.

## Implementation sketch

```python
def resolve_all(domains, max_workers=5, max_queries=15):
    cache = {}   # (normalized_name, server_ip) -> DNSResponse

    def cached_send_query(name, server_ip):
        key = (name, server_ip)
        if key not in cache:
            cache[key] = send_query(name, server_ip)
        return cache[key]

    # rebuild your resolve() to call cached_send_query instead of send_query
    # (or pass it in as a parameter). The cache lives only as long as this call.

    return {d: _resolve_with(d, cached_send_query, max_queries) for d in domains}
```

Refactor your Level 1–5 `resolve()` so the `send_query` call point is parameterized — that's the only structural change you need.

## Tests check

- Result dict keys exactly match the input list (preserves case + missing trailing dot).
- Duplicate inputs only do the network work once (assertable via the per-test `query_count()`).
- Overlapping recursive paths (multiple domains sharing a TLD) share cache hits.
- A single bad domain (returns `None`) does not poison cache for other resolves in the same batch.

## Don't worry about

- Concurrency — Level 7.

## Run

```bash
python3 test_level6.py
```
