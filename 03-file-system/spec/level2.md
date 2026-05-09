# Level 2 — Prefix Search

## What you're implementing

Level 1 operations still work unchanged. Add one new operation: `FILE_SEARCH`.

## Mental model

You now need to search files by name prefix and return the "most important" results first. Importance is defined as: **largest file first** (by size, descending). When two files have the same size, break the tie **alphabetically by name, ascending** (so `alpha.txt` comes before `beta.txt` if they're the same size).

Cap the result at **10 files**. Return them as a single comma-space-separated string: `"name1(size1), name2(size2), ..."`.

There's no special data structure required here — a simple scan + sort works fine at interview scale. But think about what "prefix" means: `"re"` matches `"report.pdf"` and `"readme.txt"` but not `"archive.pdf"`.

## The 1 new command for Level 2

### 4. `["FILE_SEARCH", <timestamp>, <prefix>]`

Return the top-10 files whose name **starts with** `<prefix>`, sorted by size descending, ties broken by name ascending.

| Situation | Return |
|-----------|--------|
| 1 or more files match | `"name1(size1), name2(size2), ..."` (up to 10, comma+space sep.) |
| No files match | `""` (empty string) |

**Format detail:** each entry is `name(size)` with no spaces inside the parentheses. Example: `"report.pdf(500), notes.txt(200)"`.

## Worked example — trace through it

```python
queries = [
    ["FILE_UPLOAD", "1",  "alpha.txt",  "300"],
    ["FILE_UPLOAD", "2",  "alpha.md",   "300"],   # same size as alpha.txt
    ["FILE_UPLOAD", "3",  "beta.txt",   "500"],
    ["FILE_UPLOAD", "4",  "alphabet",   "100"],
    ["FILE_UPLOAD", "5",  "gamma.txt",  "200"],
    ["FILE_SEARCH", "6",  "alpha"],               # matches alpha.txt, alpha.md, alphabet
    ["FILE_SEARCH", "7",  "be"],                  # matches beta.txt
    ["FILE_SEARCH", "8",  "zz"],                  # no match
    ["FILE_SEARCH", "9",  ""],                    # empty prefix matches everything
    ["FILE_SEARCH", "10", "ALPHA"],               # case-sensitive — no match
]
```

Matching and sorting for query 6 (`prefix="alpha"`):
- Candidates: `alpha.txt(300)`, `alpha.md(300)`, `alphabet(100)`
- Sort: size desc → `alpha.md(300)` and `alpha.txt(300)` tied at 300; `alphabet(100)` last
- Tie-break by name asc: `alpha.md` < `alpha.txt` alphabetically
- Result: `"alpha.md(300), alpha.txt(300), alphabet(100)"`

| # | Query | Output |
|---|-------|--------|
| 1–5 | FILE_UPLOAD × 5 | `"true"` × 5 |
| 6 | `FILE_SEARCH alpha` | `"alpha.md(300), alpha.txt(300), alphabet(100)"` |
| 7 | `FILE_SEARCH be` | `"beta.txt(500)"` |
| 8 | `FILE_SEARCH zz` | `""` |
| 9 | `FILE_SEARCH ""` (empty prefix) | `"beta.txt(500), alpha.md(300), alpha.txt(300), gamma.txt(200), alphabet(100)"` |
| 10 | `FILE_SEARCH ALPHA` | `""` |

Final return value:

```python
["true", "true", "true", "true", "true",
 "alpha.md(300), alpha.txt(300), alphabet(100)",
 "beta.txt(500)",
 "",
 "beta.txt(500), alpha.md(300), alpha.txt(300), gamma.txt(200), alphabet(100)",
 ""]
```

## Constraints

- All Level 1 constraints still hold.
- Prefix matching is **case-sensitive**.
- An **empty prefix** (`""`) matches every file.
- If fewer than 10 files match, return all of them (no padding).
- If more than 10 files match, return only the top 10 after sorting.

## Common gotchas

1. **Sort is (size DESC, name ASC) — not size ASC.** A common mistake is sorting in the wrong direction for size.
2. **Ties broken by name ascending.** `"a.txt"` before `"b.txt"` when sizes match — same direction as `str.sort()` default.
3. **Empty prefix is valid and matches everything.** Don't early-return on empty string.
4. **Return `""`, not `"[]"` or `"none"`, when nothing matches.**
5. **Cap at exactly 10.** If 15 files match, return only the top 10 after sorting — not all 15.

## When you're done

```
cd 03-file-system
python3 test_level2.py
```

All tests must pass before Level 3 is revealed.
