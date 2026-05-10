# Level 2 — Transfer & Top Spenders

## What you're implementing

You extend the same `solution(queries)` function from Level 1 with two new commands:
`TRANSFER` and `TOP_SPENDERS`. All Level 1 commands continue to work unchanged.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

The function signature does not change. You're adding two new `elif` branches inside the
same loop.

## Mental model

Level 2 adds two new dimensions to your bank:

**Moving money between accounts.** A transfer is an atomic debit+credit — money leaves one
account and arrives at another in one step. If either party is invalid (missing account,
insufficient funds, same-to-same), the entire transfer is rejected and nothing changes.

**Reporting on spending behaviour.** The bank needs to rank accounts by how much they've
paid out in total — both PAY withdrawals and TRANSFER sends count as "outgoing money".
You'll need to track a running outgoing total per account so you can answer this query in
any order.

The key insight: start tracking outgoing spend at account creation (zero), and increment it
every time a PAY or TRANSFER succeeds. TOP_SPENDERS then just sorts that dict.

## The 2 commands for Level 2

### 1. `["TRANSFER", <timestamp>, <from_id>, <to_id>, <amount>]`

Move `amount` from `from_id` to `to_id` atomically.

| Situation | Return |
|-----------|--------|
| Both accounts exist, `from_id != to_id`, and `from_id.balance >= amount` | new balance of `from_id` as a string |
| Either account does not exist | `""` (empty string) |
| `from_id == to_id` | `""` (empty string) |
| `from_id.balance < amount` (insufficient funds) | `""` (empty string) |

The `amount` transferred **counts toward `from_id`'s outgoing total** (just like a PAY).

### 2. `["TOP_SPENDERS", <timestamp>, <n>]`

Return the top-N accounts ranked by total outgoing money (sum of all successful PAY and
TRANSFER amounts sent by the account).

| Situation | Return |
|-----------|--------|
| There are `>= N` accounts | the top-N formatted string (see below) |
| There are `< N` accounts | all accounts, same format |
| `n == 0` | `""` (empty string — no accounts to return) |

**Output format:** `"alice(500), bob(300), carol(200)"`
- Accounts listed as `account_id(outgoing_total)`.
- Separated by `", "` (comma followed by a single space).
- Sorted by outgoing DESCENDING; ties broken by `account_id` ALPHABETICALLY ASCENDING.
- All accounts that have ever existed are eligible, even those with 0 outgoing spend.
- `n` is a positive integer **string** (convert with `int(n)`).

## Worked example — trace through it

```python
queries = [
    ["CREATE_ACCOUNT", "1",  "alice"],
    ["CREATE_ACCOUNT", "2",  "bob"],
    ["CREATE_ACCOUNT", "3",  "carol"],
    ["DEPOSIT",        "4",  "alice", "500"],
    ["DEPOSIT",        "5",  "bob",   "300"],
    ["PAY",            "6",  "alice", "200"],
    ["TRANSFER",       "7",  "alice", "bob", "100"],
    ["TRANSFER",       "8",  "carol", "alice", "50"],
    ["TRANSFER",       "9",  "alice", "alice", "50"],
    ["TOP_SPENDERS",   "10", "2"],
    ["TOP_SPENDERS",   "11", "5"],
]
```

Tracking extra state: `outgoing = {account_id: int}` (starts at 0 on CREATE_ACCOUNT).

| # | Query | balance state | outgoing state | Output |
|---|-------|---------------|----------------|--------|
| 1 | `CREATE_ACCOUNT alice` | `{alice:0}` | `{alice:0}` | `"true"` |
| 2 | `CREATE_ACCOUNT bob` | `{alice:0, bob:0}` | `{alice:0, bob:0}` | `"true"` |
| 3 | `CREATE_ACCOUNT carol` | `{alice:0, bob:0, carol:0}` | `{alice:0, bob:0, carol:0}` | `"true"` |
| 4 | `DEPOSIT alice 500` | `{alice:500, ...}` | unchanged | `"500"` |
| 5 | `DEPOSIT bob 300` | `{alice:500, bob:300, carol:0}` | unchanged | `"300"` |
| 6 | `PAY alice 200` | `{alice:300, bob:300, carol:0}` | `{alice:200, bob:0, carol:0}` | `"300"` |
| 7 | `TRANSFER alice→bob 100` | `{alice:200, bob:400, carol:0}` | `{alice:300, bob:0, carol:0}` | `"200"` |
| 8 | `TRANSFER carol→alice 50` | unchanged (carol has 0, insufficient) | unchanged | `""` |
| 9 | `TRANSFER alice→alice 50` | unchanged (from_id == to_id) | unchanged | `""` |
| 10 | `TOP_SPENDERS 2` | unchanged | unchanged | `"alice(300), bob(0)"` |
| 11 | `TOP_SPENDERS 5` | unchanged | unchanged | `"alice(300), bob(0), carol(0)"` |

Notes on rows 10–11:
- alice has 300 outgoing (200 PAY + 100 TRANSFER); bob and carol have 0.
- TOP_SPENDERS 2 → alice first (300 > 0), then the next highest: bob and carol are tied at 0, bob comes first alphabetically.
- TOP_SPENDERS 5 → only 3 accounts exist, so all 3 are returned.

Final return value:

```python
["true", "true", "true", "500", "300", "300", "200", "", "", "alice(300), bob(0), carol(0)", "alice(300), bob(0), carol(0)"]
```

## Constraints

- All Level 1 constraints still apply.
- `<amount>` in TRANSFER is a positive integer string (`> 0`).
- `<n>` in TOP_SPENDERS is a positive integer string (`>= 1`).
- Up to `10^5` queries total.
- Aim for `O(A log A)` for TOP_SPENDERS where A = number of accounts (sort on demand).

## Common gotchas

1. **TRANSFER to self returns `""`** — check `from_id == to_id` *before* looking up balances.
2. **Both accounts must exist** — if *either* is missing, return `""` and touch nothing.
3. **Only successful PAY and TRANSFER count as outgoing** — a failed PAY (insufficient funds) or failed TRANSFER does NOT increment the outgoing counter.
4. **TOP_SPENDERS includes ALL accounts** — even accounts with 0 outgoing spend appear in the ranking. They sort after positive spenders, ties broken alphabetically.
5. **TOP_SPENDERS with n > account count** — return all accounts, not an error. Never pad with empty strings.

## When you're done

```
cd 01-bank-transactions
python3 test_level2.py
```

All Level 2 tests must pass before moving to Level 3.
