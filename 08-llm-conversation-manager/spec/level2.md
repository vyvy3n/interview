# Level 2 — Activity Reports

## What you're implementing

You extend `solution(queries)` with two reporting commands. All Level 1 commands continue to work unchanged.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

The function signature does not change.

## Mental model

In a real LLM service, operations teams need dashboards: which conversations are busiest, which users have the most active threads? Level 2 adds two read-only reporting commands that answer exactly those questions.

These operations scan your existing conversation state — no new state fields are needed. But the sorting rules have edge cases that trip up fast implementations. A conversation with zero messages still appears in `TOP_K_ACTIVE` (it exists). A user who has never created a conversation returns `""` from `LIST_USER_CONVERSATIONS`, but a user whose conversations all have zero messages still gets a list.

## The 2 commands for Level 2

### 1. `["TOP_K_ACTIVE", <ts>, <k>]`

Return the top-`k` conversations by **message count**, descending.

- Ties broken by `conv_id` alphabetically **ascending**.
- Include conversations with zero messages.
- If fewer than `k` conversations exist, return all of them.
- Returns `""` if **no conversations exist at all** (the system is empty).

**Format:** `"conv1(50), conv2(30), conv3(0)"`

| Situation | Return |
|-----------|--------|
| At least one conversation exists | formatted string of up to k entries |
| No conversations exist | `""` |

### 2. `["LIST_USER_CONVERSATIONS", <ts>, <user_id>]`

Return all `conv_id`s owned by `user_id`, sorted alphabetically **ascending**.

- Returns `""` if the user has no conversations, or if `user_id` has never been the owner of any conversation.

**Format:** `"conv_a, conv_b, conv_c"`

| Situation | Return |
|-----------|--------|
| User has one or more conversations | space-separated list |
| User has no conversations / unknown user | `""` |

## Worked example — trace through it

```python
queries = [
    ["CREATE_CONVERSATION",    "1",  "conv_b", "alice"],
    ["CREATE_CONVERSATION",    "2",  "conv_a", "alice"],
    ["CREATE_CONVERSATION",    "3",  "conv_c", "bob"],
    ["ADD_MESSAGE",            "4",  "conv_a", "user",      "Hi",   "5"],
    ["ADD_MESSAGE",            "5",  "conv_a", "assistant", "Hey",  "8"],
    ["ADD_MESSAGE",            "6",  "conv_b", "user",      "Yo",   "3"],
    ["TOP_K_ACTIVE",           "7",  "2"],
    ["TOP_K_ACTIVE",           "8",  "5"],
    ["LIST_USER_CONVERSATIONS","9",  "alice"],
    ["LIST_USER_CONVERSATIONS","10", "bob"],
    ["LIST_USER_CONVERSATIONS","11", "carol"],
]
```

State at query 7: conv_a has 2 msgs, conv_b has 1 msg, conv_c has 0 msgs.

| # | Query | Output | Explanation |
|---|-------|--------|-------------|
| 1–6 | (setup) | — | L1 ops |
| 7 | `TOP_K_ACTIVE 2` | `"conv_a(2), conv_b(1)"` | top 2 by count DESC |
| 8 | `TOP_K_ACTIVE 5` | `"conv_a(2), conv_b(1), conv_c(0)"` | k=5 but only 3 convs; conv_c included at 0 |
| 9 | `LIST_USER_CONVERSATIONS alice` | `"conv_a, conv_b"` | alice owns conv_a and conv_b; alphabetical |
| 10 | `LIST_USER_CONVERSATIONS bob` | `"conv_c"` | bob owns conv_c |
| 11 | `LIST_USER_CONVERSATIONS carol` | `""` | carol owns nothing |

Final return value (including L1 ops):

```python
["true", "true", "true", "5", "13", "3", "conv_a(2), conv_b(1)", "conv_a(2), conv_b(1), conv_c(0)", "conv_a, conv_b", "conv_c", ""]
```

## Constraints

- All Level 1 constraints still apply.
- `<k>` is a positive integer string.
- Alphabetical tie-breaking is standard Python string sort (`sorted()` default).
- Up to `10^5` queries total; reporting ops may be O(N log N) in conversation count.

## Common gotchas

1. **Zero-message conversations appear in `TOP_K_ACTIVE`** — they exist; do not skip them. The only time `TOP_K_ACTIVE` returns `""` is when the system has zero conversations.
2. **`LIST_USER_CONVERSATIONS` returns `""` for unknown users AND for users with no conversations** — both collapse to `""`. You do not need to distinguish them.
3. **Alphabetical tie-breaking in `TOP_K_ACTIVE` is ASC** — among convs with the same count, the lexicographically smaller `conv_id` comes first.
4. **`k` may exceed the number of conversations** — return all of them, not an error.
5. **Sorting is by current message count, not token count** — `TOP_K_ACTIVE` counts messages, not tokens.

## When you're done

```
cd 08-llm-conversation-manager
python3 test_level2.py
```

All Level 2 tests must pass.
