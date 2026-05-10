---
layout: ../../layouts/Layout.astro
title: Six-Level Starter Template
---

# Six-Level Starter Template

> Distilled from 14 mock problems — paste this skeleton, then fill in the level-specific bodies as the test reveals them.

## When to use

- Anthropic Fellows OA (90 min, 6 levels, single class with methods, unittest tests)
- Any progressive CodeSignal problem with concurrency requirement at later levels

## The level shape (always the same)

| Level | What it adds | Time budget |
|---|---|---|
| L1 | Basic CRUD on one entity (`create`, `get`, `delete`) | ~8 min |
| L2 | Aggregations / queries (`top_k`, `list_by_x`, counts) | ~12 min |
| L3 | Time/scheduling/TTL dimension (`schedule`, `tick(now)`, `set_ttl`) | ~20 min |
| L4 | Compose op (`merge`, `fork`, `backup_restore`) | ~20 min |
| L5 | Concurrency: wrap with lock + maybe workers | ~10 min if bolt-on, ~25 if real workers |
| L6 | Atomic compound (`compare_and_X`, `batch_X`, `wait_for_X`) | ~15 min |

**Realistic 90-min target: L1-L4 clean + L5 lock-wrap. L6 is bonus.** Submit early, submit often — CodeSignal records your highest-scoring submission.

## Threading starter (use when test mentions `threading`)

```python
"""
Paste this at the start. Replace TODOs as levels reveal.
"""

import threading
from collections import deque
from dataclasses import dataclass, field


@dataclass
class Entity:
    entity_id: str
    # L2+: add fields as levels demand
    # balance: int = 0
    # outgoing: int = 0
    # messages: list = field(default_factory=list)


class Service:
    def __init__(self):
        self.entities: dict[str, Entity] = {}
        self._counter = 0                      # for "id_1", "id_2" generation
        self._lock = threading.RLock()         # RLock so methods can call methods
        self._cond = threading.Condition(self._lock)  # L6 wait_for_X
        # L5 worker bookkeeping
        self._workers: list[threading.Thread] = []
        self._stop_event = threading.Event()

    # ---------- L1: CRUD ----------

    def create(self, entity_id: str) -> bool:
        with self._lock:
            if entity_id in self.entities:
                return False
            self.entities[entity_id] = Entity(entity_id)
            return True

    def get_x(self, entity_id: str) -> int:
        with self._lock:
            if entity_id not in self.entities:
                return -1
            return self.entities[entity_id].x  # adjust field

    def delete(self, entity_id: str) -> bool:
        with self._lock:
            return self.entities.pop(entity_id, None) is not None

    # ---------- L2: Aggregations ----------

    def top_k(self, k: int) -> list[tuple[str, int]]:
        with self._lock:
            ranked = sorted(
                self.entities.values(),
                key=lambda e: (-e.score, e.entity_id),  # DESC, ties alpha ASC
            )
            return [(e.entity_id, e.score) for e in ranked[:k]]

    # ---------- L3: Scheduling / TTL ----------

    def schedule(self, entity_id: str, payload, execute_at: int) -> str:
        with self._lock:
            if entity_id not in self.entities: return ""
            self._counter += 1
            sched_id = f"sched_{self._counter}"
            # store: {sched_id: (entity_id, payload, execute_at, executed=False)}
            return sched_id

    def tick(self, now: int) -> int:
        """Execute all scheduled items with execute_at <= now, in creation order."""
        with self._lock:
            count = 0
            # iterate scheduled items sorted by (execute_at, sched_id)
            # for each not-yet-executed and execute_at <= now: try to apply, mark done
            self._cond.notify_all()  # for L6 wait_for_X
            return count

    # ---------- L4: Compose ----------

    def merge(self, survivor: str, absorbed: str) -> bool:
        with self._lock:
            if survivor == absorbed: return False
            if survivor not in self.entities: return False
            if absorbed not in self.entities: return False
            s, a = self.entities[survivor], self.entities[absorbed]
            # combine fields (sum, list extend, etc.)
            # reassign references (pending payments, etc.) from absorbed to survivor
            del self.entities[absorbed]
            self._cond.notify_all()
            return True

    # ---------- L5: Workers (only if test asks for them) ----------

    def start_workers(self, count: int):
        for _ in range(count):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self._workers.append(t)

    def stop_workers(self):
        self._stop_event.set()
        for t in self._workers:
            t.join()
        self._workers.clear()
        self._stop_event.clear()

    def _worker_loop(self):
        while not self._stop_event.is_set():
            # acquire lock, find work atomically, RELEASE before sleeping
            with self._lock:
                task = self._find_next_runnable()  # marks running atomically
                if task is None:
                    continue
            # do the work OUTSIDE the lock (e.g., time.sleep(task.duration))
            # then re-acquire to commit
            with self._lock:
                if task.status == "running":  # not cancelled
                    task.status = "completed"
                self._cond.notify_all()

    # ---------- L6: Atomic compound ----------

    def compare_and_set(self, entity_id: str, expected, new) -> bool:
        with self._lock:
            if entity_id not in self.entities: return False
            current = self.entities[entity_id].x
            if current != expected: return False
            self.entities[entity_id].x = new
            self._cond.notify_all()
            return True

    def batch_apply(self, items: list) -> int:
        with self._lock:
            # 1) Validate ALL items against the STARTING state
            # 2) If any fails: return -1 without mutating anything
            # 3) Otherwise apply all
            # ALL-or-nothing semantics
            return len(items)

    def wait_for_condition(self, predicate_args, timeout: float = None) -> bool:
        with self._cond:
            return self._cond.wait_for(
                lambda: self._check_predicate(predicate_args),
                timeout=timeout,
            )
```

## Asyncio starter (use when test mentions `asyncio`)

```python
"""
Paste this at the start. asyncio version.
"""

import asyncio
from dataclasses import dataclass, field


@dataclass
class Entity:
    entity_id: str
    # add fields per level


class Service:
    def __init__(self):
        self.entities: dict[str, Entity] = {}
        self._counter = 0
        self._lock = None  # lazy-init on first async call

    def _get_lock(self):
        # Avoid "no running event loop" in __init__ on Python 3.9-
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    # ---------- L1-L4: Sync methods (no lock needed for sync caller) ----------

    def create(self, entity_id: str) -> bool:
        if entity_id in self.entities: return False
        self.entities[entity_id] = Entity(entity_id)
        return True

    # ... L2-L4 sync methods identical to threading version, MINUS the `with self._lock:` ...

    # ---------- L5: Async wrappers ----------
    # Pattern: extract the LOGIC into _do_X helpers, then have:
    #   - sync methods call _do_X directly (no lock)
    #   - async methods acquire lock then call _do_X
    # This avoids deadlocks (async methods never call other async methods inside lock).

    def _do_set(self, entity_id, value):
        if entity_id not in self.entities: return False
        self.entities[entity_id].value = value
        return True

    def set(self, entity_id, value):                # sync
        return self._do_set(entity_id, value)

    async def aset(self, entity_id, value):         # async
        async with self._get_lock():
            return self._do_set(entity_id, value)

    # ---------- L6: Atomic compound (async) ----------

    async def acompare_and_set(self, entity_id, expected, new) -> bool:
        async with self._get_lock():
            if entity_id not in self.entities: return False
            if self.entities[entity_id].value != expected: return False
            self.entities[entity_id].value = new
            return True

    async def aincrement(self, entity_id, delta) -> int:
        """Atomic read-modify-write — must hold lock across full sequence."""
        async with self._get_lock():
            if entity_id not in self.entities: return -1
            self.entities[entity_id].value += delta
            return self.entities[entity_id].value

    async def abatch_apply(self, items: list) -> int:
        async with self._get_lock():
            # validate ALL against starting state
            # commit ALL or return -1
            return len(items)
```

## Test scaffolding

```python
import unittest
# import asyncio  # only if testing async
from solution import Service

class TestLevel1(unittest.TestCase):
    def test_create_basic(self):
        s = Service()
        self.assertTrue(s.create("e1"))

# For async (L5+ asyncio):
# class TestLevel5(unittest.IsolatedAsyncioTestCase):
#     async def test_concurrent_no_lost_updates(self):
#         s = Service()
#         await s.acreate("e1")
#         await asyncio.gather(*[s.aincrement("e1", 1) for _ in range(100)])
#         self.assertEqual(await s.aget("e1"), 100)

if __name__ == "__main__":
    unittest.main()
```

## What to add at each level (decision crib)

| Level | Action |
|---|---|
| **L1** | 3-4 dispatch methods. State = single dict. Returns: int or "". |
| **L2** | Add `top_k`, `list_*`, `count_*`. Sort by `(-score, id)` for DESC + alpha ASC ties. |
| **L3** | Add scheduling (counter for ids, `tick(now)` to fire due) OR TTL (store expiry; check on every read). Retrofit existing reads to respect TTL. |
| **L4** | Add `merge` (sum fields, reassign references, delete absorbed) OR `fork` (deep copy state to new id) OR `backup/restore` (snapshot remaining_ttl, re-anchor on restore). |
| **L5** | Add `self._lock = RLock()` (or asyncio.Lock). Wrap every method body with `with self._lock:`. If test mentions WORKERS: add Thread + Event + queue.Queue. |
| **L6** | Add `compare_and_X` (lock + read + compare + write), `batch_X` (lock + validate-all + commit-all-or-none), `wait_for_X` (Condition.wait_for with predicate). |

## The submit-often rule

CodeSignal grading takes your **highest-scoring submission** as final. So:

1. The moment L1 tests pass — **submit**.
2. The moment L2 tests pass — **submit**.
3. ...repeat through L4.
4. Now try L5 freely. If you break L4 mid-refactor, your prior submission still counts.
5. If you finish L5 without breaking L4 — **submit**. Try L6.
6. If L6 stalls — your L5 submission is still your floor.

Never end a session with broken code in the editor when you had passing code 10 minutes ago. Submit the moment something works.

## Reference solutions in the repo

These follow the templates above:

- **Threading**: [Problem 09](https://github.com/vyvy3n/interview/tree/main/09-concurrent-task-scheduler), [Problem 11](https://github.com/vyvy3n/interview/tree/main/11-bank-account-system), [Problem 13](https://github.com/vyvy3n/interview/tree/main/13-llm-conversation-service). *Insight:* RLock + Condition for wait-for-X; workers acquire-find-mark-running, release before sleep.
- **Asyncio**: [Problem 10](https://github.com/vyvy3n/interview/tree/main/10-thread-safe-keyvalue), [Problem 12](https://github.com/vyvy3n/interview/tree/main/12-file-cache-multitenant), [Problem 14](https://github.com/vyvy3n/interview/tree/main/14-llm-api-gateway). *Insight:* `_do_X` helpers shared between sync + async to avoid deadlocks; lazy `asyncio.Lock` init.

## Honest calibration warning

Reference solutions for Problems 11-14 are 250-360 SLOC — that's "complete polished work" not "what you write in 90 min." Realistic 90-min target is **L1-L4 clean + L5 lock-wrap**. Treat L6 in those problems as bonus practice, not the bar.
