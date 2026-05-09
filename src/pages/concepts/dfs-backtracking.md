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

- **Subsets** — all 2^n subsets of `nums`. *Insight:* canonical backtracking — at each `i`, choose to include or skip; snapshot `path[:]` at every node. [LC 78](https://leetcode.com/problems/subsets/)
- **Permutations** — all n! orderings of `nums`. *Insight:* track a `used[]` bitmap; in each frame iterate all unused indices. [LC 46](https://leetcode.com/problems/permutations/)
- **Combination Sum** — all combinations summing to target (unlimited reuse). *Insight:* recurse with same `start` index (allows reuse); subtract candidate from remaining sum. [LC 39](https://leetcode.com/problems/combination-sum/)
- **Letter Combinations of a Phone Number** — given digits `2-9`, all letter combos (T9 keypad). *Insight:* DFS with index `i` over digits; for each digit, branch over its letter set. [LC 17](https://leetcode.com/problems/letter-combinations-of-a-phone-number/)
- **Factorization** — all multiplicative factorizations of `n` (excluding `n × 1`). *Insight:* DFS over factors `f ∈ [start, √remain]`; pass `f` as next start to avoid duplicate orderings; also try `remain` itself as the final factor. [LintCode 652](https://www.lintcode.com/problem/factorization/)
- **Word Squares** — build NxN grid of words where row `i` == column `i`. *Insight:* DFS row-by-row; the next row must start with the prefix formed by column letters above — bucket words by prefix (or trie) to look up candidates O(1). [LintCode 634](https://www.lintcode.com/problem/word-squares/)
- **Expression Add Operators** — insert `+ - *` between digits of `num` so the expression equals target. *Insight:* DFS over split points; carry running `total` and `prev` (so `*` can undo last addition); careful with leading-zero numbers. [LC 282](https://leetcode.com/problems/expression-add-operators/)
- **Word Ladder II** — *all* shortest transformation chains from `begin` to `end`. *Insight:* BFS first to compute distance from `end` to every word; then DFS from `begin`, only stepping to neighbors with `dist == cur_dist - 1`. [LC 126](https://leetcode.com/problems/word-ladder-ii/)
- **N-Queens** — place N queens on NxN so none attack. *Insight:* row-by-row DFS; track occupied columns + 2 diagonals as sets `(c, r-c, r+c)` for O(1) attack check. [LC 51](https://leetcode.com/problems/n-queens/)
