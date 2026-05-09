---
layout: ../../layouts/Layout.astro
title: CodeSignal Workflow & Pytest
---

# CodeSignal Workflow & Pytest

> The Industry Coding Framework (ICF) format used by Anthropic, Meta, Coinbase and others. 4 progressive levels, ~90 minutes, pytest-style tests.

## The format at a glance

| | What you get |
|---|---|
| **Stub** | a single function — usually `def solution(queries: list[list[str]]) -> list[str]` |
| **Levels** | 4 levels revealed *one at a time*. Each level adds new commands or constraints. |
| **Tests** | `test_level1.py` … `test_level4.py` — all visible, all pytest-compatible. |
| **Time** | ~90 minutes total; budget ~20 / 25 / 25 / 20 across levels. |
| **Scoring** | level-weighted; passing all of L1+L2 is usually the bar. L3 is the differentiator; L4 is bonus. |
| **What's tested** | "industry coding": correctness + design that doesn't collapse when L4 lands on top of L1's hack. |

The "queries" pattern: input is a list of `["COMMAND", "arg1", "arg2"]`; output is a list of strings, **one string per query, in order**. Strings, not numbers — this trips people up.

## First 60 seconds — setup

Each problem ships with a few files. Get them runnable immediately:

```bash
cd 01-bank-transactions/

# Most CodeSignal stubs run on stdlib only; pytest is just for the harness.
python3 -m venv .venv && source .venv/bin/activate
pip install pytest

# Sanity check — should fail (you haven't written anything yet)
pytest test_level1.py -vv
```

If the stub came with `python test_level1.py` style runners (no pytest needed), use those — they're identical for failing-fast purposes.

## Running tests — the commands you'll actually type

| Goal | Command |
|---|---|
| **Run all tests in a level** | `pytest test_level1.py -vv` |
| **Run one specific test** | `pytest test_level3.py::test_schedule_payment_basic -vv --tb=long` |
| **Pattern match across files** | `pytest -k "schedule_payment" -vv` |
| **Stop on first failure** | `pytest test_level2.py -x` |
| **Show `print()` output** | `pytest test_level2.py -s` |
| **Run all levels** | `pytest test_level*.py -vv` |
| **Run from a specific test onward** | `pytest test_level2.py --sw` (stepwise) |
| **Re-run only failures from last run** | `pytest --lf` |
| **Quiet pass, verbose fail** | `pytest --tb=short -q` |
| **Show the slowest 5 tests** | `pytest --durations=5` |

### The flag set you actually want

```bash
pytest test_level3.py::test_schedule_payment_basic -vv --tb=long -s
```

- `-vv`: full assertion expansion. Shows you `assert ['true', 'false'] == ['true', '']` instead of just "False".
- `--tb=long`: complete traceback with local variables — see what your function returned vs what was expected.
- `-s`: don't capture stdout — your `print()` statements appear inline.

When a test fails confusingly, this is the trio.

### Other tracebacks worth knowing

| Flag | When |
|---|---|
| `--tb=short` | normal dev loop |
| `--tb=long` | "what was the exact return value at each step?" |
| `--tb=line` | one line per failure — useful for big test suites |
| `--tb=no` | just the pass/fail summary |
| `-l` / `--showlocals` | print local variable values in tracebacks (often clearer than `--tb=long` alone) |

## Strategy — the meta game

### 1. Read **all** revealed specs before you code

If your harness reveals multiple levels at once, **read them all first**. Knowing L4 needs `MERGE_ACCOUNTS` changes how you store accounts in L1 (don't hard-code IDs into globals).

If only L1 is revealed, still skim the function signature and any visible test names — they leak structure.

### 2. Pick a state shape that survives all 4 levels

The most common failure mode: L1 uses a flat `balances: dict[str, int]`, L3 needs scheduled payments, and now you're refactoring under time pressure.

A safer default skeleton:

```python
def solution(queries):
    accounts = {}                  # account_id -> Account object
    out = []
    for q in queries:
        cmd, *args = q
        ts = int(args[0]) if args else 0
        out.append(handlers[cmd](accounts, ts, *args[1:]))
    return out
```

Each command becomes a small function. Adding L3's `SCHEDULE_PAYMENT` is then "add an entry to `handlers` and a `scheduled` field on `Account`" — not a rewrite.

### 3. Per-query timestamp processing — the universal trick

Almost every ICF problem hands you queries with a `timestamp` arg, monotonically non-decreasing. Many L3+ features ("expire after 24 hours", "scheduled at T+1000") become easy if you process *all* time-driven side effects at the start of every handler:

```python
def handle_query(accounts, ts, ...):
    process_pending(accounts, ts)   # fire scheduled payments, expire cashbacks, etc.
    # ... actual command logic
```

Centralizes time logic. No "I forgot to expire that cashback before computing the balance" bugs.

### 4. Return types are **strings**, always

`"true"` not `True`. `"42"` not `42`. `""` for "invalid / nothing to return", not `None` or `"null"`. Wrap your final value in `str()` or build the literal directly.

The classic 2-AM bug: `return balance` instead of `return str(balance)`.

### 5. Test as you build, level by level

Don't write all 4 levels then test. The cycle is:

```bash
# while iterating on level 1
pytest test_level1.py -vv -x        # stop on first failure, see the input/output
# ... edit solution.py ...
pytest test_level1.py -vv -x
# pass? commit. Then move on.
git commit -am "feat(L1): pass CREATE/DEPOSIT/PAY"
pytest test_level2.py -vv -x
```

Commit between levels so you can `git diff` exactly what L2 changed in your code — useful both during the interview (to undo a bad refactor) and for review afterward.

## Debugging — when a single test fails

```bash
# 1. Run just that test, max verbosity
pytest test_level3.py::test_schedule_payment_basic -vv --tb=long -s

# 2. If still unclear, drop a breakpoint
```

```python
def handle_schedule_payment(accounts, ts, account_id, amount, delay):
    breakpoint()                    # pytest will drop into pdb here
    # ...
```

Then:

```bash
pytest test_level3.py::test_schedule_payment_basic -s     # -s = don't capture stdin
```

You're now at a `(Pdb)` prompt. Useful pdb commands:

| Cmd | Does |
|---|---|
| `p var` | print value |
| `pp obj` | pretty-print |
| `n` | next line |
| `s` | step into call |
| `c` | continue (until next breakpoint or end) |
| `l` | list source around current line |
| `w` | show stack trace |
| `q` | quit |

If you hate pdb, `print(f"DEBUG ts={ts} accounts={accounts}")` + `pytest -s` is fine. Just remove before submission.

## Reading test failures fast

A typical pytest failure looks like:

```
FAILED test_level3.py::test_schedule_payment_fires_at_due_time
AssertionError: assert ['true', 'true', '', '50'] == ['true', 'true', '50', '0']
  At index 2 diff: '' != '50'
```

Read the diff: at query index 2, you returned `""`, the expected was `"50"`. So query 3 is your bug — find it in the test file:

```python
def test_schedule_payment_fires_at_due_time():
    queries = [
        ["CREATE_ACCOUNT", "1", "alice"],         # → "true"
        ["DEPOSIT", "2", "alice", "100"],         # → "100"
        ["SCHEDULE_PAYMENT", "3", "alice", "50", "100"],  # → "" expected, you got ""? wait —
        ["WAIT_AND_PROCESS", "200"],              # → "50" expected (cashback or payment fire)
    ]
```

The diff is showing you exactly where to look. Don't print-debug from the start of the test — start at the failing index.

## Common gotchas

- **Stringify return values** — `str(balance)`, `"true"` / `"false"`, `""` for empty.
- **Timestamps are strings** in the input — `int(ts)` before arithmetic.
- **Order matters** — return list must align query-by-query.
- **Mutating shared dicts during iteration** — copy keys with `list(d.keys())` if you might delete during the loop.
- **Tie-breaking** — when L4 says "highest balance, then lexicographic id", *that* exact ordering matters. Sort with a tuple key: `key=lambda a: (-a.balance, a.id)`.
- **L4 refactor budget** — if L4 needs a deep change (e.g. `MERGE_ACCOUNTS` with referential integrity to scheduled payments), and you've got 10 minutes left, ship a partial — passing 1 of 5 L4 tests is better than 0.

## Pre-flight checklist (run before submitting)

```bash
pytest test_level*.py -vv 2>&1 | tail -30   # all levels still pass
ruff check solution.py 2>/dev/null          # if available — catch unused vars
python -c "from solution import solution; print(solution([['CREATE_ACCOUNT','1','alice']]))"
```

A common silent failure: you passed L1–L3 along the way, but a refactor for L4 broke L1 and you didn't notice. Always re-run all levels at the end.

## Practice (the canonical ICF problems people share)

- **Bank Transaction System** — accounts, deposits, payments, scheduled payments, cashback, merge accounts. *Insight:* design `Account` as a class with optional `scheduled` queue and `cashback_pending` map; handle all time-driven effects at the *top* of every handler. **(The most-cited Anthropic prompt.)**
- **In-Memory File System** — `mkdir`, `addFile`, `delete`, `copy`, `find`, with TTL on files. *Insight:* trie of path segments; node holds `is_file`, `content`, `expires_at`. [LC 588 variant](https://leetcode.com/problems/design-in-memory-file-system/)
- **Cloud Storage** — files with sizes per user, capacity quotas, transfers, backups. *Insight:* per-user `total_size` cache; transfers update both sides; "compaction" loop runs at every command boundary.
- **Hotel Booking System** — rooms, reservations, scheduled cleanings, dynamic pricing. *Insight:* same time-driven side-effects pattern; sort active reservations by end time for fast availability lookups.
- **Inventory Management** — items, deposits, withdrawals, low-stock alerts, deferred replenishment. *Insight:* event queue keyed by timestamp; process due events at the top of each handler.
