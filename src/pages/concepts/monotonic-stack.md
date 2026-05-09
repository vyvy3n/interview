---
layout: ../../layouts/Layout.astro
title: Monotonic Stack
---

# Monotonic Stack

> A stack whose elements always go in one direction. Used to find "next greater / smaller" in O(n).

## When to use

- "Next greater element to the right / left"
- "Largest rectangle in histogram"
- "Trapping rain water" (alt to two-pointer)
- "Daily temperatures" / "stock span"
- Sum of subarray min/max — count-contributions problems

## Template: next-greater-to-the-right

```python
def next_greater(nums):
    n = len(nums)
    res = [-1] * n
    stack = []                   # indices with strictly decreasing values
    for i, x in enumerate(nums):
        while stack and nums[stack[-1]] < x:
            res[stack.pop()] = x
        stack.append(i)
    return res
```

Sweep right-to-left for "next greater to the right" if it's more natural; the stack direction flips.

## Largest rectangle in histogram

Sentinel approach — push a `0` height at the end to flush the stack:

```python
def largest_rect(h):
    h = h + [0]
    stack = []
    best = 0
    for i, x in enumerate(h):
        while stack and h[stack[-1]] > x:
            top = stack.pop()
            width = i if not stack else i - stack[-1] - 1
            best = max(best, h[top] * width)
        stack.append(i)
    return best
```

Pattern: when an item is popped, you know its right boundary (current i) **and** left boundary (the new top of stack).

## Trapping rain water (stack flavor)

Each popped bar, water above it is bounded by `min(left_bar, current_bar) - popped_bar`.

```python
def trap(h):
    stack = []
    water = 0
    for i, x in enumerate(h):
        while stack and h[stack[-1]] < x:
            mid = stack.pop()
            if not stack: break
            left = stack[-1]
            width = i - left - 1
            bounded = min(h[left], x) - h[mid]
            water += width * bounded
        stack.append(i)
    return water
```

## When stack direction matters

| Goal | Maintain on stack |
|---|---|
| Next *greater* to right | Decreasing |
| Next *smaller* to right | Increasing |
| Previous *greater* | Decreasing (sweep L→R) |
| Previous *smaller* | Increasing (sweep L→R) |

## Gotchas

- Push **indices**, not values, when you'll need distances later.
- Use **strict** vs **non-strict** comparisons consciously: `<` vs `<=` decides handling of equal heights.
- For "circular array" next-greater, iterate `2n` and mod by `n`.

## Practice

- [Next Greater Element I/II](https://leetcode.com/problems/next-greater-element-ii/)
- [Daily Temperatures](https://leetcode.com/problems/daily-temperatures/)
- [Largest Rectangle in Histogram](https://leetcode.com/problems/largest-rectangle-in-histogram/) · [Maximal Rectangle](https://leetcode.com/problems/maximal-rectangle/)
- [Trapping Rain Water](https://leetcode.com/problems/trapping-rain-water/)
- [Sum of Subarray Minimums](https://leetcode.com/problems/sum-of-subarray-minimums/)
- [Remove K Digits](https://leetcode.com/problems/remove-k-digits/) (greedy + monotonic stack)
