# Level 6 — Step 6: Cached batch resolution

> Verbatim from the assessment, **partial** — the screenshot scrolled past before the full description was visible. The text below is everything that was on screen.

Implement `resolve_all()`. Given a list of domains, resolve each one and return a mapping from each input domain (note that inputs are not necessarily normalized) to its resolved IP (or `None` if it couldn't be resolved).

The key requirement: cache the result of every `send_query` call so that no `(name, server)` pair is queried twice across the…

*[screenshot cuts off here]*

The `resolve_all()` signature visible in `dns_exercise.py` was:

```python
def resolve_all(
    domains: list[str],
    max_workers: int = 5,
    max_queries: int = 15,
) -> dict[str, ServerIP | None]:
    """Resolve all domains, caching calls to send_query.

    The cache must be scoped to this call (not global) so
    that each invocation of resolve_all() starts fresh.

    Starting at Step 7, at most max_workers calls to send_query
    may be in flight at any time.
    """
    # TODO: STEP 6: YOUR CODE HERE
    return {}
```

```
./test.sh 6
```
