# Problem 05: LLM Request Router

A production-grade LLM inference routing problem modelled on real GPU scheduling challenges at Anthropic.

You will build a KV-cache-aware GPU request router. The system evolves across 4 levels — each level adds requirements that may force you to refactor your previous design.

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

1. GPU registration and basic round-trip routing
2. Load reporting and fleet-wide observability
3. Prefix-aware routing with per-GPU LRU caches
4. GPU failure detection and automatic request rebalancing

Each level builds on the last. Code that's clean and modular at L1 makes L4 survivable.
