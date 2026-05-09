---
layout: ../../layouts/Layout.astro
title: BFS
---

# BFS

> Visit nodes level-by-level. Shortest path on **unweighted** graphs.

## When to use

- Shortest path / minimum steps on unweighted graph or grid
- Level-order traversal of a tree
- "Implicit graph" search: words, board states, puzzles
- Multi-source flood fill (start with multiple things in queue at step 0)

## Template: layered BFS (count steps)

```python
from collections import deque

def shortest_path(grid, start, end):
    m, n = len(grid), len(grid[0])
    q = deque([start])
    seen = {start}
    steps = 0
    DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    while q:
        for _ in range(len(q)):           # process whole level
            x, y = q.popleft()
            if (x, y) == end:
                return steps
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < m and 0 <= ny < n \
                   and grid[nx][ny] != WALL \
                   and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    q.append((nx, ny))
        steps += 1
    return -1
```

## Implicit graph: word ladder (build neighbors on the fly)

```python
from collections import defaultdict, deque

def ladder_length(begin, end, words):
    words = set(words)
    if end not in words: return 0
    # bucket by wildcard pattern: "h*t" → {"hat", "hot", ...}
    buckets = defaultdict(list)
    for w in words | {begin}:
        for i in range(len(w)):
            buckets[w[:i] + "*" + w[i+1:]].append(w)

    q = deque([(begin, 1)])
    seen = {begin}
    while q:
        word, d = q.popleft()
        if word == end: return d
        for i in range(len(word)):
            for nb in buckets[word[:i] + "*" + word[i+1:]]:
                if nb not in seen:
                    seen.add(nb)
                    q.append((nb, d + 1))
    return 0
```

## Multi-source BFS (Walls and Gates / rotting oranges)

Push **all** sources into the queue at step 0; mutate the grid in place to record distance.

```python
def walls_and_gates(rooms):
    q = deque()
    for i, row in enumerate(rooms):
        for j, v in enumerate(row):
            if v == 0: q.append((i, j))
    while q:
        i, j = q.popleft()
        for di, dj in [(0,1),(0,-1),(1,0),(-1,0)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < len(rooms) and 0 <= nj < len(rooms[0]) \
               and rooms[ni][nj] > rooms[i][j] + 1:
                rooms[ni][nj] = rooms[i][j] + 1
                q.append((ni, nj))
```

## Bidirectional BFS

When start and end both known and graph is huge: expand from both sides, swap to expand the smaller frontier each iteration. Cuts cost from `O(b^d)` to `O(b^(d/2))`.

## Gotchas

- **Mark visited when you enqueue**, not when you pop — otherwise you'll add duplicates.
- For shortest-path counting, a node's *first* visit is the shortest distance; ignore re-visits.
- Layered BFS uses `for _ in range(len(q))` to bound the level — capturing `len` once.
- Avoid `list.pop(0)` (O(n)) — always `collections.deque`.

## Practice

- [Knight Shortest Path](https://www.lintcode.com/problem/knight-shortest-path/) · [Shortest Path in Binary Matrix](https://leetcode.com/problems/shortest-path-in-binary-matrix/)
- [Word Ladder](https://leetcode.com/problems/word-ladder/) · [Sliding Puzzle](https://leetcode.com/problems/sliding-puzzle/)
- [Walls and Gates](https://www.lintcode.com/problem/walls-and-gates) · [Rotting Oranges](https://leetcode.com/problems/rotting-oranges/)
- [Snakes and Ladders](https://leetcode.com/problems/snakes-and-ladders/)
- [Open the Lock](https://leetcode.com/problems/open-the-lock/) (bidirectional BFS shines)
