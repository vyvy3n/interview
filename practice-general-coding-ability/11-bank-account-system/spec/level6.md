# Level 6 — Atomic Compound Operations

## What you're implementing

Add three advanced operations that require lock-held atomicity and condition-variable signaling:

```python
class Bank:
    # ... (L1-L5 methods) ...
    def compare_and_deposit(self, account_id: str, expected_balance: int, deposit_amount: int) -> bool: ...
    def batch_transfer(self, transfers: list[tuple[str, str, int]]) -> bool: ...
    def wait_for_balance(self, account_id: str, target_balance: int, timeout: float = None) -> bool: ...
```

## Mental model

These three operations mirror real-world concurrent programming patterns:

- **`compare_and_deposit`** is an **optimistic lock / CAS (Compare-And-Swap)**: "if the balance is exactly what I expect, update it; otherwise fail." Only one of N concurrent threads that check the same expected_balance can succeed — they race, and the winner updates the balance, making all others' expected_balance stale.

- **`batch_transfer`** is an **all-or-nothing atomic transaction**: validate all transfers against the start state, then execute all of them. No partial execution.

- **`wait_for_balance`** is **condition variable blocking**: a thread parks itself until some other thread deposits enough money into the account. Uses `threading.Condition` built on top of the `RLock`.

## The 3 methods for Level 6

### 1. `compare_and_deposit(account_id: str, expected_balance: int, deposit_amount: int) -> bool`

Atomically:

1. Check if `account_id` exists. If not, return `False`.
2. Read current balance.
3. If `current_balance == expected_balance`: add `deposit_amount`, record in history, return `True`.
4. If `current_balance != expected_balance`: return `False` (no side effect).

The entire read-check-write must happen under the lock. Record as `"deposit:{deposit_amount}"` in history on success.

| Situation | Returns |
|-----------|---------|
| Account missing | `False` |
| Balance matches expected | `True`; balance += deposit_amount |
| Balance does not match | `False`; no side effect |

### 2. `batch_transfer(transfers: list[tuple[str, str, int]]) -> bool`

Atomically execute a list of `(from_id, to_id, amount)` transfers. All must succeed or none.

**Validation (done under lock, before any mutations):**

- Every `from_id` must exist.
- Every `to_id` must exist.
- No transfer where `from_id == to_id`.
- The sum of all amounts being withdrawn from each `from_id` must not exceed that account's **starting balance** (balance at the moment `batch_transfer` is called, before any of the transfers execute).

If **any** validation check fails, return `False` immediately without modifying any state.

If all checks pass, execute all transfers (recording in history) and return `True`.

| Situation | Returns |
|-----------|---------|
| All transfers valid | `True`; all balances updated, history recorded |
| Any validation failure | `False`; no state change |

### 3. `wait_for_balance(account_id: str, target_balance: int, timeout: float = None) -> bool`

Block the calling thread until `account_id`'s balance `>= target_balance` (or timeout).

| Situation | Returns |
|-----------|---------|
| Account missing | `False` immediately |
| Balance already `>= target_balance` | `True` immediately |
| Balance reaches target within timeout | `True` |
| Timeout expires before balance reached | `False` |
| `timeout=None` | Wait indefinitely |

**Implementation:** use `threading.Condition(self._lock)`. Every deposit/transfer_in operation must call `condition.notify_all()` to wake up waiting threads.

## Worked example

```python
import threading, time
from solution import Bank

b = Bank()
b.open_account("alice")
b.open_account("bob")
b.deposit("alice", 100)

# compare_and_deposit: 100 threads all check balance == 100; only one wins
results = []
lock = threading.Lock()

def try_cas():
    ok = b.compare_and_deposit("alice", 100, 50)
    with lock:
        results.append(ok)

threads = [threading.Thread(target=try_cas) for _ in range(100)]
for t in threads: t.start()
for t in threads: t.join()

assert results.count(True) == 1    # exactly one winner
assert results.count(False) == 99  # all others saw wrong balance

# batch_transfer: all-or-nothing
b2 = Bank()
b2.open_account("x")
b2.open_account("y")
b2.open_account("z")
b2.deposit("x", 1000)
b2.deposit("y", 500)

ok = b2.batch_transfer([("x", "z", 300), ("y", "z", 200)])
assert ok == True
assert b2.get_balance("x") == 700
assert b2.get_balance("y") == 300
assert b2.get_balance("z") == 500

# Fails: x only has 700 but tries to send 800
ok2 = b2.batch_transfer([("x", "z", 500), ("x", "z", 400)])  # 900 total > 700
assert ok2 == False
assert b2.get_balance("x") == 700  # unchanged

# wait_for_balance: writer deposits after 0.1 s
b3 = Bank()
b3.open_account("fund")

def delayed_deposit():
    time.sleep(0.1)
    b3.deposit("fund", 500)

writer = threading.Thread(target=delayed_deposit)
writer.start()

result = b3.wait_for_balance("fund", 500, timeout=2.0)
writer.join()
assert result == True

# Timeout expires
b4 = Bank()
b4.open_account("empty")
result4 = b4.wait_for_balance("empty", 9999, timeout=0.1)
assert result4 == False
```

## Constraints

- All three methods must hold the `RLock` for their full critical section.
- `wait_for_balance` must use `threading.Condition` (not polling) to avoid busy-waiting.
- `batch_transfer` checks all `from_id` withdrawals against each account's balance at call time — the sum of all withdrawals from the same `from_id` must not exceed its starting balance.
- `timeout=None` in `wait_for_balance` means wait forever.

## Concurrency notes

### Condition variable pattern

```python
# In __init__:
self._balance_condition = threading.Condition(self._lock)

# In deposit / transfer_in:
with self._lock:
    ...mutate balance...
    self._balance_condition.notify_all()

# In wait_for_balance:
with self._lock:          # also acquires _balance_condition's lock
    while balance < target:
        self._balance_condition.wait(timeout=remaining)
        # wait() releases the lock, sleeps, then re-acquires on wakeup
```

`threading.Condition(self._lock)` wraps the existing RLock — the condition uses it as its underlying mutex.

### Why RLock for Condition?

`threading.Condition` requires that its underlying lock be held when you call `.wait()`. Since we're using `RLock` throughout, passing it to `Condition` keeps everything consistent. The `.wait()` call atomically releases the lock and sleeps, then re-acquires it on wakeup.

## Common gotchas

1. **`compare_and_deposit` is truly atomic** — the read, compare, and write must all happen inside `with self._lock:`. Never release and re-acquire between the check and the update.
2. **`batch_transfer` checks START state** — compute total withdrawals per `from_id` across all transfers, then compare each to its balance before any modification.
3. **`wait_for_balance` uses `notify_all`, not `notify`** — multiple threads may be waiting; `notify` only wakes one.
4. **Condition spurious wakeups** — always recheck the condition after `wait()` returns. The `while balance < target` loop handles this correctly.
5. **`wait_for_balance` with `timeout` must track real elapsed time** — use `deadline = time.monotonic() + timeout` and `remaining = deadline - time.monotonic()` on each iteration.

## When you're done

```bash
python3 test_level6.py
```
