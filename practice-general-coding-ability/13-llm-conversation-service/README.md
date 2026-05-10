# Problem 13: LLM Conversation Service

Build a concurrent chatbot backend progressively — from basic conversation management through thread-safe worker pools and atomic compound operations — mirroring what you'd implement at Anthropic for a production chatbot product.

## Files

- `solution.py` — your implementation (`ConversationService` class)
- `spec/levelN.md` — spec for each level
- `test_levelN.py` — unittest test suite; run with `python3 test_levelN.py`

## Workflow

1. Read `spec/level1.md`
2. Implement the required methods in `solution.py`
3. Run `python3 test_level1.py` until all tests pass
4. Move to the next level — repeat

## The 6 levels (high-level only)

| Level | Title | Time | Key idea |
|-------|-------|------|----------|
| 1 | Basic Conversation Lifecycle | ~10 min | create, add_message, get_messages, delete |
| 2 | User-level Activity Reports | ~10 min | list convs, top-k active, per-user token sums |
| 3 | Context Window + Truncation | ~15 min | token budget, drop oldest messages, rejection |
| 4 | Fork + Branch + Merge | ~15 min | deep copy, branch at index, ts-based merge |
| 5 | Concurrent Sessions | ~20 min | RLock thread-safety, async worker pool, queue |
| 6 | Atomic Compound Operations | ~20 min | CAS, all-or-nothing batch, condition-var wait |

Levels 1–4 are fully sequential. Levels 5–6 introduce `threading` — no external libraries.

## Running tests

```bash
cd 13-llm-conversation-service
python3 test_level1.py   # run after implementing L1
python3 test_level2.py   # run after implementing L2
python3 test_level3.py   # run after implementing L3
python3 test_level4.py   # run after implementing L4
python3 test_level5.py   # run after implementing L5
python3 test_level6.py   # run after implementing L6
```

Each file uses Python's standard `unittest` library and is self-contained.

## Notes for the assessment

- You will not be evaluated on code quality or readability.
- Execution speed only matters when explicitly mentioned.
- Don't worry about edge cases not covered by tests.
- Tests are the final word on requirements — read them freely and run them often.
- For threading (Levels 5–6): use `threading.RLock` (reentrant, not plain `Lock`) to avoid deadlocks when methods call other methods.
- The L1 `add_message` does NOT enforce any context limit even after Level 3 — use `add_message_with_budget` for enforcement.
- Messages have an internal monotonic `ts` field used for merge ordering in Level 4.
