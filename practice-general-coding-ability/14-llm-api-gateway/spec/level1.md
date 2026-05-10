# Level 1 — Basic Request Lifecycle

## What you're implementing

A minimal gateway that registers users and processes requests. This is the foundation every later level builds on.

```python
class LLMGateway:
    def register_user(self, user_id: str, tier: str) -> bool: ...
    def handle_request(self, user_id: str, prompt: str, tokens_used: int) -> str: ...
    def get_request_count(self, user_id: str) -> int: ...
    def get_total_tokens_used(self, user_id: str) -> int: ...
```

## Mental model

Think of this as a front-desk receptionist. Before any LLM call can happen, the user must have an account (`register_user`). Once registered, each call to `handle_request` is logged: how many tokens it consumed and whether it went through. The gateway needs to be able to answer: "How many requests has this user made?" and "How many tokens total have they burned?"

At this level there is **no rate limiting** — every registered user's request is accepted. Rate limiting comes in Level 3.

## The 4 methods

### 1. `register_user(user_id: str, tier: str) -> bool`

Create an account for `user_id` with the given `tier` string (e.g., `"free"`, `"build"`, `"scale"`).

| Situation | Return |
|-----------|--------|
| `user_id` is new | `True` |
| `user_id` already exists | `False` |

Do **not** validate the tier string — accept any string.

### 2. `handle_request(user_id: str, prompt: str, tokens_used: int) -> str`

Process a request. At this level, every registered user's request is accepted.

| Situation | Return |
|-----------|--------|
| `user_id` registered | `"ok"` — increments request count and total tokens |
| `user_id` not registered | `""` (empty string) |

The `prompt` parameter is accepted but ignored at this level (used in later levels).

### 3. `get_request_count(user_id: str) -> int`

Return the total number of successful requests (calls that returned `"ok"`) by this user.

| Situation | Return |
|-----------|--------|
| `user_id` registered | count (0 if no requests yet) |
| `user_id` missing | `-1` |

### 4. `get_total_tokens_used(user_id: str) -> int`

Return the cumulative tokens consumed across all accepted requests.

| Situation | Return |
|-----------|--------|
| `user_id` registered | sum of `tokens_used` over all accepted requests |
| `user_id` missing | `-1` |

## Worked example

```python
gw = LLMGateway()

gw.register_user("alice", "free")   # True
gw.register_user("alice", "build")  # False — already exists

gw.handle_request("alice", "hello world", 50)   # "ok"
gw.handle_request("alice", "what is 2+2", 30)   # "ok"
gw.handle_request("bob",   "hi", 10)             # "" — bob not registered

gw.get_request_count("alice")       # 2
gw.get_total_tokens_used("alice")   # 80
gw.get_request_count("bob")         # -1
gw.get_total_tokens_used("bob")     # -1
```

## Constraints

- `user_id` and `tier` are non-empty strings.
- `tokens_used` is a positive integer.
- No rate limiting at this level — all registered users' requests are accepted.

## Common gotchas

1. **Double registration returns False** — registering the same `user_id` twice must not overwrite the existing user and must return `False`.
2. **Unregistered user returns "" not "error"** — the sentinel for a missing user is the empty string `""` for string-returning methods and `-1` for int-returning methods.
3. **Only accepted requests count** — the request count and token total only include requests that returned `"ok"`.

## When you're done

```
python3 test_level1.py
```

All tests must pass before moving to Level 2.
