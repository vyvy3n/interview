# Level 2 — Transfers + History

## What you're implementing

Extend `Bank` with two new methods:

```python
class Bank:
    # ... (L1 methods) ...
    def transfer(self, from_id: str, to_id: str, amount: int) -> int: ...
    def get_transaction_history(self, account_id: str, n: int) -> list[str]: ...
```

Every deposit, withdrawal, and transfer must now be recorded in a per-account transaction log.

## Mental model

`transfer` is an atomic debit-plus-credit: money leaves one account and arrives in another in a single operation. If anything is wrong (missing account, same source and target, insufficient funds), the entire operation fails and neither balance changes.

`get_transaction_history` is a read-only audit log. Every mutation — deposits, withdrawals, and both sides of a transfer — appends a structured string to the account's history. The log is returned newest-first (most recent transaction at index 0).

## The 2 methods for Level 2

### 1. `transfer(from_id: str, to_id: str, amount: int) -> int`

Move `amount` from `from_id` to `to_id`.

| Situation | Returns |
|-----------|---------|
| Success | new balance of `from_id` |
| `from_id` does not exist | `-1` |
| `to_id` does not exist | `-1` |
| `from_id == to_id` | `-1` |
| `from_id` has insufficient funds | `-1` |

On any failure, neither balance changes.

### 2. `get_transaction_history(account_id: str, n: int) -> list[str]`

Return the last `n` transactions for `account_id`, newest first.

| Situation | Returns |
|-----------|---------|
| Account exists with >= n transactions | list of `n` strings |
| Account exists with < n transactions | all available transactions (fewer than n) |
| Account does not exist | `[]` |
| Account exists but has no history | `[]` |

**Transaction format strings:**

| Operation | Format |
|-----------|--------|
| `deposit(account_id, amount)` | `"deposit:{amount}"` |
| `withdraw(account_id, amount)` | `"withdraw:{amount}"` |
| Transfer out | `"transfer_out:{amount}:to_{to_id}"` |
| Transfer in | `"transfer_in:{amount}:from_{from_id}"` |

Both sides of a transfer must be recorded: `from_id` gets `"transfer_out:..."` and `to_id` gets `"transfer_in:..."`.

## Worked example

```python
b = Bank()
b.open_account("alice")
b.open_account("bob")

b.deposit("alice", 500)
b.deposit("alice", 200)
b.withdraw("alice", 100)

# History newest-first
assert b.get_transaction_history("alice", 3) == [
    "withdraw:100",
    "deposit:200",
    "deposit:500",
]
assert b.get_transaction_history("alice", 1) == ["withdraw:100"]
assert b.get_transaction_history("alice", 10) == [
    "withdraw:100",
    "deposit:200",
    "deposit:500",
]  # fewer than 10 available, return all 3

# Transfer records on both sides
b.transfer("alice", "bob", 300)  # alice: 600 - 300 = 300
assert b.get_transaction_history("alice", 1) == ["transfer_out:300:to_bob"]
assert b.get_transaction_history("bob",   1) == ["transfer_in:300:from_alice"]

# Failure cases
assert b.transfer("alice", "alice", 10) == -1          # same account
assert b.transfer("alice", "carol", 10) == -1          # carol missing
assert b.transfer("alice", "bob",   999) == -1         # insufficient
assert b.get_transaction_history("carol", 5) == []     # missing account
```

## Constraints

- `amount` is always a positive integer.
- `n` is always a positive integer.
- History is unbounded in size — store all transactions.
- Returning fewer than `n` items when history is short is correct behaviour, not an error.

## Common gotchas

1. **History is newest-first** — insert new entries at the front of the list (or reverse on read).
2. **Both sides of a transfer are recorded** — the sender gets `transfer_out`, the receiver gets `transfer_in`, both in the same call.
3. **Failed operations must not touch history** — if `transfer` returns `-1`, neither account's history changes.
4. **`get_transaction_history` returns `[]` for missing accounts, not `-1`** — the return type is always a list.
5. **`n` can exceed history length** — return all available entries, not an error.

## When you're done

```bash
python3 test_level2.py
```
