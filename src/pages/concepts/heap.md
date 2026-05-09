---
layout: ../../layouts/Layout.astro
title: Heap & Top-K
---

# Heap & Top-K

> Get the min/max in O(log n). Heapify a list in O(n). Workhorse for top-K and streaming.

## When to use

- "Top K largest / smallest / most frequent"
- "Kth element" (alt to QuickSelect — heap is more flexible online)
- "Merge K sorted lists" / "K-way merge"
- Scheduling: meetings, tasks with timestamps
- Median-from-stream (two heaps)

## Python `heapq` cheats

```python
import heapq
h = []                       # min-heap by default
heapq.heappush(h, x)
x = heapq.heappop(h)         # smallest
heapq.heapify(arr)           # in-place, O(n)

# max-heap: push negatives
heapq.heappush(h, -x); -heapq.heappop(h)

# top-K
heapq.nlargest(k, nums)      # O(n log k)
heapq.nsmallest(k, nums)
```

## Top K largest in O(n log k)

Maintain a min-heap of size k:

```python
def top_k(nums, k):
    h = []
    for x in nums:
        heapq.heappush(h, x)
        if len(h) > k:
            heapq.heappop(h)
    return h
```

## Heapify in O(n) — sift-down from the bottom

```python
def shift_down(A, k):
    while 2 * k + 1 < len(A):
        c = 2 * k + 1
        if c + 1 < len(A) and A[c + 1] < A[c]:
            c += 1
        if A[k] <= A[c]: break
        A[k], A[c] = A[c], A[k]
        k = c

def heapify(A):
    for i in range(len(A) // 2 - 1, -1, -1):
        shift_down(A, i)
```

Why O(n)? Half the nodes are leaves (work = 0); next level does 1 swap each; the geometric sum collapses to O(n).

## Kth-smallest in sorted matrix (heap variant)

```python
def kth_smallest(matrix, k):
    n = len(matrix)
    h = [(matrix[0][j], 0, j) for j in range(n)]
    heapq.heapify(h)
    for _ in range(k - 1):
        v, i, j = heapq.heappop(h)
        if i + 1 < n:
            heapq.heappush(h, (matrix[i+1][j], i+1, j))
    return h[0][0]
```

## Median from stream (two heaps)

Max-heap of lower half, min-heap of upper half; rebalance to keep sizes within 1.

## Gotchas

- Python `heapq` is **min only** — invert for max.
- Tuples compare lexicographically: `(priority, tiebreaker, payload)`.
- `heappush` then `heappop` is `heapreplace`/`heappushpop` — fewer operations.
- Updating a value in the heap is unsupported — push a new entry and lazy-delete on pop.

## Practice

- [Top K Frequent Elements](https://leetcode.com/problems/top-k-frequent-elements/)
- [Kth Largest Element in an Array](https://leetcode.com/problems/kth-largest-element-in-an-array/)
- [Merge K Sorted Lists](https://leetcode.com/problems/merge-k-sorted-lists/)
- [Find Median from Data Stream](https://leetcode.com/problems/find-median-from-data-stream/)
- [Meeting Rooms II](https://leetcode.com/problems/meeting-rooms-ii/)
- [Kth Smallest Element in a Sorted Matrix](https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/)
