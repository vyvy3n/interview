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

- **Merge Intervals** — merge all overlapping intervals. *Insight:* sort by start; for each interval either extend the last merged or push new. [LC 56](https://leetcode.com/problems/merge-intervals/)
- **Insert Interval** — insert into a sorted non-overlapping list. *Insight:* three phases: copy pre-overlap, merge while overlapping, copy post. [LC 57](https://leetcode.com/problems/insert-interval/)
- **Non-overlapping Intervals** — min number of intervals to remove so the rest don't overlap. *Insight:* sort by **end** time; greedily keep the earliest-ending non-conflicting interval. [LC 435](https://leetcode.com/problems/non-overlapping-intervals/)
- **Meeting Rooms II** — minimum number of rooms for the given meetings. *Insight:* sort by start, min-heap of end times; reuse a room when its end ≤ current start. [LC 253](https://leetcode.com/problems/meeting-rooms-ii/)
- **Jump Game** — can you reach the last index given `nums[i]` is max jump? *Insight:* track furthest reachable; fail if `i > reach`. [LC 55](https://leetcode.com/problems/jump-game/)
- **Jump Game II** — minimum jumps to reach last index. *Insight:* implicit BFS — track current "frontier end" and "next frontier end"; bump jump count when you cross the frontier. [LC 45](https://leetcode.com/problems/jump-game-ii/)
- **Gas Station** — circular array; find start station to complete loop, or -1. *Insight:* if total gas ≥ total cost, answer exists; reset start to `i+1` whenever running tank goes negative. [LC 134](https://leetcode.com/problems/gas-station/)
- **Task Scheduler** — schedule tasks with cooldown `n` between same-letter tasks. *Insight:* most-frequent task dominates: `(max_freq - 1) * (n + 1) + count_of_max_freq_tasks`. [LC 621](https://leetcode.com/problems/task-scheduler/)
- **Best Time to Buy and Sell Stock** — max profit from one buy + sell. *Insight:* sweep prices, track running min, update best `price - min`. [LC 121](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/)
