---
layout: ../../layouts/Layout.astro
title: DFS & Backtracking
---

# DFS & Backtracking

> Enumerate all configurations by making a choice, recursing, then undoing.

## When to use

- "Find all combinations / permutations / subsets / partitions"
- "Find any / all path(s) in a tree or implicit graph"
- "All ways to ..." — exponential answer space
- Constraint satisfaction (N-Queens, Sudoku)

## Template: build a path

```python
def backtrack(start, path, res):
    res.append(path[:])              # snapshot — copy!
    for i in range(start, len(nums)):
        path.append(nums[i])
        backtrack(i + 1, path, res)  # i+1 prevents reuse
        path.pop()                   # undo
```

## Enumeration as nested loops (Letter Combinations)

```python
KEYS = ["", "", "abc", "def", "ghi", "jkl", "mno", "pqrs", "tuv", "wxyz"]

def letter_combinations(digits):
    if not digits: return []
    res = []
    def dfs(i, path):
        if i == len(digits):
            res.append(path)
            return
        for c in KEYS[int(digits[i])]:
            dfs(i + 1, path + c)
    dfs(0, "")
    return res
```

## Pruning + branching (Factorization)

```python
def get_factors(n):
    res = []
    def dfs(start, remain, path):
        if remain == 1:
            if len(path) > 1:
                res.append(path[:])
            return
        # try every factor in [start, sqrt(remain)]
        for f in range(start, int(remain ** 0.5) + 1):
            if remain % f == 0:
                path.append(f)
                dfs(f, remain // f, path)
                path.pop()
        # take remain itself as the last factor
        path.append(remain)
        dfs(remain, 1, path)
        path.pop()
    dfs(2, n, [])
    return res
```

## Gotchas

- **Snapshot**: append `path[:]` not `path` — references mutate.
- **Undo discipline**: every `append` needs a matching `pop` in the same scope.
- **Avoid duplicates**: pass `start` index so you don't revisit; sort + skip equal neighbors when input has dupes.
- **Pruning is the win**: cut branches early (impossible sums, sorted-and-too-big, visited).

## Variants

- **DFS + memoization** (top-down DP): same shape, cache results — see Word Break, Scramble String.
- **DFS for shortest paths**: usually wrong — use BFS unless you must explore all.
- **DFS + BFS combined** for "all shortest paths": BFS to compute distances, DFS following only strictly-decreasing distance — see Word Ladder II.

## Practice

- [Subsets](https://leetcode.com/problems/subsets/) · [Permutations](https://leetcode.com/problems/permutations/) · [Combination Sum](https://leetcode.com/problems/combination-sum/)
- [Letter Combinations of a Phone Number](https://leetcode.com/problems/letter-combinations-of-a-phone-number/)
- [Factorization](https://www.lintcode.com/problem/factorization/)
- [Word Squares](https://www.lintcode.com/problem/word-squares/)
- [Expression Add Operators](https://leetcode.com/problems/expression-add-operators/)
- [Word Ladder II](https://leetcode.com/problems/word-ladder-ii/)
- [N-Queens](https://leetcode.com/problems/n-queens/)
