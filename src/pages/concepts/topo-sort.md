---
layout: ../../layouts/Layout.astro
title: Topological Sort
---

# Topological Sort

> Linear ordering of a DAG so every edge `u → v` puts `u` before `v`.

## When to use

- "Schedule courses / tasks with prerequisites"
- "Detect cycle in a directed graph" (if topo sort returns < n nodes, there's a cycle)
- "Build order" / dependency resolution
- Alien dictionary (infer letter order from sorted words)

## Template: BFS (Kahn's algorithm)

```python
from collections import deque, defaultdict

def topo_sort(n, edges):  # edges: list of (u, v) meaning u → v
    indeg = [0] * n
    g = defaultdict(list)
    for u, v in edges:
        g[u].append(v)
        indeg[v] += 1

    q = deque(i for i in range(n) if indeg[i] == 0)
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in g[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return order if len(order) == n else []  # [] = cycle
```

## DFS variant

Post-order DFS, then reverse:

```python
WHITE, GRAY, BLACK = 0, 1, 2
def topo_dfs(n, g):
    color = [WHITE] * n
    order = []
    def dfs(u):
        color[u] = GRAY
        for v in g[u]:
            if color[v] == GRAY:   # back edge → cycle
                raise ValueError("cycle")
            if color[v] == WHITE:
                dfs(v)
        color[u] = BLACK
        order.append(u)
    for u in range(n):
        if color[u] == WHITE:
            dfs(u)
    return order[::-1]
```

## Variants

- **Lexicographically smallest order**: replace `deque` with `heapq`.
- **All possible orders**: backtracking over zero-indegree set.
- **Unique order check**: at every step, only one node should be in the queue. If `len(q) > 1` at any point, order isn't unique.

## Gotchas

- Direction matters — if you see "B depends on A", the edge is `A → B`, not the reverse.
- Watch for **self-loops** and duplicate edges (could over-count indegree).
- Always check final order length == n to detect cycles.

## Practice

- [Course Schedule](https://leetcode.com/problems/course-schedule/) · [Course Schedule II](https://leetcode.com/problems/course-schedule-ii/)
- [Alien Dictionary](https://leetcode.com/problems/alien-dictionary/)
- [Sequence Reconstruction](https://leetcode.com/problems/sequence-reconstruction/) (uniqueness)
- [Minimum Height Trees](https://leetcode.com/problems/minimum-height-trees/) (peel leaves = topo on undirected)
- [Parallel Courses](https://leetcode.com/problems/parallel-courses/)
