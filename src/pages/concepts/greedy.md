---
layout: ../../layouts/Layout.astro
title: Greedy
---

# Greedy

> Make the locally optimal choice at each step. Works only when local choices provably extend to a global optimum.

## When to use

- Interval scheduling / merging
- Coin change with canonical denominations
- Jump game (track furthest reachable)
- Gas station / circular array
- Stock buy-sell (single pass)

## Pattern: sort by something, then sweep

```python
# Merge intervals
def merge(intervals):
    intervals.sort()
    out = [intervals[0]]
    for s, e in intervals[1:]:
        if s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out
```

```python
# Erase overlapping intervals (keep most non-overlapping)
def erase(intervals):
    intervals.sort(key=lambda x: x[1])  # by END time
    end = -float("inf")
    keep = 0
    for s, e in intervals:
        if s >= end:
            keep += 1
            end = e
    return len(intervals) - keep
```

The "sort by end" trick is the heart of activity selection.

## Pattern: track running best

```python
# Jump Game — can we reach the end?
def can_jump(nums):
    reach = 0
    for i, x in enumerate(nums):
        if i > reach: return False
        reach = max(reach, i + x)
    return True
```

```python
# Best Time to Buy and Sell Stock
def max_profit(prices):
    lo = float("inf")
    best = 0
    for p in prices:
        lo = min(lo, p)
        best = max(best, p - lo)
    return best
```

## Pattern: heap-driven greedy

When "take the cheapest / most-urgent next" — push candidates into a heap.

```python
# Meeting Rooms II — min rooms needed
def min_rooms(intervals):
    intervals.sort()
    h = []                       # heap of end times
    for s, e in intervals:
        if h and h[0] <= s:      # earliest-ending room is free
            heapq.heappop(h)
        heapq.heappush(h, e)
    return len(h)
```

## How to know greedy works

- **Exchange argument**: prove swapping any two choices in an optimal solution to match your greedy choice doesn't worsen the answer.
- **Matroid / activity selection**: classical optima have proofs. Trust them.
- If you're unsure → DP. Greedy is brittle; DP is safe.

## Gotchas

- Sorting key is everything (start vs end, ratio for fractional knapsack).
- Greedy fails on coin change with weird denominations (use DP).
- Off-by-one in "reach": update `reach` *before* checking termination.

## Practice

- [Merge Intervals](https://leetcode.com/problems/merge-intervals/) · [Insert Interval](https://leetcode.com/problems/insert-interval/)
- [Non-overlapping Intervals](https://leetcode.com/problems/non-overlapping-intervals/)
- [Meeting Rooms II](https://leetcode.com/problems/meeting-rooms-ii/)
- [Jump Game](https://leetcode.com/problems/jump-game/) · [Jump Game II](https://leetcode.com/problems/jump-game-ii/)
- [Gas Station](https://leetcode.com/problems/gas-station/)
- [Task Scheduler](https://leetcode.com/problems/task-scheduler/)
- [Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/)
