# Level 3 — Users and Storage Capacity

## What you're implementing

Level 1 and Level 2 operations still work. Add five new user-scoped operations: `USER_REGISTER`, `USER_UPLOAD`, `USER_GET`, `USER_COPY`, and `USER_SEARCH`.

## Mental model

Until now, all files lived in a single global namespace with no ownership. Now you introduce **users**, each with a **storage capacity** (maximum total bytes they can own).

**Single global namespace:** all file names — whether uploaded via `FILE_UPLOAD` (owned by `"admin"`) or `USER_UPLOAD` (owned by a user) — share the same flat namespace. No two files can have the same name, regardless of who owns them.

**Ownership:** each file has exactly one owner. `FILE_UPLOAD` files are owned by `"admin"`. `USER_UPLOAD` files are owned by the registering user. Ownership matters for `USER_GET`, `USER_COPY`, and `USER_SEARCH` — you can only read or copy your own files.

**Capacity:** each user has a `capacity` (total allowed bytes). Their `used` bytes is the sum of sizes of files they own. `USER_UPLOAD` checks `used + new_size <= capacity` before accepting. Return value is `capacity - used` (remaining) after a successful operation.

**`FILE_*` ops and admin:** `FILE_UPLOAD`, `FILE_GET`, `FILE_COPY` act as if run by an `"admin"` user with infinite capacity. Admin files count toward the global namespace but not toward any user's capacity.

## The 5 new commands for Level 3

### 5. `["USER_REGISTER", <timestamp>, <user_id>, <capacity>]`

Register a new user with a max capacity.

| Situation | Return |
|-----------|--------|
| `user_id` is new | `"true"` |
| `user_id` already exists | `"false"` |

### 6. `["USER_UPLOAD", <timestamp>, <user_id>, <name>, <size>]`

Upload a file on behalf of a user.

| Situation | Return |
|-----------|--------|
| Success (user exists, name is globally new, fits in capacity) | user's remaining capacity as a string |
| User does not exist | `""` |
| File name already exists (any owner) | `""` |
| Upload would exceed user's capacity | `""` |

### 7. `["USER_GET", <timestamp>, <user_id>, <name>]`

Get a file's size — but only if this user owns it.

| Situation | Return |
|-----------|--------|
| File exists AND owned by `user_id` | size as a string |
| File does not exist | `""` |
| File exists but owned by someone else | `""` |

### 8. `["USER_COPY", <timestamp>, <user_id>, <source>, <dest>]`

Copy one of the user's own files to a new name. The copy is owned by the same user.

| Situation | Return |
|-----------|--------|
| Success (source owned by user, dest new or owned by same user, fits in capacity) | user's remaining capacity |
| User does not exist | `""` |
| Source does not exist OR not owned by `user_id` | `""` |
| Dest exists and owned by someone else | `""` |
| After accounting for the overwrite, copy would still exceed capacity | `""` |

**Capacity math on overwrite:** if `dest` already exists and is owned by `user_id`, you first free the old dest's size from `used`, then add the new copy's size. Net change = `source_size - old_dest_size`. If this net addition causes `used > capacity`, fail.

### 9. `["USER_SEARCH", <timestamp>, <user_id>, <prefix>]`

Like `FILE_SEARCH` but scoped to files owned by `user_id`.

| Situation | Return |
|-----------|--------|
| Matches found (user exists) | top-10 owned files matching prefix, same format as `FILE_SEARCH` |
| No matches | `""` |
| User does not exist | `""` |

## Worked example — trace through it

```python
queries = [
    ["USER_REGISTER", "1",  "alice",  "1000"],
    ["USER_REGISTER", "2",  "bob",    "500"],
    ["USER_REGISTER", "3",  "alice",  "999"],   # dup
    ["USER_UPLOAD",   "4",  "alice",  "doc.txt",   "300"],  # alice used=300, rem=700
    ["USER_UPLOAD",   "5",  "bob",    "doc.txt",   "100"],  # name conflict!
    ["USER_UPLOAD",   "6",  "bob",    "img.png",   "200"],  # bob used=200, rem=300
    ["FILE_UPLOAD",   "7",  "shared.pdf",          "999"],  # admin file
    ["USER_UPLOAD",   "8",  "alice",  "shared.pdf","10"],   # name conflict with admin file
    ["USER_GET",      "9",  "alice",  "doc.txt"],           # alice owns it
    ["USER_GET",      "10", "bob",    "doc.txt"],           # bob does NOT own it
    ["USER_COPY",     "11", "alice",  "doc.txt",  "doc2.txt"], # alice: used=600, rem=400
    ["USER_COPY",     "12", "bob",    "doc.txt",  "img2.png"], # source not bob's
    ["USER_SEARCH",   "13", "alice",  "doc"],               # alice: doc.txt, doc2.txt
    ["USER_SEARCH",   "14", "bob",    ""],                  # bob: img.png only
]
```

| # | Query | State change | Output |
|---|-------|--------------|--------|
| 1 | USER_REGISTER alice 1000 | alice: cap=1000, used=0 | `"true"` |
| 2 | USER_REGISTER bob 500 | bob: cap=500, used=0 | `"true"` |
| 3 | USER_REGISTER alice 999 (dup) | unchanged | `"false"` |
| 4 | USER_UPLOAD alice doc.txt 300 | alice used=300 | `"700"` |
| 5 | USER_UPLOAD bob doc.txt 100 (name conflict) | unchanged | `""` |
| 6 | USER_UPLOAD bob img.png 200 | bob used=200 | `"300"` |
| 7 | FILE_UPLOAD shared.pdf 999 | admin file added | `"true"` |
| 8 | USER_UPLOAD alice shared.pdf 10 (conflict) | unchanged | `""` |
| 9 | USER_GET alice doc.txt | — | `"300"` |
| 10 | USER_GET bob doc.txt | — | `""` (alice owns it) |
| 11 | USER_COPY alice doc.txt → doc2.txt | alice used=600 | `"400"` |
| 12 | USER_COPY bob doc.txt → img2.png | doc.txt not bob's | `""` |
| 13 | USER_SEARCH alice doc | — | `"doc.txt(300), doc2.txt(300)"` |
| 14 | USER_SEARCH bob "" | — | `"img.png(200)"` |

Final return value:

```python
["true", "true", "false", "700", "", "300", "true", "", "300", "", "400", "", "doc.txt(300), doc2.txt(300)", "img.png(200)"]
```

**Trace check for query 13:** Alice owns `doc.txt(300)` and `doc2.txt(300)`. Both match prefix `"doc"`. Same size → sort by name asc → `doc.txt` before `doc2.txt`. Result: `"doc.txt(300), doc2.txt(300)"`.

## Constraints

- All Level 1 and Level 2 constraints still hold.
- `<capacity>` and `<size>` are positive integer strings.
- Capacity check is `used + new_size <= capacity` (equality is allowed — exactly fills capacity is OK).
- `USER_SEARCH` returns `""` for a nonexistent user (don't return files for missing users).
- `FILE_*` operations remain unchanged — they don't check user capacity.

## Common gotchas

1. **Global namespace for names.** `USER_UPLOAD` must check against ALL files (admin + every user), not just this user's files.
2. **Capacity boundary: exactly-fits is valid.** `used + size == capacity` returns `"0"`, not `""`.
3. **`USER_COPY` overwrite frees the old file first.** Forgetting to subtract old_dest_size before adding source_size causes a double-count.
4. **`USER_GET` returns `""` for files owned by others — not the file's size.** Ownership check is required.
5. **`USER_SEARCH` on a nonexistent user returns `""`** — don't accidentally return all files with a given prefix.

## When you're done

```
cd 03-file-system
python3 test_level3.py
```

All tests must pass before Level 4 is revealed.
