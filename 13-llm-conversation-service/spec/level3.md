# Level 3 — Context Window + Truncation

## What you're implementing

Add context-window management to `ConversationService`:

```python
class ConversationService:
    # ... (L1-L2 methods) ...
    def set_context_limit(self, conv_id: str, max_tokens: int) -> int: ...
    def add_message_with_budget(self, conv_id: str, role: str, content: str, tokens: int) -> int: ...
    def summarize_to_budget(self, conv_id: str, max_tokens: int) -> int: ...
```

## Mental model

LLM APIs have fixed context windows. When a conversation grows past the limit, you must decide what to drop. The simplest strategy: evict the oldest messages first ("sliding window"). This level introduces that mechanism.

**Critical**: The Level 1 `add_message` does **NOT** enforce any context limit — it always appends unconditionally. Use `add_message_with_budget` when you want enforcement.

## The 3 methods for Level 3

### 1. `set_context_limit(conv_id: str, max_tokens: int) -> int`

Set the conversation's token budget. If the current total already exceeds `max_tokens`, immediately drop the oldest messages until within budget.

| Situation | Returns |
|-----------|---------|
| Conv exists | count of messages dropped (0 if already within budget) |
| Conv does not exist | `-1` |

After this call, the conversation has `max_tokens` stored as its limit. Future calls to `add_message_with_budget` will respect it.

### 2. `add_message_with_budget(conv_id: str, role: str, content: str, tokens: int) -> int`

Add a message while enforcing the context limit (if set).

| Situation | Returns |
|-----------|---------|
| Conv does not exist | `-1` |
| No limit set | Append unconditionally; return `0` (no drops) |
| Limit set AND `tokens > max_tokens` | **Reject** — no state change; return `-1` |
| Limit set AND message fits (after possibly dropping old messages) | Drop oldest until room, then append; return count of drops |

**Drop policy**: drop the **oldest** messages one at a time until `(current_total + new_tokens) <= max_tokens`, then append the new message.

**Rejection rule**: if `new_tokens > max_tokens` (the message alone cannot fit), reject entirely — do not modify the conversation at all.

### 3. `summarize_to_budget(conv_id: str, max_tokens: int) -> int`

Immediately drop oldest messages until `total_tokens <= max_tokens`.

| Situation | Returns |
|-----------|---------|
| Conv exists | count of messages **remaining** (kept) |
| Conv does not exist | `-1` |

This is a one-shot trim — it does not set a persistent limit. Use it to compress a conversation before sending it to an LLM.

## Worked example

```python
s = ConversationService()
s.create_conversation("c1", "alice")

# Load up some messages: 5+10+8+12 = 35 tokens total
s.add_message("c1", "user", "Hello", 5)
s.add_message("c1", "assistant", "Hi there!", 10)
s.add_message("c1", "user", "How are you?", 8)
s.add_message("c1", "assistant", "I'm great!", 12)

# Set context limit — current total 35 > 30, so drop 1 oldest
dropped = s.set_context_limit("c1", 30)
assert dropped == 1
# Now 3 messages remain: 10+8+12 = 30
assert s.get_message_count("c1") == 3

# add_message_with_budget — no drops needed (30 + 7 = 37 > 30; drops 1)
# Wait, 30 is the limit. 30 + 7 = 37 > 30. Drop oldest (10 tokens). Now 20 + 7 = 27 <= 30. Append.
drops = s.add_message_with_budget("c1", "user", "More!", 7)
assert drops == 1
# Messages: [8-token, 12-token, 7-token] = 27 tokens

# Rejection: message exceeds max_tokens
result = s.add_message_with_budget("c1", "user", "A very long message", 50)
assert result == -1  # rejected; state unchanged
assert s.get_message_count("c1") == 3  # still 3

# summarize_to_budget — trim to 15 tokens
kept = s.summarize_to_budget("c1", 15)
# 27 > 15: drop 8-token msg -> 19 > 15: drop 12-token msg -> 7 <= 15. Keep [7-token msg].
assert kept == 1

# Missing conversation
assert s.set_context_limit("ghost", 100) == -1
assert s.add_message_with_budget("ghost", "user", "Hi", 5) == -1
assert s.summarize_to_budget("ghost", 50) == -1
```

## Constraints

- `max_tokens` is a positive integer.
- `tokens` per message is a positive integer.
- The L1 `add_message` NEVER enforces limits — use `add_message_with_budget` for enforcement.
- `summarize_to_budget` does NOT change the conversation's stored `max_tokens` limit.

## Common gotchas

1. **`add_message` (L1) still ignores limits** even after `set_context_limit` is called.
2. **Rejection vs. truncation**: reject only when `new_tokens > max_tokens` (message alone won't fit). Otherwise, drop old messages to make room.
3. **Return values differ**: `add_message_with_budget` returns drops (or -1), while `summarize_to_budget` returns the kept count.
4. **`set_context_limit` stores the limit persistently** — future `add_message_with_budget` calls will see it.
5. **`summarize_to_budget` is one-shot** — it doesn't update the stored limit.

## When you're done

```bash
python3 test_level3.py
```
