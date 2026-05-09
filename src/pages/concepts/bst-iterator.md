---
layout: ../../layouts/Layout.astro
title: BST Iterator
---

# BST Iterator

> Walk a BST in sorted order with `next()` / `hasNext()` — using O(h) memory, not O(n).

## Why a stack

Recursive in-order is easy but stores all n calls. To pause/resume, we explicitly push the **left spine** onto a stack — that's the next chunk of "smaller than everything else still pending."

## Template (next-larger iterator)

```python
class BSTIterator:
    def __init__(self, root):
        self.stack = []
        self._push_left(root)

    def _push_left(self, node):
        while node:
            self.stack.append(node)
            node = node.left

    def hasNext(self):
        return bool(self.stack)

    def next(self):
        node = self.stack.pop()
        self._push_left(node.right)        # the next chunk
        return node.val
```

Average `next()` cost: amortized O(1). Each node is pushed and popped exactly once across the whole traversal.

## Two-pointer style: closest-K-values in BST

Maintain **two stacks** simulating in-order forward and reverse iterators around `target`. Pop the closer one k times.

```python
def closest_k_values(root, target, k):
    forward, backward = [], []
    self._init_forward(root, target, forward)
    self._init_backward(root, target, backward)
    res = []
    for _ in range(k):
        if not forward: res.append(self._next_back(backward))
        elif not backward: res.append(self._next_fwd(forward))
        else:
            if abs(forward[-1].val - target) < abs(backward[-1].val - target):
                res.append(self._next_fwd(forward))
            else:
                res.append(self._next_back(backward))
    return res
```

(Where `_next_fwd` and `_next_back` are the symmetric "advance" operations.)

## Inorder Successor (no parent pointer)

```python
def successor(root, p):
    succ = None
    while root:
        if p.val < root.val:
            succ = root            # candidate; could be tighter
            root = root.left
        else:
            root = root.right
    return succ
```

Conceptually: keep going right; whenever you turn left, remember that node.

## Variants

- **Reverse BST iterator**: same template, swap left/right.
- **In-order with constant memory**: Morris traversal — uses each leaf's right pointer as a temporary thread to its successor.

## Gotchas

- Empty `stack.pop()` blows up — guard with `hasNext()`.
- After popping a node, **always push its right child's left spine** before returning.
- Storage is O(h), so on a balanced tree it's O(log n); on a degenerate skewed tree it's O(n).

## Practice

- **Binary Search Tree Iterator** — `next()` and `hasNext()` over BST in sorted order. *Insight:* stack holding the "left spine"; on `next`, pop, push right child's left spine. O(h) memory, amortized O(1) per `next`. [LC 173](https://leetcode.com/problems/binary-search-tree-iterator/)
- **Inorder Successor in BST** — node with smallest value > p. *Insight:* iterate down: when going left, remember candidate; final candidate is the successor. [LC 285](https://leetcode.com/problems/inorder-successor-in-bst/)
- **Closest BST Value II** — k values closest to a target. *Insight:* two stacks acting as forward and reverse iterators around target; pop the closer side k times. [LC 272](https://leetcode.com/problems/closest-binary-search-tree-value-ii/)
- **Kth Smallest Element in a BST** — kth smallest value. *Insight:* iterative in-order using the stack template; stop after k pops. [LC 230](https://leetcode.com/problems/kth-smallest-element-in-a-bst/)
- **Validate BST** — is the tree a valid BST? *Insight:* in-order traversal must produce strictly increasing values; one failure = not a BST. [LC 98](https://leetcode.com/problems/validate-binary-search-tree/)
- **Recover BST** — exactly two nodes are swapped — restore them. *Insight:* in-order to find the two violators (`prev > current`); the *first* violation's `prev` and the *last* violation's `current` are the swapped pair. [LC 99](https://leetcode.com/problems/recover-binary-search-tree/)
