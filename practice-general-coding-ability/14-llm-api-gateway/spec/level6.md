# Level 6 — Atomic Compound Operations

## What you're implementing

Add three atomic compound operations that combine multiple reads and writes into a single lock-protected transaction. These are the hardest operations to get right under concurrency.

```python
async def abatch_handle(self, user_id: str, requests: list[tuple[str, int]], now: int) -> int: ...
async def amerge_users(self, survivor: str, absorbed: str) -> bool: ...
async def acompare_and_handle(self, user_id: str, prompt: str, expected_remaining: int, tokens_used: int, now: int) -> str: ...
```

**All methods from L1–L5 remain intact and unchanged.**

## Mental model

These operations are "all-or-nothing" within a single lock acquisition. The critical insight: you must hold the lock for the **entire** operation — read, compute, and write — so no other coroutine can observe an intermediate state or cause a TOCTOU (time-of-check-to-time-of-use) race.

## The 3 methods

### 1. `abatch_handle(user_id, requests, now) -> int`

Atomically process a batch of `(prompt, tokens)` requests. All-or-nothing: if the combined token cost fits in the bucket (after refill), all requests are accepted. If any one pushes the bucket below zero, all are rejected.

**Procedure (within one lock acquisition):**
1. If user missing → return `-1`
2. Refill bucket at `now`
3. Compute `total_needed = sum(tokens for _, tokens in requests)`
4. If `current_tokens >= total_needed`: deduct all, add `len(requests)` to `request_count`, add `total_needed` to `total_tokens_used`, return `len(requests)`
5. Else: return `-1` (nothing deducted)

### 2. `amerge_users(survivor: str, absorbed: str) -> bool`

Atomically merge the `absorbed` user into the `survivor`. After the merge, `absorbed` no longer exists.

**Merge rules (within one lock acquisition):**

| Field | Rule |
|-------|------|
| `max_tokens` | sum of both |
| `current_tokens` | sum of both, capped at new `max_tokens` |
| `refill_rate` | max of both |
| `request_count` | sum |
| `total_tokens_used` | sum |
| `cache_hits` | sum |
| `tier` | keep survivor's tier |

Returns `False` if:
- Either user is missing
- `survivor == absorbed` (cannot merge a user into themselves)

### 3. `acompare_and_handle(user_id, prompt, expected_remaining, tokens_used, now) -> str`

A compare-and-swap (CAS) style request handler. Succeeds only if the bucket level after refill exactly matches the caller's expected value — a form of optimistic concurrency control.

**Procedure (within one lock acquisition):**
1. If user missing → return `""`
2. Refill bucket at `now`
3. If `current_tokens != expected_remaining` → return `"stale"`
4. If `current_tokens < tokens_used` → return `"rate_limited"`
5. Deduct tokens, increment counters → return `"ok"`

**Key invariant:** When N coroutines all call `acompare_and_handle` with the same `expected_remaining`, at most **one** can succeed — the first to acquire the lock changes the bucket level, causing all others to see `"stale"`.

## Worked example — abatch_handle

```python
gw = LLMGateway()
gw.set_tier_limits("build", 1000, 0)
gw.register_user("alice", "build")

# Batch of 3 requests totaling 600 tokens — fits
result = await gw.abatch_handle("alice", [("p1", 200), ("p2", 150), ("p3", 250)], now=0)
# result == 3

# Batch of 2 requests totaling 600 tokens — bucket only has 400, doesn't fit
result = await gw.abatch_handle("alice", [("p4", 300), ("p5", 300)], now=0)
# result == -1
# alice's bucket still has 400 tokens (nothing was deducted)
```

## Worked example — acompare_and_handle concurrency

```python
gw = LLMGateway()
gw.set_tier_limits("scale", 1000, 0)
gw.register_user("alice", "scale")

# 100 coroutines all read "1000" and try to CAS
results = await asyncio.gather(*[
    gw.acompare_and_handle("alice", f"p{i}", 1000, 100, 0)
    for i in range(100)
])
ok_count = sum(1 for r in results if r == "ok")
assert ok_count == 1  # exactly ONE wins; the other 99 see "stale"
```

## Constraints

- Hold the lock for the **full** compound operation — do not release between reads and writes.
- `abatch_handle` with an empty `requests` list: deduct 0 tokens, count 0 requests, return 0.
- `amerge_users` with the same user_id for both → return `False`.
- `acompare_and_handle` "stale" is returned BEFORE checking if tokens are sufficient — the CAS check gates everything.

## Common gotchas

1. **TOCTOU inside the lock:** within a single `async with self._get_lock():` block, you cannot be interrupted by another coroutine (asyncio is cooperative). Don't `await` anything inside the compound operation except the lock itself.
2. **`abatch_handle` is all-or-nothing** — do not deduct partially. Compute the total needed first, then commit or abort.
3. **`amerge_users` cap on current_tokens** — after summing `current_tokens`, cap at the new `max_tokens` (which is the sum of both users' `max_tokens`).
4. **`acompare_and_handle` with expected == 0 and rate_limited** — a user with 0 tokens expecting 0 would pass the CAS check but then be rate_limited for any non-zero `tokens_used`. This is correct behavior — return `"rate_limited"` in that case.
5. **Lock per instance** — each `LLMGateway` instance has its own lock. Two different `LLMGateway` instances are fully independent.

## When you're done

```
python3 test_level6.py
```

All tests must pass. Pay special attention to `test_concurrent_compare_and_handle` — it verifies the CAS invariant that only ONE of many concurrent calls with the same `expected_remaining` can succeed.
