# Level 4 — Account Merge

## What you're implementing

You extend `solution(queries)` with one final command: `MERGE_ACCOUNTS`. All Level 1, 2,
and 3 commands continue to work unchanged.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

The function signature does not change. MERGE_ACCOUNTS is the hardest operation because it
has cascading effects: balances, outgoing totals, and pending scheduled payments all
transfer from the absorbed account to the surviving account.

## Mental model

Level 4 completes the bank lifecycle with **account consolidation**. When two accounts
merge, one (id2) is absorbed into the other (id1) and ceases to exist. From that moment
on, id1 carries everything: the combined balance, the combined outgoing history (for
TOP_SPENDERS ranking), and all pending scheduled payments that id2 had.

Think of it as a corporate merger — the acquired company disappears from the org chart, but
all its assets, liabilities, and pending obligations transfer to the acquiring company. Any
future reference to the old company name is invalid. Any obligation (scheduled payment)
that was the acquired company's responsibility is now the acquirer's.

The critical design point: your code probably already uses `account_id` as the key for
balances, outgoing totals, and pending payments. Merging means reassigning all of id2's
records to id1 and deleting id2 from every data structure.

## The 1 command for Level 4

### `["MERGE_ACCOUNTS", <timestamp>, <id1>, <id2>]`

Merge `id2` into `id1`. `id1` is the surviving account; `id2` is absorbed and deleted.

| Situation | Return |
|-----------|--------|
| Both accounts exist and `id1 != id2` | `"true"` |
| Either account does not exist | `""` (empty string) |
| `id1 == id2` | `""` (empty string) |

**What merges:**

1. **Balance:** `id1.balance += id2.balance`. id2's balance becomes 0 (then id2 is deleted).
2. **Outgoing total:** `id1.outgoing += id2.outgoing`. Future TOP_SPENDERS reports show id1
   with the combined history.
3. **Pending scheduled payments:** Any payment scheduled from id2 that has not yet fired
   (and has not been cancelled) is reassigned to id1. It will fire from id1's balance at
   its original `execute_time`. After the merge, `CANCEL_PAYMENT` on those payment IDs
   must be issued against id1 (not id2) to succeed.
4. **id2 is deleted.** Subsequent DEPOSIT, PAY, TRANSFER (to or from), CREATE_ACCOUNT,
   SCHEDULE_PAYMENT, CANCEL_PAYMENT against id2 return `""` or `"false"` as appropriate.

**Timing:** Like all other queries, MERGE_ACCOUNTS fires any due scheduled payments BEFORE
executing the merge itself. So if id2 had a payment due at the merge timestamp, it fires
from id2's balance before the merge combines them.

**Edge note:** A payment originally scheduled from id2, and reassigned to id1 after merge,
counts against id1's outgoing when it fires (not id2, since id2 no longer exists).

## Worked example — trace through it

```python
queries = [
    ["CREATE_ACCOUNT",   "1",  "alice"],
    ["CREATE_ACCOUNT",   "2",  "bob"],
    ["DEPOSIT",          "3",  "alice", "300"],
    ["DEPOSIT",          "4",  "bob",   "200"],
    ["PAY",              "5",  "bob",   "50"],
    ["SCHEDULE_PAYMENT", "6",  "bob",   "100", "10"],
    ["TRANSFER",         "7",  "alice", "bob", "50"],
    ["TOP_SPENDERS",     "8",  "2"],
    ["MERGE_ACCOUNTS",   "9",  "alice", "bob"],
    ["TOP_SPENDERS",     "10", "2"],
    ["DEPOSIT",          "11", "bob",   "999"],
    ["CANCEL_PAYMENT",   "12", "alice", "payment1"],
    ["TOP_SPENDERS",     "20", "2"],
]
```

State setup:
- `accounts`, `outgoing`, `pending`, `payment_counter`

| # | Query ts | Fire before? | Query action | alice bal | bob bal | alice out | bob out | Output |
|---|----------|--------------|--------------|-----------|---------|-----------|---------|--------|
| 1 | ts=1 | — | CREATE alice | 0 | — | 0 | — | `"true"` |
| 2 | ts=2 | — | CREATE bob | 0 | 0 | 0 | 0 | `"true"` |
| 3 | ts=3 | — | DEPOSIT alice 300 | 300 | 0 | 0 | 0 | `"300"` |
| 4 | ts=4 | — | DEPOSIT bob 200 | 300 | 200 | 0 | 0 | `"200"` |
| 5 | ts=5 | — | PAY bob 50 | 300 | 150 | 0 | 50 | `"150"` |
| 6 | ts=6 | — | SCHEDULE_PAYMENT bob 100 delay=10 → fires at ts=16 | 300 | 150 | 0 | 50 | `"payment1"` |
| 7 | ts=7 | — | TRANSFER alice→bob 50 | 250 | 200 | 50 | 50 | `"250"` |
| 8 | ts=8 | — | TOP_SPENDERS 2 → alice(50), bob(50) tied; alice < bob alpha → alice first | 250 | 200 | 50 | 50 | `"alice(50), bob(50)"` |
| 9 | ts=9 | nothing due (payment1 fires at ts=16) | MERGE alice←bob: alice.bal=250+200=450; alice.out=50+50=100; payment1 reassigned to alice; bob deleted | 450 | GONE | 100 | GONE | `"true"` |
| 10 | ts=10 | nothing due | TOP_SPENDERS 2 → only alice exists: alice(100) | 450 | GONE | 100 | GONE | `"alice(100)"` |
| 11 | ts=11 | nothing due | DEPOSIT bob → bob doesn't exist | 450 | GONE | 100 | GONE | `""` |
| 12 | ts=12 | nothing due | CANCEL_PAYMENT alice payment1 → payment1 now belongs to alice, not yet fired → cancel | 450 | GONE | 100 | GONE | `"true"` |
| 13 | ts=20 | payment1 was cancelled, nothing fires | TOP_SPENDERS 2 → alice(100) | 450 | GONE | 100 | GONE | `"alice(100)"` |

Final return value:

```python
["true", "true", "300", "200", "150", "payment1", "250", "alice(50), bob(50)", "true", "alice(100)", "", "true", "alice(100)"]
```

Key trace notes:
- At ts=8, alice and bob both have 50 outgoing. Tied → alphabetical: alice before bob.
- At ts=9 (MERGE), no payments are due (payment1 fires at ts=16). Merge fires nothing.
  After merge: alice has 250+200=450 balance, 50+50=100 outgoing, and inherits payment1.
- At ts=10, TOP_SPENDERS 2 but only alice exists → returns just alice.
- At ts=11, DEPOSIT to "bob" → bob is gone → `""`.
- At ts=12, CANCEL_PAYMENT alice payment1 → payment1 now owned by alice, not yet fired → succeeds → `"true"`.
- At ts=20, payment1 was cancelled so it doesn't fire. alice.out stays 100.

## Constraints

- All Level 1, 2, and 3 constraints still apply.
- `id1 != id2` check is required (return `""` if equal).
- After a merge, the absorbed account (`id2`) must not appear in TOP_SPENDERS — only the
  surviving account (`id1`) carries its combined history.
- You may receive multiple merges in sequence (A←B then A←C, etc.). Each merge is
  processed independently after firing due payments.
- Up to `10^5` queries total.

## Common gotchas

1. **Fire due payments BEFORE the merge** — if a payment is due AT the merge timestamp,
   it fires from id2's balance before the merge, so only the post-fire balance transfers.
2. **Reassign all of id2's pending (unfired, uncancelled) payments to id1** — payments
   that already fired or were cancelled before the merge are NOT transferred (their state
   is final).
3. **After merge, CANCEL_PAYMENT for an inherited payment must reference id1** — the
   payment's `owner` field must be updated from id2 to id1 at merge time.
4. **id2 must be completely removed** — it must not appear in TOP_SPENDERS, and any
   subsequent operation referencing id2 by name must return the appropriate "not found"
   response.
5. **Merged outgoing adds to id1's history retroactively** — TOP_SPENDERS after a merge
   shows id1 with the sum of both accounts' historical outgoing, not just id1's share.
6. **MERGE_ACCOUNTS on the same id returns `""`** — `id1 == id2` is an error even if
   that account exists.

## When you're done

```
cd 01-bank-transactions
python3 test_level4.py
```

All Level 4 tests must pass. Congratulations — you've built a complete bank.
