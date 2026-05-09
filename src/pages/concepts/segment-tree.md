---
layout: ../../layouts/Layout.astro
title: Segment Tree & Fenwick (BIT)
---

# Segment Tree & Fenwick (BIT)

> Range queries + point updates in O(log n). Two flavors: segment tree (general, recursive) and Fenwick / BIT (sums only, super compact).

## When to use

- "Sum / min / max of a range, with updates" — many queries, mutable data
- "Count smaller numbers before each element" (BIT on value-frequency)
- "Range update + point query" or vice versa
- Anything where prefix sum is too slow because the array changes

## Cost comparison

|  | Update | Query | Space |
|---|---|---|---|
| Brute force | O(1) | O(n) | O(1) |
| Prefix sum array | O(n) | O(1) | O(n) |
| **Segment tree** | **O(log n)** | **O(log n)** | O(n) |
| **Fenwick (BIT)** | **O(log n)** | **O(log n)** | O(n), smaller constant |

Pick prefix sum if the array is static; segment tree / BIT if it isn't.

## Segment tree — the picture

Each node represents an interval; it stores the aggregate (sum / min / max) over that interval. Children split the interval in half.

![](/notes/segment-tree/media/image1.png)

Length convention: left child takes the floor half `[start, mid]` where `mid = (start + end) // 2`; right child takes `[mid + 1, end]`.

![](/notes/segment-tree/media/image2.png)

## Build / Query / Modify (Python)

```python
class SegNode:
    __slots__ = ("start", "end", "sum", "left", "right")
    def __init__(self, start, end):
        self.start, self.end = start, end
        self.sum = 0
        self.left = self.right = None

def build(A, l, r):
    node = SegNode(l, r)
    if l == r:
        node.sum = A[l]
        return node
    mid = (l + r) // 2
    node.left  = build(A, l, mid)
    node.right = build(A, mid + 1, r)
    node.sum = node.left.sum + node.right.sum
    return node

def query(node, l, r):
    """Sum over [l, r]."""
    if node.start == l and node.end == r:
        return node.sum
    mid = (node.start + node.end) // 2
    if r <= mid:
        return query(node.left, l, r)
    if l > mid:
        return query(node.right, l, r)
    return query(node.left, l, mid) + query(node.right, mid + 1, r)

def update(node, idx, val):
    if node.start == node.end == idx:
        node.sum = val
        return
    mid = (node.start + node.end) // 2
    if idx <= mid:
        update(node.left, idx, val)
    else:
        update(node.right, idx, val)
    node.sum = node.left.sum + node.right.sum
```

## Iterative array-based variant

Pack the tree into an array of size `4n`. Faster (no recursion overhead, cache-friendly) and easier to write for bounded n.

```python
class SegTree:
    def __init__(self, n):
        self.n = n
        self.t = [0] * (4 * n)

    def update(self, p, v, node=1, l=0, r=None):
        if r is None: r = self.n - 1
        if l == r:
            self.t[node] = v
            return
        mid = (l + r) // 2
        if p <= mid: self.update(p, v, 2*node,   l, mid)
        else:        self.update(p, v, 2*node+1, mid+1, r)
        self.t[node] = self.t[2*node] + self.t[2*node+1]

    def query(self, ql, qr, node=1, l=0, r=None):
        if r is None: r = self.n - 1
        if qr < l or r < ql: return 0
        if ql <= l and r <= qr: return self.t[node]
        mid = (l + r) // 2
        return (self.query(ql, qr, 2*node,   l, mid)
              + self.query(ql, qr, 2*node+1, mid+1, r))
```

## Lazy propagation — for *range* updates

When you want "add `v` to every element in `[l, r]`" + range queries: store a `lazy[node]` "to-be-propagated" value; push down to children only when you visit them. Keeps each op at O(log n).

## Fenwick Tree (Binary Indexed Tree)

Smaller and faster than a segment tree when you only need **prefix sums** + point updates.

![](/notes/segment-tree/media/image4.png)

Built on the trick of `lowbit(x) = x & -x`: an integer's lowest-set-bit gives the size of the range each `bit[i]` covers.

![](/notes/segment-tree/media/image5.png)

```python
class BIT:
    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 1)         # 1-indexed

    def update(self, i, delta):           # add `delta` at index i (0-indexed input)
        i += 1
        while i <= self.n:
            self.bit[i] += delta
            i += i & -i

    def prefix(self, i):                  # sum of [0..i]
        i += 1
        s = 0
        while i > 0:
            s += self.bit[i]
            i -= i & -i
        return s

    def range(self, l, r):                # sum of [l..r] inclusive
        return self.prefix(r) - (self.prefix(l - 1) if l > 0 else 0)
```

For "count of smaller numbers before itself", use BIT indexed by **value** (rank-compress first if values are large): for each `x`, query `prefix(rank(x) - 1)` then `update(rank(x), +1)`.

## Choosing between Segment Tree and BIT

- **BIT**: only sums (or any invertible binary op); compact; fastest to write.
- **Segment tree**: general aggregates (min, max, gcd, custom merges); needed for non-invertible ops or range updates with lazy.

## Gotchas

- `4 * n` array size for segment tree — never `2 * n`, that overflows for non-power-of-2 sizes.
- Off-by-one between 0-indexed problem input and 1-indexed BIT.
- For range *modify* + range *query*, you need lazy propagation OR two BITs (the "Δ trick").
- Don't forget to **compress coordinates** when indexing by value (e.g. counting smaller numbers): map values to ranks 0..n-1 first.

## Practice

- **Range Sum Query — Mutable** — `update` + `sumRange`. *Insight:* segment tree or BIT; both O(log n) per op. [LC 307](https://leetcode.com/problems/range-sum-query-mutable/)
- **Count of Smaller Numbers After Self** — for each i, count `j > i` with `nums[j] < nums[i]`. *Insight:* iterate right-to-left; BIT indexed by rank; query "count of smaller" before insert. [LC 315](https://leetcode.com/problems/count-of-smaller-numbers-after-self/)
- **Reverse Pairs** — count pairs `(i, j)` with `i < j` and `nums[i] > 2 * nums[j]`. *Insight:* like count-smaller but with the `2x` predicate; BIT or merge-sort variant. [LC 493](https://leetcode.com/problems/reverse-pairs/)
- **The Skyline Problem** — building outline given rectangles. *Insight:* sweep line with a multiset of active heights; segment tree alternative for very large coords. [LC 218](https://leetcode.com/problems/the-skyline-problem/)
- **Range Sum Query 2D — Mutable** — 2D range sum with cell updates. *Insight:* 2D BIT — `update(i, j, delta)` walks two nested while loops with `lowbit`. [LC 308](https://leetcode.com/problems/range-sum-query-2d-mutable/)
- **Falling Squares** — drop squares, return current max height after each drop. *Insight:* segment tree on (compressed) intervals with max + lazy "set" propagation. [LC 699](https://leetcode.com/problems/falling-squares/)
