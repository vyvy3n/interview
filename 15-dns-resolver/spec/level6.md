# Level 6 — Step 6: Cached batch resolution

> Verbatim from the assessment.

Implement `resolve_all()`. Given a list of domains, resolve each one and return a mapping from each input domain (note that inputs are not necessarily normalized) to its resolved IP (or `None` if it couldn't be resolved).

The key requirement: cache the result of every `send_query` call so that no `(name, server)` pair is queried twice across the batch. Many domains share the same delegation path (e.g. they all query ROOT, then the `.com` TLD), so caching eliminates redundant work.

- `NXDOMAIN` and `REFUSED` responses should also be cached.
- `max_queries` is the limit per domain. A cache hit does not call `send_query`, but still counts against the limit for that domain.
- The cache must be scoped to each `resolve_all()` call — not persisted globally.

```
./test.sh 6
```
