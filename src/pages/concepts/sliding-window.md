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

## Example questions

- Longest Substring Without Repeating Characters
- Minimum Window Substring
- Max Sum Subarray of Size K
- Permutation in String
