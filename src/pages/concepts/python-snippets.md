---
layout: ../../layouts/Layout.astro
title: Python Snippets
---

# Python Snippets

> Lean one-line-per-pattern reference. Every snippet is something I actually used in problems 01-14.

## Sorting

```python
sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))     # value DESC, key ASC tiebreak
sorted(items, key=lambda x: (-x.score, x.id))         # field DESC, ID ASC
sorted(items, key=lambda x: (x.priority, x.created))  # multi-key ASC
sorted(items, key=lambda x: -x.score)[:k]              # top-K
sorted(d.keys())                                        # alphabetical keys
list.sort(key=fn)                                       # in-place
list.sort(reverse=True)                                 # in-place DESC
min(items, key=lambda x: x.last_access)                # LRU pick (smallest)
max(rates)                                              # take max of iterable
```

## Dict

```python
d.get(k, default)                  # safe lookup
d.pop(k, None)                     # safe pop
d.setdefault(k, []).append(v)      # init-then-append
del d[k]                           # raises KeyError if missing
k in d                             # membership
{k: v for k, v in d.items() if c}  # filter/transform
list(d.keys()), list(d.values()), list(d.items())
{**a, **b}                         # merge (b wins on conflict)
```

```python
from collections import defaultdict
counts = defaultdict(int);  counts[k] += 1            # auto-init counter
groups = defaultdict(list); groups[k].append(v)       # auto-init list

from collections import Counter
Counter(words).most_common(5)                          # top-5 by count

from collections import OrderedDict
od = OrderedDict()
od.move_to_end(k)              # mark as MRU (LRU pattern)
od.popitem(last=False)         # evict LRU (front)
```

## List

```python
lst.append(x); lst.extend(other); lst.insert(0, x)
lst.pop()        # last; lst.pop(0) is O(n) — use deque for FIFO
lst[:k]          # first K (slice); lst[-k:] last K
lst[::-1]        # reversed copy; reversed(lst) is iterator
sum(lst); min(lst); max(lst); any(lst); all(lst)
[x for x in lst if cond]                # filter
[fn(x) for x in lst]                    # map
list(map(fn, lst)); list(filter(fn, lst))
enumerate(lst);  zip(a, b);  zip(*matrix)   # transpose
```

## Deque (use this for FIFO queues — O(1) on both ends)

```python
from collections import deque
q = deque()
q.append(x); q.appendleft(x)
q.pop(); q.popleft()        # both O(1)
q[0]; q[-1]                 # peek
deque(maxlen=n)             # bounded; auto-drop on overflow
```

## String

```python
s.startswith(prefix); s.endswith(suffix)
s.split(":");  s.split(":", 1)        # split on first only
":".join(parts)                        # str list -> str
f"{name}({count})"                    # f-string
str(n);  int(s);  int(s, 16)           # base conversions
s.lower(); s.upper(); s.strip()
s.replace(old, new)
s in big_string                        # substring check
```

## Threading

```python
import threading
self._lock = threading.RLock()         # RLock = re-entrant; methods can call methods
with self._lock:
    ...                                 # critical section

evt = threading.Event()
evt.set(); evt.clear(); evt.is_set()
evt.wait(timeout=5.0)                   # returns True if set, False on timeout

cond = threading.Condition(self._lock)
with cond: cond.wait_for(lambda: predicate, timeout=5.0)
with cond: cond.notify_all()           # wake all waiters

t = threading.Thread(target=fn, args=(...,), daemon=True)
t.start(); t.join(timeout=...)

import queue
q = queue.Queue(maxsize=10)
q.put(x); item = q.get();  q.task_done(); q.join()    # blocking
```

## Asyncio

```python
import asyncio

async def main():
    await asyncio.sleep(0.1)
    return await fetch()

asyncio.run(main())                     # top-level entry; ONLY ONE per process

await asyncio.gather(*coros)            # parallel; cancels all if one fails
await asyncio.gather(*coros, return_exceptions=True)  # collect errors instead

result = await asyncio.wait_for(coro, timeout=2.0)    # raises TimeoutError
done, pending = await asyncio.wait(coros, timeout=2.0)
for t in pending: t.cancel()

self._lock = asyncio.Lock()             # NOT thread-safe; for coroutines only
async with self._lock: ...              # critical section

ev = asyncio.Event(); await ev.wait(); ev.set()

sem = asyncio.Semaphore(5)
async with sem: ...                     # bound concurrency

q = asyncio.Queue()
await q.put(x); item = await q.get(); q.task_done()

t = asyncio.create_task(coro)
t.cancel(); await asyncio.sleep(0)      # let cancellation propagate

await asyncio.to_thread(blocking_fn, *args)   # bridge sync into async
```

## Heap (priority queue)

```python
import heapq
h = []
heapq.heappush(h, (priority, item))    # min-heap; negate for max-heap
heapq.heappop(h)
h[0]                                    # peek smallest
heapq.heapify(lst)                      # in-place to heap, O(n)
heapq.nsmallest(k, items, key=fn)
heapq.nlargest(k, items, key=fn)
```

## Dataclass

```python
from dataclasses import dataclass, field
@dataclass
class Account:
    account_id: str
    balance: int = 0
    outgoing: int = 0
    history: list = field(default_factory=list)   # mutable default

# field(compare=False)  to exclude from __eq__/__lt__
```

## Common one-liners

```python
# Initialize nested dict
db.setdefault(key, {})[field] = value

# Safe int parse
val = int(s) if s.isdigit() else 0

# Counter increment with default
counts[k] = counts.get(k, 0) + 1

# Top-K formatted "name(score), name(score)"
", ".join(f"{e.id}({e.score})" for e in sorted(...)[:k])

# Build dict from list of tuples
dict(items)

# Group by key
groups = defaultdict(list)
for x in items: groups[x.key].append(x)

# Check if all/any tasks complete
all(t.status == "completed" for t in tasks)

# Atomic swap
a, b = b, a

# Default-or-create
self.users.setdefault(user_id, User(user_id))

# Empty check (more Pythonic than `len(x) == 0`)
if not lst: ...
```

## CodeSignal-specific patterns

```python
# Half-open TTL check (entry expires AT exactly ts+ttl)
expired = entry.expiry is not None and ts >= entry.expiry

# Lazy refill (every operation triggers it first)
def _refill(self, now):
    elapsed = now - self.last_action_ts
    self.tokens = min(self.max_tokens, self.tokens + self.rate * elapsed)
    self.last_action_ts = now

# Validate-all-then-commit (atomic batch)
if not all(self._can_apply(x) for x in items): return False
for x in items: self._apply(x)

# Compare-and-set (CAS)
with self._lock:
    if self.state[k] != expected: return False
    self.state[k] = new
    return True

# Wait-for-condition with predicate (handles spurious wakeups)
with self._cond:
    return self._cond.wait_for(lambda: self._check(), timeout=timeout)

# Fire-on-every-query helper (for scheduled events)
def _advance_time(self, ts):
    due = sorted(p for p in self.pending if p.execute_at <= ts)
    for p in due: self._execute(p)

# Per-entity dataclass init pattern
self.entities[id] = Entity(id, **defaults)
```

## Test harness one-liners (unittest)

```python
self.assertEqual(actual, expected)
self.assertTrue(x); self.assertFalse(x)
self.assertIsNone(x); self.assertIsNotNone(x)
self.assertIn(item, container)
self.assertRaises(ValueError, fn, *args)
with self.assertRaises(KeyError): bad_call()

# Async test class
class TestL5(unittest.IsolatedAsyncioTestCase):
    async def test_x(self):
        result = await self.svc.amethod()
```
