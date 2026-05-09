# Anthropic CodeSignal Interview Prep

Comprehensive practice problems mirroring the Anthropic CodeSignal OA format:

- **Single problem, 4 progressive levels** (each unlocks the next)
- **90 minutes total** — L1/L2 fast, L3 eats time, L4 is a sprint
- **Domain modeling, not algorithms** — small system that absorbs new requirements
- **520+ score (3 of 4 levels) to advance** at most companies that use this format

## Format conventions

Every problem follows the same canonical CodeSignal shape:

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

- `queries` is a list of operations. Each operation is a list of strings.
- The first element of each operation is the command name.
- Return one string per query (use `""` for null/error/no-op).

## Problems

### Track A — General domain modeling

These mirror the canonical Anthropic OA shape. Good warmup before the LLM-systems track.

| # | Problem | Status | Tests |
|---|---------|--------|-------|
| 01 | [Bank Transaction System](./01-bank-transactions/) | ✅ all 4 levels solved | 60 |
| 02 | [In-Memory Database](./02-in-memory-db/) | scaffolded | 66 |
| 03 | [File System](./03-file-system/) | scaffolded | 71 |
| 04 | [Cloud Storage](./04-cloud-storage/) | scaffolded | 59 |

### Track B — LLM systems (Anthropic Research Fellow / ML Engineer)

These mirror the engineering work an Anthropic Research Fellow would do — LLM serving infrastructure with KV-cache routing, prompt caching, token-bucket rate limiting, and chatbot state management.

| # | Problem | Status | Tests |
|---|---------|--------|-------|
| 05 | [LLM Request Router](./05-llm-request-router/) — KV-cache-aware GPU scheduling | scaffolded | 57 |
| 06 | [LLM Prompt Cache](./06-llm-prompt-cache/) — TTL+LRU + prefix lookup | scaffolded | 57 |
| 07 | [LLM Rate Limiter](./07-llm-rate-limiter/) — token bucket with refill + tier merge | scaffolded | 58 |
| 08 | [LLM Conversation Manager](./08-llm-conversation-manager/) — context window + fork/merge | scaffolded | 59 |

## How to use

For each problem:

1. Read `spec/level1.md`. Don't peek at later levels — that's the point.
2. Implement `solution.py` until `python3 test_level1.py` is green.
3. Commit. Repeat for levels 2–4.

Commits track the learning record — each level's "before/after" is preserved.

## Recommended order

1. Start with **01-bank-transactions** to learn the 4-level pattern (canonical example, most-cited).
2. Pick any of **02–04** to practice fresh — different domain, same shape.
3. Move to **Track B** (problems 05–08) for the harder, ML-flavored systems work — these are closer to what you'd build at Anthropic in the role itself.

## Total

8 problems × 4 levels = 32 progressively-difficult systems-modeling exercises with 487 tests.
