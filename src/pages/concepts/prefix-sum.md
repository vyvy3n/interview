---
layout: ../../layouts/Layout.astro
title: Prefix Sum
---

# Prefix Sum

> Precompute cumulative sums so any range sum is O(1).

## When to use

- "Sum of subarray from i to j" called many times
- "Subarray with sum equal to K" → prefix-sum + hash
- Difference array (range updates)
- Product of array except self (left-product × right-product)

## Template

```python
def build(nums):
    pre = [0] * (len(nums) + 1)
    for i, x in enumerate(nums):
        pre[i + 1] = pre[i] + x
    return pre

def range_sum(pre, l, r):  # inclusive [l, r]
    return pre[r + 1] - pre[l]
```

## Subarray sum equals K (with hash)

```python
def subarray_sum(nums, k):
    seen = {0: 1}     # prefix → count
    s = ans = 0
    for x in nums:
        s += x
        ans += seen.get(s - k, 0)
        seen[s] = seen.get(s, 0) + 1
    return ans
```

## Product except self (no division)

```python
def product_except_self(nums):
    n = len(nums)
    out = [1] * n
    left = 1
    for i in range(n):
        out[i] = left
        left *= nums[i]
    right = 1
    for i in range(n - 1, -1, -1):
        out[i] *= right
        right *= nums[i]
    return out
```

## Gotchas

- Off-by-one: `pre[i+1] - pre[l]` for inclusive range `[l, i]`. Pad with a leading 0.
- For 2D: build `pre[i+1][j+1]` and use inclusion-exclusion.
- Hash version: seed with `{0: 1}` so a prefix that *itself* equals K is counted.

## Practice

- **Subarray Sum Equals K** — count contiguous subarrays whose sum is exactly K. *Insight:* running prefix `s`; for each `s` count how many earlier prefixes equal `s - k`. Hash map + seed `{0: 1}`. [LC 560](https://leetcode.com/problems/subarray-sum-equals-k/)
- **Product of Array Except Self** — `out[i] = product of all nums except nums[i]`, no division, O(n). *Insight:* one left-to-right pass building "product of everything to the left", one right-to-left pass multiplying in "everything to the right". [LC 238](https://leetcode.com/problems/product-of-array-except-self/)
- **Range Sum Query 2D — Immutable** — many `sum(rect)` queries on a static grid. *Insight:* 2D prefix sum `P[i+1][j+1]`; range sum = `P[r+1][c+1] - P[r+1][cl] - P[rr][c+1] + P[rr][cl]` (inclusion-exclusion). [LC 304](https://leetcode.com/problems/range-sum-query-2d-immutable/)
- **Continuous Subarray Sum** — does any subarray of length ≥ 2 sum to a multiple of K? *Insight:* take running sum mod K; if two prefix mods are equal, the slice between them is divisible by K. [LC 523](https://leetcode.com/problems/continuous-subarray-sum/)
- **Maximum Size Subarray Sum Equals K** — longest subarray with sum K. *Insight:* hash of `prefix → first_index`; for each `s` look up `s - k` and update best length. [LC 325](https://leetcode.com/problems/maximum-size-subarray-sum-equals-k/)
- **Range Sum Query — Mutable** — sum + point updates. *Insight:* prefix sum is O(n) per update; switch to a Fenwick tree (BIT) for O(log n). [LC 307](https://leetcode.com/problems/range-sum-query-mutable/)
