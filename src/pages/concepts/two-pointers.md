---
layout: ../../layouts/Layout.astro
title: Two Pointers
---

# Two Pointers

Use two indices that traverse the array from different positions.

## When to use

- Sorted array, find pair with target sum
- In-place partitioning / removing duplicates
- Reversing or palindrome checks
- Linked list cycle (fast/slow)

## Pattern: opposite ends

```python
def two_sum_sorted(nums, target):
    l, r = 0, len(nums) - 1
    while l < r:
        s = nums[l] + nums[r]
        if s == target: return [l, r]
        if s < target: l += 1
        else: r -= 1
    return []
```

## Pattern: fast / slow

```python
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast: return True
    return False
```

## Gotchas

- Always confirm input is sorted before opposite-ends.
- Off-by-one: `while l < r` vs `l <= r` — depends on whether same index can pair with itself.

## Example questions

- Two Sum II (sorted)
- Container With Most Water
- 3Sum
- Linked List Cycle
- Remove Duplicates from Sorted Array
