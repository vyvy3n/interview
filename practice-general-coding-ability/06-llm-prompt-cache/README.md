# Problem 06: LLM Prompt Cache

A realistic implementation of the prompt caching layer used in production LLM serving infrastructure.

You will build a prompt cache that evolves through 4 levels — each level adds requirements that may force you to refactor your previous design.

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

1. Basic cache: PUT / GET / DELETE on prompt → response pairs
2. Hit tracking and popularity reporting
3. TTL-based expiry and LRU eviction under capacity limits
4. Prefix-cache lookup and bulk invalidation

Each level builds on the last. Code that's clean and modular at L1 makes L4 survivable.
