# Level 5 — Cycle detection via max_queries

## The bug to defend against

Properly configured DNS shouldn't have cycles, but two real-world misconfigurations cause them:

1. **CNAME loops:** `A` aliases to `B`, `B` aliases back to `A`.
2. **Glue cycles:** zone A's NS is in zone B, and zone B's NS is in zone A — neither can be resolved without the other.

Without protection, your resolver will recurse forever (or until `send_query` raises `QueryLimitExceeded`).

## What to implement

Cap the **total number of `send_query` calls per top-level `resolve()` call** at `max_queries` (default `15`). Once you've made that many calls, give up and return `None`.

The cap must include calls made on behalf of recursive sub-resolutions (CNAME restarts, NS-name lookups). It's *one global counter for one top-level resolve*, not per recursive frame.

## Recommended structure

Pass the counter as a mutable container (or use a closure / instance attribute):

```python
def resolve(domain_name: str, max_queries: int = 15) -> str | None:
    state = {"queries": 0, "limit": max_queries}
    return _resolve_inner(normalize(domain_name), state)

def _resolve_inner(name, state):
    # every send_query is wrapped:
    def query(n, server):
        if state["queries"] >= state["limit"]:
            raise _GiveUp
        state["queries"] += 1
        return send_query(n, server)
    ...
```

Wrap the wrap-and-bail in a try/except for `_GiveUp` at the top level → return `None`.

## Tests check

- A 2-cycle CNAME (A → B → A) returns `None` instead of looping.
- A glue cycle (each zone's NS lives in the other zone) returns `None` instead of looping.
- A clean resolve uses < `max_queries` calls and returns the IP normally.
- Setting `max_queries=2` on a domain that needs 5 hops returns `None`.

## Don't worry about

- Batching multiple domains — Level 6.
- Concurrency — Level 7.

## Run

```bash
python3 test_level5.py
```
