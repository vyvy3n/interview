---
layout: ../../layouts/Layout.astro
title: Tree Divide & Conquer
---

# Tree Divide & Conquer

> Solve a tree problem by combining results from `left` and `right` subtrees.

## When to use

- "Max / min / count something **across the whole tree**"
- The answer at a node depends on answers from its children
- You need *two* things from each child: a "downward chain" answer and a "passing-through this node" answer

## Template 1: one return value

```python
def helper(node):
    if not node: return 0       # base
    l = helper(node.left)
    r = helper(node.right)
    return combine(l, r, node)  # post-order
```

## Template 2: chain + pass-through (max path sum)

```python
def maxPathSum(root):
    self.best = float("-inf")
    def chain(node):                       # max sum of a path ending at node, going down
        if not node: return 0
        l = max(0, chain(node.left))       # negative chains drop to 0
        r = max(0, chain(node.right))
        self.best = max(self.best, l + r + node.val)   # path through node
        return node.val + max(l, r)        # only one side can extend upward
    chain(root)
    return self.best
```

The trick: a path "through" a node can branch left+right, but the *return* to the parent can only follow one side.

## House Robber III (children DP)

Each call returns `(rob_this, skip_this)`:

```python
def rob(root):
    def dfs(node):
        if not node: return (0, 0)
        l = dfs(node.left)
        r = dfs(node.right)
        rob_node = node.val + l[1] + r[1]
        skip_node = max(l) + max(r)
        return (rob_node, skip_node)
    return max(dfs(root))
```

## BST traversal patterns

- **In-order** = sorted order. Use for: validate BST, kth smallest, BST iterator.
- **Pre-order + post-order** to serialize/clone.
- **Convert BST to greater tree**: reverse in-order (right → node → left), accumulate.

## Implicit tree D&C

When the tree isn't a literal tree but the recursion forms one:

- **Word Break** — split string at every position; cache.
- **Scramble String** — try every split + every (swap or no-swap); cache by `(s1, s2)`.

```python
@cache
def can_split(s):
    if s in word_set: return True
    for i in range(1, len(s)):
        if s[:i] in word_set and can_split(s[i:]):
            return True
    return False
```

## Gotchas

- **Always handle `node is None`** as the base case — it's the most common bug.
- For "path sum" problems, distinguish "path *ending* at node" vs "path *through* node".
- For implicit trees, **memoize** or you'll TLE on overlapping subproblems.

## Practice

- [Binary Tree Maximum Path Sum](https://leetcode.com/problems/binary-tree-maximum-path-sum/)
- [House Robber III](https://leetcode.com/problems/house-robber-iii/)
- [Validate BST](https://leetcode.com/problems/validate-binary-search-tree/) · [Kth Smallest in BST](https://leetcode.com/problems/kth-smallest-element-in-a-bst/)
- [Convert BST to Greater Tree](https://leetcode.com/problems/convert-bst-to-greater-tree/)
- [Lowest Common Ancestor](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/)
- [Word Break](https://leetcode.com/problems/word-break/) · [Scramble String](https://leetcode.com/problems/scramble-string/)
- [Diameter of Binary Tree](https://leetcode.com/problems/diameter-of-binary-tree/)
