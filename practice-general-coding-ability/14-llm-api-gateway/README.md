# Problem 14: LLM API Gateway

A simulated API gateway in front of a large-language-model service. You build per-user accounts, usage tracking, token-bucket rate limiting with lazy refill, per-prompt response caching, and concurrent async request handling — the same core subsystems Anthropic's API platform runs.

## Files

- `solution.py` — your implementation (`LLMGateway` class)
- `spec/levelN.md` — the spec for each level (revealed sequentially)
- `test_levelN.py` — standard `unittest` runner; just `python3 test_levelN.py`

## Workflow

1. Read `spec/level1.md`
2. Implement `solution.py`
3. Run `python3 test_level1.py` until all tests pass
4. Move to the next level — repeat

## The 6 levels (high-level only — don't think ahead)

1. Basic request lifecycle — register users, process requests, track usage
2. Usage reports — top-K rankings, tier queries, global counters
3. Token-bucket rate limiting — per-user buckets with lazy time-based refill
4. Per-prompt response caching — shared cache with hit tracking and invalidation
5. Async concurrent handling — `asyncio.Lock` protecting shared state
6. Atomic compound operations — batch handle, user merge, compare-and-handle

## Concurrency note

Levels 5–6 use Python's `asyncio` stdlib — no external packages. Use `asyncio.Lock` to protect shared state. Tests use `unittest.IsolatedAsyncioTestCase` (Python 3.8+).

## Running tests

```bash
python3 test_level1.py
python3 test_level2.py
python3 test_level3.py
python3 test_level4.py
python3 test_level5.py
python3 test_level6.py
```
