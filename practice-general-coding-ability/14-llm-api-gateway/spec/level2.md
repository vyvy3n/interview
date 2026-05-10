# Level 2 — Usage Tracking + Reports

## What you're implementing

Add four reporting methods that answer questions about usage across the entire gateway. These are the kinds of dashboards an API ops team would run.

```python
def top_k_users_by_tokens(self, k: int) -> list[tuple[str, int]]: ...
def top_k_users_by_requests(self, k: int) -> list[tuple[str, int]]: ...
def get_users_in_tier(self, tier: str) -> list[str]: ...
def get_total_requests(self) -> int: ...
```

**All Level 1 methods still work unchanged.**

## Mental model

You now have a dashboard view over all users. Product managers want to know the heaviest consumers of the API (by tokens and by request count). The billing team wants to know which users are on which pricing tier. The ops team wants a single global request counter.

## The 4 methods

### 1. `top_k_users_by_tokens(k: int) -> list[tuple[str, int]]`

Return the top `k` users ranked by **total tokens used**, descending.

- Each entry is `(user_id, total_tokens)`.
- **Ties** are broken by `user_id` alphabetical order, ascending.
- If there are fewer than `k` users, return all users.
- If `k == 0`, return `[]`.

### 2. `top_k_users_by_requests(k: int) -> list[tuple[str, int]]`

Return the top `k` users ranked by **total request count**, descending.

- Each entry is `(user_id, request_count)`.
- **Ties** broken by `user_id` alphabetical order, ascending.
- Same edge-case rules as above.

### 3. `get_users_in_tier(tier: str) -> list[str]`

Return a list of all `user_id`s currently in the given tier, sorted alphabetically.

- If no users in that tier, return `[]`.
- The tier argument is an exact match — no prefix or pattern matching.

### 4. `get_total_requests() -> int`

Return the total number of accepted requests across **all** users.

- Returns `0` if no requests have been made yet.

## Worked example

```python
gw = LLMGateway()
gw.register_user("alice", "free")
gw.register_user("bob",   "build")
gw.register_user("carol", "free")
gw.register_user("dave",  "scale")

gw.handle_request("alice", "p1", 300)
gw.handle_request("alice", "p2", 200)
gw.handle_request("bob",   "p3", 500)
gw.handle_request("carol", "p4", 100)
gw.handle_request("carol", "p5", 200)

# alice: 2 req, 500 tokens
# bob:   1 req, 500 tokens
# carol: 2 req, 300 tokens
# dave:  0 req, 0 tokens

gw.top_k_users_by_tokens(2)
# [("alice", 500), ("bob", 500)]   ← tie broken by user_id asc: alice < bob

gw.top_k_users_by_requests(3)
# [("alice", 2), ("carol", 2), ("bob", 1)]   ← tie broken by user_id: alice < carol

gw.get_users_in_tier("free")
# ["alice", "carol"]   ← alphabetical

gw.get_total_requests()
# 5
```

## Constraints

- All Level 1 constraints apply.
- `k` is a non-negative integer.
- Rankings reflect the state at the moment of the call.

## Common gotchas

1. **Tie-breaking is mandatory** — two users with equal token counts must appear in alphabetical order. Don't rely on dictionary insertion order.
2. **`top_k` with k > number of users** — return all users, just fewer than `k` entries.
3. **Users with 0 tokens/requests are included** — they rank last but are not excluded.
4. **`get_total_requests` sums across all users** — it is NOT the max or the most recent; it's the sum.

## When you're done

```
python3 test_level2.py
```

All tests must pass before moving to Level 3.
