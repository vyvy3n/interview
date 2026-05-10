# Level 1 — Conversations and Messages

## What you're implementing

You write **one Python function**:

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

- **Input:** a list of "queries". Each query is a list of strings — the first string is a command name (`"CREATE_CONVERSATION"`, `"ADD_MESSAGE"`, or `"GET_MESSAGE_COUNT"`); the rest are arguments.
- **Output:** a list of strings, **exactly one string per query**, in the same order. Each string is the result of running that query against your chatbot state.

## Mental model

Imagine your function is a tiny multi-user chatbot service. Users open conversations, then take turns sending messages. Internally, each conversation is a named slot that belongs to one user and holds an ordered list of messages. Each message records its role (`"user"` or `"assistant"`), its text content, how many tokens it consumed, and the timestamp at which it was added.

You are not building a web server or REPL — just a pure function that loops through `queries`, mutates an internal dict of conversations, and emits one response string per query.

The token count is a bookkeeping field for now; Level 3 will use it to enforce a context-window budget. Storing it correctly from the start will save you a refactor later.

## The 3 commands for Level 1

### 1. `["CREATE_CONVERSATION", <ts>, <conv_id>, <user_id>]`

Open a new conversation owned by `user_id` with an empty message list.

| Situation | Return |
|-----------|--------|
| `conv_id` is new | `"true"` |
| `conv_id` already exists | `"false"` |

### 2. `["ADD_MESSAGE", <ts>, <conv_id>, <role>, <content>, <tokens>]`

Append a message to `conv_id`'s message list. The message records:
- `role` — the string passed in (no validation needed)
- `content` — the string passed in
- `tokens` — positive integer (passed as a string; convert with `int()`)
- `ts` — the timestamp of this query (useful later for merge ordering)

Returns the conversation's **total token count** (sum of all messages' tokens) after addition.

| Situation | Return |
|-----------|--------|
| `conv_id` exists | total token count as a string, e.g. `"350"` |
| `conv_id` does not exist | `""` (empty string) |

### 3. `["GET_MESSAGE_COUNT", <ts>, <conv_id>]`

Return the number of messages currently in the conversation.

| Situation | Return |
|-----------|--------|
| `conv_id` exists | message count as a string, e.g. `"4"` |
| `conv_id` does not exist | `""` (empty string) |

## Worked example — trace through it

```python
queries = [
    ["CREATE_CONVERSATION", "1",  "conv_a", "alice"],
    ["CREATE_CONVERSATION", "2",  "conv_a", "alice"],  # duplicate
    ["CREATE_CONVERSATION", "3",  "conv_b", "bob"],
    ["ADD_MESSAGE",         "4",  "conv_a", "user",      "Hello!",     "10"],
    ["ADD_MESSAGE",         "5",  "conv_a", "assistant", "Hi there!",  "15"],
    ["ADD_MESSAGE",         "6",  "conv_z", "user",      "Nobody?",    "5"],   # missing
    ["GET_MESSAGE_COUNT",   "7",  "conv_a"],
    ["GET_MESSAGE_COUNT",   "8",  "conv_b"],
    ["ADD_MESSAGE",         "9",  "conv_a", "user",      "One more.",  "20"],
    ["GET_MESSAGE_COUNT",   "10", "conv_z"],                                   # missing
]
```

Step by step:

| # | Query | State after | Output |
|---|-------|-------------|--------|
| 1 | `CREATE_CONVERSATION conv_a alice` | `{conv_a: owner=alice, msgs=[]}` | `"true"` |
| 2 | `CREATE_CONVERSATION conv_a alice` (dup) | unchanged | `"false"` |
| 3 | `CREATE_CONVERSATION conv_b bob` | `{conv_a: …, conv_b: owner=bob, msgs=[]}` | `"true"` |
| 4 | `ADD_MESSAGE conv_a user "Hello!" 10` | conv_a: msgs=[{user,10}], total_tokens=10 | `"10"` |
| 5 | `ADD_MESSAGE conv_a assistant "Hi there!" 15` | conv_a: msgs=[…,{asst,15}], total_tokens=25 | `"25"` |
| 6 | `ADD_MESSAGE conv_z …` (missing conv) | unchanged | `""` |
| 7 | `GET_MESSAGE_COUNT conv_a` | — | `"2"` |
| 8 | `GET_MESSAGE_COUNT conv_b` | — | `"0"` |
| 9 | `ADD_MESSAGE conv_a user "One more." 20` | conv_a total_tokens=45 | `"45"` |
| 10 | `GET_MESSAGE_COUNT conv_z` (missing) | — | `""` |

Final return value:

```python
["true", "false", "true", "10", "25", "", "2", "0", "45", ""]
```

## Constraints

- All `<ts>` values are positive integer **strings**, strictly increasing across queries.
- All `<tokens>` values are positive integer **strings** (`> 0`).
- `<conv_id>` and `<user_id>` are any non-empty strings.
- `<role>` is typically `"user"` or `"assistant"` — but do not validate it; accept anything.
- Up to `10^5` queries — aim for O(1) per operation (use dicts, not linear scans).
- Strings everywhere: convert with `int(tokens)` for arithmetic, `str(n)` to return.

## Common gotchas

1. **Total tokens, not per-message tokens** — `ADD_MESSAGE` returns the running sum across ALL messages in the conversation, not just the tokens of the message just added.
2. **Empty conversation returns `"0"` for count, not `""`** — `GET_MESSAGE_COUNT` on an existing but empty conversation returns `"0"`, not `""`. Only a missing `conv_id` returns `""`.
3. **Duplicate CREATE returns `"false"`, not `""`** — the distinction matters; `""` is reserved for "operation failed due to missing resource".
4. **Store `ts` on each message** — you will need it at Level 4 to merge two conversations by message timestamp. Adding it now costs nothing.
5. **One `conv_id` namespace** — all conversations live in a single global dict. Two different users can own conversations with different IDs; they cannot share an ID.

## When you're done

```
cd 08-llm-conversation-manager
python3 test_level1.py
```

All tests must pass before Level 2 is revealed.
