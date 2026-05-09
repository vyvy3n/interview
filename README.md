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

| # | Problem | Status |
|---|---------|--------|
| 01 | [Bank Transaction System](./01-bank-transactions/) | in progress |

(More to come: in-memory database, file system, cloud storage, inventory.)

## How to use

For each problem:

1. Read `spec/level1.md`. Don't peek at later levels — that's the point.
2. Implement `solution.py` until `python test_level1.py` is green.
3. Commit. Then the next level's spec + tests get added.
4. Repeat for levels 2–4.

Commits track the learning record — each level's "before/after" is preserved.
