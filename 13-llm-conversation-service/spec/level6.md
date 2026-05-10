# Level 6 — Atomic Compound Operations

## What you're implementing

Add three advanced operations requiring lock-held atomicity and condition-variable signaling:

```python
class ConversationService:
    # ... (L1-L5 methods) ...
    def compare_and_swap_message(self, conv_id: str, msg_index: int,
                                  expected_content: str, new_content: str,
                                  new_tokens: int) -> bool: ...
    def batch_add_messages(self, conv_id: str, messages: list[tuple[str, str, int]]) -> int: ...
    def wait_for_message_count(self, conv_id: str, target_count: int,
                                timeout: float = None) -> bool: ...
```

## Mental model

These three operations mirror real concurrent programming patterns:

- **`compare_and_swap_message`** is a **CAS (Compare-And-Swap)**: "if the message at this position still has the content I expect, update it; otherwise fail." Useful for optimistic concurrency — only one of N racing threads that all see the same expected content can win the swap.

- **`batch_add_messages`** is an **all-or-nothing atomic batch write**: if the full batch fits (with allowed drops of existing messages), add them all. If even the batch alone exceeds the limit, reject the entire batch — no partial adds.

- **`wait_for_message_count`** is a **condition variable**: a thread sleeps until the conversation reaches a target size. Another thread adding messages triggers a `notify_all()` to wake waiters.

## The 3 methods for Level 6

### 1. `compare_and_swap_message(conv_id, msg_index, expected_content, new_content, new_tokens) -> bool`

Atomically check and update a message.

| Situation | Returns |
|-----------|---------|
| Conv missing | `False` |
| `msg_index` out of range | `False` |
| `messages[msg_index].content != expected_content` | `False`; no state change |
| Content matches | `True`; content updated to `new_content`, tokens updated, cumulative total adjusted |

The full read-check-write must happen under the lock. The cumulative `total_tokens` is adjusted by `(new_tokens - old_tokens)`.

### 2. `batch_add_messages(conv_id: str, messages: list[tuple[str, str, int]]) -> int`

Atomically add a list of `(role, content, tokens)` tuples.

| Situation | Returns |
|-----------|---------|
| Conv missing | `-1` |
| No limit set | Add all; return `len(messages)` |
| Limit set AND `sum(batch tokens) > max_tokens` | **Reject ALL**; no state change; return `-1` |
| Limit set AND batch fits (possibly after dropping old messages) | Drop oldest existing messages to make room, then add all batch messages; return `len(messages)` |

**Key distinction from `add_message_with_budget`**: here we check if the *entire batch* (not just one message) can fit. If the batch total exceeds the limit, reject all — don't try to drop batch messages.

Existing messages may be dropped (oldest first) to make room for the batch. The batch messages themselves are never partially added.

### 3. `wait_for_message_count(conv_id: str, target_count: int, timeout: float = None) -> bool`

Block until the conversation has `>= target_count` messages.

| Situation | Returns |
|-----------|---------|
| Conv missing | `False` immediately |
| Already has `>= target_count` messages | `True` immediately |
| Reaches target within timeout | `True` |
| Timeout expires | `False` |
| `timeout=None` | Wait indefinitely |

**Implementation**: Use `threading.Condition(self._lock)`. Every successful message add (including from worker queue completions) must call `condition.notify_all()` to wake waiting threads. Use `while` loop to handle spurious wakeups.

## Worked example

```python
import threading, time
from solution import ConversationService

# compare_and_swap_message — only one of N concurrent threads wins
s = ConversationService()
s.create_conversation("c1", "alice")
s.add_message("c1", "user", "Original", 10)

results = []
lock = threading.Lock()

def try_swap():
    ok = s.compare_and_swap_message("c1", 0, "Original", "Updated", 20)
    with lock:
        results.append(ok)

threads = [threading.Thread(target=try_swap) for _ in range(100)]
for t in threads: t.start()
for t in threads: t.join()

assert results.count(True) == 1    # exactly one winner
assert results.count(False) == 99
assert s.get_messages("c1") == ["user:Updated"]

# batch_add_messages
s2 = ConversationService()
s2.create_conversation("c2", "bob")
s2.add_message("c2", "user", "Old1", 10)
s2.add_message("c2", "user", "Old2", 10)
s2.set_context_limit("c2", 25)  # limit 25; current 20

# Batch that fits (after dropping oldest): sum=15, need 20+15=35>25; drop Old1, 10+15=25<=25
count = s2.batch_add_messages("c2", [("user", "New1", 8), ("assistant", "New2", 7)])
assert count == 2
# After: [Old2(10), New1(8), New2(7)] = 25

# Batch that's too big: sum=30 > limit 25 -> reject
count2 = s2.batch_add_messages("c2", [("user", "X", 15), ("user", "Y", 15)])
assert count2 == -1

# wait_for_message_count
s3 = ConversationService()
s3.create_conversation("c3", "carol")

def delayed_add():
    time.sleep(0.1)
    s3.add_message("c3", "user", "Hello", 5)
    time.sleep(0.1)
    s3.add_message("c3", "assistant", "Hi!", 8)

writer = threading.Thread(target=delayed_add)
writer.start()

result = s3.wait_for_message_count("c3", 2, timeout=2.0)
writer.join()
assert result == True

# Timeout
s4 = ConversationService()
s4.create_conversation("c4", "dave")
assert s4.wait_for_message_count("c4", 10, timeout=0.1) == False
```

## Constraints

- All three methods must hold the `RLock` for their full critical section.
- `wait_for_message_count` must use `threading.Condition` (not polling).
- `compare_and_swap_message` with 100+ concurrent threads: exactly one `True` expected.
- `batch_add_messages` checks the sum of ALL batch tokens vs. `max_tokens` for rejection.

## Concurrency notes

### Condition variable pattern

```python
# In __init__:
self._msg_condition = threading.Condition(self._lock)

# In add_message / batch_add_messages (after state update):
self._msg_condition.notify_all()

# In wait_for_message_count:
with self._lock:
    while len(conv["messages"]) < target_count:
        self._msg_condition.wait(timeout=remaining)
        # wait() releases the lock, sleeps, reacquires on wakeup
```

### Why `notify_all`, not `notify`?

Multiple threads may be waiting on different target counts. `notify` only wakes one; `notify_all` wakes all of them, letting each one recheck its own condition.

## Common gotchas

1. **CAS is truly atomic** — read, compare, and write all under the lock. Never release between check and update.
2. **`batch_add_messages` rejects if batch TOTAL > max_tokens** — individual messages within the batch that might fit individually are irrelevant.
3. **Adjust `total_tokens` in `compare_and_swap_message`** — swap updates content AND token count.
4. **Spurious wakeups** — always recheck the condition after `wait()` returns (use a `while` loop).
5. **Track elapsed time** when `timeout` is given — use `deadline = time.monotonic() + timeout` and recompute remaining on each iteration.

## When you're done

```bash
python3 test_level6.py
```
