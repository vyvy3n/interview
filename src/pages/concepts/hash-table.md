---
layout: ../../layouts/Layout.astro
title: Hash Table Tricks
---

# Hash Table Tricks

> O(1) average lookup. The default tool to convert "for every pair" O(n²) brute force into O(n).

## When to use

- Two-sum family (looking up complement)
- Counting frequencies / first-occurrence index
- Grouping (anagrams, by some key)
- "Have I seen this prefix sum / state before?"
- Caching / memoization (`@functools.cache`)

## Two-sum (the canonical pattern)

```python
def two_sum(nums, target):
    seen = {}            # value → index
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
```

Insert *after* checking — handles `x + x = target` correctly only if duplicates allowed.

## Group anagrams (key by sorted tuple or count)

```python
from collections import defaultdict
def group_anagrams(strs):
    g = defaultdict(list)
    for s in strs:
        g[tuple(sorted(s))].append(s)
        # alt key: tuple of 26-letter counts
    return list(g.values())
```

## Prefix-sum hash (subarray with sum K)

```python
def subarray_sum_k(nums, k):
    seen = {0: 1}        # one empty prefix
    s = ans = 0
    for x in nums:
        s += x
        ans += seen.get(s - k, 0)
        seen[s] = seen.get(s, 0) + 1
    return ans
```

Generalizes: replace `s` with running mod / running parity / running multiset hash.

## Sliding-window count (longest substring with at most K distinct)

```python
def longest_k_distinct(s, k):
    cnt = {}
    l = best = 0
    for r, c in enumerate(s):
        cnt[c] = cnt.get(c, 0) + 1
        while len(cnt) > k:
            cnt[s[l]] -= 1
            if cnt[s[l]] == 0: del cnt[s[l]]
            l += 1
        best = max(best, r - l + 1)
    return best
```

## Counter (`collections.Counter`) idioms

```python
from collections import Counter
Counter("abcab")           # → {'a': 2, 'b': 2, 'c': 1}
Counter(a) == Counter(b)   # are anagrams?
Counter(a) - Counter(b)    # multiset difference (negatives drop)
Counter(a).most_common(3)  # top 3
```

## Gotchas

- Lists/dicts aren't hashable — convert to `tuple` / `frozenset` for keys.
- For ordered iteration, Python 3.7+ dicts preserve insertion order; `OrderedDict.move_to_end` is still useful for LRU.
- `defaultdict(list)` saves a `setdefault` dance but creates entries on read — careful when checking membership.
- Negative-number prefix hashes: store `(running_state)` as int, mod with `m` only after taking mod.

## Practice

- **Two Sum** — indices of two numbers summing to target. *Insight:* one-pass hash; check `target - x` *before* inserting `x`. [LC 1](https://leetcode.com/problems/two-sum/)
- **4Sum II** — count tuples `(i,j,k,l)` from 4 arrays where `A+B+C+D=0`. *Insight:* hash sums of pairs from the first two arrays; lookup `-(C+D)` from pairs of last two. O(n²) instead of O(n⁴). [LC 454](https://leetcode.com/problems/4sum-ii/)
- **Group Anagrams** — group strings that are anagrams of each other. *Insight:* hash key = sorted string OR 26-tuple of counts. [LC 49](https://leetcode.com/problems/group-anagrams/)
- **Subarray Sum Equals K** — count subarrays summing to K. *Insight:* hash of `prefix_sum → count`; for each prefix, add count of `prefix - k` previously seen. [LC 560](https://leetcode.com/problems/subarray-sum-equals-k/)
- **Longest Substring with At Most K Distinct Chars** — longest substring containing ≤K distinct. *Insight:* sliding window + counter dict; shrink from left while distinct count > K. [LC 340](https://leetcode.com/problems/longest-substring-with-at-most-k-distinct-characters/)
- **Continuous Subarray Sum** — any subarray length ≥ 2 summing to a multiple of K? *Insight:* prefix mod K; if same mod seen at indices ≥ 2 apart, slice between is divisible by K. [LC 523](https://leetcode.com/problems/continuous-subarray-sum/)
- **Find All Anagrams in a String** — start indices of all anagrams of `p` in `s`. *Insight:* fixed-window of `len(p)`; compare 26-letter count vector to `p`'s. [LC 438](https://leetcode.com/problems/find-all-anagrams-in-a-string/)
- **Longest Consecutive Sequence** — longest run of consecutive ints in unsorted array (O(n)). *Insight:* hash all nums; only start counting from `x` if `x-1` is not in set (avoid duplicate work). [LC 128](https://leetcode.com/problems/longest-consecutive-sequence/)
