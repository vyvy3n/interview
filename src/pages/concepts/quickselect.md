---
layout: ../../layouts/Layout.astro
title: QuickSelect / Partition
---

# QuickSelect / Partition

> Find the kth element in O(n) average — without sorting the whole array.

## When to use

- "Kth largest / smallest element"
- "Top K" when you don't need them ordered (else use heap)
- "Median of an array"
- "Wiggle sort II", "Sort colors" (partition variants)

## Lomuto-style partition

Simple, swaps a lot:

```python
def partition(nums, lo, hi):
    pivot = nums[hi]
    i = lo
    for j in range(lo, hi):
        if nums[j] < pivot:
            nums[i], nums[j] = nums[j], nums[i]
            i += 1
    nums[i], nums[hi] = nums[hi], nums[i]
    return i        # final pivot index
```

## Hoare-style partition (preferred — fewer swaps, better with duplicates)

```python
def partition(A, lo, hi):
    pivot = A[(lo + hi) // 2]
    l, r = lo, hi
    while l <= r:
        while l <= r and A[l] < pivot: l += 1
        while l <= r and A[r] > pivot: r -= 1
        if l <= r:
            A[l], A[r] = A[r], A[l]
            l, r = l + 1, r - 1
    return l, r     # split index pair
```

## QuickSelect (kth largest)

```python
def kth_largest(nums, k):
    target = len(nums) - k          # convert to "kth smallest from 0"
    def select(lo, hi):
        if lo == hi: return nums[lo]
        l, r = partition(nums, lo, hi)
        if target <= r: return select(lo, r)
        if target >= l: return select(l, hi)
        return nums[target]
    return select(0, len(nums) - 1)
```

Average O(n), worst O(n²) (very rare with random pivot or median-of-three).

## QuickSort (full sort built on partition)

```python
def quicksort(A, lo, hi):
    if lo >= hi: return
    l, r = partition(A, lo, hi)
    quicksort(A, lo, r)
    quicksort(A, l, hi)
```

## Three-way partition (Dutch flag — for many duplicates)

```python
def sort_colors(A):                     # 0s, 1s, 2s
    lo, mid, hi = 0, 0, len(A) - 1
    while mid <= hi:
        if A[mid] == 0:
            A[lo], A[mid] = A[mid], A[lo]
            lo += 1; mid += 1
        elif A[mid] == 2:
            A[mid], A[hi] = A[hi], A[mid]
            hi -= 1                     # don't advance mid — re-check
        else:
            mid += 1
```

## Gotchas

- **Pivot is a value, not an index** in Hoare-style — index can shift during swaps.
- **Use `<=` in the outer loop and inner conditions** — symmetry prevents infinite loop.
- For QuickSelect, comparing **with the partition boundaries** (not pivot index) avoids subtle bugs.
- Random pivot or median-of-three to avoid O(n²) on sorted/adversarial inputs.

## Practice

- [Kth Largest Element in an Array](https://leetcode.com/problems/kth-largest-element-in-an-array/)
- [Wiggle Sort II](https://leetcode.com/problems/wiggle-sort-ii/)
- [Sort Colors](https://leetcode.com/problems/sort-colors/)
- [Top K Frequent Elements](https://leetcode.com/problems/top-k-frequent-elements/)
- [K Closest Points to Origin](https://leetcode.com/problems/k-closest-points-to-origin/)
- [Partition Array](https://www.lintcode.com/problem/partition-array/)
