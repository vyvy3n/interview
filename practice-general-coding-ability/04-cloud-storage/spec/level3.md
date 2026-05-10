# Level 3 — File Sharing

## What you're implementing

All Level 1 and Level 2 operations still work. You add the ability for users to share files with each other.

## Mental model

Sharing means: user A can grant user B "visibility" into a specific file. **Crucially, the file always counts against A's quota, never B's.** B can see the file but it doesn't eat B's space. Think of it like a Google Drive shared link — the file lives in A's storage, A pays the bytes, but B can access it.

You need to track which files are shared with whom. The share is directional: `(owner, file_id, recipient)` is one share record. The same file can be shared with multiple recipients (one SHARE call per recipient). When the owner deletes a file, all shares attached to it must be automatically revoked.

`LIST_SHARED_WITH` shows files shared **to** a user — what others have shared with them — not what they've shared out.

## The 3 new commands for Level 3

### 6. `["SHARE", <timestamp>, <owner_user>, <file_id>, <recipient_user>]`

Grant `recipient_user` access to `owner_user`'s file `file_id`.

| Situation | Return |
|-----------|--------|
| Share created successfully | `"true"` |
| `owner_user` does not exist | `""` |
| `file_id` does not exist for `owner_user` | `""` |
| `recipient_user` does not exist | `""` |
| `owner_user == recipient_user` | `""` |
| Share already exists (same owner+file+recipient) | `""` |

### 7. `["UNSHARE", <timestamp>, <owner_user>, <file_id>, <recipient_user>]`

Revoke a specific share.

| Situation | Return |
|-----------|--------|
| Share existed and was removed | `"true"` |
| Share did not exist (any reason) | `""` |

### 8. `["LIST_SHARED_WITH", <timestamp>, <user_id>]`

List all files that other users have shared **with** `user_id`.

- Format each entry as `"<owner_user>:<file_id>"`.
- Sort: first by `owner_user` ascending (alphabetical), then by `file_id` ascending within the same owner.
- Join with `", "`.

| Situation | Return |
|-----------|--------|
| At least one file is shared with this user | sorted formatted string |
| Nothing is shared with this user (or user doesn't exist) | `""` |

## Worked example — trace through it

```python
queries = [
    ["CREATE_USER",      "1",  "alice", "1000"],
    ["CREATE_USER",      "2",  "bob",   "500"],
    ["CREATE_USER",      "3",  "carol", "500"],
    ["UPLOAD",           "4",  "alice", "doc",   "200"],
    ["UPLOAD",           "5",  "alice", "photo", "100"],
    ["SHARE",            "6",  "alice", "doc",   "bob"],
    ["SHARE",            "7",  "alice", "doc",   "carol"],
    ["SHARE",            "8",  "alice", "photo", "bob"],
    ["SHARE",            "9",  "alice", "doc",   "bob"],
    ["SHARE",            "10", "alice", "doc",   "alice"],
    ["LIST_SHARED_WITH", "11", "bob"],
    ["LIST_SHARED_WITH", "12", "carol"],
    ["UNSHARE",          "13", "alice", "doc",   "bob"],
    ["LIST_SHARED_WITH", "14", "bob"],
    ["DELETE",           "15", "alice", "photo"],
    ["LIST_SHARED_WITH", "16", "bob"],
]
```

State: alice has doc(200) and photo(100); alice used=300/1000; bob used=0/500; carol used=0/500.

| # | Query | Output | Reason |
|---|-------|--------|--------|
| 1-5 | setup | `"true","true","true","200","100"` | L1 ops |
| 6 | SHARE alice doc bob | `"true"` | new share created |
| 7 | SHARE alice doc carol | `"true"` | second recipient for same file |
| 8 | SHARE alice photo bob | `"true"` | different file, same recipient |
| 9 | SHARE alice doc bob (dup) | `""` | already shared |
| 10 | SHARE alice doc alice (self) | `""` | owner == recipient |
| 11 | LIST_SHARED_WITH bob | `"alice:doc, alice:photo"` | bob has 2 shares from alice |
| 12 | LIST_SHARED_WITH carol | `"alice:doc"` | carol has 1 share |
| 13 | UNSHARE alice doc bob | `"true"` | removed share |
| 14 | LIST_SHARED_WITH bob | `"alice:photo"` | only photo remains |
| 15 | DELETE alice photo | `"true"` | photo deleted, share cascade |
| 16 | LIST_SHARED_WITH bob | `""` | cascade removed alice:photo share |

Final return value:

```python
["true", "true", "true", "200", "100",
 "true", "true", "true", "", "",
 "alice:doc, alice:photo",
 "alice:doc",
 "true",
 "alice:photo",
 "true",
 ""]
```

## Constraints

- A user can share the same file with **multiple** different recipients (one SHARE per recipient).
- The same `(owner, file_id, recipient)` triple can only be shared once.
- Shared files **never** count against the recipient's quota.
- When a file is deleted by its owner, ALL shares of that file are automatically removed.
- LIST_SHARED_WITH returns `""` for a user who exists but has nothing shared with them — same return as a non-existent user.
- All Level 1–2 constraints still apply.

## Common gotchas

1. **DELETE cascades shares**: when you delete a file, you must also clean up every share record that references `(owner, file_id)`. If you store shares in a set/dict that's keyed per-recipient, you must iterate and clean all of them. A reverse index (`(owner, file_id) → set of recipients`) makes this `O(1)`.
2. **Self-share is invalid**: `SHARE alice doc alice` returns `""`. Don't just check that the recipient exists.
3. **Duplicate share returns `""`**: the second SHARE with the same triple is not an update — it's a no-op that signals an error.
4. **LIST_SHARED_WITH sorted by owner then file_id**: not by insertion order, not by file_id alone.
5. **alice's quota is unaffected by sharing**: sharing `doc` with bob does not move any bytes. Alice's `used` only changes via UPLOAD/DELETE.
6. **UNSHARE is lenient**: any invalid/nonexistent share — wrong owner, wrong file, no share — all return `""` with no state change.

## When you're done

```
cd 04-cloud-storage
python3 test_level3.py
```

All tests must pass before moving to Level 4.
