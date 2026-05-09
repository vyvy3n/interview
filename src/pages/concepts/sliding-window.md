---
layout: ../../layouts/Layout.astro
title: Sliding Window
---

# Sliding Window

Maintain a window `[l, r]` over a sequence; expand `r`, shrink `l` to keep an invariant.

## When to use

- Longest / shortest subarray with property
- Substring problems with character counts
- Fixed-size sums or averages

## Pattern: variable window

```python
def longest_no_repeat(s):
    seen = {}
    l = best = 0
    for r, c in enumerate(s):
        if c in seen and seen[c] >= l:
            l = seen[c] + 1
        seen[c] = r
        best = max(best, r - l + 1)
    return best
```

## Pattern: fixed window

```python
def max_sum_k(nums, k):
    s = sum(nums[:k])
    best = s
    for i in range(k, len(nums)):
        s += nums[i] - nums[i - k]
        best = max(best, s)
    return best
```

## Gotchas

- Reset / move `l` only when invariant breaks; don't reset `seen` map.
- Off-by-one on window length: `r - l + 1`.

## Practice

- **Longest Substring Without Repeating Characters** — longest contiguous substring with all distinct chars. *Insight:* dict of char→last-index; when seeing a repeat inside the window, jump `l` past the previous occurrence. [LC 3](https://leetcode.com/problems/longest-substring-without-repeating-characters/)
- **Minimum Window Substring** — smallest window in `s` containing all chars of `t` (with multiplicity). *Insight:* expand `r` until valid (`have == need`); contract `l` while still valid; track best. [LC 76](https://leetcode.com/problems/minimum-window-substring/)
- **Max Sum Subarray of Size K** — fixed-size window: max sum over all length-K subarrays. *Insight:* compute first window, then slide by adding `nums[r] - nums[r-k]`. [LC 643 variant](https://leetcode.com/problems/maximum-average-subarray-i/)
- **Permutation in String** — does `s2` contain any permutation of `s1` as a substring? *Insight:* fixed-size window of `len(s1)`; compare 26-letter count vector to `s1`'s. [LC 567](https://leetcode.com/problems/permutation-in-string/)
- **Longest Substring with At Most K Distinct Chars** — longest window with ≤K distinct characters. *Insight:* counter dict; shrink from left when distinct count exceeds K. [LC 340](https://leetcode.com/problems/longest-substring-with-at-most-k-distinct-characters/)
- **Subarrays with K Different Integers** — count subarrays with exactly K distinct ints. *Insight:* `exactly(K) = atMost(K) - atMost(K-1)`. [LC 992](https://leetcode.com/problems/subarrays-with-k-different-integers/)
