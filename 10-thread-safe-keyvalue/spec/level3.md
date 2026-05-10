# Level 3 — TTL / Expiration

## What you're implementing

Add time-to-live (TTL) support. Instead of real wall-clock time, callers pass an explicit integer timestamp `now` so tests are deterministic. Add three new methods:

```python
def put_with_ttl(self, key: str, value: str, ttl: int, now: int) -> None: ...
def get_at(self, key: str, now: int) -> str: ...
def cleanup_expired(self, now: int) -> int: ...
```

All Level 1-2 methods still work.

## Mental model

Caches often need entries to expire automatically — session tokens, rate-limit counters, temporary flags. TTL = "time-to-live": an entry written at time `now` with `ttl=10` expires at `now + 10`.

Rather than importing `time.time()` (which makes tests non-deterministic), the caller provides `now` explicitly. This is a common design in interview problems — you control the clock.

## The 3 methods for Level 3

### A. `put_with_ttl(key: str, value: str, ttl: int, now: int) -> None`

Store `value` under `key` with an **expiry time** of `now + ttl`.

- If `key` already exists (with or without TTL), overwrite everything.
- A plain `put()` on a key that had a TTL clears the TTL (the entry becomes permanent).
- `ttl` is a positive integer (seconds, conceptually).

### B. `get_at(key: str, now: int) -> str`

Fetch the value for `key` as of time `now`, respecting TTL.

| Situation | Return |
|-----------|--------|
| Key exists, no TTL | value |
| Key exists, TTL not yet expired (`expiry > now`) | value |
| Key exists, TTL expired (`expiry <= now`) | `""` |
| Key missing | `""` |

**Important:** the plain `get()` from Level 1 does **not** check TTL. Only `get_at()` does. This is intentional — `get()` is the "raw" accessor; `get_at()` is the "cache-aware" accessor.

### C. `cleanup_expired(now: int) -> int`

Remove all entries whose TTL has expired at time `now` (i.e. `expiry <= now`). Entries without a TTL are never removed. Returns the count of entries removed.

## Worked example

```python
kv = KVStore()

kv.put_with_ttl("session", "tok123", ttl=10, now=100)
# entry: key="session", value="tok123", expiry=110

kv.get_at("session", now=105)   # "tok123"  (not yet expired)
kv.get_at("session", now=110)   # ""        (expired: 110 <= 110)
kv.get("session")               # "tok123"  (plain get ignores TTL!)

kv.put_with_ttl("a", "1", ttl=5, now=0)   # expiry=5
kv.put_with_ttl("b", "2", ttl=5, now=0)   # expiry=5
kv.put("c", "3")                            # no TTL
kv.count()                                  # 4

kv.cleanup_expired(now=5)       # 3 removed ("session" expiry=110 still alive? No:
                                 # at now=5: "session" expiry=110 > 5, so NOT removed.
                                 # "a" expiry=5 <= 5 → removed.
                                 # "b" expiry=5 <= 5 → removed.
                                 # Returns 2)
kv.count()                      # 2 ("session" + "c")
```

Corrected trace (cleaner example):

```python
kv = KVStore()
kv.put_with_ttl("x", "hello", ttl=10, now=0)   # expiry=10
kv.put_with_ttl("y", "world", ttl=20, now=0)   # expiry=20
kv.put("z", "perm")                              # no TTL

kv.get_at("x", now=9)    # "hello"
kv.get_at("x", now=10)   # ""        (expired)
kv.get("x")              # "hello"   (plain get ignores TTL)

kv.cleanup_expired(now=10)   # 1 removed ("x")
kv.count()                   # 2  ("y" + "z")
kv.cleanup_expired(now=10)   # 0  (nothing new to remove)
```

## Constraints

- `ttl` is always a positive integer.
- `now` is a non-negative integer; it is always non-decreasing across calls in any realistic usage (but tests may not enforce this — your code just does math).
- Entries without TTL are permanent and never cleaned up by `cleanup_expired`.
- Plain `put()` on a TTL'd key makes it permanent (clears the expiry).

## Common gotchas

1. **Expiry boundary: `expiry <= now` means expired.** An entry with `expiry=10` at `now=10` is expired. Greater-than-or-equal, not strictly greater.
2. **`get()` never checks TTL.** Only `get_at()` does. Don't accidentally add TTL logic to `get()`.
3. **`put()` after `put_with_ttl` clears the TTL.** If you store expiry in a parallel dict, make sure `put()` removes it.
4. **`cleanup_expired` returns a count**, not a list of keys. Count the removals and return the integer.
5. **Entries without TTL are ignored by `cleanup_expired`.** Only entries that were set with `put_with_ttl` (and have an expiry) should be candidates.

## When you're done

```
python3 test_level3.py
```

All Level 1-3 tests must pass before moving to Level 4.
