---
layout: ../../layouts/Layout.astro
title: Union Find
---

# Union Find

> Disjoint-set structure: track which group each element belongs to. Near-O(1) per op with path compression + union by rank.

## When to use

- "How many connected components after these edges?"
- "Are two nodes connected?" (offline / streaming edges)
- "Detect cycle in undirected graph" (union both endpoints; if already in same set, cycle)
- Kruskal's MST
- Grid problems where you merge cells

## Template (with path compression)

```python
class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.count = n          # number of components

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]   # path halving
            x = self.parent[x]
        return x

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry: return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        self.count -= 1
        return True
```

## Inline / dict-based shortcut

When IDs aren't 0..n-1 (strings, coords), use a dict:

```python
parent = {}
def find(x):
    parent.setdefault(x, x)
    if parent[x] != x:
        parent[x] = find(parent[x])
    return parent[x]
def union(a, b):
    parent[find(a)] = find(b)
```

## Recursive find (cleaner, Python recursion-limit OK on small n)

```python
def find(x):
    if parent[x] == x: return x
    parent[x] = find(parent[x])   # full path compression
    return parent[x]
```

## Path compression — picture

![](/notes/leetcode/media/image10.png)

Without compression, repeatedly walking up to the root costs O(n) per `find` in the worst case (a linear chain). Compression flattens the chain on each `find`, making subsequent calls almost O(1) amortized.

## Pattern: "is the new edge redundant?"

```python
for u, v in edges:
    if find(u) == find(v): return [u, v]   # cycle edge
    union(u, v)
```

## Gotchas

- **Always call `find` before comparing** — direct `parent[x] == parent[y]` is wrong without compression.
- Path compression alone is enough for most problems; add union-by-rank only if benchmarking.
- For grids: flatten `(i, j)` → `i * cols + j` as the int ID.
- For "number of islands II" (online): when you flip a cell to land, do unions with land neighbors and decrement count.

## Practice

- **Number of Connected Components** — given `n` nodes and edges, how many components? *Insight:* DSU with `count = n` initial; decrement count on every successful union. [LC 323](https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph/)
- **Number of Provinces (Friend Circles)** — `M[i][j] = 1` if `i, j` friends; count friend groups. *Insight:* same as connected components; iterate the upper triangle and union each `1`. [LC 547](https://leetcode.com/problems/number-of-provinces/)
- **Redundant Connection** — find the extra edge that creates a cycle in a tree. *Insight:* iterate edges; the first one whose endpoints are already in the same set is the redundant one. [LC 684](https://leetcode.com/problems/redundant-connection/)
- **Accounts Merge** — merge accounts that share any email. *Insight:* union accounts by shared email — use `email → account_id` first-seen map; union the two account ids; then group by root. [LC 721](https://leetcode.com/problems/accounts-merge/)
- **Number of Islands II** — for each addLand operation, return current island count. *Insight:* online union-find — when flipping a cell, init its component (count++), then union with land neighbors (count-- per successful union). [LC 305](https://leetcode.com/problems/number-of-islands-ii/)
- **Most Stones Removed with Same Row or Column** — max stones removable (each removal needs a stone in same row/col). *Insight:* union stones sharing a row OR column (use `row_id` and `~col_id` as separate keys); answer = `n - num_components`. [LC 947](https://leetcode.com/problems/most-stones-removed-with-same-row-or-column/)
- **Graph Valid Tree** — is the graph a tree (connected + no cycle)? *Insight:* must have exactly `n-1` edges AND every union must succeed (else cycle). [LC 261](https://leetcode.com/problems/graph-valid-tree/)
