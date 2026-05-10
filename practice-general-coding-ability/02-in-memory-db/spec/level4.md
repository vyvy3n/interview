# Level 4 — Backup and Restore

## What you're implementing

Level 4 adds two new commands: `BACKUP` (snapshot the current database state) and `RESTORE` (roll back to a previous snapshot). All previous commands continue to work.

## Mental model

Think of BACKUP as a "checkpoint": you freeze the current state and store it. Crucially, for TTL'd entries you don't store the absolute expiry timestamp — you store the **remaining TTL** at the time of the backup. This way, when you RESTORE later, the TTL is re-anchored to the restore timestamp.

Backups are stored keyed by their timestamp. Multiple backups can exist at once.

RESTORE replaces the entire current state with the snapshot. TTL'd entries get new expiry times: `restore_ts + remaining_ttl`. Non-TTL entries are restored with no expiry (they never expire again).

Expired entries are **not included** in a backup — they are treated as if they don't exist at the backup timestamp.

## The 2 commands for Level 4

### 1. `["BACKUP", <ts>]`

Take a snapshot of the current database state.

Steps performed:
1. Collect all (key, field, value) triples that are **not expired** at `ts` (i.e., have no TTL, or `ts < expiry`).
2. For each TTL'd entry, compute `remaining_ttl = expiry_ts - ts`. For non-TTL entries, store `None` as the remaining_ttl.
3. Store this snapshot under key `ts`.
4. Count the total number of non-expired (key, field) pairs in the snapshot.

| Situation | Return |
|-----------|--------|
| Always | count of non-expired (key, field) pairs as a string, e.g. `"5"` |

### 2. `["RESTORE", <ts>, <backup_ts>]`

Replace the current state with the snapshot taken at `backup_ts`.

Steps performed:
1. Look up the snapshot at `backup_ts`.
2. If no snapshot exists at `backup_ts`, return `""` and leave state unchanged.
3. Rebuild the database from the snapshot:
   - For each entry with `remaining_ttl = None`: restore with no expiry.
   - For each entry with `remaining_ttl = R`: new expiry = `int(ts) + R`.
4. Replace the current state entirely.

| Situation | Return |
|-----------|--------|
| Snapshot at `backup_ts` exists | `""` |
| No snapshot at `backup_ts` | `""` |

(Both cases return `""` — use a side-effect to tell them apart in tests: check subsequent GETs.)

## Worked example — trace through it

```python
queries = [
    ["SET",          "1",  "a", "x", "hello"],
    ["SET_WITH_TTL", "2",  "a", "y", "world", "10"],
    ["SET",          "3",  "b", "p", "foo"],
    ["BACKUP",       "5"],
    ["SET",          "6",  "a", "x", "CHANGED"],
    ["DELETE",       "7",  "b", "p"],
    ["SET",          "8",  "c", "z", "new"],
    ["RESTORE",      "9",  "5"],
    ["GET",          "10", "a", "x"],
    ["GET",          "10", "a", "y"],
    ["GET",          "10", "b", "p"],
    ["GET",          "10", "c", "z"],
    ["GET",          "16", "a", "y"],
]
```

Tracing state step by step:

| # | Query | State summary | Output | Notes |
|---|-------|---------------|--------|-------|
| 1 | `SET 1 a x hello` | a.x=hello (no TTL) | `""` | |
| 2 | `SET_WITH_TTL 2 a y world 10` | a.y=world (expiry=12) | `""` | |
| 3 | `SET 3 b p foo` | b.p=foo (no TTL) | `""` | |
| 4 | `BACKUP 5` | snapshot@5 taken | `"3"` | 3 pairs: (a,x), (a,y), (b,p); a.y has remaining_ttl=12-5=7 |
| 5 | `SET 6 a x CHANGED` | a.x=CHANGED | `""` | |
| 6 | `DELETE 7 b p` | b.p gone | `"true"` | |
| 7 | `SET 8 c z new` | c.z=new | `""` | |
| 8 | `RESTORE 9 5` | state from snapshot@5; a.y expiry=9+7=16 | `""` | c.z gone; a.x=hello restored |
| 9 | `GET 10 a x` | | `"hello"` | restored to original value |
| 10 | `GET 10 a y` | | `"world"` | ts=10 < 16, still valid |
| 11 | `GET 10 b p` | | `"foo"` | restored |
| 12 | `GET 10 c z` | | `""` | c.z was not in snapshot |
| 13 | `GET 16 a y` | | `""` | ts=16 >= 16, EXPIRED (re-anchored expiry=9+7=16) |

Final return value:

```python
["", "", "", "3", "", "true", "", "", "hello", "world", "foo", "", ""]
```

## TTL re-anchoring explained

At BACKUP ts=5: `a.y` has expiry=12, so remaining_ttl = 12 - 5 = **7**.
At RESTORE ts=9: new expiry = 9 + 7 = **16**.
So `a.y` is valid at ts=10, 11, ..., 15 and expired at ts=16 and beyond.

If we had stored the absolute expiry (12) and applied it unchanged, the entry would already be expired at restore ts=9 (since 9 < 12 ... actually still valid, but at ts=13 it would wrongly expire — the intent is 7 more seconds from restore time, not from original set time).

## Constraints

- All Level 1, 2, and 3 constraints still apply.
- Multiple `BACKUP` commands can be issued; each is stored by its timestamp.
- `RESTORE` does **not** clear the backups — you can restore the same backup multiple times.
- `backup_ts` in `RESTORE` refers to the timestamp of a previous `BACKUP` call.
- After `RESTORE`, all subsequent commands (including L1-L3) operate on the restored state.

## Common gotchas

1. **Re-anchoring TTL, not copying absolute expiry** — at BACKUP time, store `remaining_ttl = expiry_ts - backup_ts`. At RESTORE time, set `new_expiry = restore_ts + remaining_ttl`. If you store the absolute expiry and restore it directly, the entry will expire at the wrong time.
2. **Expired entries at BACKUP time are excluded** — if an entry is expired at the BACKUP timestamp (ts >= expiry), don't include it in the snapshot at all. The count returned by BACKUP excludes them.
3. **RESTORE to a nonexistent backup_ts returns `""` and does nothing** — don't crash or clear state. Check for existence before replacing.
4. **RESTORE replaces the entire state** — all keys/fields not in the snapshot are gone after a RESTORE. Entries created after the backup are wiped.
5. **Operations after RESTORE work on the restored state** — SCAN, GET, DELETE, SET, etc. all act on the new state. This includes TTL checks using the current query timestamp (not the backup timestamp).
6. **No-TTL entries in the snapshot stay no-TTL after RESTORE** — store `None` (or similar sentinel) for no-TTL entries, and restore them without expiry.

## When you're done

```
cd 02-in-memory-db
python3 test_level4.py
```

All Level 1, 2, 3, and 4 tests must pass.
