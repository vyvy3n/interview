# Problem 04: Cloud Storage System

A multi-user file storage system with sharing and backup. Distinct from Problem 03 (File System) — this problem focuses on **per-user quotas, file sharing between users, and backup/restore snapshots** rather than compression or directory merging.

## Files

- `solution.py` — your implementation (single function: `solution(queries)`)
- `spec/levelN.md` — the spec for each level (revealed sequentially)
- `test_levelN.py` — pytest-free test runner; just `python test_levelN.py`

## Workflow

1. Read `spec/level1.md`
2. Implement `solution.py`
3. Run `python test_level1.py` until all tests pass
4. Move to the next level

## The 4 levels (high-level only — don't think ahead)

1. User accounts + per-user file uploads with quota enforcement
2. Usage reports and top-K rankings
3. File sharing between users (shared files count against owner's quota only)
4. Backup snapshots, restore, and ownership transfer

Each level builds on the last. A clean data model at L1 — separating user metadata from file records and share lists — makes L4's BACKUP/RESTORE and TRANSFER_OWNERSHIP tractable without a rewrite.

## Key differences from Problem 03 (File System)

| | Problem 03 (File System) | Problem 04 (Cloud Storage) |
|---|---|---|
| Multi-user | No | Yes |
| Quota | No | Per-user |
| Sharing | No | Yes (owner pays, not recipient) |
| Snapshot | No | Backup + restore per user |
| Merge | Directory merge | Ownership transfer |
