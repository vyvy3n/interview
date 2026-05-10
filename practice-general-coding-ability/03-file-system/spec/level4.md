# Level 4 — Compress, Decompress, and User Merge

## What you're implementing

All previous operations still work. Add three new operations: `COMPRESS_FILE`, `DECOMPRESS_FILE`, and `USER_MERGE`.

## Mental model

**Compression:** a user can compress one of their own files, halving its stored size (floor division). The original size is remembered so decompression can perfectly restore it. A file can only be compressed once — a compressed file cannot be compressed again. Compression frees up capacity immediately (the file shrinks, so `used` drops).

**Decompression:** restore a compressed file to its original size. The restored size is larger, so you must check that the delta fits in the user's remaining capacity before proceeding.

**User merge:** merge two users together. All of user B's files transfer to user A. User A's new capacity is the sum of both capacities; their used bytes is the sum of both used bytes. User B ceases to exist. If a conflict arises — i.e., a file owned by B has the same name as a file owned by A — the entire merge fails and returns `""`.

**Compression state is preserved** across merge: if user B had a compressed file, after the merge it's still compressed and owned by A.

## The 3 new commands for Level 4

### 10. `["COMPRESS_FILE", <timestamp>, <user_id>, <name>]`

Compress a file owned by `user_id`. New size = `floor(original_size / 2)`.

| Situation | Return |
|-----------|--------|
| Success (user exists, owns file, file not yet compressed) | new (compressed) size as a string |
| User does not exist | `""` |
| File does not exist OR not owned by `user_id` | `""` |
| File is already compressed | `""` |

**Capacity effect:** `used` decreases by `original_size - floor(original_size / 2)`.

### 11. `["DECOMPRESS_FILE", <timestamp>, <user_id>, <name>]`

Restore a compressed file to its original size.

| Situation | Return |
|-----------|--------|
| Success (user exists, owns file, file is compressed, delta fits in remaining capacity) | user's remaining capacity after decompression |
| User does not exist | `""` |
| File does not exist OR not owned by `user_id` | `""` |
| File is not compressed | `""` |
| Restoring would exceed user's capacity | `""` |

**Delta check:** let `delta = original_size - compressed_size`. The user must have `remaining >= delta` before decompressing. After decompressing: `used` increases by `delta`.

### 12. `["USER_MERGE", <timestamp>, <user_id_a>, <user_id_b>]`

Merge user B into user A.

| Situation | Return |
|-----------|--------|
| Success | user A's remaining capacity after merge |
| Either user does not exist | `""` |
| `user_id_a == user_id_b` | `""` |
| Any file owned by B has the same name as a file owned by A | `""` (merge does NOT happen) |

**After merge:**
- All files owned by B are now owned by A.
- `cap_a_new = cap_a + cap_b`
- `used_a_new = used_a + used_b`
- User B is deleted (any subsequent operation involving B returns `""`).
- Remaining = `cap_a_new - used_a_new`.

## Worked example — trace through it

```python
queries = [
    ["USER_REGISTER",   "1",  "alice",  "1000"],
    ["USER_REGISTER",   "2",  "bob",    "600"],
    ["USER_UPLOAD",     "3",  "alice",  "big.bin",    "400"],  # alice used=400, rem=600
    ["USER_UPLOAD",     "4",  "bob",    "small.txt",  "100"],  # bob used=100, rem=500
    ["USER_UPLOAD",     "5",  "bob",    "data.csv",   "200"],  # bob used=300, rem=300
    ["COMPRESS_FILE",   "6",  "alice",  "big.bin"],            # 400→200, alice rem=800
    ["COMPRESS_FILE",   "7",  "alice",  "big.bin"],            # already compressed
    ["DECOMPRESS_FILE", "8",  "alice",  "big.bin"],            # 200→400, alice rem=600
    ["DECOMPRESS_FILE", "9",  "alice",  "big.bin"],            # not compressed
    ["COMPRESS_FILE",   "10", "bob",    "data.csv"],           # 200→100, bob rem=400
    ["USER_MERGE",      "11", "alice",  "bob"],                # merge bob→alice
    # After merge: alice cap=1600, used=400+100+100=600, rem=1000
    ["USER_GET",        "12", "alice",  "small.txt"],          # alice owns it now
    ["USER_GET",        "12", "bob",    "small.txt"],          # bob gone
    ["DECOMPRESS_FILE", "14", "alice",  "data.csv"],           # 100→200, delta=100, rem=900
]
```

Compression traces:

- Query 6: `COMPRESS big.bin` → floor(400/2)=200. alice used: 400→200. rem=800. Return `"200"`.
- Query 7: `COMPRESS big.bin` again → already compressed. Return `""`.
- Query 8: `DECOMPRESS big.bin` → delta=400-200=200. alice rem=800 ≥ 200 ✓. used: 200→400. rem=600. Return `"600"`.
- Query 9: `DECOMPRESS big.bin` → file is not compressed (just decompressed). Return `""`.
- Query 10: `COMPRESS data.csv` → floor(200/2)=100. bob used: 300→200. rem=400. Return `"100"`.

Merge (query 11): alice files: `{big.bin}`. bob files: `{small.txt, data.csv}`. No name conflicts. alice cap=1000+600=1600, used=400+200=600, rem=1000.

- Query 14: `DECOMPRESS data.csv` → delta=200-100=100. alice rem=1000 ≥ 100 ✓. used: 600→700. rem=900. Return `"900"`.

| # | Query | Output |
|---|-------|--------|
| 1 | USER_REGISTER alice 1000 | `"true"` |
| 2 | USER_REGISTER bob 600 | `"true"` |
| 3 | USER_UPLOAD alice big.bin 400 | `"600"` |
| 4 | USER_UPLOAD bob small.txt 100 | `"500"` |
| 5 | USER_UPLOAD bob data.csv 200 | `"300"` |
| 6 | COMPRESS_FILE alice big.bin | `"200"` |
| 7 | COMPRESS_FILE alice big.bin (again) | `""` |
| 8 | DECOMPRESS_FILE alice big.bin | `"600"` |
| 9 | DECOMPRESS_FILE alice big.bin (not compressed) | `""` |
| 10 | COMPRESS_FILE bob data.csv | `"100"` |
| 11 | USER_MERGE alice bob | `"1000"` |
| 12 | USER_GET alice small.txt | `"100"` |
| 13 | USER_GET bob small.txt | `""` |
| 14 | DECOMPRESS_FILE alice data.csv | `"900"` |

Final return value:

```python
["true", "true", "600", "500", "300", "200", "", "600", "", "100", "1000", "100", "", "900"]
```

## Constraints

- All previous constraints still hold.
- `floor(size / 2)` uses Python integer division: `size // 2`.
- A file with `original_size = 1` compresses to `0` — this is valid (size 0 is allowed only as a compressed state; upload requires `> 0`).
- Merge conflict check: scan all of B's files; if **any** name appears in A's owned files, the entire merge fails atomically (no partial transfer).
- After a failed merge, both users A and B remain unchanged.

## Common gotchas

1. **Double-compress is rejected.** Track a `is_compressed` flag (or an `original_size` field — if it's set, the file is compressed).
2. **Decompress checks delta against remaining capacity, not total capacity.** `remaining = cap - used`. You need `remaining >= delta`.
3. **Merge conflict is a name-level check across owned files only.** A file owned by admin doesn't conflict with a user's file for merge purposes — but it's still in the global namespace, so `USER_UPLOAD` would reject it.
4. **Failed merge is atomic.** If there's a conflict, return `""` immediately; do not transfer any files or adjust any capacities.
5. **After merge, B is gone.** `USER_UPLOAD` for B, `USER_GET` for B, etc., all return `""` as if B never existed.
6. **Compression changes `used` immediately.** After compressing, the user's remaining capacity increases — subsequent uploads may succeed that wouldn't have before.

## When you're done

```
cd 03-file-system
python3 test_level4.py
```

All tests must pass. You've built a complete in-memory file system with ownership, capacity management, compression, and user merging.
