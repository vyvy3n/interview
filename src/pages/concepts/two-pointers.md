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

## Practice

- **Two Sum II — sorted array** — given a sorted array, find two numbers that sum to target. *Insight:* opposite-ends pointers; move L right if sum too small, R left if too big. [LC 167](https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/)
- **Container With Most Water** — heights `h[i]`; pick two lines forming the largest area. *Insight:* area is bounded by the shorter line; always move the shorter pointer inward. [LC 11](https://leetcode.com/problems/container-with-most-water/)
- **3Sum** — find all unique triplets summing to 0. *Insight:* sort, then for each `i` do two-pointer on the remaining array; skip duplicates by comparing to previous index. [LC 15](https://leetcode.com/problems/3sum/)
- **Linked List Cycle** — does this list have a cycle? *Insight:* fast pointer moves 2x speed; if it laps slow they meet. [LC 141](https://leetcode.com/problems/linked-list-cycle/)
- **Remove Duplicates from Sorted Array** — in-place compact a sorted array, return new length. *Insight:* slow pointer marks the next write slot; fast pointer scans. [LC 26](https://leetcode.com/problems/remove-duplicates-from-sorted-array/)
- **Valid Palindrome** — does the string read the same forward/backward (alphanumeric only)? *Insight:* opposite ends, skip non-alphanumeric, compare lowercased. [LC 125](https://leetcode.com/problems/valid-palindrome/)
