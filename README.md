# Anthropic Fellows / CodeSignal Interview Prep

## ⚠️ Read this first if you're prepping for the actual Anthropic Fellows assessment

The real Anthropic Fellows OA differs from the canonical "4-level" CodeSignal shape:

- **6 levels, not 4.** 90 minutes total.
- **`unittest` framework** (not a custom runner).
- **Concurrency required** — `threading` OR `asyncio` from stdlib.
- **"Standard LeetCode-style problems"** is the prep recommendation.

**→ Use Track C (problems 09, 10) and the concurrency primer for the actual Fellows assessment.**

Tracks A and B (problems 01–08) are 4-level domain-modeling and useful as warmups, but they don't match the 6-level + concurrency format.

---

## Tracks

### Track A — Canonical 4-level domain modeling (warmup)

Mirrors the general Anthropic OA shape. Single `solution(queries) -> list[str]` function, 4 progressive levels.

| # | Problem | Status | Tests |
|---|---------|--------|-------|
| 01 | [Bank Transaction System](./01-bank-transactions/) | ✅ all 4 levels solved | 60 |
| 02 | [In-Memory Database](./02-in-memory-db/) | ✅ all 4 levels solved | 66 |
| 03 | [File System](./03-file-system/) | scaffolded | 71 |
| 04 | [Cloud Storage](./04-cloud-storage/) | scaffolded | 59 |

### Track B — LLM systems (4-level, ML-flavored)

LLM serving infrastructure problems. Same 4-level shape as Track A.

| # | Problem | Status | Tests |
|---|---------|--------|-------|
| 05 | [LLM Request Router](./05-llm-request-router/) — KV-cache-aware GPU scheduling | scaffolded | 57 |
| 06 | [LLM Prompt Cache](./06-llm-prompt-cache/) — TTL+LRU + prefix lookup | scaffolded | 57 |
| 07 | [LLM Rate Limiter](./07-llm-rate-limiter/) — token bucket + lazy refill | scaffolded | 58 |
| 08 | [LLM Conversation Manager](./08-llm-conversation-manager/) — context window + fork/merge | scaffolded | 59 |

### Track C — 6-level + concurrency (matches Anthropic Fellows assessment)

Mirrors the actual Fellows assessment format: 6 levels, `unittest` tests, concurrency at L5–L6.

| # | Problem | Concurrency style | Tests |
|---|---------|-------------------|-------|
| 09 | [Concurrent Task Scheduler](./09-concurrent-task-scheduler/) | `threading` (Lock, Event, Condition) | 96 |
| 10 | [Async KV Store](./10-thread-safe-keyvalue/) | `asyncio` (Lock, IsolatedAsyncioTestCase) | 117 |

### Concurrency Primer

10 standalone exercises building muscle memory for `threading` and `asyncio` primitives. **Do these BEFORE attempting Track C if your concurrency reflexes are rusty.**

[`concurrency-primer/`](./concurrency-primer/) — thread-safe counter, print-in-order, bounded blocking queue, async rate limiter, RWLock, FizzBuzz multithreaded, etc.

---

## Recommended path for Anthropic Fellows assessment (5-day prep)

| Day | What | Why |
|---|---|---|
| 1 | Concurrency primer (exercises 01–05) | Build threading + asyncio reflexes |
| 2 | Concurrency primer (06–10), start Problem 09 | Solidify, then 6-level practice |
| 3 | Finish Problem 09, start Problem 10 | Both concurrency styles |
| 4 | Finish Problem 10, take CodeSignal's free practice OA on their platform | Timed dry-run, get used to UI |
| 5 | Take the actual assessment | Fresh, rested |

For warmup: do 1-2 levels of Problem 01 or 02 first if you've never done a CodeSignal-style problem at all.

## Format conventions

**Tracks A and B** (4-level): single `solution(queries) -> list[str]` function. Custom test runner via `python3 test_levelN.py`.

**Track C** (6-level): a class (`TaskScheduler`, `KVStore`) with methods. Tests use `unittest`. Run via `python3 test_levelN.py`.

## How to use

For each problem:
1. Read `spec/level1.md`. Don't peek at later levels — that's the point.
2. Implement until `python3 test_level1.py` is green.
3. Commit. Repeat for next level.

Commits track the learning record — each level's "before/after" is preserved.

## Total

| | Problems | Levels | Tests |
|---|---|---|---|
| Track A | 4 | 16 | 256 |
| Track B | 4 | 16 | 231 |
| Track C | 2 | 12 | 213 |
| Concurrency primer | 10 exercises | — | ~50 |
| **Total** | **10 problems + 10 exercises** | **44 levels** | **~750 tests** |
