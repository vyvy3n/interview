# Level 1 — Accounts, Deposits, Payments

## What you're implementing

You write **one Python function**:

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

- **Input:** a list of "queries". Each query is a list of strings — the first string is a command name (`"CREATE_ACCOUNT"`, `"DEPOSIT"`, or `"PAY"`); the rest are arguments.
- **Output:** a list of strings, **exactly one string per query**, in the same order. Each string is the result of running that query against your bank state.

## Mental model

Imagine your function is a tiny bank server. It receives a sequence of commands (the queries) one at a time, mutates an internal state (a dict of `account_id → balance`), and emits a one-line response for each command.

You're not building a CLI, REPL, or REST API. Just a pure function that loops through `queries` and returns one response per query.

## The 3 commands for Level 1

### 1. `["CREATE_ACCOUNT", <timestamp>, <account_id>]`

Open a new account with starting balance `0`.

| Situation | Return |
|-----------|--------|
| `account_id` is new | `"true"` |
| `account_id` already exists | `"false"` |

### 2. `["DEPOSIT", <timestamp>, <account_id>, <amount>]`

Add `amount` to the account's balance.

| Situation | Return |
|-----------|--------|
| Account exists | new balance as a string, e.g. `"150"` |
| Account does not exist | `""` (empty string) |

### 3. `["PAY", <timestamp>, <account_id>, <amount>]`

Withdraw `amount` from the account's balance.

| Situation | Return |
|-----------|--------|
| Account exists AND `balance >= amount` | new balance as a string |
| Account does not exist | `""` (empty string) |
| Account exists but `balance < amount` | `""` (empty string) — and **do NOT deduct** |

## Worked example — trace through it

```python
queries = [
    ["CREATE_ACCOUNT", "1", "alice"],
    ["CREATE_ACCOUNT", "2", "alice"],
    ["DEPOSIT",        "3", "alice", "100"],
    ["DEPOSIT",        "4", "bob",   "50"],
    ["PAY",            "5", "alice", "30"],
    ["PAY",            "6", "alice", "200"],
]
```

Step by step, watching the internal state and the output collected so far:

| # | Query | Internal state after | Output for this query |
|---|-------|----------------------|-----------------------|
| 1 | `CREATE_ACCOUNT alice` | `{"alice": 0}` | `"true"` |
| 2 | `CREATE_ACCOUNT alice` (dup) | `{"alice": 0}` | `"false"` |
| 3 | `DEPOSIT alice 100` | `{"alice": 100}` | `"100"` |
| 4 | `DEPOSIT bob 50` (no acct) | `{"alice": 100}` | `""` |
| 5 | `PAY alice 30` | `{"alice": 70}` | `"70"` |
| 6 | `PAY alice 200` (insufficient) | `{"alice": 70}` (unchanged) | `""` |

Final return value:

```python
["true", "false", "100", "", "70", ""]
```

That's it. You return that list. The test harness compares your list to the expected list.

## Constraints

- All `<timestamp>` values are positive integer **strings**, strictly increasing across queries.
- All `<amount>` values are positive integer **strings** (`> 0`).
- `<account_id>` is any non-empty string.
- Up to `10^5` queries — aim for `O(1)` per operation.
- **Note:** strings everywhere. You must convert with `int(amount)` to do math, and `str(balance)` to return.

## When you're done

```
cd 01-bank-transactions
python3 test_level1.py
```

All tests must pass before Level 2 is revealed.
