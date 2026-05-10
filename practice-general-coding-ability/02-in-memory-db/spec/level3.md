# Level 3 — TTL / Expiration

## What you're implementing

Level 3 adds two new commands that let entries expire after a specified time-to-live. All Level 1 and Level 2 commands continue to work — but now every read-like operation must check whether an entry has expired before returning it.

## Mental model

Each `(key, field)` entry can now have an optional **expiry timestamp**. When a query arrives at timestamp `ts`, any entry whose expiry timestamp is `<= ts` is treated as if it does not exist.

The interval is **half-open**: an entry set with `ts=10, ttl=5` is valid for queries at timestamps 10, 11, 12, 13, 14 — and expired at timestamp 15 (`10 + 5`). The expiry formula is `expiry = set_ts + ttl`.

Entries created with plain `SET` (Level 1) never expire. Entries created with `SET_WITH_TTL` expire unless their TTL is updated or overwritten.

## The 2 commands for Level 3

### 1. `["SET_WITH_TTL", <ts>, <key>, <field>, <value>, <ttl>]`

Set `(key, field) = value` and schedule it to expire at `ts + int(ttl)`.

| Situation | Return |
|-----------|--------|
| Always | `""` (empty string) |

Rules:
- If `(key, field)` already existed (with or without a TTL), overwrite completely: new value, new expiry.
- `ttl` is a positive integer string.
- Expiry timestamp = `int(ts) + int(ttl)`.

### 2. `["UPDATE_TTL", <ts>, <key>, <field>, <ttl>]`

Re-anchor the TTL on an existing entry. New expiry = `int(ts) + int(ttl)`.

| Situation | Return |
|-----------|--------|
| `(key, field)` exists AND is not expired at `ts` | `"true"` — expiry updated |
| `(key, field)` does not exist | `"false"` |
| `(key, field)` is expired at `ts` (expiry `<= ts`) | `"false"` |

Rules:
- Only updates the expiry; **does not change the value**.
- Works on entries with or without an existing TTL (you can add a TTL to a plain-SET entry via UPDATE_TTL).

## TTL semantics that apply to ALL operations

Starting at Level 3, every operation that reads or deletes data must check expiry:

- **GET**: return `""` if the entry is expired.
- **DELETE**: return `"false"` if the entry is expired (treat as nonexistent).
- **SCAN / SCAN_BY_PREFIX**: exclude expired fields from the result.
- **UPDATE_TTL**: return `"false"` if the entry is expired.
- **SET_WITH_TTL overwriting an expired entry**: allowed — the new entry replaces the old one (which is gone conceptually).
- **SET (plain)**: if it overwrites a `SET_WITH_TTL` entry, the new entry has **no TTL** (never expires).

**Expiry check:** an entry with expiry `E` is expired at query timestamp `ts` if `ts >= E`.
Equivalently: valid while `ts < E`.

## Worked example — trace through it

```python
queries = [
    ["SET_WITH_TTL", "10", "session", "token", "abc123", "5"],
    ["GET",          "12", "session", "token"],
    ["GET",          "15", "session", "token"],
    ["SET_WITH_TTL", "20", "session", "token", "xyz999", "10"],
    ["UPDATE_TTL",   "22", "session", "token", "3"],
    ["GET",          "24", "session", "token"],
    ["GET",          "25", "session", "token"],
    ["SET",          "30", "session", "token", "permanent"],
    ["GET",          "50", "session", "token"],
    ["UPDATE_TTL",   "60", "session", "token", "100"],
    ["GET",          "61", "session", "token"],
]
```

Working through each step:

| # | Query | Expiry after | Output | Explanation |
|---|-------|--------------|--------|-------------|
| 1 | `SET_WITH_TTL 10 session token abc123 5` | expiry=15 | `""` | set, expires at 10+5=15 |
| 2 | `GET 12 session token` | expiry=15 | `"abc123"` | ts=12 < 15, still valid |
| 3 | `GET 15 session token` | expiry=15 | `""` | ts=15 >= 15, EXPIRED |
| 4 | `SET_WITH_TTL 20 session token xyz999 10` | expiry=30 | `""` | reset, expires at 20+10=30 |
| 5 | `UPDATE_TTL 22 session token 3` | expiry=25 | `"true"` | ts=22 < 30, valid; new expiry=22+3=25 |
| 6 | `GET 24 session token` | expiry=25 | `"xyz999"` | ts=24 < 25, valid |
| 7 | `GET 25 session token` | expiry=25 | `""` | ts=25 >= 25, EXPIRED |
| 8 | `SET 30 session token permanent` | no expiry | `""` | plain SET removes TTL |
| 9 | `GET 50 session token` | no expiry | `"permanent"` | no TTL, never expires |
| 10 | `UPDATE_TTL 60 session token 100` | expiry=160 | `"true"` | plain entry can gain a TTL |
| 11 | `GET 61 session token` | expiry=160 | `"permanent"` | ts=61 < 160, still valid |

Final return value:

```python
["", "abc123", "", "", "true", "xyz999", "", "", "permanent", "true", "permanent"]
```

## Constraints

- All Level 1 and Level 2 constraints still apply.
- `ttl` is always a positive integer string (`>= 1`).
- Timestamps are strictly increasing across all queries (both TTL and non-TTL operations).
- An entry may be overwritten any number of times.

## Common gotchas

1. **The half-open interval** — expired AT `ts + ttl`, not after. At exactly `expiry_ts`, the entry is GONE. Test right at the boundary: if you set with ttl=5 at ts=10, a GET at ts=15 must return `""`.
2. **UPDATE_TTL on an expired entry returns `"false"`** — even though the key/field would be there in your dict. You must check expiry before updating.
3. **Plain SET clears TTL** — if you store expiry as `None` for no-TTL entries, make sure SET (not SET_WITH_TTL) sets expiry back to `None`, even if overwriting a TTL'd entry.
4. **SCAN must skip expired fields** — don't just filter by field name; also filter out fields where `current_ts >= expiry`.
5. **DELETE on an expired entry returns `"false"`** — expired = nonexistent. Do not physically remove it and return `"true"`.

## When you're done

```
cd 02-in-memory-db
python3 test_level3.py
```

All Level 1, 2, and 3 tests must pass before moving to Level 4.
