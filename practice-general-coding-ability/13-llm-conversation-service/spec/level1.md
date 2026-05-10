# Level 1 — Basic Conversation Lifecycle

## What you're implementing

You write a **class** `ConversationService` in `solution.py`:

```python
class ConversationService:
    def create_conversation(self, conv_id: str, user_id: str) -> bool: ...
    def add_message(self, conv_id: str, role: str, content: str, tokens: int) -> int: ...
    def get_messages(self, conv_id: str) -> list[str]: ...
    def get_message_count(self, conv_id: str) -> int: ...
    def delete_conversation(self, conv_id: str) -> bool: ...
```

Each test creates a fresh `ConversationService()` instance and calls these five methods.

## Mental model

Think of `ConversationService` as the backend storage layer for a chatbot product. When someone calls `create_conversation("conv-1", "alice")`, you register a new empty conversation owned by Alice. As the chat proceeds, `add_message` appends each turn (alternating "user" and "assistant") and tracks the cumulative token count consumed by this conversation. `get_messages` retrieves the full history in order. `delete_conversation` cleans up when the session ends.

At this level everything is single-threaded and synchronous. No concurrency, no token budgets, no forking — just the five primitive operations.

## The 5 methods for Level 1

### 1. `create_conversation(conv_id: str, user_id: str) -> bool`

Register a new conversation owned by `user_id` with no messages.

| Situation | Returns |
|-----------|---------|
| `conv_id` is new | `True` |
| `conv_id` already exists | `False` (do NOT reset existing conv) |

### 2. `add_message(conv_id: str, role: str, content: str, tokens: int) -> int`

Append a message to the conversation.

| Situation | Returns |
|-----------|---------|
| Conv exists | cumulative token total (int) after appending |
| Conv does not exist | `-1` (no side effect) |

- `role` is `"user"` or `"assistant"` — do not validate.
- `tokens` is a positive integer representing the message's token cost.
- Return value is the **sum** of all message tokens in this conversation so far.

### 3. `get_messages(conv_id: str) -> list[str]`

Return the conversation history as formatted strings.

| Situation | Returns |
|-----------|---------|
| Conv exists | list of `"role:content"` strings in chronological order |
| Conv does not exist | `[]` |

Example format: `["user:Hello!", "assistant:Hi there!"]`

### 4. `get_message_count(conv_id: str) -> int`

Return the number of messages in the conversation.

| Situation | Returns |
|-----------|---------|
| Conv exists | number of messages (int, >= 0) |
| Conv does not exist | `-1` |

### 5. `delete_conversation(conv_id: str) -> bool`

Remove a conversation permanently.

| Situation | Returns |
|-----------|---------|
| Conv exists | `True`; conversation removed |
| Conv does not exist | `False` |

## Worked example

```python
s = ConversationService()

# Create conversations
assert s.create_conversation("conv-1", "alice") == True
assert s.create_conversation("conv-2", "bob") == True
assert s.create_conversation("conv-1", "alice") == False  # duplicate

# Add messages — returns cumulative token count
assert s.add_message("conv-1", "user", "Hello!", 5) == 5
assert s.add_message("conv-1", "assistant", "Hi there!", 10) == 15
assert s.add_message("conv-1", "user", "How are you?", 8) == 23

# Missing conversation
assert s.add_message("ghost", "user", "Hello", 5) == -1

# Get message history (formatted "role:content")
msgs = s.get_messages("conv-1")
assert msgs == ["user:Hello!", "assistant:Hi there!", "user:How are you?"]
assert s.get_messages("ghost") == []

# Message count
assert s.get_message_count("conv-1") == 3
assert s.get_message_count("ghost") == -1

# Delete
assert s.delete_conversation("conv-1") == True
assert s.delete_conversation("conv-1") == False  # already gone
assert s.get_messages("conv-1") == []
```

## Constraints

- `conv_id` and `user_id` are any non-empty strings.
- `tokens` is a positive integer.
- Up to 10,000 conversations per test.
- No concurrency at this level — all calls are sequential.

## Common gotchas

1. **`create_conversation` on an existing id must NOT reset it** — return `False` and leave the existing conversation untouched.
2. **`get_message_count` returns `-1`, not `0`** for a missing conversation — do not confuse an empty conversation with a missing one.
3. **`add_message` returns the cumulative total**, not just the tokens for the new message.
4. **`get_messages` format is `"role:content"`** (colon separator, no spaces around the colon).
5. **`delete_conversation` called twice** — second call returns `False`, not an error.

## When you're done

```bash
python3 test_level1.py
```

All tests in `TestLevel1` must pass before moving to Level 2.
