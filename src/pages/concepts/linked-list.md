---
layout: ../../layouts/Layout.astro
title: Linked List
---

# Linked List

> Pointer manipulation. Cheap insert/delete given a node, no random access.

## When to use

- The problem hands you a list head — usually means do it in O(1) extra space.
- Preserve order while removing duplicates, partitioning, or merging.
- LRU / LFU caches need O(1) node-from-anywhere removal → **doubly** linked.

## Three idioms to memorize

**1. Dummy head** — never special-case the first node.
**2. Two pointers (fast / slow)** — cycle detection, middle, kth-from-end.
**3. Reversal** — three-pointer rewrite.

## Reverse a list

```python
def reverse(head):
    prev = None
    cur = head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    return prev
```

## Cycle detection (Floyd)

```python
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast: return True
    return False

def cycle_start(head):              # also returns where the cycle begins
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        if slow is fast:
            slow = head
            while slow is not fast:
                slow, fast = slow.next, fast.next
            return slow
    return None
```

## Find middle (always rounds up to upper-middle when even)

```python
def middle(head):
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
    return slow
```

## Merge two sorted lists

```python
def merge(a, b):
    dummy = tail = ListNode()
    while a and b:
        if a.val <= b.val:
            tail.next, a = a, a.next
        else:
            tail.next, b = b, b.next
        tail = tail.next
    tail.next = a or b
    return dummy.next
```

## Doubly linked list (for LRU and friends)

```python
class Node:
    def __init__(self, key=None, val=None):
        self.key, self.val = key, val
        self.prev = self.next = None

# always use two dummy sentinels
head, tail = Node(), Node()
head.next, tail.prev = tail, head

def remove(node):
    node.prev.next = node.next
    node.next.prev = node.prev

def add_to_tail(node):
    node.prev = tail.prev
    node.next = tail
    tail.prev.next = node
    tail.prev = node
```

Sentinels mean you never check for None at the boundaries.

## Gotchas

- **Always save `cur.next` before reassigning** — losing the rest of the list is the #1 bug.
- For reversal, return `prev`, not `cur` (cur ends as None).
- Fast/slow: stop on `while fast and fast.next` to avoid NPE on even length.
- When deleting a node by value, you need the *previous* node — use a dummy head.

## Practice

- **Reverse Linked List** — reverse in place. *Insight:* three-pointer iteration `(prev, cur, nxt)`; return `prev`. [LC 206](https://leetcode.com/problems/reverse-linked-list/)
- **Reverse Nodes in k-Group** — reverse every k consecutive nodes (skip last group if shorter). *Insight:* check k nodes ahead exist; reverse k nodes; recurse on rest with the new tail's `next`. [LC 25](https://leetcode.com/problems/reverse-nodes-in-k-group/)
- **Linked List Cycle** — does the list cycle? *Insight:* fast/slow Floyd; they meet iff cycle. [LC 141](https://leetcode.com/problems/linked-list-cycle/)
- **Linked List Cycle II** — return cycle start node. *Insight:* after Floyd meet, reset one pointer to head; advance both at speed 1; meeting point is cycle start. [LC 142](https://leetcode.com/problems/linked-list-cycle-ii/)
- **Merge Two Sorted Lists** — merge two sorted lists. *Insight:* dummy head + tail pointer; pick smaller, advance. [LC 21](https://leetcode.com/problems/merge-two-sorted-lists/)
- **Merge K Sorted Lists** — merge k sorted lists. *Insight:* min-heap of `(val, idx, node)` across heads; pop, push next. O(N log k). [LC 23](https://leetcode.com/problems/merge-k-sorted-lists/)
- **Remove Nth Node From End** — drop the n-th from the end in one pass. *Insight:* dummy head + two pointers, `right` advances n steps first; then both advance until right hits end. [LC 19](https://leetcode.com/problems/remove-nth-node-from-end-of-list/)
- **Copy List with Random Pointer** — deep-copy list where each node has a `random` pointer. *Insight:* pass 1 — interleave copy nodes after originals; pass 2 — set `copy.random`; pass 3 — un-interleave. (Or hash original→copy.) [LC 138](https://leetcode.com/problems/copy-list-with-random-pointer/)
- **Reorder List** — `1→2→…→n` becomes `1→n→2→n-1…`. *Insight:* find middle (fast/slow); reverse second half; merge alternating. [LC 143](https://leetcode.com/problems/reorder-list/)
- **LRU Cache** — see the [full LRU page](/concepts/lru-cache). [LC 146](https://leetcode.com/problems/lru-cache/)
