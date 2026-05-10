# Level 7 — Bounded concurrency for batch resolution

## What you're building

Same `resolve_all(domains, max_workers=5, max_queries=15)` signature as Level 6, but now:

- **At most `max_workers` calls to `send_query` may be in flight at any given time** across the whole batch.
- The cache from Level 6 still applies — duplicate `(name, server)` queries should still dedupe and not count against the in-flight budget.

The user-facing return value is unchanged: `{input_domain: ip_or_None}`.

## Two reasonable designs

### Design A — `concurrent.futures.ThreadPoolExecutor`

```python
from concurrent.futures import ThreadPoolExecutor

def resolve_all(domains, max_workers=5, max_queries=15):
    cache = {}
    cache_lock = threading.Lock()
    semaphore = threading.Semaphore(max_workers)   # at-most-N in-flight calls

    def cached_send_query(name, server_ip):
        key = (name, server_ip)
        with cache_lock:
            if key in cache:
                return cache[key]
        with semaphore:
            response = send_query(name, server_ip)
        with cache_lock:
            cache[key] = response
        return response

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {d: pool.submit(_resolve_with, d, cached_send_query, max_queries) for d in domains}
        return {d: f.result() for d, f in futures.items()}
```

Note: the `ThreadPoolExecutor`'s `max_workers` and the `Semaphore` serve different purposes. The pool caps the *number of in-progress resolves*; the semaphore caps the *number of in-flight `send_query` calls*. Tests assert on the second one.

### Design B — `asyncio` with `asyncio.Semaphore`

If you've structured `resolve()` as `async def`, use `asyncio.Semaphore(max_workers)` around the `send_query` call (wrap the sync `send_query` with `asyncio.to_thread`). Then `await asyncio.gather(*[resolve(d) for d in domains])`.

Pick whichever you're more comfortable with — the spec only checks observable behavior.

## Tests check

- Concurrency cap respected: at no point are more than `max_workers` `send_query` calls in flight (asserted via the mock's observer hook).
- Duplicate inputs and overlapping recursive paths still dedupe via cache.
- Total wall-time scales sub-linearly with `len(domains)` for independent domains (smoke test).
- Errors (cycle, NXDOMAIN, all-NS-fail) inside one resolve don't block others.

## What "in-flight" means precisely

A `send_query` call is in-flight from the moment it begins until the moment it returns. The semaphore acquire happens *immediately before* the underlying `send_query`, and the release happens *immediately after*. Cache hits don't acquire the semaphore.

## Don't worry about

- Fairness, ordering of results within the dict, retry logic. Just cap the in-flight count and dedupe.

## Run

```bash
python3 test_level7.py
```
