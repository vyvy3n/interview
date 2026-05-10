# Problem 08: LLM Conversation Manager

A multi-user chatbot state machine — the kind of system that runs behind every production LLM API.

You will build the core conversation lifecycle manager: creating conversations, accumulating messages, enforcing token budgets via truncation, and supporting branching (fork) and merging of conversation threads. The system evolves across 4 levels — each level adds requirements that may force you to refactor your previous design.

## Files

- `solution.py` — your implementation (single function: `solution(queries)`)
- `spec/levelN.md` — the spec for each level (revealed sequentially)
- `test_levelN.py` — pytest-free test runner; just `python test_levelN.py`

## Workflow

1. Read `spec/level1.md`
2. Implement `solution.py`
3. Run `python test_level1.py` until all tests pass
4. Commit
5. Next level's spec + tests get added — repeat

## The 4 levels (high-level only — don't think ahead)

1. Conversations and messages — create conversations, add messages, count them
2. Activity reports — top-K by message count, list conversations per user
3. Context window + truncation — token budgets, FIFO dropping, budget-aware append
4. Fork + merge — deep-copy branching, timestamp-ordered merge with overflow handling

Each level builds on the last. Code that is clean and modular at L1 makes L4 survivable.
