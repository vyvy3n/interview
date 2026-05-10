# Level 3 — Token-Bucket Rate Limiting (Lazy Refill)

## What you're implementing

Add per-user token-bucket rate limiting with lazy time-based refill. Each user has their own bucket. A new time-parameterized request handler checks the bucket before accepting.

```python
def set_tier_limits(self, tier: str, max_tokens: int, refill_per_sec: int) -> bool: ...
def handle_request_at(self, user_id: str, prompt: str, tokens_used: int, now: int) -> str: ...
def get_remaining_tokens_at(self, user_id: str, now: int) -> int: ...
def update_user_tier(self, user_id: str, new_tier: str, now: int) -> bool: ...
```

**All Level 1–2 methods still work unchanged.** `handle_request` (no timestamp) continues to work and does NOT enforce rate limits — only `handle_request_at` does.

## Mental model

Think of a token bucket as a bucket that slowly fills with water. You draw water (tokens) when you make a request; the bucket refills over time. If the bucket is empty, your request is rejected. This is Anthropic's actual rate-limiting strategy.

The clever implementation trick: **lazy refill**. Instead of a background timer topping up the bucket every second, you compute the refill *on demand* — only when a user's bucket is accessed. You look at how much time has passed since the last touch, multiply by the refill rate, and add that many tokens (capped at the maximum). This produces exactly the same result with no background work.

## Bucket fields (per user)

Each user tracks these fields (in addition to L1 data):

| Field | Meaning | Initialized to |
|-------|---------|----------------|
| `max_tokens` | bucket capacity | tier's max (or 1,000,000 if tier has no limits set) |
| `current_tokens` | tokens currently available | `max_tokens` (starts full) |
| `refill_rate` | tokens added per second | tier's rate (or 0 if no limits set) |
| `last_action_ts` | timestamp of last refill | `0` |

## Tier defaults

If no limits have been set for a tier at the time a user registers, use defaults:
- `max_tokens = 1_000_000`
- `refill_rate = 0` (no refill)

`set_tier_limits` is applied **retroactively** to existing users in that tier.

## The 4 methods

### 1. `set_tier_limits(tier: str, max_tokens: int, refill_per_sec: int) -> bool`

Set a tier's bucket capacity and refill rate. Always returns `True`.

Also immediately updates **all existing users** in that tier:
- Their `max_tokens` and `refill_rate` are updated.
- Their `current_tokens` is capped at the new `max_tokens` if it would exceed it.

### 2. `handle_request_at(user_id, prompt, tokens_used, now) -> str`

Like `handle_request` but with explicit integer timestamp and rate limiting.

**Procedure:**
1. If user missing → return `""`
2. **Refill:** `current_tokens = min(max_tokens, current_tokens + refill_rate * (now - last_action_ts))`, then `last_action_ts = now`
3. If `current_tokens >= tokens_used`: deduct tokens, increment request_count and total_tokens_used → return `"ok"`
4. If `current_tokens < tokens_used`: return `"rate_limited"` (nothing is deducted, request NOT counted)

### 3. `get_remaining_tokens_at(user_id, now) -> int`

Trigger refill (same formula as above), then return `current_tokens`.

Returns `-1` if user missing.

### 4. `update_user_tier(user_id, new_tier, now) -> bool`

Move user to a new tier, preserving bucket state.

**Procedure:**
1. If user missing → return `False`
2. Refill using current rate at `now`
3. Switch to `new_tier`'s limits (`max_tokens`, `refill_rate`)
4. Cap `current_tokens` at new `max_tokens`
5. Return `True`

## Refill semantics (the heart of Level 3)

```
elapsed = now - last_action_ts
current_tokens = min(max_tokens, current_tokens + refill_rate * elapsed)
last_action_ts = now
```

- All arithmetic is **integer** — no floats.
- Keys with `refill_rate == 0` never refill.
- Bucket cannot exceed `max_tokens`.
- Bucket can never go below 0 (rate_limited requests leave it unchanged).

## Worked example

```python
gw = LLMGateway()
gw.set_tier_limits("free", max_tokens=1000, refill_per_sec=100)
gw.register_user("alice", "free")
# alice: max=1000, current=1000, rate=100, last_ts=0

gw.handle_request_at("alice", "hello", 600, now=0)
# refill: elapsed=0, +0 → 1000. Deduct 600. current=400. return "ok"

gw.get_remaining_tokens_at("alice", now=2)
# refill: elapsed=2, +200 → 600. return 600

gw.handle_request_at("alice", "big prompt", 700, now=5)
# refill: elapsed=3, +300 → 900. Deduct 700. current=200. return "ok"

gw.handle_request_at("alice", "another", 500, now=5)
# refill: elapsed=0, +0 → 200. 200 < 500 → return "rate_limited"

gw.get_remaining_tokens_at("alice", now=10)
# refill: elapsed=5, +500 → 700. return 700

gw.update_user_tier("alice", "scale", now=10)
# refill first (already refilled above; elapsed=0, +0 → 700)
# switch to "scale" tier limits (if not set, defaults: max=1_000_000, rate=0)
# current_tokens = min(700, 1_000_000) = 700
```

## Constraints

- Timestamps are non-negative integers; they can be equal (elapsed = 0, no refill).
- Timestamps should be non-decreasing across calls for the same user (not enforced, but assume it).
- `tokens_used` is a positive integer.

## Common gotchas

1. **Refill is lazy** — only the specific user being accessed is refilled, not all users.
2. **`handle_request` (no timestamp) still works and skips rate limiting entirely** — don't break it.
3. **Cap at `max_tokens`** — `current_tokens + refill * elapsed` can exceed `max_tokens`. Always apply `min(max_tokens, ...)`.
4. **Rate-limited requests do NOT count** — `request_count` and `total_tokens_used` are only incremented on `"ok"`.
5. **`set_tier_limits` updates existing users** — existing users in the tier get new limits immediately (cap `current_tokens`).
6. **`update_user_tier` refills BEFORE switching limits** — use the OLD rate for the refill step.

## When you're done

```
python3 test_level3.py
```

All tests must pass before moving to Level 4.
