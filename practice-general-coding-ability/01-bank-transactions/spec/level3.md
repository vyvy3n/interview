# Level 3 — Scheduled Payments

## What you're implementing

You extend `solution(queries)` with two new commands: `SCHEDULE_PAYMENT` and
`CANCEL_PAYMENT`. All Level 1 and Level 2 commands continue to work unchanged.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

The function signature does not change. The tricky part is the timing logic that fires
pending payments before processing each new query.

## Mental model

Level 3 introduces **time-deferred side effects**. Instead of taking money immediately,
SCHEDULE_PAYMENT registers a future withdrawal to fire at a specific timestamp. Every time
a new query arrives, you first fast-forward the clock: fire any scheduled payments whose
execute time is ≤ the current query's timestamp, then process the query itself.

Think of it like a cron job inside your bank. At every "tick" (each query timestamp), you
drain the queue of due payments before handling the actual command. A payment that can't
execute (insufficient funds) is silently dropped — no retry, no error, no notification.

The key implementation pattern: before every query, iterate over all pending payments with
`execute_time <= current_ts`, sorted by `(execute_time, payment_id_creation_order)`, and
attempt each one. Successful fires increment the account's outgoing total (they count for
TOP_SPENDERS just like a PAY).

## The 2 commands for Level 3

### 1. `["SCHEDULE_PAYMENT", <timestamp>, <account_id>, <amount>, <delay>]`

Register a future payment of `amount` from `account_id`, scheduled to execute at
`ts + delay`.

| Situation | Return |
|-----------|--------|
| Account exists | payment ID string, e.g. `"payment1"` |
| Account does not exist | `""` (empty string) |

- Payment IDs are **global** (across all accounts) and **sequential**: `"payment1"`,
  `"payment2"`, `"payment3"`, … The counter increments each time a payment is
  **successfully scheduled** (i.e., the account existed). A failed scheduling attempt
  (account missing) does **not** increment the counter.
- `<delay>` is a positive integer string. The payment fires at `int(timestamp) + int(delay)`.
- Scheduling a payment does NOT immediately deduct anything from the balance.

### 2. `["CANCEL_PAYMENT", <timestamp>, <account_id>, <payment_id>]`

Cancel a scheduled payment before it fires.

| Situation | Return |
|-----------|--------|
| Account exists, payment exists, belongs to account, and has NOT yet fired | `"true"` |
| Account does not exist | `""` (empty string) |
| `payment_id` does not exist | `""` (empty string) |
| `payment_id` belongs to a different account | `""` (empty string) |
| Payment has already fired (or was already cancelled) | `""` (empty string) |

## Critical timing semantics

**Before processing each query at timestamp T:**
1. Collect all pending (not yet fired, not cancelled) payments with `execute_time <= T`.
2. Sort them: first by `execute_time` ascending, then by creation order ascending (i.e.,
   lower payment number fires first among ties).
3. For each, in that order: if the account has enough balance, deduct the amount and mark
   the payment as fired; otherwise silently skip (mark as skipped/dropped).
4. Fired payments count toward the account's outgoing total for TOP_SPENDERS.

"Before processing" is strict: even a SCHEDULE_PAYMENT query at timestamp T fires any
pending payments with execute_time ≤ T before registering the new one.

## Worked example — trace through it

```python
queries = [
    ["CREATE_ACCOUNT",   "1",  "alice"],
    ["DEPOSIT",          "2",  "alice", "500"],
    ["SCHEDULE_PAYMENT", "3",  "alice", "200", "5"],
    ["SCHEDULE_PAYMENT", "4",  "alice", "100", "4"],
    ["TOP_SPENDERS",     "6",  "1"],
    ["SCHEDULE_PAYMENT", "7",  "ghost", "50",  "1"],
    ["CANCEL_PAYMENT",   "8",  "alice", "payment2"],
    ["TOP_SPENDERS",     "15", "1"],
    ["TOP_SPENDERS",     "20", "1"],
]
```

State: `accounts = {alice: 500}`, `outgoing = {alice: 0}`, `pending = {}`,
`payment_counter = 0`

| # | Query ts | Fire before query? | Query action | balance | outgoing | Output |
|---|----------|--------------------|--------------|---------|----------|--------|
| 1 | ts=1 | nothing due | CREATE_ACCOUNT alice | alice:0 | alice:0 | `"true"` |
| 2 | ts=2 | nothing due | DEPOSIT alice 500 | alice:500 | alice:0 | `"500"` |
| 3 | ts=3 | nothing due | SCHEDULE_PAYMENT alice 200 delay=5 → fires at ts=8 | alice:500 | alice:0 | `"payment1"` |
| 4 | ts=4 | nothing due (earliest due is ts=8) | SCHEDULE_PAYMENT alice 100 delay=4 → fires at ts=8 | alice:500 | alice:0 | `"payment2"` |
| 5 | ts=6 | nothing due (ts=8 > 6) | TOP_SPENDERS 1 | unchanged | unchanged | `"alice(0)"` |
| 6 | ts=7 | nothing due | SCHEDULE_PAYMENT ghost → account missing | unchanged | unchanged | `""` |
| 7 | ts=8 | **fire due payments!** execute_time=8: payment1 fires first (created first), then payment2. alice: 500-200=300, then 300-100=200. Both fire. outgoing: alice += 200+100 = 300. | CANCEL_PAYMENT alice payment2 → already fired | alice:200 | alice:300 | `""` |
| 8 | ts=15 | nothing new due | TOP_SPENDERS 1 | unchanged | unchanged | `"alice(300)"` |
| 9 | ts=20 | nothing new due | TOP_SPENDERS 1 | unchanged | unchanged | `"alice(300)"` |

Final return value:

```python
["true", "500", "payment1", "payment2", "alice(0)", "", "", "alice(300)", "alice(300)"]
```

Key trace notes:
- At ts=4, payment2 is scheduled to fire at ts=4+4=8 (same as payment1 which fires at ts=3+5=8).
- At ts=7, "ghost" doesn't exist → returns `""`, counter stays at 2.
- At ts=8 (CANCEL_PAYMENT query), before processing the cancel we fire: payment1 and payment2 both have execute_time=8 ≤ 8. payment1 fires first (lower creation order) → alice 500→300. payment2 fires next → alice 300→200. Both are now marked "fired". The CANCEL_PAYMENT query then finds payment2 already fired → `""`.

## Constraints

- All Level 1 and Level 2 constraints still apply.
- `<delay>` is a positive integer string (`> 0`).
- `<amount>` in SCHEDULE_PAYMENT is a positive integer string (`> 0`).
- `payment_id` strings are of the form `"paymentN"` where N is the global sequential counter.
- Timestamps are strictly increasing across queries.
- Up to `10^5` queries; up to `10^5` scheduled payments total.

## Common gotchas

1. **Fire BEFORE the current query executes** — this applies to ALL queries including
   SCHEDULE_PAYMENT and CANCEL_PAYMENT themselves. Don't fire after.
2. **Insufficient funds = silent skip** — a payment that can't execute is simply dropped
   (marked as fired/expired). It does NOT decrement a counter or appear in any error.
3. **Failed scheduling (missing account) does NOT increment the payment counter** — only
   successful SCHEDULE_PAYMENT calls consume a payment ID.
4. **CANCEL_PAYMENT on a fired or skipped payment returns `""`** — "already executed"
   and "silently skipped due to insufficient funds" are both terminal states.
5. **Ties in execute_time are broken by creation order** — payment1 fires before payment2
   if both are due at the same timestamp. Use the numeric suffix (or creation order index)
   to break ties, not the string lexicographic order (payment10 > payment2 numerically but
   < payment2 lexicographically).

## When you're done

```
cd 01-bank-transactions
python3 test_level3.py
```

All Level 3 tests must pass before moving to Level 4.
