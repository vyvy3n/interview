# Level 4 — Backup, Restore & Ownership Transfer

## What you're implementing

All Level 1–3 operations still work. You add snapshotting, rollback, and complete ownership transfer.

## Mental model

**BACKUP / RESTORE** works like a version control snapshot for a single user. When you BACKUP, you freeze a copy of the user's current files (names + sizes) and their share relationships (outgoing shares they created, and incoming shares they received). When you RESTORE, you roll the user back to that exact snapshot — but with awareness of the current world: you can only restore incoming shares for recipients who still exist today.

**TRANSFER_OWNERSHIP** is a full migration: every file from user A is moved to user B. A ceases to exist. Outgoing shares that A created are re-anchored to B (so anyone who had A's files shared with them now has B's files shared with them instead).

Key design pressures:
- **RESTORE must be atomic**: if the restored file set doesn't fit in the user's current quota, do nothing and return `""`.
- **TRANSFER_OWNERSHIP must check quota**: `to_user.used + from_user.used <= to_user.quota` must hold.
- **Backups are cheap**: they don't count against quota. You're just recording state.
- **RESTORE only re-establishes incoming shares if the sender still exists and the file is in the restored set.** Outgoing shares are always restored (they're from this user — we're restoring this user's state).

## The 3 new commands for Level 4

### 9. `["BACKUP", <timestamp>, <user_id>]`

Snapshot the user's current state: all owned files (file_id → size) and all share relationships (both outgoing and incoming).

- Backups are global and numbered sequentially: `"backup1"`, `"backup2"`, `"backup3"`, ... starting from 1.
- Each call to BACKUP increments the global counter, regardless of which user is backed up.
- A user can have multiple backups.

| Situation | Return |
|-----------|--------|
| User exists | the new backup_id, e.g. `"backup1"` |
| User does not exist | `""` |

### 10. `["RESTORE", <timestamp>, <user_id>, <backup_id>]`

Roll the user back to the state captured in `backup_id`.

Steps (all-or-nothing):
1. Verify: `backup_id` belongs to `user_id` (not another user). If not, return `""`.
2. Verify: total size of all files in the backup ≤ user's current `quota`. If not, return `""`.
3. Remove all of the user's current files (freeing space).
4. Restore all files from the backup.
5. Revoke all current outgoing shares from this user (since we're replacing their file set).
6. Remove all current incoming shares to this user (since their identity is being reset).
7. Restore outgoing shares from the backup — but only for files that exist in the restored set AND the recipient currently exists. Skip any recipient who no longer exists.
8. Restore incoming shares from the backup — but only if the original owner currently exists AND still owns that file (i.e. the owner was not transferred, deleted, etc.). Skip mismatches.

Returns `"true"` on success, `""` otherwise.

**Atomicity rule**: steps 3–8 only happen if steps 1 and 2 both pass. Never partially apply.

### 11. `["TRANSFER_OWNERSHIP", <timestamp>, <from_user>, <to_user>]`

Move all files from `from_user` to `to_user`. `from_user` ceases to exist.

- Quota check: `to_user.used + from_user.used <= to_user.quota`. If this fails, return `""`.
- All files move to `to_user`'s namespace. If a file_id collision occurs (both users have a file with the same name), the **from_user's file overwrites to_user's file** (to_user loses that file, and the size delta is already accounted for in the quota check — re-compute: `(to_user.used - conflicting_size) + from_user.used`).
- All outgoing shares where `from_user` was the owner are re-anchored to `to_user`. Recipients don't notice any change in terms of what they have access to (LIST_SHARED_WITH for those recipients would now show `to_user:file_id` instead of `from_user:file_id`).
- `from_user` is deleted (including any backups — they are gone).
- Returns `"true"` on success.
- Returns `""` if: either user doesn't exist, `from_user == to_user`, or quota would be exceeded.

**File ID collision quota note**: the correct quota check is: the sum of all unique file_ids across both users, where collisions use `from_user`'s size. Equivalently: `to_user.used - sum(size of to_user files that collide with from_user) + from_user.used <= to_user.quota`.

## Worked example — trace through it

```python
queries = [
    ["CREATE_USER",        "1",  "alice", "1000"],
    ["CREATE_USER",        "2",  "bob",   "600"],
    ["CREATE_USER",        "3",  "carol", "500"],
    ["UPLOAD",             "4",  "alice", "doc",   "200"],
    ["UPLOAD",             "5",  "alice", "photo", "150"],
    ["SHARE",              "6",  "alice", "doc",   "bob"],
    ["BACKUP",             "7",  "alice"],
    ["UPLOAD",             "8",  "alice", "video", "400"],
    ["SHARE",              "9",  "alice", "video", "carol"],
    ["BACKUP",             "10", "alice"],
    ["DELETE",             "11", "alice", "doc"],
    ["RESTORE",            "12", "alice", "backup1"],
    ["GET_USAGE",          "13", "alice"],
    ["LIST_SHARED_WITH",   "14", "bob"],
    ["BACKUP",             "15", "bob"],
    ["TRANSFER_OWNERSHIP", "16", "bob",   "carol"],
    ["GET_USAGE",          "17", "carol"],
    ["GET_USAGE",          "18", "bob"],
]
```

Trace:

| # | Query | Output | Key state after |
|---|-------|--------|-----------------|
| 1 | CREATE_USER alice 1000 | `"true"` | alice: 0/1000 |
| 2 | CREATE_USER bob 600 | `"true"` | bob: 0/600 |
| 3 | CREATE_USER carol 500 | `"true"` | carol: 0/500 |
| 4 | UPLOAD alice doc 200 | `"200"` | alice: 200/1000 |
| 5 | UPLOAD alice photo 150 | `"350"` | alice: 350/1000 |
| 6 | SHARE alice doc bob | `"true"` | bob can see alice:doc |
| 7 | BACKUP alice | `"backup1"` | snapshot: files={doc:200,photo:150}, out_shares={doc→[bob]}, in_shares={} |
| 8 | UPLOAD alice video 400 | `"750"` | alice: 750/1000 |
| 9 | SHARE alice video carol | `"true"` | carol can see alice:video |
| 10 | BACKUP alice | `"backup2"` | snapshot: files={doc:200,photo:150,video:400}, out={doc→[bob],video→[carol]}, in={} |
| 11 | DELETE alice doc | `"true"` | alice: 550/1000; doc share to bob auto-revoked |
| 12 | RESTORE alice backup1 | `"true"` | alice reset to {doc:200,photo:150}=350 bytes; bob exists → restore doc share; video share gone |
| 13 | GET_USAGE alice | `"350/1000"` | 350 used after restore |
| 14 | LIST_SHARED_WITH bob | `"alice:doc"` | restored; video share to carol not in backup1 |
| 15 | BACKUP bob | `"backup3"` | bob's backup (bob has 0 files, no shares) |
| 16 | TRANSFER_OWNERSHIP bob carol | `"true"` | bob used=0, fits in carol's 500-0=500; bob deleted |
| 17 | GET_USAGE carol | `"0/500"` | carol unchanged (bob had no files) |
| 18 | GET_USAGE bob | `""` | bob no longer exists |

Final return value:

```python
["true", "true", "true", "200", "350", "true",
 "backup1", "750", "true", "backup2", "true", "true",
 "350/1000", "alice:doc", "backup3", "true", "0/500", ""]
```

## Constraints

- Backup IDs are global and monotonically increasing (not per-user).
- Restoring another user's backup_id returns `""`.
- RESTORE atomicity: the user's state must not change at all if quota check fails.
- TRANSFER_OWNERSHIP removes `from_user` and all their backups.
- In TRANSFER_OWNERSHIP, file collisions: `from_user`'s file wins, overwriting `to_user`'s file.
- All Level 1–3 constraints still apply.

## Common gotchas

1. **RESTORE atomicity**: don't delete current files and then fail the restore partway through. Do the quota check FIRST (step 2), then apply the changes (steps 3–8) only on success.
2. **Backup stores a deep copy**: if you store a reference to the user's live file dict, subsequent uploads/deletes will mutate the backup. Use `dict(files)` and a copy of share sets at backup time.
3. **RESTORE incoming shares**: only re-establish if the original owner still exists AND still owns the file. This requires looking up the current state of the world, not just the backup.
4. **TRANSFER_OWNERSHIP quota math with collisions**: the naive check (`to_used + from_used <= quota`) overcounts when files collide. Subtract the to_user's size for any file_id that appears in both.
5. **Re-anchoring shares in TRANSFER_OWNERSHIP**: after moving files, update any share record where `owner == from_user` to have `owner = to_user`. Recipients' LIST_SHARED_WITH results will change automatically.
6. **Backups survive RESTORE**: restoring `backup1` does not delete `backup2`. Backups are never deleted (except when the user is deleted via TRANSFER_OWNERSHIP).
7. **Backup counter is global**: `BACKUP alice` at ts=7 gives `backup1`, then `BACKUP bob` at ts=15 gives `backup3` (not `backup1` for bob). The counter does not reset per user.

## When you're done

```
cd 04-cloud-storage
python3 test_level4.py
```

All tests must pass. You've completed the Cloud Storage System problem.
