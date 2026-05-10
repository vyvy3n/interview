# Level 4 — Prefix-Cache Lookup and Bulk Invalidation

## What you're implementing

You extend `solution(queries)` with two new commands: `PREFIX_LOOKUP` and `INVALIDATE_PREFIX`. All Level 1, 2, and 3 commands continue to work unchanged.

```python
def solution(queries: list[list[str]]) -> list[str]:
    ...
```

## Mental model

This is the hardest and most realistic level — it mirrors how modern LLM inference engines like vLLM and TensorRT-LLM actually reuse computation.

**KV-cache prefix matching:** When an LLM processes a prompt, it computes a "KV cache" — a per-token attention state — for each token in the prompt. If a new prompt *starts with* an already-cached prompt, the server can reuse all the KV states up to the cached prefix length, only computing the new suffix. This is called "prefix caching" or "RadixAttention."

`PREFIX_LOOKUP` simulates this: given a new incoming prompt, find the longest currently-cached prompt that is a string prefix of it. Returning that prompt tells the caller "here's the prefix you can reuse from cache — your GPU only needs to process the remainder."

**Bulk invalidation:** When a system prompt or a document used in many prompts changes, you need to invalidate all cache entries whose prompt starts with that changed prefix — potentially thousands of entries at once.

`INVALIDATE_PREFIX` handles this: delete every cached entry (live or expired) whose prompt key starts with the given prefix string.

## The 2 commands for Level 4

### 1. `["PREFIX_LOOKUP", <ts>, <new_prompt>]`

Find the longest currently-cached prompt that is a **string prefix** of `new_prompt`.

| Situation | Return |
|-----------|--------|
| A matching prefix exists | the matching prompt string (not its response) |
| No cached prompt is a prefix of `new_prompt` | `""` (empty string) |

**"Currently cached"** means the entry is present in the cache AND not expired at timestamp `ts`.

**Prefix definition:** prompt P is a prefix of new_prompt N if `N.startswith(P)`. This includes the case where P == N (exact match is a valid prefix match).

**Tie-breaking:** if multiple cached prompts are prefixes of `new_prompt` and they have the **same length** (impossible since two different strings of equal length can't both be prefixes of N unless they're equal), this can't actually happen. But if for some reason ties arise by length — break ties by prompt string **alphabetical ascending**.

**Side effects:** A successful `PREFIX_LOOKUP` (match found) counts as a `CACHE_GET` hit on the matched prompt:
- Increments that prompt's hit count by 1.
- Updates that prompt's `last_access` to `ts` (for LRU purposes).

If no match is found, no side effects.

### 2. `["INVALIDATE_PREFIX", <ts>, <prefix>]`

Delete all cached entries whose prompt **starts with** `prefix`.

| Situation | Return |
|-----------|--------|
| Always | count of entries deleted as string |

**Scope:** deletes both live **and** expired entries whose prompt starts with `prefix`. (Expired entries are invisible to most operations but still occupy storage — bulk invalidation cleans them up too.)

Returns `"0"` if no entries match.

**Side effects:** Deleted entries lose their hit counts (same as `CACHE_DELETE`).

**Note:** `prefix` itself may or may not be in the cache. If `prefix` is `"abc"` and the cache contains `"abcdef"` and `"abcxyz"`, both are deleted.

## Worked example — trace through it

```python
queries = [
    ["CACHE_PUT",         "1",  "You are a helpful assistant.",            "sys-resp"],
    ["CACHE_PUT",         "2",  "You are a helpful assistant. User: hi",   "hi-resp"],
    ["CACHE_PUT",         "3",  "You are a helpful assistant. User: bye",  "bye-resp"],
    ["CACHE_PUT",         "4",  "Tell me a joke",                          "joke-resp"],
    ["PREFIX_LOOKUP",     "5",  "You are a helpful assistant. User: hi, how are you?"],
    ["PREFIX_LOOKUP",     "6",  "You are a helpful assistant. User: hi"],
    ["PREFIX_LOOKUP",     "7",  "Completely different prompt"],
    ["HIT_COUNT",         "8",  "You are a helpful assistant. User: hi"],
    ["HIT_COUNT",         "9",  "You are a helpful assistant."],
    ["INVALIDATE_PREFIX", "10", "You are a helpful assistant"],
    ["CACHE_GET",         "11", "Tell me a joke"],
    ["CACHE_GET",         "12", "You are a helpful assistant."],
    ["PREFIX_LOOKUP",     "13", "You are a helpful assistant. User: hello"],
]
```

Initial state: `{}`, capacity = unlimited

| # | ts | Query | Notes | Output |
|---|----|----|---|---|
| 1 | 1 | `CACHE_PUT "You are a helpful assistant."` | Stored. hits=0, la=1 | `""` |
| 2 | 2 | `CACHE_PUT "You are a helpful assistant. User: hi"` | Stored. hits=0, la=2 | `""` |
| 3 | 3 | `CACHE_PUT "You are a helpful assistant. User: bye"` | Stored. hits=0, la=3 | `""` |
| 4 | 4 | `CACHE_PUT "Tell me a joke"` | Stored. hits=0, la=4 | `""` |
| 5 | 5 | `PREFIX_LOOKUP "You are a helpful assistant. User: hi, how are you?"` | Two cached entries are prefixes: "You are a helpful assistant." (29 chars) and "You are a helpful assistant. User: hi" (37 chars). Longest wins → `"You are a helpful assistant. User: hi"`. Hit count increments → hits=1, la=5. | `"You are a helpful assistant. User: hi"` |
| 6 | 6 | `PREFIX_LOOKUP "You are a helpful assistant. User: hi"` | Exact match is a valid prefix. "You are a helpful assistant." (29 chars) and "You are a helpful assistant. User: hi" (37 chars, exact) both match. Longest wins → `"You are a helpful assistant. User: hi"`. Hits→2, la=6. | `"You are a helpful assistant. User: hi"` |
| 7 | 7 | `PREFIX_LOOKUP "Completely different prompt"` | No cached entry is a prefix of this. | `""` |
| 8 | 8 | `HIT_COUNT "You are a helpful assistant. User: hi"` | 2 hits from steps 5 and 6. | `"2"` |
| 9 | 9 | `HIT_COUNT "You are a helpful assistant."` | Never hit directly. | `"0"` |
| 10 | 10 | `INVALIDATE_PREFIX "You are a helpful assistant"` | All 3 "You are a helpful assistant*" entries deleted (live+expired). "Tell me a joke" doesn't start with that prefix. | `"3"` |
| 11 | 11 | `CACHE_GET "Tell me a joke"` | Still in cache. | `"joke-resp"` |
| 12 | 12 | `CACHE_GET "You are a helpful assistant."` | Deleted in step 10 → miss. | `""` |
| 13 | 13 | `PREFIX_LOOKUP "You are a helpful assistant. User: hello"` | No entries starting with "You are..." remain. | `""` |

Final return value:

```python
["", "", "", "", "You are a helpful assistant. User: hi", "You are a helpful assistant. User: hi", "", "2", "0", "3", "joke-resp", "", ""]
```

Key trace notes:
- Step 5: The new prompt `"You are a helpful assistant. User: hi, how are you?"` starts with both `"You are a helpful assistant."` AND `"You are a helpful assistant. User: hi"`. The longer match wins (37 chars > 29 chars).
- Step 6: An exact match is a valid prefix match (the string starts with itself). The 37-char entry matches exactly.
- Step 10: `INVALIDATE_PREFIX "You are a helpful assistant"` — note no trailing period. All three "You are a helpful assistant*" prompts start with this string. "Tell me a joke" does not.

## Constraints

- All Level 1, 2, and 3 constraints still apply.
- `<new_prompt>` in `PREFIX_LOOKUP` is a non-empty string.
- `<prefix>` in `INVALIDATE_PREFIX` is a non-empty string.
- Up to `10^5` queries total; up to `10^5` cached entries at any time.
- For `PREFIX_LOOKUP`, a linear scan over all cache entries is acceptable. Trie-based solutions are not required (but earn bonus points conceptually).

## Common gotchas

1. **Exact match is a valid prefix match** — if the new prompt is identical to a cached prompt, that cached entry is a valid match (length = len(new_prompt)).
2. **PREFIX_LOOKUP only matches non-expired entries** — respect TTL just like CACHE_GET does.
3. **PREFIX_LOOKUP updates hit count and last_access on the matched entry** — it's a real cache hit, not just a lookup.
4. **INVALIDATE_PREFIX deletes both live AND expired entries** — unlike most operations, it doesn't treat expired entries as invisible. It cleans up storage.
5. **INVALIDATE_PREFIX with no matching entries returns `"0"`, not `""`** — this is always a numeric response.
6. **Multiple cached prompts may be prefixes of the new prompt** — you must find the *longest* one, not the first one or the exact match. Longest by string length wins; ties (different strings of equal length cannot both be strict prefixes of the same string) are broken alphabetically.

## When you're done

```
cd 06-llm-prompt-cache
python3 test_level4.py
```

All Level 4 tests must pass. Congratulations — you've implemented the core of a production LLM KV-cache serving layer.
