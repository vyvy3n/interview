# Level 2 — User-level Activity Reports

## What you're implementing

Add three query methods to `ConversationService`:

```python
class ConversationService:
    # ... (L1 methods) ...
    def list_user_conversations(self, user_id: str) -> list[str]: ...
    def top_k_active(self, k: int) -> list[tuple[str, int]]: ...
    def get_user_total_tokens(self, user_id: str) -> int: ...
```

## Mental model

The service now supports operational dashboards and user-facing features. A user wants to see all their active conversations sorted by name. An admin wants to see which chats are growing fastest (most messages). A billing system needs to know how many tokens a user has consumed across all their conversations.

These methods are **read-only** — they query existing state without modifying it.

## The 3 methods for Level 2

### 1. `list_user_conversations(user_id: str) -> list[str]`

Return all conversation IDs owned by `user_id`, sorted alphabetically.

| Situation | Returns |
|-----------|---------|
| User has conversations | list of `conv_id` strings, sorted A→Z |
| User has no conversations (or user doesn't exist) | `[]` |

### 2. `top_k_active(k: int) -> list[tuple[str, int]]`

Return the top `k` conversations by message count.

| Situation | Returns |
|-----------|---------|
| Service has >= k conversations | list of `(conv_id, message_count)` tuples, length k |
| Service has < k conversations | all conversations (fewer than k) |
| No conversations | `[]` |

**Ordering rules:**
1. Primary: message count **descending** (most messages first).
2. Secondary (ties): `conv_id` **ascending** alphabetically.

### 3. `get_user_total_tokens(user_id: str) -> int`

Return the sum of `total_tokens` across all conversations owned by `user_id`.

| Situation | Returns |
|-----------|---------|
| User has >= 1 conversation | sum of cumulative tokens (int, >= 0) |
| User has no conversations | `-1` |

Note: if the user exists but all their conversations are empty (0 tokens), this returns `0` — not `-1`. Only return `-1` when the user has no conversations at all.

## Worked example

```python
s = ConversationService()
s.create_conversation("alice-1", "alice")
s.create_conversation("alice-2", "alice")
s.create_conversation("bob-1", "bob")

s.add_message("alice-1", "user", "Hi", 10)
s.add_message("alice-1", "assistant", "Hello", 15)
s.add_message("alice-2", "user", "Hey", 5)
s.add_message("bob-1", "user", "Greetings", 20)
s.add_message("bob-1", "assistant", "Hi back", 12)
s.add_message("bob-1", "user", "How are you?", 8)

# list_user_conversations — sorted alphabetically
assert s.list_user_conversations("alice") == ["alice-1", "alice-2"]
assert s.list_user_conversations("bob") == ["bob-1"]
assert s.list_user_conversations("carol") == []

# top_k_active — by message count desc, ties break by conv_id asc
# bob-1: 3 msgs, alice-1: 2 msgs, alice-2: 1 msg
assert s.top_k_active(2) == [("bob-1", 3), ("alice-1", 2)]
assert s.top_k_active(10) == [("bob-1", 3), ("alice-1", 2), ("alice-2", 1)]

# get_user_total_tokens
assert s.get_user_total_tokens("alice") == 30   # (10+15) + 5
assert s.get_user_total_tokens("bob") == 40     # 20+12+8
assert s.get_user_total_tokens("carol") == -1   # no convs
```

## Tie-breaking in `top_k_active`

```python
s = ConversationService()
s.create_conversation("zebra", "u1")
s.create_conversation("apple", "u1")
s.create_conversation("mango", "u1")
# All have 0 messages — tied; alphabetical breaks the tie
assert s.top_k_active(3) == [("apple", 0), ("mango", 0), ("zebra", 0)]
```

## Constraints

- `k` >= 1.
- Up to 10,000 conversations per test.
- A conversation with 0 messages counts as a valid conversation (just has 0 message count).
- `get_user_total_tokens` returns `-1` only when the user owns ZERO conversations.

## Common gotchas

1. **`list_user_conversations` is purely alphabetical** — not by creation time or activity.
2. **`top_k_active` returns fewer than k items** if there are fewer conversations — do not pad with dummy entries.
3. **`get_user_total_tokens` returns `-1` for unknown users**, but `0` for users with conversations that happen to have no messages (because 0 is still a valid token sum).
4. **Tie-breaking in `top_k_active`** uses conv_id alphabetically ascending — "apple" before "zebra" even if zebra was created first.

## When you're done

```bash
python3 test_level2.py
```
