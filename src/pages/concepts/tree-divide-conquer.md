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

## The recursion picture

![](/notes/leetcode/media/image18.png)

![](/notes/leetcode/media/image19.png)

The recursion descends to leaves, then *combines* answers on the way back up. The combine step at each node uses only what its children returned — this is what makes the pattern composable.

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

- **Binary Tree Maximum Path Sum** — max sum of any node-to-node path. *Insight:* helper returns "max chain ending at node going down"; the answer-through-node is `l + r + node.val`; only one side can extend upward. [LC 124](https://leetcode.com/problems/binary-tree-maximum-path-sum/)
- **House Robber III** — max loot from a binary tree where adjacent nodes can't both be robbed. *Insight:* DFS returns tuple `(rob_node, skip_node)`; if you rob node, children must skip; if you skip node, take max of children. [LC 337](https://leetcode.com/problems/house-robber-iii/)
- **Validate BST** — is the tree a valid BST? *Insight:* in-order traversal must yield strictly increasing values; or pass `(min, max)` bounds down. [LC 98](https://leetcode.com/problems/validate-binary-search-tree/)
- **Kth Smallest in BST** — find the kth smallest value. *Insight:* in-order = sorted order; iterative stack lets you stop at the kth pop. [LC 230](https://leetcode.com/problems/kth-smallest-element-in-a-bst/)
- **Convert BST to Greater Tree** — replace each value with sum of all values ≥ it. *Insight:* reverse in-order (right → node → left) carrying a running sum. [LC 538](https://leetcode.com/problems/convert-bst-to-greater-tree/)
- **Lowest Common Ancestor (Binary Tree)** — deepest node that's an ancestor of both `p` and `q`. *Insight:* DFS returns `node` if subtree contains `p` or `q`; if both children return non-None, current node is LCA. [LC 236](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/)
- **Word Break** — can `s` be split into dictionary words? *Insight:* implicit tree of split points; recurse on `s[i:]` for every prefix `s[:i]` in dict; memoize on suffix. [LC 139](https://leetcode.com/problems/word-break/)
- **Scramble String** — can `s2` be obtained by recursively swapping subtree halves of `s1`? *Insight:* try every split `k`; recurse on `(s1[:k]==s2[:k]) AND ...` (no swap) or `(s1[:k]==s2[-k:]) AND ...` (swap); cache by `(s1, s2)`. [LC 87](https://leetcode.com/problems/scramble-string/)
- **Diameter of Binary Tree** — longest path between any two nodes (counted in edges). *Insight:* same shape as Max Path Sum — track `max(l + r)`, return `1 + max(l, r)`. [LC 543](https://leetcode.com/problems/diameter-of-binary-tree/)
