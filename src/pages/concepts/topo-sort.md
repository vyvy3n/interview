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

- **Course Schedule** — given prerequisites, can you finish all courses? *Insight:* topo sort on prereq graph; if it returns < n nodes, there's a cycle ⇒ impossible. [LC 207](https://leetcode.com/problems/course-schedule/)
- **Course Schedule II** — return the order of courses to take. *Insight:* same Kahn's algorithm, return the order list (or `[]` if cycle). [LC 210](https://leetcode.com/problems/course-schedule-ii/)
- **Alien Dictionary** — infer the letter ordering from a list of words sorted in alien lex order. *Insight:* compare adjacent word pairs; the first differing character pair gives an edge `a → b`. Topo sort the resulting graph. [LC 269](https://leetcode.com/problems/alien-dictionary/)
- **Sequence Reconstruction** — does a unique super-sequence exist that contains every given sub-sequence? *Insight:* topo sort + uniqueness check — at every step, the queue must have exactly one node; otherwise multiple valid orderings exist. [LC 444](https://leetcode.com/problems/sequence-reconstruction/)
- **Minimum Height Trees** — for an undirected tree, find roots that minimize tree height. *Insight:* "peel" leaves layer by layer (BFS on degree-1 nodes); the last 1-2 surviving nodes are the centroids. [LC 310](https://leetcode.com/problems/minimum-height-trees/)
- **Parallel Courses** — minimum semesters to take all courses, taking any non-blocked subset per semester. *Insight:* Kahn's BFS where each "round" = one semester; count rounds until queue empty. [LC 1136](https://leetcode.com/problems/parallel-courses/)
