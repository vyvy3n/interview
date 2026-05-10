# Level 3 — Scheduled Transfers

## What you're implementing

Extend `Bank` with a lightweight time-based scheduling system:

```python
class Bank:
    # ... (L1-L2 methods) ...
    def schedule_transfer(self, from_id: str, to_id: str, amount: int, execute_at: int) -> str: ...
    def cancel_scheduled(self, scheduled_id: str) -> bool: ...
    def tick(self, now: int) -> int: ...
```

## Mental model

Think of `schedule_transfer` as writing a post-dated cheque: you record the intent now, but the money doesn't move until the cheque's date arrives. `tick(now)` is the bank's clock advancing — when you call it, the bank processes all cheques whose date has passed.

Crucially, balance is **not** checked at scheduling time — only when the transfer actually tries to execute. If Alice schedules a $200 transfer but only has $50 when `tick` fires, the transfer is silently skipped.

## The 3 methods for Level 3

### 1. `schedule_transfer(from_id: str, to_id: str, amount: int, execute_at: int) -> str`

Register a future transfer.

| Situation | Returns |
|-----------|---------|
| Both accounts exist and `from_id != to_id` | `"sched_N"` where N is a global counter starting at 1 |
| `from_id` does not exist | `""` |
| `to_id` does not exist | `""` |
| `from_id == to_id` | `""` |

- The counter increments with every successful `schedule_transfer` call: first call returns `"sched_1"`, second returns `"sched_2"`, etc.
- Balance is **not** checked at scheduling time.

### 2. `cancel_scheduled(scheduled_id: str) -> bool`

Cancel a scheduled transfer before it executes.

| Situation | Returns |
|-----------|---------|
| Scheduled transfer exists and has not yet executed or been cancelled | `True` |
| `scheduled_id` does not exist | `False` |
| Transfer has already been executed | `False` |
| Transfer was already cancelled | `False` |

### 3. `tick(now: int) -> int`

Advance the bank's clock to `now` and execute all due transfers.

- Execute all scheduled transfers where `execute_at <= now`, **in ascending order of `scheduled_id`** (i.e., creation order — `sched_1` before `sched_2`).
- Skip cancelled transfers silently.
- For each non-cancelled due transfer, attempt execution:
  - If `from_id` or `to_id` no longer exists (e.g., after a merge) → skip.
  - If `from_id` has insufficient funds → skip.
  - If it executes: record the transaction in both accounts' histories (same format as `transfer`).
- Returns the count of **successfully executed** transfers (skipped ones don't count).

## Worked example

```python
b = Bank()
b.open_account("alice")
b.open_account("bob")
b.deposit("alice", 500)

# Schedule three transfers
s1 = b.schedule_transfer("alice", "bob", 100, execute_at=10)  # "sched_1"
s2 = b.schedule_transfer("alice", "bob", 200, execute_at=10)  # "sched_2"
s3 = b.schedule_transfer("alice", "bob", 100, execute_at=20)  # "sched_3"

assert s1 == "sched_1"
assert s2 == "sched_2"
assert s3 == "sched_3"

# Cancel s2 before it runs
assert b.cancel_scheduled(s2) == True
assert b.cancel_scheduled(s2) == False   # already cancelled

# Advance clock to 10 — only sched_1 runs (sched_2 cancelled, sched_3 not due)
count = b.tick(10)
assert count == 1
assert b.get_balance("alice") == 400     # 500 - 100 = 400
assert b.get_balance("bob")   == 100

# sched_1 is now executed — cancelling it fails
assert b.cancel_scheduled(s1) == False

# Advance to 20 — sched_3 runs
count = b.tick(20)
assert count == 1
assert b.get_balance("alice") == 300

# Insufficient funds at execution time
b.open_account("carol")
s4 = b.schedule_transfer("alice", "carol", 9999, execute_at=30)
b.tick(30)  # alice only has 300; skip silently
assert b.get_balance("alice") == 300     # unchanged
assert b.get_balance("carol") == 0
```

## Constraints

- `execute_at` is a non-negative integer (monotonic clock tick).
- `amount` is a positive integer.
- `tick` may be called with the same `now` multiple times — only transfers with `execute_at <= now` that haven't executed yet are affected. Transfers already executed are not re-executed.
- The global counter never resets (even if transfers are cancelled or executed).

## Common gotchas

1. **Balance NOT checked at schedule time** — always valid to schedule with any balance; only the execution-time balance matters.
2. **Execution order is by sched_id (creation order), not by execute_at** — when multiple transfers are due at the same tick, execute `sched_1` before `sched_2`, etc.
3. **A transfer that fails to execute (insufficient funds, missing account) is still marked "done"** — it won't be retried on the next `tick`.
4. **`cancel_scheduled` on an already-executed transfer returns `False`** — executed and cancelled are both terminal states.
5. **History is updated by successful scheduled transfers** — same `transfer_out`/`transfer_in` format as regular transfers.

## When you're done

```bash
python3 test_level3.py
```
