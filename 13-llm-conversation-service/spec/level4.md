# Level 4 — Fork, Branch, and Merge

## What you're implementing

Add conversation tree operations to `ConversationService`:

```python
class ConversationService:
    # ... (L1-L3 methods) ...
    def fork_conversation(self, source_id: str, new_id: str) -> bool: ...
    def branch_at_message(self, conv_id: str, msg_index: int, new_id: str) -> bool: ...
    def merge_conversations(self, survivor: str, absorbed: str) -> bool: ...
```

## Mental model

When exploring different approaches with an LLM, you may want to fork a conversation and try two different continuations. Later, you might want to merge two conversation branches back together — keeping the most useful messages from each.

**Forking** creates a new, independent copy of an existing conversation. Changes to either copy don't affect the other. **Branching** is like forking but truncates at a specific message — useful when you want to retry from a particular point. **Merging** combines two conversations, ordered by when each message was originally created.

**Key detail**: each message has an internal monotonic timestamp (`ts`) assigned at add time. This timestamp is used for merge ordering.

## The 3 methods for Level 4

### 1. `fork_conversation(source_id: str, new_id: str) -> bool`

Create an independent deep copy of `source_id` under `new_id`.

| Situation | Returns |
|-----------|---------|
| `source_id` missing | `False` |
| `new_id` already exists | `False` |
| Success | `True`; `new_id` is a fully independent copy |

The fork copies: messages (deep copy), `user_id`, and `max_tokens` limit (if any). Future modifications to either conversation do not affect the other.

### 2. `branch_at_message(conv_id: str, msg_index: int, new_id: str) -> bool`

Create a new conversation from `conv_id`, keeping only messages `[0 .. msg_index]` inclusive.

| Situation | Returns |
|-----------|---------|
| `conv_id` missing | `False` |
| `new_id` already exists | `False` |
| `msg_index < 0` or `msg_index >= len(messages)` | `False` |
| Success | `True`; `new_id` has messages 0 through msg_index |

Like `fork_conversation`, the branch copies `user_id` and `max_tokens`. The branch's `total_tokens` is recomputed from the kept messages.

### 3. `merge_conversations(survivor: str, absorbed: str) -> bool`

Combine two conversations. `absorbed` is deleted; `survivor` keeps its owner and context limit.

| Situation | Returns |
|-----------|---------|
| `survivor` missing | `False` |
| `absorbed` missing | `False` |
| `survivor == absorbed` | `False` |
| Success | `True` |

**Merge semantics:**
- Combine messages from both conversations.
- Sort merged message list by `ts` **ascending** (chronological).
- **Tie-breaking**: if survivor and absorbed have messages with the same `ts` (impossible in practice with a global counter, but handle it anyway), survivor's message comes first.
- If the survivor has a context limit and the merged total exceeds it, drop the oldest messages until within budget.
- `absorbed` is permanently deleted.

## Worked example

```python
s = ConversationService()

# Fork
s.create_conversation("original", "alice")
s.add_message("original", "user", "Hello", 5)
s.add_message("original", "assistant", "Hi!", 8)

s.fork_conversation("original", "fork-1")
assert s.get_message_count("fork-1") == 2

# Independent — changes to fork don't affect original
s.add_message("fork-1", "user", "Taking a different path", 12)
assert s.get_message_count("original") == 2  # unchanged
assert s.get_message_count("fork-1") == 3

# Branch at message index 0 (just the first message)
s.branch_at_message("original", 0, "branch-1")
assert s.get_messages("branch-1") == ["user:Hello"]

# Error cases
assert s.fork_conversation("ghost", "new") == False  # missing source
assert s.fork_conversation("original", "fork-1") == False  # new_id exists
assert s.branch_at_message("original", 99, "branch-2") == False  # invalid index

# Merge
s.create_conversation("conv-a", "bob")
s.create_conversation("conv-b", "bob")
s.add_message("conv-a", "user", "First", 5)    # ts=1
s.add_message("conv-b", "user", "Second", 10)  # ts=2
s.add_message("conv-a", "assistant", "Third", 8)  # ts=3

result = s.merge_conversations("conv-a", "conv-b")
assert result == True
# Messages sorted by ts: First(ts=1), Second(ts=2), Third(ts=3)
assert s.get_messages("conv-a") == ["user:First", "user:Second", "assistant:Third"]
assert s.get_message_count("conv-b") == -1  # absorbed is deleted
```

## Constraints

- `msg_index` is 0-based.
- Messages have an internal monotonic `ts` field incremented globally (not per-conversation).
- Merge with context limit: applies survivor's existing limit (not a new one).
- The deep copy in fork/branch means changes to the copy's messages list don't affect the original.

## Common gotchas

1. **Deep copy the messages list** — a shallow copy means both conversations share the same message dict objects and mutations bleed across.
2. **Branch recomputes total_tokens** from the kept messages (don't copy the source's total).
3. **`merge_conversations` deletes `absorbed`** regardless of context-limit enforcement.
4. **Merge sorts by `ts`, not by insertion order** — in practice `ts` values are monotonically increasing, so the sort is deterministic.
5. **`fork_conversation` copies the context limit** — the fork inherits `max_tokens` from the source.

## When you're done

```bash
python3 test_level4.py
```
