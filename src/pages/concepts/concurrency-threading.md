---
layout: ../../layouts/Layout.astro
title: Concurrency — threading
---

# Concurrency — threading

> Use threads for I/O-bound concurrency; the GIL blocks CPU-bound parallelism — reach for `multiprocessing` instead.

## When to use

- Network I/O: HTTP calls, DB queries, file reads where threads block and release the GIL
- Multiple independent blocking tasks that should overlap in time
- Shared mutable state between workers (vs. multiprocessing which has separate heaps)
- LeetCode concurrency problems (print-in-order, producer-consumer, bounded queue)

**Do NOT use** for pure CPU work (matrix math, sorting) — the GIL serialises Python bytecode execution.

## The core primitives

- **`threading.Lock`** — mutual exclusion; only one thread in the critical section at a time
- **`threading.RLock`** — re-entrant lock; the same thread can `acquire` multiple times without deadlocking
- **`threading.Event`** — one-shot boolean flag; `set()` unblocks all threads calling `wait()`
- **`threading.Condition`** — `wait()`/`notify()`/`notify_all()` gated on an arbitrary predicate; built on a Lock
- **`threading.Semaphore`** — counter; limits concurrent access to N slots (e.g. connection pools)
- **`threading.Barrier`** — N threads all block until every last one arrives, then all proceed together
- **`concurrent.futures.ThreadPoolExecutor`** — high-level pool; submit callables, get `Future` objects back
- **`queue.Queue`** — thread-safe FIFO; `put` blocks when full, `get` blocks when empty

---

## Template: thread-safe data structure (Lock)

Protect every read-modify-write with the same lock. Use the `with` context manager so the lock
releases even if an exception is raised.

```python
import threading

class SafeCounter:
    def __init__(self):
        self._lock = threading.Lock()
        self._count = 0

    def increment(self):
        with self._lock:          # acquire on enter, release on exit
            self._count += 1      # LOAD + ADD + STORE — not atomic without the lock

    def value(self):
        with self._lock:
            return self._count

# Demo
counter = SafeCounter()
threads = [threading.Thread(target=counter.increment) for _ in range(1000)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(counter.value())            # always 1000
```

**Use case:** any object whose state multiple threads mutate — counters, caches, lists.
Without the lock, `count += 1` compiles to three bytecodes (LOAD_FAST / BINARY_ADD / STORE_FAST)
and the GIL can switch threads between any two of them.

---

## Template: re-entrant locking (RLock)

When a locked method calls another locked method **on the same lock**, a plain `Lock` deadlocks.
`RLock` counts acquisitions and only releases on the matching number of `release()` calls.

```python
import threading

class Tree:
    def __init__(self):
        self._lock = threading.RLock()  # re-entrant
        self.data = []

    def add(self, value):
        with self._lock:
            self.data.append(value)
            self._rebalance()           # calls another method that also acquires _lock

    def _rebalance(self):
        with self._lock:                # same thread — OK with RLock, deadlock with Lock
            self.data.sort()
```

**Use case:** recursive algorithms or class hierarchies where a public method calls private helpers
that each acquire the same lock.

---

## Template: signal completion (Event)

`Event.wait()` blocks until `Event.set()` is called. Perfect for one-shot "gate open" signals
and chaining ordering constraints across threads.

```python
import threading

done = threading.Event()

def worker():
    print("doing work...")
    done.set()             # signal: work is complete

def waiter():
    done.wait()            # blocks until set(); optional timeout=N
    print("work finished, proceeding")

t1 = threading.Thread(target=worker)
t2 = threading.Thread(target=waiter)
t2.start(); t1.start()
t1.join(); t2.join()
```

**Chained ordering (LC 1114 style):** create one Event per "step done" and chain them:

```python
first_done  = threading.Event()
second_done = threading.Event()

def first():  print("first");  first_done.set()
def second(): first_done.wait();  print("second"); second_done.set()
def third():  second_done.wait(); print("third")
```

---

## Template: producer-consumer (Condition)

`Condition.wait()` atomically releases the lock and sleeps; `notify()` wakes one waiter.
**Always re-check the predicate in a `while` loop** — spurious wakeups can occur and a
notification may arrive before `wait()` is entered.

```python
import threading
from collections import deque

buf: deque = deque()
MAX = 5
cond = threading.Condition()

def producer(item):
    with cond:
        while len(buf) >= MAX:
            cond.wait()            # releases lock; re-acquires before returning
        buf.append(item)
        cond.notify_all()

def consumer():
    with cond:
        while len(buf) == 0:
            cond.wait()            # while-loop guards against spurious wakeups
        item = buf.popleft()
        cond.notify_all()
    return item
```

**Use case:** bounded buffer, readers-writers, FizzBuzz multithreaded — any scenario
where threads must wait for a shared-state predicate to become true.

---

## Template: worker pool (Thread + queue.Queue)

`queue.Queue` is already thread-safe. Workers call `get()` (blocks if empty) and call
`task_done()` when finished; `join()` on the queue blocks until all tasks are marked done.

```python
import threading
import queue

def worker(q: queue.Queue):
    while True:
        item = q.get()             # blocks until an item is available
        if item is None:           # sentinel: time to exit
            q.task_done()
            break
        process(item)
        q.task_done()

def process(item):
    print(f"processed {item}")

NUM_WORKERS = 4
q: queue.Queue = queue.Queue(maxsize=20)
threads = [threading.Thread(target=worker, args=(q,), daemon=True)
           for _ in range(NUM_WORKERS)]
for t in threads:
    t.start()

for item in range(20):
    q.put(item)
for _ in range(NUM_WORKERS):     # one sentinel per worker
    q.put(None)

q.join()                          # wait until every task_done() has been called
```

**Use case:** crawlers, batch I/O jobs, any fan-out-then-collect pattern.

---

## Template: bounded concurrency (Semaphore)

A `Semaphore(N)` allows at most N threads inside the guarded block at once — useful for
rate-limiting connections or parallel downloads.

```python
import threading
import time

sem = threading.Semaphore(3)      # at most 3 concurrent workers

def fetch(url):
    with sem:                     # blocks if 3 workers already inside
        print(f"fetching {url}")
        time.sleep(0.5)           # simulate I/O

urls = [f"http://example.com/{i}" for i in range(10)]
threads = [threading.Thread(target=fetch, args=(u,)) for u in urls]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

**Use case:** connection pools, API rate limits (LC 1117 H2O — two H permits, one O permit).

---

## Template: coordinated wait (Barrier)

All N threads block at `barrier.wait()` until every one has arrived; then all are released
simultaneously. A broken barrier (exception in one thread) raises `BrokenBarrierError` in all.

```python
import threading

NUM = 3
barrier = threading.Barrier(NUM)

def phase(name):
    print(f"{name} finished phase 1")
    barrier.wait()                # everyone waits here
    print(f"{name} starting phase 2")

threads = [threading.Thread(target=phase, args=(f"T{i}",)) for i in range(NUM)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

**Use case:** parallel simulation phases, multi-stage pipelines where each stage must
complete before the next begins.

---

## Template: ThreadPoolExecutor (high-level pool)

Submit callables and collect results via `Future` objects. The `with` block waits for all
submitted tasks before exiting.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request

URLS = ["https://example.com", "https://python.org", "https://docs.python.org"]

def fetch(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return url, len(r.read())

with ThreadPoolExecutor(max_workers=4) as pool:
    futures = {pool.submit(fetch, url): url for url in URLS}
    for future in as_completed(futures):
        url = futures[future]
        try:
            _, size = future.result()
            print(f"{url}: {size} bytes")
        except Exception as e:
            print(f"{url} failed: {e}")
```

**Use case:** any I/O fan-out where you want results back — prefer over manual Thread management
when you need return values or exception propagation.

---

## Variants / Gotchas

- **GIL does not make `+=` atomic.** `count += 1` compiles to LOAD_FAST / BINARY_ADD / STORE_FAST — the GIL can switch threads between any two bytecodes. Always protect with a `Lock`.
- **Always use `with lock:` not manual `acquire/release`.** If the body raises an exception, `release()` is never called — instant deadlock for any other thread waiting on that lock.
- **`Lock` is NOT re-entrant.** Calling `acquire()` twice from the same thread deadlocks. Use `RLock` when locked methods call other locked methods.
- **Always check predicates in a `while` loop after `condition.wait()`.** The OS can deliver spurious wakeups; another thread may consume the item before yours runs; `notify` may be called before `wait` is entered.
- **Always `join()` threads or set `daemon=True`.** A non-daemon thread keeps the process alive after `main` exits. A daemon thread is killed abruptly on exit — don't use for threads that must flush state.
- **Don't share `threading.Lock` across processes.** Locks live in process memory; use `multiprocessing.Lock` for cross-process synchronisation.
- **Holding a lock during I/O or `sleep` starves other threads.** Do heavy I/O outside the lock, collect the result, then lock only for the state update.
- **`Semaphore` vs `BoundedSemaphore`.** `BoundedSemaphore` raises `ValueError` if `release()` is called more times than `acquire()` — safer when you want to catch bugs where you release without acquiring.

---

## Common deadlock patterns to avoid

- **Nested locks acquired in different order** — always establish a global lock ordering:

```python
# DEADLOCK: thread A holds lock_a and waits for lock_b;
#           thread B holds lock_b and waits for lock_a
def transfer_bad(a, b):
    with a.lock:
        with b.lock:          # thread A: a→b
            ...

def transfer_bad2(a, b):
    with b.lock:
        with a.lock:          # thread B: b→a  ← opposite order = deadlock
            ...

# FIX: always acquire in a canonical order (e.g. by id)
def transfer(src, dst):
    first, second = (src, dst) if id(src) < id(dst) else (dst, src)
    with first.lock:
        with second.lock:
            ...
```

- **Lock + recursive call** — a plain `Lock` deadlocks if the holding thread calls a function that also acquires the same lock; switch to `RLock`:

```python
lock = threading.Lock()

def process(node):
    with lock:                 # DEADLOCK on recursive call
        if node.child:
            process(node.child)  # tries to acquire lock again — hangs forever

# FIX: use threading.RLock()
```

- **Forgetting to release on exception** — never use manual acquire/release:

```python
lock.acquire()
risky_operation()   # if this raises, release() is never called
lock.release()

# FIX: always use the context manager
with lock:
    risky_operation()
```

---

## Practice

**In-repo exercises**

- **Thread-safe counter** — increment a shared counter from 1 000 threads without losing updates. *Insight:* every read-modify-write needs a lock; `count += 1` is 3 bytecodes and the GIL can switch mid-way. [concurrency-primer/01-thread-safe-counter](https://github.com/vyvy3n/interview/blob/main/concurrency-primer/01-thread-safe-counter/solution.py)

- **Print in order (threading)** — three functions `first`, `second`, `third` run in arbitrary threads; guarantee they print in order. *Insight:* chain `threading.Event` objects — each function waits on the previous Event then sets its own. [concurrency-primer/02-print-in-order-threading](https://github.com/vyvy3n/interview/blob/main/concurrency-primer/02-print-in-order-threading/solution.py)

- **Bounded blocking queue** — implement a queue with a max capacity; `put` blocks when full, `get` blocks when empty. *Insight:* use `Condition.wait_for(predicate)` (or a `while` loop + `wait`) on a single Condition guarding both not-full and not-empty; `notify_all` after every state change. [concurrency-primer/04-bounded-blocking-queue](https://github.com/vyvy3n/interview/blob/main/concurrency-primer/04-bounded-blocking-queue/solution.py)

- **Readers-writers lock** — allow unlimited concurrent readers but exclusive writer access. *Insight:* track reader count under a Lock; the first reader acquires the write lock (blocking writers), the last reader releases it; writers call `acquire` on the write lock directly. [concurrency-primer/07-readers-writers-lock](https://github.com/vyvy3n/interview/blob/main/concurrency-primer/07-readers-writers-lock/solution.py)

- **FizzBuzz multithreaded** — four threads print Fizz / Buzz / FizzBuzz / number for their respective cases. *Insight:* shared counter under a Condition; each thread loops, waits if the counter doesn't match its divisibility rule, prints, increments, and `notify_all`. [concurrency-primer/08-fizzbuzz-multithreaded](https://github.com/vyvy3n/interview/blob/main/concurrency-primer/08-fizzbuzz-multithreaded/solution.py)

- **Condition-variable blocking cache** — a `get(key)` call blocks until another thread calls `set(key, value)`. *Insight:* one `Condition` per key (or a global one); `wait` until the key appears in the dict; `set` stores the value then calls `notify_all` to wake all blocked readers. [concurrency-primer/10-condvar-blocking-cache](https://github.com/vyvy3n/interview/blob/main/concurrency-primer/10-condvar-blocking-cache/solution.py)

**LeetCode multithreading**

- **Print in Order** — guarantee `second()` runs after `first()`, `third()` after `second()`, across arbitrary threads. *Insight:* two Events (or Semaphores) chained in sequence; each method waits then signals the next. [LC 1114](https://leetcode.com/problems/print-in-order/)

- **Print FooBar Alternately** — two threads alternate printing "foo" and "bar" N times. *Insight:* two Semaphores initialised to 1 / 0; each thread releases the other's semaphore after printing. [LC 1115](https://leetcode.com/problems/print-foobar-alternately/)

- **Print Zero Even Odd** — three threads: one prints zeros, one prints evens, one prints odds, interleaved as 0,1,0,2,0,3,…. *Insight:* three Semaphores — zero starts at 1; after printing zero, signal odd or even based on parity; that thread prints then signals zero. [LC 1116](https://leetcode.com/problems/print-zero-even-odd/)

- **Building H2O** — two hydrogen threads and one oxygen thread must release together in correct ratio. *Insight:* Semaphore(2) for H, Semaphore(1) for O, plus a Barrier(3) to make all three bond simultaneously before proceeding. [LC 1117](https://leetcode.com/problems/building-h2o/)

- **Design Bounded Blocking Queue** — implement `BoundedBlockingQueue` with a given capacity. *Insight:* `Condition` with while-loops checking full/empty; always `notify_all` so both producers and consumers are woken on each change. [LC 1188](https://leetcode.com/problems/design-bounded-blocking-queue/)

- **FizzBuzz Multithreaded** — four threads each responsible for one case; shared counter controls which fires. *Insight:* shared counter + Condition; each thread's loop calls `wait()` until the counter satisfies its predicate, then prints and increments. [LC 1195](https://leetcode.com/problems/fizzbuzz-multithreaded/)

- **Web Crawler Multithreaded** — BFS crawl starting from a seed URL, scraping only same-hostname links in parallel. *Insight:* `ThreadPoolExecutor` + a `Lock`-protected visited set; submit each unvisited URL as a future, collect new URLs from results, re-submit. [LC 1242](https://leetcode.com/problems/web-crawler-multithreaded/)
