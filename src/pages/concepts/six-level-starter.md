---
layout: ../../layouts/Layout.astro
title: Six-Level Starter Template
---

# Six-Level Starter Template

> Paste-first reference for Anthropic Fellows-style 6-level CodeSignal problems. Every snippet stands alone — code first, explanation after.

## 1. Paste at start of solution.py

```python
import threading
from dataclasses import dataclass, field

@dataclass
class Entity:
    eid: str
    # add fields per level

class Service:
    def __init__(self):
        self.entities: dict[str, Entity] = {}
        self._counter = 0                      # for "id_1", "id_2"
        self._lock = threading.RLock()
        self._cond = threading.Condition(self._lock)
```

The skeleton works for both threading-style and asyncio-style problems (asyncio swaps the lock — see §8). `RLock` (re-entrant) lets methods safely call other locked methods. `_counter` is for any "generate the Nth ID" requirement.

---

## 2. L1 — CRUD

```python
def create(self, eid: str) -> bool:
    with self._lock:
        if eid in self.entities: return False
        self.entities[eid] = Entity(eid)
        return True

def get(self, eid: str) -> int:
    with self._lock:
        if eid not in self.entities: return -1
        return self.entities[eid].value

def update(self, eid: str, delta: int) -> int:
    with self._lock:
        if eid not in self.entities: return -1
        self.entities[eid].value += delta
        return self.entities[eid].value

def delete(self, eid: str) -> bool:
    with self._lock:
        return self.entities.pop(eid, None) is not None
```

Standard pattern: lock → existence check → mutate → return. `-1` for missing-int returns; `False` for boolean returns; `""` for missing-string returns. **Pick a return convention that matches the test suite.**

---

## 3. L2 — Top-K + listing

```python
def top_k(self, k: int) -> list[tuple[str, int]]:
    with self._lock:
        ranked = sorted(
            self.entities.values(),
            key=lambda e: (-e.score, e.eid),  # value DESC, ID ASC tiebreak
        )
        return [(e.eid, e.score) for e in ranked[:k]]

def list_by_filter(self, predicate) -> list[str]:
    with self._lock:
        return sorted(e.eid for e in self.entities.values() if predicate(e))
```

The `(-x, y)` tuple key gives DESC primary + ASC secondary in one sort call. Slice `[:k]` after sort — Python handles k > len gracefully.

---

## 4. L3 — Time / TTL / scheduling (pick the one your spec needs)

### 4a. TTL (half-open `[set_ts, expiry)`)

```python
def set_with_ttl(self, eid, value, ts: int, ttl: int):
    with self._lock:
        self.entities[eid] = Entity(eid, value=value, expiry=ts + ttl)

def get_at(self, eid, ts: int):
    with self._lock:
        e = self.entities.get(eid)
        if e is None: return -1
        if e.expiry is not None and ts >= e.expiry: return -1   # expired
        return e.value
```

Half-open means at exactly `ts == expiry`, the entry is gone. Tests almost always check the boundary.

### 4b. Lazy refill (token bucket / rate limiter)

```python
def _refill(self, e: Entity, now: int):
    elapsed = now - e.last_action_ts
    e.tokens = min(e.max_tokens, e.tokens + e.refill_rate * elapsed)
    e.last_action_ts = now

def consume(self, eid, amount: int, now: int) -> bool:
    with self._lock:
        if eid not in self.entities: return False
        e = self.entities[eid]
        self._refill(e, now)                   # ALWAYS refill first
        if e.tokens < amount: return False
        e.tokens -= amount
        return True
```

Call `_refill(e, now)` at the start of every operation that touches the entity — `consume`, `get_remaining`, `set_rate`, `merge`, etc. This is the heart of L3.

### 4c. Scheduled events + tick

```python
def schedule(self, payload, execute_at: int) -> str:
    with self._lock:
        self._counter += 1
        sid = f"id_{self._counter}"
        self.scheduled[sid] = (payload, execute_at, False)   # (payload, when, fired)
        return sid

def tick(self, now: int) -> int:
    with self._lock:
        due = sorted(
            (sid for sid, (_, t, fired) in self.scheduled.items() if not fired and t <= now),
            key=lambda s: int(s.split("_")[1]),                # numeric, not lex
        )
        for sid in due:
            payload, t, _ = self.scheduled[sid]
            self._apply(payload)                                # may silently fail
            self.scheduled[sid] = (payload, t, True)
        self._cond.notify_all()                                 # for L6 wait_for_X
        return len(due)
```

Sort due IDs numerically (`int(s.split("_")[1])`) not lexicographically — `id_10` < `id_2` lexicographically is wrong.

---

## 5. L4 — Merge / fork / restore (pick what your spec needs)

### 5a. Merge

```python
def merge(self, survivor: str, absorbed: str) -> bool:
    with self._lock:
        if survivor == absorbed: return False
        if survivor not in self.entities: return False
        if absorbed not in self.entities: return False
        s, a = self.entities[survivor], self.entities[absorbed]
        s.balance += a.balance                          # combine fields
        s.history.extend(a.history)
        for sid, (payload, t, fired) in self.scheduled.items():
            if payload.get("owner") == absorbed:        # reassign references
                payload["owner"] = survivor
        del self.entities[absorbed]
        self._cond.notify_all()
        return True
```

Validate ALL preconditions BEFORE any mutation. Reassign references in any other dicts that pointed to the absorbed entity. Don't forget `notify_all()` if L6's `wait_for_X` exists.

### 5b. Fork (deep copy)

```python
def fork(self, source: str, new_id: str) -> bool:
    with self._lock:
        if source not in self.entities or new_id in self.entities: return False
        src = self.entities[source]
        # Manual deep copy (faster than copy.deepcopy for known shape):
        self.entities[new_id] = Entity(
            new_id,
            value=src.value,
            history=list(src.history),                  # copy mutable fields
        )
        return True
```

Manual field-by-field copy is faster than `copy.deepcopy` and makes the data model explicit.

### 5c. Backup + restore (with TTL re-anchoring)

```python
def backup(self, ts: int) -> int:
    with self._lock:
        snap = {}
        for eid, e in self.entities.items():
            if e.expiry is not None and ts >= e.expiry: continue   # skip expired
            remaining = None if e.expiry is None else e.expiry - ts
            snap[eid] = (e.value, remaining)
        self.backups[ts] = snap
        return len(snap)

def restore(self, ts: int, backup_ts: int) -> bool:
    with self._lock:
        if backup_ts not in self.backups: return False
        snap = self.backups[backup_ts]
        self.entities = {                                # full replace
            eid: Entity(eid, value=v, expiry=None if r is None else ts + r)
            for eid, (v, r) in snap.items()
        }
        return True
```

Store **remaining_ttl** in the snapshot, not absolute expiry. On restore, re-anchor: `new_expiry = restore_ts + remaining_ttl`.

---

## 6. L5 — Concurrency (pick the right shape)

### 6a. Lock-wrap only (90% of L5 problems)

```python
# Already done in §1-5. The `with self._lock:` in every method body IS L5.
# Verify L1-L4 tests still pass after the wrap. That's it.
```

If your test mentions "thread-safe" but doesn't add new operations, you're done with L5 in 5 minutes. Wrap-and-submit.

### 6b. Worker pool (only if test asks for `start_workers`)

```python
def start_workers(self, count: int):
    for _ in range(count):
        t = threading.Thread(target=self._worker_loop, daemon=True)
        t.start()
        self._workers.append(t)

def stop_workers(self):
    self._stop_event.set()
    for t in self._workers: t.join()
    self._workers.clear(); self._stop_event.clear()

def _worker_loop(self):
    while not self._stop_event.is_set():
        with self._lock:
            task = self._pick_next_runnable()              # marks running atomically
        if task is None: continue
        time.sleep(task.duration)                          # SLEEP OUTSIDE LOCK
        with self._lock:
            if task.status == "running":                   # not cancelled
                task.status = "completed"
            self._cond.notify_all()
```

Acquire lock to find-and-mark-running atomically. **Release the lock BEFORE sleeping** or you serialize all workers. Re-acquire to commit. Workers are daemon threads so they die when the process dies.

---

## 7. L6 — Atomic compound (pick what your spec needs)

### 7a. Compare-and-set (CAS)

```python
def compare_and_set(self, eid, expected, new) -> bool:
    with self._lock:
        if eid not in self.entities: return False
        if self.entities[eid].value != expected: return False
        self.entities[eid].value = new
        self._cond.notify_all()
        return True
```

The whole read-compare-write must be inside ONE `with self._lock:` block. Test will spawn many concurrent CAS calls; exactly one should win.

### 7b. Atomic batch (all-or-nothing)

```python
def batch_apply(self, items: list) -> int:
    with self._lock:
        # 1) Validate ALL items against the STARTING state
        if not all(self._can_apply(x) for x in items): return -1
        # 2) Apply ALL — guaranteed to succeed past validation
        for x in items: self._apply(x)
        return len(items)
```

Validate-all-then-commit. Critically: when validating, simulate cumulative effects (e.g., total withdrawals per account) — don't just check each item independently.

### 7c. Wait-for-condition

```python
def wait_for(self, predicate_args, timeout: float = None) -> bool:
    with self._cond:
        return self._cond.wait_for(
            lambda: self._check(predicate_args),
            timeout=timeout,
        )
```

`Condition.wait_for(predicate, timeout)` handles spurious wakeups + missed notifies + timeout in one call. Every state-changing method must call `self._cond.notify_all()` to wake waiters.

---

## 8. Asyncio variant (deltas from threading version)

```python
import asyncio
from dataclasses import dataclass

class Service:
    def __init__(self):
        self.entities = {}
        self._lock = None                                  # lazy-init

    def _get_lock(self):
        if self._lock is None: self._lock = asyncio.Lock()
        return self._lock

    # Sync methods (L1-L4) DO NOT acquire lock — keep them lock-free.
    def _do_set(self, eid, value):
        if eid not in self.entities: return False
        self.entities[eid].value = value; return True

    def set(self, eid, value):                             # sync caller
        return self._do_set(eid, value)

    async def aset(self, eid, value):                      # async caller
        async with self._get_lock():
            return self._do_set(eid, value)

    async def aincrement(self, eid, delta):                # L6 atomic compound
        async with self._get_lock():
            if eid not in self.entities: return -1
            self.entities[eid].value += delta
            return self.entities[eid].value
```

Three deltas vs threading: (1) lazy `_get_lock()` avoids "no event loop" errors in `__init__`, (2) extract logic into `_do_X` helpers so sync + async share one body without deadlock, (3) `asyncio.Lock` is NOT thread-safe — only safe between coroutines on the same loop.

---

## 9. Test scaffolding

```python
import unittest
from solution import Service

class TestL1(unittest.TestCase):
    def test_create(self):
        s = Service()
        self.assertTrue(s.create("e1"))

# Async (L5+ asyncio):
import asyncio
class TestL5(unittest.IsolatedAsyncioTestCase):
    async def test_no_lost_updates(self):
        s = Service(); await s.acreate("e1")
        await asyncio.gather(*[s.aincrement("e1", 1) for _ in range(100)])
        self.assertEqual(await s.aget("e1"), 100)

if __name__ == "__main__":
    unittest.main()
```

Async tests use `IsolatedAsyncioTestCase` (Python 3.8+). The `gather` of 100 increments is the canonical "did you actually lock?" test — without proper locking, the result is < 100.

---

## 10. Per-level decision crib

| L | Add | Time |
|---|---|---|
| 1 | 3-4 dispatch methods on a single dict | 8 min |
| 2 | `top_k` with `(-score, id)` sort key | 12 min |
| 3 | TTL (§4a) OR refill (§4b) OR schedule+tick (§4c) | 20 min |
| 4 | merge (§5a) OR fork (§5b) OR backup/restore (§5c) | 20 min |
| 5 | lock-wrap (§6a) OR workers (§6b) | 10-25 min |
| 6 | CAS (§7a) OR batch (§7b) OR wait-for (§7c) | 15 min |

---

## 11. The submit-often rule

CodeSignal records your **highest-scoring submission** as final. So:

1. L1 tests pass → **submit**.
2. L2 tests pass → **submit**.
3. ...repeat through L4.
4. Try L5; if you break something, your floor is the last submission.
5. Submit again whenever something passes.

Never end with broken code in the editor when you had passing code 10 minutes ago.

---

## 12. Reference solutions

| Problem | Concurrency | Patterns it exercises |
|---|---|---|
| [09 Task Scheduler](https://github.com/vyvy3n/interview/blob/main/09-concurrent-task-scheduler/solution.py) | threading | workers (§6b), wait-for (§7c), DAG cycle detection |
| [10 KV Store](https://github.com/vyvy3n/interview/blob/main/10-thread-safe-keyvalue/solution.py) | asyncio | TTL (§4a), LRU, CAS (§7a), aincrement |
| [11 Bank](https://github.com/vyvy3n/interview/blob/main/11-bank-account-system/solution.py) | threading | schedule+tick (§4c), merge (§5a), batch (§7b), Condition |
| [12 File Cache](https://github.com/vyvy3n/interview/blob/main/12-file-cache-multitenant/solution.py) | asyncio | LRU + multi-tenant, atomic batch + bulk, lazy lock init |
| [13 LLM Conv Service](https://github.com/vyvy3n/interview/blob/main/13-llm-conversation-service/solution.py) | threading | fork (§5b), worker queue, batch (§7b) |
| [14 LLM API Gateway](https://github.com/vyvy3n/interview/blob/main/14-llm-api-gateway/solution.py) | asyncio | refill (§4b), prompt cache, atomic batch + merge + CAS |

---

## Honest calibration warning

L5 §6b (worker pool) and L6 (atomic compound) in the reference solutions are 250-360 SLOC — that's "complete polished" not "what you write in 90 min." Realistic 90-min target is **L1-L4 clean + L5 lock-wrap (§6a)**. L6 = bonus.
