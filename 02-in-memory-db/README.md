# Problem 02: In-Memory Key-Value-Field Database

A multi-level problem where you build a small in-memory database from scratch, progressively adding expiration and snapshot semantics.

## Files

- `solution.py` — your implementation (single function: `solution(queries)`)
- `spec/levelN.md` — the spec for each level (revealed sequentially)
- `test_levelN.py` — pytest-free test runner; just `python test_levelN.py`

## Workflow

1. Read `spec/level1.md`
2. Implement `solution.py`
3. Run `python test_level1.py` until all tests pass
4. Next level's spec + tests — repeat

## The 4 levels (high-level only — don't think ahead)

1. SET / GET / DELETE on (key, field) pairs
2. SCAN operations — list all fields at a key, optionally filtered by prefix
3. TTL / expiration — entries can expire at a given timestamp
4. Backup / Restore — snapshot and restore entire database state

## Data model

The internal state is `Dict[str, Dict[str, str]]` — a top-level "key" maps to a dict of (field → value). Think of "key" as a record/row name and "field" as a column name.

All commands take a timestamp as the second argument. Timestamps are strictly increasing positive integer strings across all queries.

## Signature

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

Each query is a list of strings. The first string is the command name. Return exactly one string per query.
