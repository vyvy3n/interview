# Problem 03: File System (mini Dropbox in memory)

Build a lightweight in-memory file system — think of it as a stripped-down Dropbox API. The system evolves across 4 levels; each level adds requirements that will test how cleanly you designed the previous layer.

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

1. Basic file upload, get, and copy
2. Prefix search with ranked results
3. Users, ownership, and storage capacity
4. File compression, decompression, and user merging

Each level builds on the last. Keep your data structures flat and well-named — Level 3's ownership layer will be painful if Level 1 stored filenames as opaque keys.
