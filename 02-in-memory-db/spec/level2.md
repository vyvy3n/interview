# Level 2 — SCAN and SCAN_BY_PREFIX

## What you're implementing

Level 2 adds two new commands to the database you built in Level 1. All three Level 1 commands (`SET`, `GET`, `DELETE`) continue to work exactly as before.

## Mental model

SCAN is the "list all fields" operation. You've already been storing `(key → {field → value})`. Now you need to enumerate the fields at a given key — optionally filtered by a prefix — and return them in a formatted string. The tricky part is the output format and the alphabetical ordering requirement.

Think of SCAN as a SELECT * on a single row, and SCAN_BY_PREFIX as a SELECT with a WHERE clause on the column name.

## The 2 commands for Level 2

### 1. `["SCAN", <ts>, <key>]`

List all (field, value) pairs stored under `key`, sorted alphabetically by field name (ascending).

| Situation | Return |
|-----------|--------|
| `key` has one or more fields | `"field1(value1), field2(value2), ..."` |
| `key` does not exist | `""` (empty string) |
| `key` exists but has no fields (all were deleted) | `""` (empty string) |

Output format details:
- Each entry is `fieldName(value)` — field name, immediately followed by `(value)` with no space before the `(`.
- Entries are separated by `", "` (comma then space).
- The entire result is a single string with no trailing comma or space.

### 2. `["SCAN_BY_PREFIX", <ts>, <key>, <prefix>]`

Same as SCAN but filtered to only fields whose name **starts with** `prefix`.

| Situation | Return |
|-----------|--------|
| One or more fields match | same format as SCAN, alphabetically sorted |
| No fields match (or key missing) | `""` (empty string) |

## Worked example — trace through it

```python
queries = [
    ["SET",            "1", "planet", "name",        "earth"],
    ["SET",            "2", "planet", "diameter_km",  "12742"],
    ["SET",            "3", "planet", "distance_au",  "1.0"],
    ["SET",            "4", "planet", "color",        "blue"],
    ["SCAN",           "5", "planet"],
    ["SCAN_BY_PREFIX", "6", "planet", "d"],
    ["SCAN_BY_PREFIX", "7", "planet", "diameter"],
    ["SCAN_BY_PREFIX", "8", "planet", "z"],
    ["SCAN",           "9", "moon"],
    ["DELETE",         "10", "planet", "color"],
    ["DELETE",         "11", "planet", "name"],
    ["SCAN",           "12", "planet"],
]
```

State after queries 1-4: `{"planet": {"name": "earth", "diameter_km": "12742", "distance_au": "1.0", "color": "blue"}}`

| # | Query | Output | Notes |
|---|-------|--------|-------|
| 5 | `SCAN planet` | `"color(blue), diameter_km(12742), distance_au(1.0), name(earth)"` | all 4 fields, alpha order |
| 6 | `SCAN_BY_PREFIX planet d` | `"diameter_km(12742), distance_au(1.0)"` | "d" matches diameter_km, distance_au |
| 7 | `SCAN_BY_PREFIX planet diameter` | `"diameter_km(12742)"` | only exact prefix match |
| 8 | `SCAN_BY_PREFIX planet z` | `""` | no matches |
| 9 | `SCAN moon` | `""` | key doesn't exist |
| 10 | `DELETE planet color` | `"true"` | deleted |
| 11 | `DELETE planet name` | `"true"` | deleted |
| 12 | `SCAN planet` | `"diameter_km(12742), distance_au(1.0)"` | only remaining fields |

Final return value (only showing rows 5-12):

```python
[
    "color(blue), diameter_km(12742), distance_au(1.0), name(earth)",
    "diameter_km(12742), distance_au(1.0)",
    "diameter_km(12742)",
    "",
    "",
    "true",
    "true",
    "diameter_km(12742), distance_au(1.0)",
]
```

## Constraints

- All Level 1 constraints still apply.
- `<prefix>` is a non-empty string.
- A field "starts with prefix" means Python's `str.startswith(prefix)` returns `True`.
- Output is alphabetically sorted by field name (standard Python `sorted()` order).

## Common gotchas

1. **Alphabetical sort is on the field name, not on `fieldName(value)`** — sort your list of fields first, then format; don't sort the formatted strings.
2. **Empty key after all deletes** — if every field under a key has been deleted, SCAN must return `""`, not a weird empty format like `""` inside a list. Simply check if the inner dict is empty (or doesn't exist).
3. **Output format: no trailing separator** — `"a(1), b(2)"` is correct; `"a(1), b(2), "` is wrong. Use `", ".join(...)`.
4. **SCAN_BY_PREFIX with an empty result** — even if the key exists and has fields, if none match the prefix, return `""` not `"()"` or any other non-empty string.
5. **Prefix is case-sensitive** — `"D"` does not match `"diameter_km"`. Use exact Python `startswith`.

## When you're done

```
cd 02-in-memory-db
python3 test_level2.py
```

All Level 1 AND Level 2 tests must pass before moving to Level 3.
