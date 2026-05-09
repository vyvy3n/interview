# Level 1 — Accounts, Deposits, Payments

You are implementing the core of a bank ledger. Implement `solution(queries)` in `solution.py`. The function takes a list of queries (each a list of strings) and returns a list of strings (one per query).

## Operations

### 1. `["CREATE_ACCOUNT", <timestamp>, <account_id>]`

Create a new account with `account_id` and starting balance `0`.

- Returns `"true"` if the account was created.
- Returns `"false"` if `account_id` already exists.

### 2. `["DEPOSIT", <timestamp>, <account_id>, <amount>]`

Add `amount` to the account's balance.

- Returns the new balance as a string (e.g. `"150"`).
- Returns `""` (empty string) if the account does not exist.

### 3. `["PAY", <timestamp>, <account_id>, <amount>]`

Withdraw `amount` from the account's balance.

- Returns the new balance as a string.
- Returns `""` if the account does not exist.
- Returns `""` if the account's balance is less than `amount` (insufficient funds — the payment must NOT go through).

## Constraints

- All `<timestamp>` values are positive integer strings, **strictly increasing** across the queries.
- All `<amount>` values are positive integer strings (`> 0`).
- `<account_id>` is any non-empty string.
- Number of queries: up to `10^5`. Aim for `O(1)` per operation.

## Example

```python
queries = [
    ["CREATE_ACCOUNT", "1", "alice"],
    ["CREATE_ACCOUNT", "2", "alice"],     # duplicate
    ["DEPOSIT",        "3", "alice", "100"],
    ["DEPOSIT",        "4", "bob",   "50"],   # bob doesn't exist
    ["PAY",            "5", "alice", "30"],
    ["PAY",            "6", "alice", "200"],  # insufficient
]

solution(queries)
# => ["true", "false", "100", "", "70", ""]
```

## When you're done

Run `python test_level1.py` from inside `01-bank-transactions/`. All tests must pass before Level 2 is revealed.
