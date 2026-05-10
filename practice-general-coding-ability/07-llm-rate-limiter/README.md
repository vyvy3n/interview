# Problem 07: LLM API Rate Limiter

A classic Anthropic infrastructure problem: implement the per-API-key token bucket rate limiter that enforces usage limits in Anthropic's API.

You will build the system end-to-end across 4 levels — each level adds requirements that may force you to refactor your previous design.

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

1. Register API keys, consume tokens, check remaining capacity
2. Usage tracking — cumulative totals and top-K consumers
3. Time-based refill — the bucket continuously replenishes over time
4. Tier upgrades and key merging

## Domain background

Anthropic's API enforces rate limits using a **per-API-key token bucket**: each key has a
`max_tokens` (capacity cap) and a `refill_rate` (tokens added per second). API calls consume
tokens proportional to request size. The bucket refills continuously up to its cap. Tiers
(Free, Build, Scale) have different limits; accounts can be upgraded or merged when customers
grow. This problem implements that system end-to-end.

Each level builds on the last. Code that's clean and modular at L1 makes L4 survivable.
