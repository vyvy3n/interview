---
layout: ../../layouts/Layout.astro
title: Rate Limiter Patterns
---

# Rate Limiter Patterns

> Token bucket wins when bursts are OK; leaky bucket when output must be smooth; sliding window when you need precision — every variant exposes `allow(key, cost=1) -> bool`.

## When to use

- API gateway throttling (per-user, per-tenant, per-tier)
- LLM inference cost control (tokens/sec instead of requests/sec)
- Protecting a downstream service from thundering-herd
- Interview asks: "design a rate limiter", "per-tenant isolation", or "how do you handle bursts"

## The four canonical algorithms

- **Token bucket** — bucket fills at a fixed rate; requests consume tokens; allows short bursts up to capacity
- **Leaky bucket** — requests queue and drain at a constant rate; excess drops immediately; output is perfectly smooth
- **Fixed window counter** — divide time into equal windows, count per window; simplest impl, but the window boundary is a burst seam
- **Sliding window log** — store every request timestamp; trim old ones; exact count, but O(N) memory per key
- **Sliding window counter** — weighted average of current + previous fixed windows; accurate enough, O(1) memory

## Algorithm comparison table

| Algorithm | Burst tolerance | Memory per key | Math complexity |
|---|---|---|---|
| Token bucket | YES (up to capacity) | O(1) | trivial |
| Leaky bucket | NO (smooths out) | O(1) | trivial |
| Fixed window | partial (at boundary) | O(1) | trivial |
| Sliding log | NO | O(N) per window | O(log N) |
| Sliding counter | partial | O(1) | weighted avg |

## Template: Token Bucket (lazy refill)

Key insight: no background thread needed — on each request, compute how many tokens should have accumulated since the last touch and add them in. This is the lazy refill pattern.

```python
import time

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()

    def _refill(self, now: float):
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def allow(self, cost: int = 1, now: float = None) -> bool:
        now = now if now is not None else time.time()
        self._refill(now)
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False
```

## Template: Leaky Bucket

Think of it as a FIFO queue draining at a constant rate. Each `allow` call drains virtually — check whether the queue would overflow.

```python
import time

class LeakyBucket:
    def __init__(self, capacity: int, drain_rate: float):
        self.capacity = capacity     # max queue depth
        self.drain_rate = drain_rate # requests drained per second
        self.queue_size = 0.0
        self.last_drain = time.time()

    def _drain(self, now: float):
        elapsed = now - self.last_drain
        self.queue_size = max(0.0, self.queue_size - elapsed * self.drain_rate)
        self.last_drain = now

    def allow(self, cost: int = 1, now: float = None) -> bool:
        now = now if now is not None else time.time()
        self._drain(now)
        if self.queue_size + cost <= self.capacity:
            self.queue_size += cost
            return True
        return False  # burst dropped immediately
```

## Template: Fixed Window Counter

Per-key dict mapping `window_id -> count`. Window ID is just `int(now // window_size)`.

```python
import time

class FixedWindowCounter:
    def __init__(self, limit: int, window_sec: float):
        self.limit = limit
        self.window_sec = window_sec
        self.counts: dict[str, tuple[int, int]] = {}  # key -> (window_id, count)

    def allow(self, key: str, now: float = None) -> bool:
        now = now if now is not None else time.time()
        window_id = int(now // self.window_sec)
        stored_window, count = self.counts.get(key, (-1, 0))
        if stored_window != window_id:
            count = 0  # new window — reset
        if count < self.limit:
            self.counts[key] = (window_id, count + 1)
            return True
        return False
```

## Template: Sliding Window Log

Store a deque of timestamps per key. Trim expired entries BEFORE checking size.

```python
import time
from collections import deque

class SlidingWindowLog:
    def __init__(self, limit: int, window_sec: float):
        self.limit = limit
        self.window_sec = window_sec
        self.logs: dict[str, deque] = {}

    def allow(self, key: str, now: float = None) -> bool:
        now = now if now is not None else time.time()
        cutoff = now - self.window_sec
        dq = self.logs.setdefault(key, deque())
        # Trim FIRST, then check — order matters
        while dq and dq[0] <= cutoff:
            dq.popleft()
        if len(dq) < self.limit:
            dq.append(now)
            return True
        return False
```

## Template: Sliding Window Counter

Weighted average: `prev_count * overlap_ratio + curr_count`. One O(1) division — no stored timestamps.

```python
import time

class SlidingWindowCounter:
    def __init__(self, limit: int, window_sec: float):
        self.limit = limit
        self.window_sec = window_sec
        # key -> (prev_window_id, prev_count, curr_window_id, curr_count)
        self.state: dict[str, tuple] = {}

    def allow(self, key: str, now: float = None) -> bool:
        now = now if now is not None else time.time()
        window_id = int(now // self.window_sec)
        offset = (now % self.window_sec) / self.window_sec  # progress through current window

        prev_wid, prev_cnt, curr_wid, curr_cnt = self.state.get(
            key, (window_id - 1, 0, window_id, 0)
        )
        if curr_wid != window_id:
            # Rotate: current becomes previous
            prev_wid, prev_cnt = curr_wid, curr_cnt
            curr_wid, curr_cnt = window_id, 0

        # Weight previous window by how much of it overlaps the sliding window
        estimated = prev_cnt * (1 - offset) + curr_cnt
        if estimated < self.limit:
            self.state[key] = (prev_wid, prev_cnt, curr_wid, curr_cnt + 1)
            return True
        return False
```

## Per-tenant isolation

Wrap any bucket in a per-key dict; lazy-create on first request. Works with any algorithm above.

```python
class PerTenantLimiter:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: dict[str, TokenBucket] = {}

    def allow(self, tenant_id: str, cost: int = 1) -> bool:
        if tenant_id not in self.buckets:
            self.buckets[tenant_id] = TokenBucket(self.capacity, self.refill_rate)
        return self.buckets[tenant_id].allow(cost)
```

Never delete buckets mid-stream (you'll reset their token count). For long-running services, add TTL eviction via `last_seen` timestamp.

## Thread safety

Each bucket's `_refill` + `allow` must be one atomic critical section — a read-modify-write pair that races without a lock.

```python
import threading

class ConcurrentTokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self._lock = threading.Lock()  # one lock per bucket

    def allow(self, cost: int = 1, now: float = None) -> bool:
        now = now if now is not None else time.time()
        with self._lock:
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            if self.tokens >= cost:
                self.tokens -= cost
                return True
            return False

class ConcurrentPerTenantLimiter:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: dict[str, ConcurrentTokenBucket] = {}
        self._map_lock = threading.Lock()  # protects dict mutation only

    def allow(self, tenant_id: str, cost: int = 1) -> bool:
        with self._map_lock:
            if tenant_id not in self.buckets:
                self.buckets[tenant_id] = ConcurrentTokenBucket(
                    self.capacity, self.refill_rate
                )
            bucket = self.buckets[tenant_id]
        return bucket.allow(cost)  # bucket has its own lock
```

Two-lock design: a short-held map lock for lookup/insert, then per-bucket lock for the actual refill math. Reduces contention for high-tenant-count systems.

## Variants / Gotchas

- **Lazy refill is mandatory** — a background thread incrementing tokens would require coordination with every `allow` call and adds complexity for no benefit; the lazy pattern computes the same result on demand
- **Bursts are a feature** — token bucket intentionally allows a burst of up to `capacity` requests; if the problem says "no burst allowed", use leaky bucket instead
- **Don't forget the cap** — refill formula must be `min(capacity, tokens + elapsed * rate)`; omitting the `min` gives unlimited accumulation during idle periods
- **Trim before check in sliding log** — checking `len(dq) < limit` before trimming expired entries causes spurious rejections
- **Never delete per-tenant buckets** — deletion resets the token count, which looks like a fresh grant; use TTL eviction based on `last_refill` if memory is a concern
- **`_refill` and token deduction must share the same lock** — splitting them creates a TOCTOU race where two threads both see enough tokens
- **Lazy refill generalises broadly** — TTL caches ("has this key expired?"), sliding-window analytics, and scheduled-event systems all use the same "compute elapsed, apply delta" idiom

## Practice

- **In-repo Problem 07 — LLM Rate Limiter** — full 4-level token bucket with lazy refill, top-K consumers, tier upgrade, and key merge. *Insight:* lazy refill is the heart of L3 — every operation that touches a bucket starts with `(now - last_action_ts) * rate` before any decision. [07-llm-rate-limiter](https://github.com/vyvy3n/interview/blob/main/07-llm-rate-limiter/solution.py)
- **LC 1188 — Design Bounded Blocking Queue** — fixed-capacity producer-consumer queue with blocking semantics. *Insight:* model capacity as a semaphore; `enqueue` acquires a "space" permit, `dequeue` releases it — the bounded queue is a leaky-bucket cousin. [LC 1188](https://leetcode.com/problems/design-bounded-blocking-queue/)
- **LC 359 — Logger Rate Limiter** — print each unique message at most once per 10 seconds. *Insight:* hash map of `message -> next_allowed_timestamp`; this is a fixed window counter with window size = 10 s, one key per message. [LC 359](https://leetcode.com/problems/logger-rate-limiter/)
- **Anthropic-reported Per-Tenant Token Bucket** — actual interview question per hackerprep.io. *Insight:* combine the `TokenBucket` class with a per-tenant lazy-init dict; thread safety requires one lock per bucket (low contention) or a single global lock (simpler, fine for interviews). The two-lock design above (`ConcurrentPerTenantLimiter`) is the production-grade answer.
