# Level 4 — Fork and Merge

## What you're implementing

You extend `solution(queries)` with two final commands: `FORK_CONVERSATION` and `MERGE_CONVERSATIONS`. All Level 1, 2, and 3 commands continue to work unchanged.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

The function signature does not change. `FORK_CONVERSATION` is the easier of the two — it is a deep copy. `MERGE_CONVERSATIONS` is the hardest: it interleaves messages by timestamp, then re-enforces the surviving conversation's budget.

## Mental model

Level 4 completes the conversation lifecycle with **branching and consolidation**. In a real LLM service, forking lets a user explore an alternative response path without losing the original thread — like "regenerate response" implemented as a copy-on-write branch. Merging combines two threads into one, useful when two conversation branches need to be reconciled (e.g., a human reviewer merges a bot-drafted thread with the user's continued thread).

The merge sort is **by message timestamp** (the `ts` value stored on each message at the time it was added). This is not the conversation creation time — it is the query timestamp of each individual `ADD_MESSAGE` or `ADD_MESSAGE_WITH_BUDGET` call. If two messages share the same timestamp, the surviving conversation's message comes first (stable ordering).

After merging, if the surviving conversation has a context limit and the merged total exceeds it, the same FIFO truncation from Level 3 fires automatically.

## The 2 commands for Level 4

### 1. `["FORK_CONVERSATION", <ts>, <source_conv_id>, <new_conv_id>]`

Create a new conversation `new_conv_id` that is an independent deep copy of `source_conv_id`.

**What copies:**
- Owner (same `user_id` as source)
- Message list (deep copy — independent list of independent message objects)
- Context limit (if any was set on source)

**What is independent after the fork:**
- Any future `ADD_MESSAGE`, `SET_CONTEXT_LIMIT`, or `ADD_MESSAGE_WITH_BUDGET` on either conversation does **not** affect the other.

| Situation | Return |
|-----------|--------|
| `source_conv_id` exists AND `new_conv_id` does not exist | `"true"` |
| `source_conv_id` does not exist | `""` |
| `new_conv_id` already exists | `""` |

### 2. `["MERGE_CONVERSATIONS", <ts>, <surviving_conv>, <absorbed_conv>]`

Merge `absorbed_conv` into `surviving_conv`. `absorbed_conv` ceases to exist after this operation.

**What merges:**
1. **Messages:** Combine both message lists. Sort the merged list by each message's stored `ts` ascending. Ties broken by conversation of origin: surviving's message comes before absorbed's message at equal timestamps.
2. **Owner:** `surviving_conv` keeps its own owner. `absorbed_conv`'s owner is discarded.
3. **Context limit:** `surviving_conv` keeps its own context limit (if any). If the merged total tokens exceed that limit, drop oldest messages (FIFO) until `total_tokens <= max_tokens`.
4. **Deletion:** `absorbed_conv` ceases to exist. All subsequent operations referencing `absorbed_conv` return `""` or `"false"` as appropriate.

| Situation | Return |
|-----------|--------|
| Both exist AND `surviving_conv != absorbed_conv` | `"true"` |
| Either does not exist | `""` |
| `surviving_conv == absorbed_conv` | `""` |

## Worked example — trace through it

```python
queries = [
    ["CREATE_CONVERSATION",     "1",  "main",   "alice"],
    ["ADD_MESSAGE",             "2",  "main",   "user",      "Hello",     "50"],
    ["ADD_MESSAGE",             "3",  "main",   "assistant", "Hi back",   "60"],
    ["FORK_CONVERSATION",       "4",  "main",   "branch"],
    ["ADD_MESSAGE",             "5",  "main",   "user",      "Continue",  "40"],
    ["ADD_MESSAGE",             "6",  "branch", "assistant", "Alternate", "45"],
    ["GET_MESSAGE_COUNT",       "7",  "main"],
    ["GET_MESSAGE_COUNT",       "8",  "branch"],
    ["MERGE_CONVERSATIONS",     "9",  "main",   "branch"],
    ["GET_MESSAGE_COUNT",       "10", "main"],
    ["GET_MESSAGE_COUNT",       "11", "branch"],
    ["SET_CONTEXT_LIMIT",       "12", "main",   "120"],
    ["FORK_CONVERSATION",       "13", "main",   "trimmed"],
    ["ADD_MESSAGE_WITH_BUDGET", "14", "trimmed","user",      "Extra",     "30"],
    ["GET_MESSAGE_COUNT",       "15", "main"],
    ["GET_MESSAGE_COUNT",       "16", "trimmed"],
]
```

State trace:

| # | Query | main msgs (ts order) | branch msgs | Output | Notes |
|---|-------|----------------------|-------------|--------|-------|
| 1 | CREATE main/alice | [] | — | `"true"` | |
| 2 | ADD_MESSAGE main user 50 ts=2 | [{ts=2,50}] | — | `"50"` | |
| 3 | ADD_MESSAGE main asst 60 ts=3 | [{ts=2},{ts=3}] | — | `"110"` | |
| 4 | FORK main→branch | branch gets copy: [{ts=2},{ts=3}] | [{ts=2},{ts=3}] | `"true"` | Deep copy |
| 5 | ADD_MESSAGE main user 40 ts=5 | [{ts=2},{ts=3},{ts=5}] | [{ts=2},{ts=3}] | `"150"` | Only main |
| 6 | ADD_MESSAGE branch asst 45 ts=6 | [{ts=2},{ts=3},{ts=5}] | [{ts=2},{ts=3},{ts=6}] | `"155"` | Only branch |
| 7 | GET_MESSAGE_COUNT main | — | — | `"3"` | |
| 8 | GET_MESSAGE_COUNT branch | — | — | `"3"` | |
| 9 | MERGE main←branch | merge: sort by ts: [ts=2(m),ts=2(b),ts=3(m),ts=3(b),ts=5(m),ts=6(b)] → 6 msgs; no limit → keep all | branch gone | `"true"` | Tie at ts=2 and ts=3: surviving (main) first |
| 10 | GET_MESSAGE_COUNT main | — | — | `"6"` | |
| 11 | GET_MESSAGE_COUNT branch | — | — | `""` | branch is gone |
| 12 | SET_CONTEXT_LIMIT main 120 | merged total = 50+50+60+60+40+45=305 > 120; drop oldest until ≤ 120: drop 50(ts=2m), 50(ts=2b), 60(ts=3m), 60(ts=3b) = 220 dropped; remaining: 40(ts=5)+45(ts=6)=85 ≤ 120 → 4 dropped | 2 msgs | `"4"` | |
| 13 | FORK main→trimmed | trimmed = copy of main: [{ts=5,40},{ts=6,45}], limit=120 | — | `"true"` | |
| 14 | ADD_MSG_BUDGET trimmed user 30 ts=14 | 85+30=115 ≤ 120 → no drop, append | — | `"0"` | |
| 15 | GET_MESSAGE_COUNT main | 2 msgs (unchanged by trimmed ops) | — | `"2"` | Fork is independent |
| 16 | GET_MESSAGE_COUNT trimmed | 3 msgs | — | `"3"` | |

Final return value:

```python
["true", "50", "110", "true", "150", "155", "3", "3", "true", "6", "", "4", "true", "0", "2", "3"]
```

Key trace notes:
- At query 9 (MERGE): messages from main (ts=2, ts=3, ts=5) and branch (ts=2, ts=3, ts=6). After sort by ts with surviving first on ties: [ts=2-main, ts=2-branch, ts=3-main, ts=3-branch, ts=5-main, ts=6-branch]. 6 total messages. No context limit on main at this point → all kept.
- At query 11: branch is gone, GET_MESSAGE_COUNT returns `""`.
- At query 12: SET_CONTEXT_LIMIT 120 on main which has 305 total tokens. Drop messages oldest-first: 50, 50, 60, 60 = 220 tokens dropped in 4 messages; remaining is 40+45=85 ≤ 120. Returns `"4"`.
- At query 14: trimmed has 85 total, adding 30 → 115 ≤ 120, no drop needed → `"0"`.
- At query 15: main still has 2 messages — fork is fully independent.

## Constraints

- All Level 1, 2, and 3 constraints still apply.
- `surviving_conv == absorbed_conv` must return `""` even if the conversation exists.
- After a merge, `absorbed_conv` must not appear in `TOP_K_ACTIVE`, `LIST_USER_CONVERSATIONS`, or any other operation.
- You may receive multiple forks from the same source, and multiple merges in sequence.
- FORK copies the **current** message list; messages added to source after the fork do not appear in the fork.
- Up to `10^5` queries total.

## Common gotchas

1. **Deep copy the message list on FORK** — if you store message objects and copy the list shallowly, mutations to one conversation (e.g., `SET_CONTEXT_LIMIT` dropping messages) will corrupt the other. Each conversation must own its own list of independent message objects.
2. **Merge sort is by message `ts`, not by insertion order** — the `ts` stored on each message at `ADD_MESSAGE` time is the sort key. Do not use the current query timestamp for ordering.
3. **Tie-breaking in MERGE: surviving before absorbed** — when two messages share the same `ts`, surviving's message comes first. Implement with a stable sort using `(msg.ts, origin_flag)` where `origin_flag=0` for surviving, `1` for absorbed.
4. **After MERGE, enforce context limit** — if surviving_conv had a `SET_CONTEXT_LIMIT`, the merged message list must be truncated (FIFO) to fit within that limit. Do not forget this step.
5. **FORK copies the context limit** — the forked conversation starts with the same `max_tokens` budget as the source. Subsequent `SET_CONTEXT_LIMIT` calls on either are independent.
6. **`absorbed_conv` is fully deleted** — remove it from every data structure: the main conversations dict, any per-user index, everything. It must not appear in reports.

## When you're done

```
cd 08-llm-conversation-manager
python3 test_level4.py
```

All Level 4 tests must pass. Congratulations — you've built a complete LLM conversation manager.
