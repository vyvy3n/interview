---
layout: ../../layouts/Layout.astro
title: Interval DP
---

# Interval DP

> State `dp[l][r]` = answer for the sub-interval `[l, r]`. Combine by enumerating a split point `k` between `l` and `r`.

## When to use

- "Optimal way to merge / partition a sequence into pieces"
- "Last operation defines the answer" (last balloon to burst, last stone to crush…)
- Palindromic substring / subsequence
- Matrix chain multiplication

## State template

```
dp[l][r] = best (or count) for the sub-interval s[l..r]
dp[l][r] = combine(dp[l][k], dp[k+1][r])  for some split k in [l, r-1]
       OR dp[l][r] = something with dp[l+1][r-1]  (palindromes)
```

Compute by **increasing interval length**, not by `l` or `r` directly.

```python
n = len(s)
dp = [[0] * n for _ in range(n)]
for length in range(1, n + 1):
    for l in range(n - length + 1):
        r = l + length - 1
        # transition for dp[l][r]
```

## Longest Palindromic Subsequence

```python
def longestPalindromeSubseq(s):
    n = len(s)
    dp = [[0] * n for _ in range(n)]
    for i in range(n): dp[i][i] = 1
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            r = l + length - 1
            if s[l] == s[r]:
                dp[l][r] = dp[l+1][r-1] + 2
            else:
                dp[l][r] = max(dp[l+1][r], dp[l][r-1])
    return dp[0][n-1]
```

State: `dp[l][r]` = length of LPS of `s[l..r]`. Two cases: matching ends extend the inner answer; non-matching, take the better of dropping each side.

## Palindromic Substring count

Count contiguous palindromes — different state shape:

```python
def countSubstrings(s):
    n = len(s)
    dp = [[False] * n for _ in range(n)]
    count = 0
    for length in range(1, n + 1):
        for l in range(n - length + 1):
            r = l + length - 1
            if s[l] == s[r] and (length <= 2 or dp[l+1][r-1]):
                dp[l][r] = True
                count += 1
    return count
```

## Burst Balloons — "last action" framing

Instead of "first balloon", think "**last** balloon". When `k` is burst last in `[l, r]`, its neighbors are `nums[l-1]` and `nums[r+1]` (everything else already gone):

```python
def maxCoins(nums):
    nums = [1] + nums + [1]
    n = len(nums)
    dp = [[0] * n for _ in range(n)]
    for length in range(2, n):
        for l in range(n - length):
            r = l + length
            for k in range(l + 1, r):
                dp[l][r] = max(dp[l][r],
                               dp[l][k] + dp[k][r] + nums[l] * nums[k] * nums[r])
    return dp[0][n-1]
```

The "last" framing is the key trick — "first" gives a coupled recurrence that can't be cleanly memoized.

## Matrix Chain Multiplication

For dimensions `p[0..n]` (matrix `i` is `p[i] × p[i+1]`):

```python
def matrix_chain(p):
    n = len(p) - 1
    dp = [[0] * n for _ in range(n)]
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            r = l + length - 1
            dp[l][r] = float("inf")
            for k in range(l, r):
                cost = dp[l][k] + dp[k+1][r] + p[l] * p[k+1] * p[r+1]
                dp[l][r] = min(dp[l][r], cost)
    return dp[0][n-1]
```

## Game DP (interval flavor)

Two players alternate; both play optimally. State usually includes whose turn:

```python
# Coins in a Line III — pick from either end; max your score over opponent
def stoneGame(piles):
    n = len(piles)
    # dp[l][r] = (current player's max - opponent's max) on piles[l..r]
    dp = [[0] * n for _ in range(n)]
    for i in range(n): dp[i][i] = piles[i]
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            r = l + length - 1
            dp[l][r] = max(piles[l] - dp[l+1][r], piles[r] - dp[l][r-1])
    return dp[0][n-1] > 0
```

## Gotchas

- **Iterate by interval length**, not by `l` or `r` first — otherwise transitions read uncomputed cells.
- Off-by-one: `r = l + length - 1` for inclusive intervals; `dp[l+1][r-1]` only valid when `length ≥ 2`.
- For "last action" problems, sentinel-pad both ends to handle boundary nicely.
- O(n³) is the typical complexity — fine up to n ≈ 500.

## Practice

- **Longest Palindromic Substring** — longest contiguous palindrome. *Insight:* either expand around centers (O(n²) easy) or interval DP. [LC 5](https://leetcode.com/problems/longest-palindromic-substring/)
- **Longest Palindromic Subsequence** — longest palindrome as subsequence. *Insight:* `dp[l][r]` extends when ends match; else max of dropping either side. [LC 516](https://leetcode.com/problems/longest-palindromic-subsequence/)
- **Palindromic Substrings (count)** — count of palindromic substrings. *Insight:* `dp[l][r]` boolean; `s[l]==s[r] AND dp[l+1][r-1]`. [LC 647](https://leetcode.com/problems/palindromic-substrings/)
- **Burst Balloons** — max coins from bursting (`nums[l-1] * nums[k] * nums[r+1]` per balloon). *Insight:* enumerate **last** balloon `k` in interval, not first. [LC 312](https://leetcode.com/problems/burst-balloons/)
- **Matrix Chain Multiplication** — min scalar multiplications. *Insight:* `dp[l][r]` = min cost; split point `k`; cost adds `p[l]*p[k+1]*p[r+1]`. [Classic — not on LC]
- **Stone Game** / **Coins in a Line** — alternating pick from ends; max score diff. *Insight:* `dp[l][r] = max(a[l] - dp[l+1][r], a[r] - dp[l][r-1])`. [LC 877](https://leetcode.com/problems/stone-game/)
- **Minimum Cost to Cut a Stick** — cut a stick of length n at given positions, cost = current piece length. *Insight:* sort cuts; `dp[l][r]` over cut indices; enumerate which cut to do first in `(l, r)`. [LC 1547](https://leetcode.com/problems/minimum-cost-to-cut-a-stick/)
- **Palindrome Partitioning II** — min cuts so each piece is a palindrome. *Insight:* precompute `is_pal[l][r]` interval DP, then 1D `cuts[i]` over end positions. [LC 132](https://leetcode.com/problems/palindrome-partitioning-ii/)
