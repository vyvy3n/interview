# Level 3 — Context Window and Truncation

## What you're implementing

You extend `solution(queries)` with two new commands that enforce token budgets — the same FIFO truncation logic that real LLM APIs use to keep conversations within a model's context window. All Level 1 and 2 commands continue to work unchanged.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

The function signature does not change.

## Mental model

Every LLM has a maximum context window (e.g., 200 000 tokens). When a conversation grows too long, the service must drop the oldest messages to make room — this is called **FIFO truncation**. Level 3 adds exactly this mechanism.

`SET_CONTEXT_LIMIT` sets the budget for a conversation and immediately enforces it: if the existing messages already exceed the budget, it evicts the oldest ones until the total fits. `ADD_MESSAGE_WITH_BUDGET` is like `ADD_MESSAGE` but budget-aware: before appending, it drops the oldest messages until the new message fits. If the new message is larger than the entire budget (impossible to fit even in an empty conversation), it is rejected outright with no state change.

Crucially, the original `ADD_MESSAGE` from Level 1 is **not** affected by `SET_CONTEXT_LIMIT` — it always appends unconditionally. This mirrors real systems where some internal paths bypass the budget check.

## The 2 commands for Level 3

### 1. `["SET_CONTEXT_LIMIT", <ts>, <conv_id>, <max_tokens>]`

Set this conversation's token budget to `max_tokens` (positive integer string).

If the current total tokens already exceed `max_tokens`, drop the **oldest messages first** (FIFO) until `total_tokens <= max_tokens`.

Return the **count of messages dropped** as a string. If no messages were dropped, return `"0"`.

| Situation | Return |
|-----------|--------|
| `conv_id` exists | count of messages dropped (0 or more) as string |
| `conv_id` does not exist | `""` |

### 2. `["ADD_MESSAGE_WITH_BUDGET", <ts>, <conv_id>, <role>, <content>, <tokens>]`

Like `ADD_MESSAGE`, but enforces the conversation's context limit (if one has been set via `SET_CONTEXT_LIMIT`).

**Algorithm:**
1. If `new_tokens > max_tokens` → **reject**: return `""`, drop nothing, add nothing.
2. While `total_tokens + new_tokens > max_tokens` → drop the oldest message.
3. Append the new message. Return the count of messages dropped (not counting the one added).

**If no `SET_CONTEXT_LIMIT` has been set** on this conversation, behave exactly like `ADD_MESSAGE` — no truncation, return `"0"`.

| Situation | Return |
|-----------|--------|
| `conv_id` does not exist | `""` |
| `new_tokens > max_tokens` (rejection) | `""` |
| Accepted, no truncation needed | `"0"` |
| Accepted, N messages were dropped | `"N"` as string |

**Important:** `ADD_MESSAGE` (the Level 1 op) does NOT enforce the context limit even after Level 3 — it always appends.

## Worked example — trace through it

```python
queries = [
    ["CREATE_CONVERSATION",       "1",  "chat1", "alice"],
    ["ADD_MESSAGE",               "2",  "chat1", "user",      "First",   "100"],
    ["ADD_MESSAGE",               "3",  "chat1", "assistant", "Second",  "100"],
    ["ADD_MESSAGE",               "4",  "chat1", "user",      "Third",   "100"],
    ["SET_CONTEXT_LIMIT",         "5",  "chat1", "250"],
    ["ADD_MESSAGE_WITH_BUDGET",   "6",  "chat1", "user",      "Fourth",  "100"],
    ["ADD_MESSAGE_WITH_BUDGET",   "7",  "chat1", "user",      "TooBig",  "999"],
    ["GET_MESSAGE_COUNT",         "8",  "chat1"],
    ["ADD_MESSAGE",               "9",  "chat1", "user",      "Raw",     "500"],
    ["GET_MESSAGE_COUNT",         "10", "chat1"],
    ["SET_CONTEXT_LIMIT",         "11", "chat1", "50"],
    ["GET_MESSAGE_COUNT",         "12", "chat1"],
]
```

State trace:

| # | Query | total_tokens | msgs | Output | Notes |
|---|-------|-------------|------|--------|-------|
| 1 | CREATE chat1 | 0 | 0 | `"true"` | |
| 2 | ADD_MESSAGE … 100 | 100 | 1 | `"100"` | First |
| 3 | ADD_MESSAGE … 100 | 200 | 2 | `"200"` | Second |
| 4 | ADD_MESSAGE … 100 | 300 | 3 | `"300"` | Third |
| 5 | SET_CONTEXT_LIMIT 250 | 300→200 | 3→2 | `"1"` | Drop "First" (oldest); now 200 ≤ 250 |
| 6 | ADD_MESSAGE_WITH_BUDGET … 100 | 200+100=300>250 → drop "Second"; 100+100=200 ≤ 250 → add | 200 | 2 | `"1"` | 1 dropped |
| 7 | ADD_MESSAGE_WITH_BUDGET … 999 | 999 > 250 (max) → reject | 200 | 2 | `""` | Rejection; no state change |
| 8 | GET_MESSAGE_COUNT | — | 2 | `"2"` | |
| 9 | ADD_MESSAGE … 500 | 200+500=700 | 3 | `"700"` | L1 op ignores limit |
| 10 | GET_MESSAGE_COUNT | — | 3 | `"3"` | |
| 11 | SET_CONTEXT_LIMIT 50 | 700>50 → drop until ≤50; all 3 messages (100+500+100=700) get dropped | 0 | 0 | `"3"` | Dropped all 3 |
| 12 | GET_MESSAGE_COUNT | — | 0 | `"0"` | |

Final return value:

```python
["true", "100", "200", "300", "1", "1", "", "2", "700", "3", "3", "0"]
```

## Constraints

- All Level 1 and 2 constraints still apply.
- `<max_tokens>` is a positive integer string.
- `SET_CONTEXT_LIMIT` can be called multiple times on the same conversation — each call overwrites the previous limit and re-enforces immediately.
- A conversation without a `SET_CONTEXT_LIMIT` has no budget; `ADD_MESSAGE_WITH_BUDGET` on it behaves like `ADD_MESSAGE` (no truncation, returns `"0"`).
- Dropping happens FIFO — always the oldest message first.
- Up to `10^5` queries; use a `collections.deque` for O(1) popleft when dropping.

## Common gotchas

1. **Rejection vs. truncation** — if `new_tokens > max_tokens`, reject the whole operation (return `""`, change nothing). Only truncate if the message could fit in an empty conversation but current messages are in the way.
2. **`ADD_MESSAGE` bypasses the budget** — the Level 1 op always appends, even if it blows past the limit. Only `ADD_MESSAGE_WITH_BUDGET` enforces the limit.
3. **`SET_CONTEXT_LIMIT` drops messages immediately** — it is not a soft cap. If the existing conversation is already over budget, it starts dropping from the oldest right away.
4. **Return value is count of dropped messages, not count of remaining messages** — `SET_CONTEXT_LIMIT` returns how many it evicted; `ADD_MESSAGE_WITH_BUDGET` returns how many it evicted to make room (excluding the new message itself).
5. **Multiple calls to `SET_CONTEXT_LIMIT` overwrite** — the second call uses the new limit, drops again if needed, and any previously stored limit is gone.

## When you're done

```
cd 08-llm-conversation-manager
python3 test_level3.py
```

All Level 3 tests must pass.
