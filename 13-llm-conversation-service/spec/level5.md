# Level 5 — Concurrent Sessions (Threading)

## What you're implementing

Make all L1–L4 methods **thread-safe** and add an async message worker pool:

```python
class ConversationService:
    # ... (L1-L4 methods, now thread-safe) ...
    def start_session_workers(self, count: int) -> None: ...
    def stop_session_workers(self) -> None: ...
    def queue_message(self, conv_id: str, role: str, content: str, tokens: int) -> str: ...
    def wait_for_processed(self, queue_id: str, timeout: float = None) -> bool: ...
```

## Mental model

Before this level, the service was a passive data store. Now multiple concurrent clients may call any method at the same time — a race condition without locks would corrupt conversation state. Additionally, you need an **async message ingestion pipeline**: clients can fire-and-forget messages via a queue; worker threads drain the queue in the background.

The worker pool mirrors the architecture of real LLM chatbot backends where message writes are decoupled from client requests for throughput.

## Thread-safety requirements

- Add `self._lock = threading.RLock()` in `__init__`.
- Wrap every method body with `with self._lock:`.
- Use `RLock` (reentrant lock) — some methods call other methods that also acquire the lock. A plain `Lock` would deadlock.

### Why RLock?

```python
def add_message(self, ...):
    with self._lock:          # acquires lock
        ...
        self._msg_condition.notify_all()  # still holding lock

def batch_add_messages(self, ...):
    with self._lock:          # acquires lock (count = 1)
        ...
        # If this internally calls add_message, that would try to acquire again
        # -> RLock: count goes 1->2->1, not deadlock
```

## The 4 methods for Level 5

### 1. `start_session_workers(count: int) -> None`

Spawn `count` background worker threads that process queued message additions.

| Situation | Behavior |
|-----------|----------|
| No workers running | Start `count` worker threads |
| Workers already running | Return immediately (no-op) |

Each worker loops:
1. Pull an item from the internal `queue.Queue`.
2. If the conversation has a `max_tokens` limit set, call `add_message_with_budget`. Otherwise call `add_message`.
3. Signal the item's `threading.Event` to mark it done.
4. Stop when a sentinel (`None`) is received or the stop event is set.

Use `queue.Queue` (thread-safe FIFO). Workers are `daemon=True`.

### 2. `stop_session_workers() -> None`

Signal all workers to stop and join them.

| Situation | Behavior |
|-----------|----------|
| Workers running | Set stop event, send sentinels, join all threads, clear list |
| No workers running | No-op |

After `stop_session_workers()` returns, all worker threads have exited.

### 3. `queue_message(conv_id: str, role: str, content: str, tokens: int) -> str`

Enqueue an async message addition.

| Situation | Returns |
|-----------|---------|
| Conv exists | queue_id like `"q_1"`, `"q_2"`, ... (global counter) |
| Conv does not exist | `""` |

The queue_id counter is global, monotonically increasing across all calls.

### 4. `wait_for_processed(queue_id: str, timeout: float = None) -> bool`

Block until the queued item is processed by a worker.

| Situation | Returns |
|-----------|---------|
| `queue_id` was returned by `queue_message` and is now processed | `True` |
| Timeout expires before processing | `False` |
| Unknown `queue_id` | `False` |
| `timeout=None` | Wait indefinitely |

Uses `threading.Event.wait(timeout)` internally.

## Worked example

```python
import threading, time
from solution import ConversationService

s = ConversationService()
s.create_conversation("chat-1", "alice")
s.create_conversation("chat-2", "bob")

# Start 2 workers
s.start_session_workers(2)

# Queue messages asynchronously
q1 = s.queue_message("chat-1", "user", "Hello", 10)
q2 = s.queue_message("chat-2", "user", "Hi", 5)
q3 = s.queue_message("ghost", "user", "Ignored", 5)  # missing conv

assert q1 == "q_1"
assert q2 == "q_2"
assert q3 == ""  # conv doesn't exist

# Wait for them to be processed
assert s.wait_for_processed(q1, timeout=2.0) == True
assert s.wait_for_processed(q2, timeout=2.0) == True
assert s.wait_for_processed("q_999", timeout=0.1) == False  # unknown

assert s.get_message_count("chat-1") == 1
assert s.get_message_count("chat-2") == 1

s.stop_session_workers()

# Concurrent thread-safety
s2 = ConversationService()
s2.create_conversation("shared", "u1")

def add_many():
    for _ in range(100):
        s2.add_message("shared", "user", "msg", 1)

threads = [threading.Thread(target=add_many) for _ in range(5)]
for t in threads: t.start()
for t in threads: t.join()

assert s2.get_message_count("shared") == 500  # 5 threads × 100 messages
```

## Constraints

- Use `threading.RLock`, not `threading.Lock`.
- Only one pool of workers at a time — `start_session_workers` is idempotent.
- Worker threads should be `daemon=True` to avoid blocking interpreter exit.
- `stop_session_workers` must join all threads before returning.

## Common gotchas

1. **Use `RLock`, not `Lock`** — the lock is reentrant; methods call other methods internally.
2. **`start_session_workers` is idempotent** — don't start more workers if already running.
3. **Send sentinels to unblock workers** on stop — workers blocked on `queue.get()` need a wake-up.
4. **`queue_message` returns `""` for missing convs** — validate conv existence before enqueueing.
5. **Worker checks `max_tokens`** — dispatches to `add_message_with_budget` if limit is set, else `add_message`.

## When you're done

```bash
python3 test_level5.py
```
