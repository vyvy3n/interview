# Level 4 — Interest + Account Merging

## What you're implementing

Extend `Bank` with two bulk operations:

```python
class Bank:
    # ... (L1-L3 methods) ...
    def apply_interest(self, rate_basis_points: int) -> dict[str, int]: ...
    def merge_accounts(self, survivor_id: str, absorbed_id: str) -> bool: ...
```

## Mental model

`apply_interest` is the bank's end-of-period sweep: every account earns a percentage of its current balance. The rate is expressed in **basis points** (bps), where 10,000 bps = 100%. So 500 bps = 5% interest. Integer (floor) division is used to avoid floating-point issues.

`merge_accounts` is the bank's response to a customer consolidation: two accounts become one. The surviving account absorbs all the money and all the history from the absorbed account. Any scheduled (pending) transfers that referenced the absorbed account are silently re-pointed to the survivor.

## The 2 methods for Level 4

### 1. `apply_interest(rate_basis_points: int) -> dict[str, int]`

Apply interest to every account:

```
new_balance = old_balance + (old_balance * rate_basis_points // 10000)
```

Use **integer (floor) division** (`//`). The interest amount itself is truncated, not the final balance.

| Situation | Behavior |
|-----------|----------|
| Normal case | Update all account balances; return result dict |
| Account with balance 0 | Interest = 0; balance stays 0 |

Returns a `dict` mapping `account_id -> new_balance`, with keys in **alphabetical order** by `account_id`. (In Python 3.7+, dict preserves insertion order — insert keys in sorted order to satisfy this requirement.)

Interest is **not** recorded in transaction history (it's a system-level sweep, not a user transaction).

### 2. `merge_accounts(survivor_id: str, absorbed_id: str) -> bool`

Merge `absorbed_id` into `survivor_id`.

| Situation | Returns |
|-----------|---------|
| Both accounts exist and `survivor_id != absorbed_id` | `True`; merge performed |
| `survivor_id` does not exist | `False` |
| `absorbed_id` does not exist | `False` |
| `survivor_id == absorbed_id` | `False` |

When merging:

1. **Balance**: `survivor.balance += absorbed.balance`
2. **History**: both lists are stored newest-first. The survivor's recent events are still the most recent after the merge, so they stay at the front. The absorbed account's history is appended after (treated as "older" in the combined log).  
   Combined history = `survivor.history + absorbed.history`  
   (survivor entries at indices 0..k, absorbed entries appended after)
3. **Pending scheduled transfers**: any transfer with `from_id == absorbed_id` or `to_id == absorbed_id` is re-pointed to `survivor_id`. Executed or cancelled transfers are left untouched.
4. The absorbed account is **removed** — any subsequent call referencing `absorbed_id` will behave as if it never existed.

## Worked example

```python
b = Bank()
b.open_account("alice")
b.open_account("bob")
b.deposit("alice", 1000)
b.deposit("bob", 500)

# Apply 10% interest (1000 bps)
result = b.apply_interest(1000)
assert result == {"alice": 1100, "bob": 550}

# Result is alphabetically sorted
assert list(result.keys()) == ["alice", "bob"]

# Truncation: 1 * 300 // 10000 = 0
b.open_account("penny")
b.deposit("penny", 1)
r2 = b.apply_interest(300)  # 0.03% — 1 * 300 // 10000 = 0
assert r2["penny"] == 1     # unchanged

# Merge: alice absorbs bob
b.deposit("alice", 100)     # alice history: [deposit:100, ...]
b.withdraw("bob", 50)       # bob history: [withdraw:50, ...]

result = b.merge_accounts("alice", "bob")
assert result == True
assert b.get_balance("alice") == 1200 + 550 - 50 + 100  # all combined
assert b.get_balance("bob") == -1   # no longer exists

# History order: absorbed (bob's) history comes before survivor (alice's existing)
history = b.get_transaction_history("alice", 100)
# bob's transactions appear after alice's in newest-first order
# alice's most recent (deposit:100) is first
assert history[0] == "deposit:100"
```

## Constraints

- `rate_basis_points` is a non-negative integer.
- 10,000 basis points = 100% interest rate.
- Integer division truncates toward zero (Python's `//` operator).
- Up to 10,000 accounts per test.

## Common gotchas

1. **Integer division, not rounding** — `(balance * rate) // 10000`, not `round(...)`.
2. **History ordering in merge** — both lists are newest-first. Use `survivor.history + absorbed.history` so the survivor's most recent events remain at index 0 in the combined list; absorbed entries are appended at the tail.
3. **Re-anchor ALL pending scheduled transfers** — both `from_id` and `to_id` fields must be updated. A transfer from absorbed to survivor would become a self-transfer after re-anchoring — but don't remove it; it will fail at execution time because `from_id == to_id`.  
   Actually: re-anchor both fields independently; self-transfers created this way will simply fail at `tick` time with `-1` (no-op).
4. **`apply_interest` does NOT record history entries** — purely a balance update.
5. **Return dict is sorted alphabetically** — build it by iterating `sorted(self._accounts.keys())`.

## When you're done

```bash
python3 test_level4.py
```
