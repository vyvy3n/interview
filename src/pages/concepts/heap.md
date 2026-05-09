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

- **Top K Frequent Elements** — k most frequent values in `nums`. *Insight:* Counter → min-heap of size k of `(count, value)`; or bucket sort by frequency for O(n). [LC 347](https://leetcode.com/problems/top-k-frequent-elements/)
- **Kth Largest Element in an Array** — kth largest. *Insight:* min-heap of size k; final heap top is the answer. (QuickSelect is O(n) avg if asked.) [LC 215](https://leetcode.com/problems/kth-largest-element-in-an-array/)
- **Merge K Sorted Lists** — merge `k` sorted linked lists into one. *Insight:* push the head of each list into a min-heap of `(val, list_idx, node)`; pop, advance, repeat. [LC 23](https://leetcode.com/problems/merge-k-sorted-lists/)
- **Find Median from Data Stream** — `addNum` + `findMedian` over a growing stream. *Insight:* two heaps — max-heap of lower half, min-heap of upper half; rebalance so sizes differ by at most 1. [LC 295](https://leetcode.com/problems/find-median-from-data-stream/)
- **Meeting Rooms II** — minimum rooms needed for given meeting intervals. *Insight:* sort by start; min-heap of end times; if earliest end ≤ current start, reuse that room (pop). Heap size = answer. [LC 253](https://leetcode.com/problems/meeting-rooms-ii/)
- **Kth Smallest Element in a Sorted Matrix** — both rows and columns sorted ascending. *Insight:* push first row into min-heap with `(val, row, col)`; pop k times, push the cell below each pop. [LC 378](https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/)
- **K Closest Points to Origin** — k nearest points to (0, 0). *Insight:* max-heap of size k by `-distance²`; or QuickSelect partition by distance. [LC 973](https://leetcode.com/problems/k-closest-points-to-origin/)
