---
layout: ../../layouts/Layout.astro
title: Grid / Coordinate DP
---

# Grid / Coordinate DP

> State indexed by position on a 1D or 2D grid. Transitions come from neighbors you can reach from.

## When to use

- Walking on a grid with restricted moves (only right/down, knight, etc.)
- "Min/max cost" or "count of paths" to reach `(i, j)`
- "Largest square / rectangle of 1s"
- Problems where state = "currently at coordinate X"

## State template

```
dp[i][j] = best (or count, or boolean) for "ending at cell (i, j)"
```

Transition typically reads from `dp[i-1][j]`, `dp[i][j-1]`, or other previously-computed neighbors.

## Recursion vs DP — the key visual

![](/notes/dp/media/image3.png)

Naive recursion recomputes the same `(i, j)` cell exponentially many times. DP fills the table once.

## Unique Paths — count of paths to (m-1, n-1) moving only right or down

![](/notes/dp/media/image5.png)

```python
def uniquePaths(self, m: int, n: int) -> int:
    dp = [[1] * n for _ in range(m)]
    for r in range(1, m):
        for c in range(1, n):
            dp[r][c] = dp[r-1][c] + dp[r][c-1]
    return dp[m-1][n-1]
```

State `dp[r][c]` = number of paths from `(0,0)` to `(r,c)`. Boundary: top row and left column are all 1.

### Rolling-array optimization

`dp[r][c]` only needs the row above and the cell to the left:

```python
def uniquePaths(self, m: int, n: int) -> int:
    dp = [1] * n
    for _ in range(1, m):
        for c in range(1, n):
            dp[c] += dp[c - 1]   # dp[c] is "above", dp[c-1] is "left" already updated
    return dp[-1]
```

O(n) memory instead of O(mn).

## Min Path Sum — minimize sum walking right/down

```python
def minPathSum(grid):
    m, n = len(grid), len(grid[0])
    for i in range(m):
        for j in range(n):
            if i == 0 and j == 0: continue
            if i == 0:   grid[i][j] += grid[i][j-1]
            elif j == 0: grid[i][j] += grid[i-1][j]
            else:        grid[i][j] += min(grid[i-1][j], grid[i][j-1])
    return grid[-1][-1]
```

In-place — mutates the grid. Pad with a sentinel column/row of `inf` to drop the if-ladder.

## Triangle (variant — irregular shape)

```python
def minimumTotal(triangle):
    dp = list(triangle[-1])
    for i in range(len(triangle) - 2, -1, -1):
        for j in range(i + 1):
            dp[j] = min(dp[j], dp[j+1]) + triangle[i][j]
    return dp[0]
```

Bottom-up avoids the boundary mess that top-down has at row edges.

## Path *reconstruction*

When you also need the path (not just the cost), keep a parallel `from[r][c]` matrix recording which predecessor won, then walk backward from the goal.

## Obstacles — Unique Paths II

```python
def uniquePathsWithObstacles(grid):
    m, n = len(grid), len(grid[0])
    dp = [[0] * n for _ in range(m)]
    dp[0][0] = 1 - grid[0][0]
    for i in range(m):
        for j in range(n):
            if grid[i][j]: continue
            if i: dp[i][j] += dp[i-1][j]
            if j: dp[i][j] += dp[i][j-1]
    return dp[-1][-1]
```

Cells with obstacles stay 0 (no path goes through them).

## Bomb Enemy — pre-aggregate per row/column

For "from cell (i,j) shoot in 4 directions, counting enemies until hitting a wall", precompute four directional kill-counts then `max(L[i][j] + R[i][j] + U[i][j] + D[i][j])` over empty cells.

## Maximal Square — largest square of 1s

```python
def maximalSquare(grid):
    m, n = len(grid), len(grid[0])
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    best = 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if grid[i-1][j-1] == "1":
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
                best = max(best, dp[i][j])
    return best * best
```

`dp[i][j]` = side length of largest square with bottom-right corner at `(i-1,j-1)`. Min of three neighbors enforces the square constraint.

## Gotchas

- **Pad the table** with a row 0 and column 0 to avoid boundary checks.
- For "in-place" mutation, make sure you don't read a cell after overwriting it.
- 2D rolling can be tricky: prefer 1D + careful order over two-row alternation.
- For diagonals (like Maximal Square), don't forget the `dp[i-1][j-1]` term.

## Practice

- **Unique Paths** — count of paths in m×n grid, only right/down. *Insight:* `dp[i][j] = dp[i-1][j] + dp[i][j-1]`; or closed-form `C(m+n-2, m-1)`. [LC 62](https://leetcode.com/problems/unique-paths/)
- **Unique Paths II** — same with obstacles. *Insight:* skip obstacle cells (leave dp = 0); init top-left to 1 only if not obstacle. [LC 63](https://leetcode.com/problems/unique-paths-ii/)
- **Min Path Sum** — sum-min path top-left to bottom-right. *Insight:* `dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])`. [LC 64](https://leetcode.com/problems/minimum-path-sum/)
- **Triangle** — min path top to bottom. *Insight:* bottom-up sweep with 1D dp; row r has r+1 elements. [LC 120](https://leetcode.com/problems/triangle/)
- **Maximal Square** — largest 1-square in 0/1 matrix. *Insight:* `dp[i][j]` = side of square ending at `(i,j)`; min of three neighbors. [LC 221](https://leetcode.com/problems/maximal-square/)
- **Maximal Rectangle** — largest 1-rectangle in 0/1 matrix. *Insight:* row-by-row reduce to histogram + monotonic stack (largest rectangle in histogram). [LC 85](https://leetcode.com/problems/maximal-rectangle/)
- **Bomb Enemy** — max enemies one bomb can kill (blocked by walls). *Insight:* precompute four directional kill counts; answer is max sum at empty cell. [LC 361](https://leetcode.com/problems/bomb-enemy/)
- **Dungeon Game** — min HP to start to survive grid (right/down moves). *Insight:* DP from bottom-right backward — `dp[i][j] = max(1, min(dp[i+1][j], dp[i][j+1]) - grid[i][j])`. [LC 174](https://leetcode.com/problems/dungeon-game/)
