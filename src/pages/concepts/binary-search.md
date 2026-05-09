---
layout: ../../layouts/Layout.astro
title: Binary Search
---

# Binary Search

Halve the search space each step. Works on sorted arrays *or* any monotonic predicate.

## Canonical template (find leftmost true)

```python
def lower_bound(nums, target):
    l, r = 0, len(nums)  # half-open [l, r)
    while l < r:
        m = (l + r) // 2
        if nums[m] < target:
            l = m + 1
        else:
            r = m
    return l  # first index with nums[i] >= target
```

## Predicate-on-answer pattern

When the array isn't directly searched but the *answer* is monotonic (e.g. min capacity, max distance):

```python
def feasible(x): ...  # True for x >= answer

l, r = lo, hi
while l < r:
    m = (l + r) // 2
    if feasible(m): r = m
    else: l = m + 1
return l
```

## Gotchas

- Use `(l + r) // 2` (Python is fine; in C++/Java prefer `l + (r - l) // 2` to avoid overflow).
- Decide closed `[l, r]` vs half-open `[l, r)` and stick with it — most off-by-ones come from mixing.
- For floats, replace `l < r` with a fixed iteration count or epsilon check.

## Practice

- **Search Insert Position** — given a sorted array, return the index where `target` would be inserted. *Insight:* this *is* `lower_bound` — return `l` after the half-open binary search. [LC 35](https://leetcode.com/problems/search-insert-position/)
- **Find First and Last Position of Element** — leftmost and rightmost index of `target` in sorted array. *Insight:* run two binary searches: one for `lower_bound(t)`, one for `lower_bound(t+1) - 1`. [LC 34](https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/)
- **Koko Eating Bananas** — minimum eating speed to finish all piles within `H` hours. *Insight:* binary search on the *answer* (speed); predicate "can finish at speed K" is monotonic. [LC 875](https://leetcode.com/problems/koko-eating-bananas/)
- **Capacity to Ship Packages Within D Days** — minimum ship capacity to deliver all weights within D days. *Insight:* binary search on capacity in `[max(weights), sum(weights)]`; predicate "fits in D days" is monotonic. [LC 1011](https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/)
- **Median of Two Sorted Arrays** — median over the union without merging. *Insight:* binary-search the partition point in the smaller array such that left halves total `(m+n+1)//2` elements. [LC 4](https://leetcode.com/problems/median-of-two-sorted-arrays/)
- **Find Peak Element** — any local max in unsorted array (neighbors strictly smaller). *Insight:* compare `mid` with `mid+1`; the larger side must contain a peak. [LC 162](https://leetcode.com/problems/find-peak-element/)
