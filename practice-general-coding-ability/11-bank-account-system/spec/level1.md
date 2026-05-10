# Level 1 — Account Lifecycle

## What you're implementing

You write a **class** `Bank` in `solution.py`:

```python
class Bank:
    def open_account(self, account_id: str) -> bool: ...
    def get_balance(self, account_id: str) -> int: ...
    def deposit(self, account_id: str, amount: int) -> int: ...
    def withdraw(self, account_id: str, amount: int) -> int: ...
```

Each test creates a fresh `Bank()` instance and calls these four methods.

## Mental model

Think of `Bank` as a ledger at a small credit union. When someone calls `open_account("alice")`, you add a new row for Alice with a zero balance. When they call `deposit("alice", 100)`, you add 100 to Alice's balance and return the new total. `withdraw` removes money — but only if Alice has enough. `get_balance` lets anyone read the current balance at any moment.

At this level everything is single-threaded and synchronous. No concurrency, no history, no interest — just the four primitive operations.

## The 4 methods for Level 1

### 1. `open_account(account_id: str) -> bool`

Register a new account with a starting balance of `0`.

| Situation | Returns |
|-----------|---------|
| `account_id` is new | `True` |
| `account_id` already exists | `False` (do NOT reset balance) |

### 2. `get_balance(account_id: str) -> int`

Read the current balance.

| Situation | Returns |
|-----------|---------|
| Account exists | current balance (int, always >= 0) |
| Account does not exist | `-1` |

### 3. `deposit(account_id: str, amount: int) -> int`

Add `amount` to the account balance.

| Situation | Returns |
|-----------|---------|
| Account exists | new balance after deposit |
| Account does not exist | `-1` (no side effect) |

- `amount` is always a positive integer in tests.

### 4. `withdraw(account_id: str, amount: int) -> int`

Subtract `amount` from the account balance.

| Situation | Returns |
|-----------|---------|
| Account exists AND balance >= amount | new balance after withdrawal |
| Account does not exist | `-1` (no side effect) |
| Account exists BUT balance < amount | `-1` (no side effect — balance unchanged) |

- `amount` is always a positive integer in tests.

## Worked example

```python
b = Bank()

# Open accounts
assert b.open_account("alice") == True
assert b.open_account("bob")   == True
assert b.open_account("alice") == False   # duplicate

# Starting balances
assert b.get_balance("alice") == 0
assert b.get_balance("carol") == -1       # doesn't exist

# Deposits
assert b.deposit("alice", 200) == 200
assert b.deposit("alice", 50)  == 250
assert b.deposit("carol", 10)  == -1      # no account

# Withdrawals
assert b.withdraw("alice", 100) == 150    # 250 - 100 = 150
assert b.withdraw("alice", 200) == -1     # insufficient; balance stays 150
assert b.get_balance("alice")   == 150    # confirmed unchanged
assert b.withdraw("carol", 10)  == -1     # no account
```

## Constraints

- `account_id` is any non-empty string.
- `amount` is a positive integer.
- Up to 10,000 accounts per test.
- No concurrency at this level — all calls are sequential.

## Common gotchas

1. **`open_account` on an existing id must NOT reset its balance** — just return `False` and leave the account alone.
2. **`get_balance` returns `-1`, not `0`** for a missing account — do not confuse a zero-balance account with a missing one.
3. **Insufficient funds returns `-1` AND leaves the balance unchanged** — do not partially mutate.
4. **Return types are `int`** — never return `None` or a string.
5. **`withdraw` checks existence BEFORE checking funds** — if the account doesn't exist, return `-1` (not "insufficient funds" logic).

## When you're done

```bash
python3 test_level1.py
```

All tests in `TestLevel1` must pass before moving to Level 2.
