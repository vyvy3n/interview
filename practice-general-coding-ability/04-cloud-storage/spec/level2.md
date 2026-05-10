# Level 2 — Usage Reports

## What you're implementing

All Level 1 operations still work. You add two new commands for reporting and ranking.

## Mental model

Your storage server now needs to answer management queries: "how much is user X using?" and "who are my top storage consumers?". These are read-only — they don't change state. The tricky part is `TOP_K_USERS`: you must sort correctly (descending by usage, ascending by user_id on ties), build the formatted string correctly, and handle edge cases (fewer than k users, zero-usage users included in ranking).

## The 2 new commands for Level 2

### 4. `["GET_USAGE", <timestamp>, <user_id>]`

Return the user's used bytes and quota as a formatted fraction.

| Situation | Return |
|-----------|--------|
| User exists | `"<used>/<quota>"` e.g. `"300/1000"` |
| User does not exist | `""` (empty string) |

### 5. `["TOP_K_USERS", <timestamp>, <k>]`

Return the top `k` users ranked by **used bytes descending**. Ties are broken by **user_id ascending** (alphabetical). All users are eligible, including those with 0 usage.

- If fewer than `k` users exist, return all users in rank order.
- Format each user as `"<user_id>(<used>/<quota>)"` and join with `", "` (comma then space).

| Situation | Return |
|-----------|--------|
| At least 1 user exists | comma+space-separated ranked list |
| No users exist at all | `""` (empty string) |

**Example format:** `"alice(800/1000), bob(300/400), carol(0/200)"`

## Worked example — trace through it

```python
queries = [
    ["CREATE_USER",   "1", "alice", "1000"],
    ["CREATE_USER",   "2", "bob",   "400"],
    ["CREATE_USER",   "3", "carol", "200"],
    ["UPLOAD",        "4", "alice", "doc",   "800"],
    ["UPLOAD",        "5", "bob",   "img",   "300"],
    ["GET_USAGE",     "6", "alice"],
    ["GET_USAGE",     "7", "dave"],
    ["TOP_K_USERS",   "8", "2"],
    ["TOP_K_USERS",   "9", "5"],
    ["DELETE",        "10","bob",   "img"],
    ["TOP_K_USERS",   "11","3"],
]
```

State after uploads: alice used=800/1000, bob used=300/400, carol used=0/200.

| # | Query | Output | Reason |
|---|-------|--------|--------|
| 1-5 | setup | `"true","true","true","800","300"` | standard L1 ops |
| 6 | GET_USAGE alice | `"800/1000"` | 800 used of 1000 |
| 7 | GET_USAGE dave | `""` | user not found |
| 8 | TOP_K_USERS 2 | `"alice(800/1000), bob(300/400)"` | top 2 by usage |
| 9 | TOP_K_USERS 5 | `"alice(800/1000), bob(300/400), carol(0/200)"` | only 3 users exist |
| 10 | DELETE bob img | `"true"` | bob used → 0 |
| 11 | TOP_K_USERS 3 | `"alice(800/1000), bob(0/400), carol(0/200)"` | bob and carol both 0; bob < carol alphabetically |

Final return value:

```python
["true", "true", "true", "800", "300",
 "800/1000", "",
 "alice(800/1000), bob(300/400)",
 "alice(800/1000), bob(300/400), carol(0/200)",
 "true",
 "alice(800/1000), bob(0/400), carol(0/200)"]
```

## Constraints

- `<k>` is a positive integer string (`>= 1`).
- Users with 0 usage **are included** in TOP_K_USERS (they just rank last).
- All Level 1 constraints still apply.

## Common gotchas

1. **Tie-breaking is required**: two users with identical used bytes must appear in alphabetical order by user_id. Don't rely on insertion order.
2. **k larger than user count**: silently return all users — don't pad or error.
3. **Format precision**: the separator is `", "` (comma + one space). Missing the space or using a different separator fails string comparison.
4. **Zero-usage users still appear**: `TOP_K_USERS` is not a "top active users" query — every user is ranked.
5. **GET_USAGE reflects deletes**: if a file was deleted, the freed space is immediately reflected. There's no stale cache to worry about if your data model is correct.

## When you're done

```
cd 04-cloud-storage
python3 test_level2.py
```

All tests must pass before moving to Level 3.
