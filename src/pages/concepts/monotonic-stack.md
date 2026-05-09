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

## Min Stack — store `(value, running_min)` pairs

![](/notes/leetcode/media/image5.png)

```python
class MinStack:
    def __init__(self):
        self.stack = []                     # list of (value, current_min)
    def push(self, x):
        m = x if not self.stack else min(x, self.stack[-1][1])
        self.stack.append((x, m))
    def pop(self):  self.stack.pop()
    def top(self):  return self.stack[-1][0]
    def getMin(self): return self.stack[-1][1]
```

Pairs trick: bundle the running aggregate with each element so pop never has to recompute.

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

- **Next Greater Element II** — circular array; next-greater for each index. *Insight:* sweep `2n` indices mod `n`; decreasing-value stack of indices, pop when current beats them. [LC 503](https://leetcode.com/problems/next-greater-element-ii/)
- **Daily Temperatures** — for each day, days until a warmer day. *Insight:* decreasing-temperature stack of indices; on a warmer day, pop and record `i - popped`. [LC 739](https://leetcode.com/problems/daily-temperatures/)
- **Largest Rectangle in Histogram** — max-area axis-aligned rectangle in histogram. *Insight:* increasing-height stack; on smaller bar, pop and compute rect with `width = i - new_top - 1`. Sentinel `0` at end flushes stack. [LC 84](https://leetcode.com/problems/largest-rectangle-in-histogram/)
- **Maximal Rectangle** — largest rectangle of 1s in binary matrix. *Insight:* row-by-row, maintain heights array; apply largest-rectangle-in-histogram per row. [LC 85](https://leetcode.com/problems/maximal-rectangle/)
- **Trapping Rain Water** — total water trapped between bars. *Insight:* stack of indices in decreasing height; on taller bar, pop "valley" and add `width × min(left, right) - popped` to total. [LC 42](https://leetcode.com/problems/trapping-rain-water/)
- **Sum of Subarray Minimums** — sum of min over all subarrays. *Insight:* for each element, count subarrays where it's the min — bounded by previous-smaller (left) and next-smaller-or-equal (right). [LC 907](https://leetcode.com/problems/sum-of-subarray-minimums/)
- **Remove K Digits** — remove K digits from numeric string to make smallest number. *Insight:* increasing-digit stack; pop when current < top and budget remains. [LC 402](https://leetcode.com/problems/remove-k-digits/)
