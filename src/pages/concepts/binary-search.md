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

## Example questions

- Search Insert Position
- Find First and Last Position of Element
- Koko Eating Bananas
- Capacity to Ship Packages
- Median of Two Sorted Arrays
