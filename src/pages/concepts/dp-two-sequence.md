---
layout: ../../layouts/Layout.astro
title: Two-Sequence DP
---

# Two-Sequence DP

> State `dp[i][j]` = answer for `prefix(s1, i)` vs `prefix(s2, j)`. Decide on the last char(s) of each.

## When to use

- "Compare / align / transform between two strings or sequences"
- LCS, edit distance, regex matching, distinct subsequences
- "Number of ways to interleave / match"

## State template

```
dp[i][j] = answer comparing s1[:i] (first i chars) and s2[:j]
```

Pad with row 0 / col 0 representing empty prefix → boundary cases handled by initial values, not by branching.

## Longest Common Subsequence (LCS)

```python
def LCS(a, b):
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]
```

State: longest common subsequence of `a[:i]` and `b[:j]`.
- Match: extend the diagonal
- No match: take the better of dropping one char from either side

## LCS — reconstruct the actual subsequence

```python
def LCS_string(a, b):
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    # walk back
    i, j = m, n
    out = []
    while i > 0 and j > 0:
        if a[i-1] == b[j-1]:
            out.append(a[i-1])
            i -= 1; j -= 1
        elif dp[i-1][j] >= dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    return "".join(reversed(out))
```

## Edit Distance (Levenshtein)

Three operations: insert, delete, substitute.

```python
def editDistance(a, b):
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = i      # delete all of a
    for j in range(n + 1): dp[0][j] = j      # insert all of b
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],     # delete a[i-1]
                    dp[i][j-1],     # insert b[j-1]
                    dp[i-1][j-1],   # substitute
                )
    return dp[m][n]
```

State: min ops to transform `a[:i]` to `b[:j]`. Boundary: empty → `j` inserts; `i` chars → empty needs `i` deletes.

## Distinct Subsequences

Count how many ways `t` appears as a subsequence in `s`:

```python
def numDistinct(s, t):
    m, n = len(s), len(t)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = 1     # empty t matches once
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp[i][j] = dp[i-1][j]                       # skip s[i-1]
            if s[i-1] == t[j-1]:
                dp[i][j] += dp[i-1][j-1]                # match s[i-1] with t[j-1]
    return dp[m][n]
```

## Interleaving String

Is `s3` a valid interleave of `s1` and `s2`?

```python
def isInterleave(s1, s2, s3):
    if len(s1) + len(s2) != len(s3): return False
    m, n = len(s1), len(s2)
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True
    for i in range(m + 1):
        for j in range(n + 1):
            k = i + j - 1
            if i and s1[i-1] == s3[k]:
                dp[i][j] = dp[i][j] or dp[i-1][j]
            if j and s2[j-1] == s3[k]:
                dp[i][j] = dp[i][j] or dp[i][j-1]
    return dp[m][n]
```

## Wildcard / Regex Matching

```python
# Wildcard: '?' matches any single, '*' matches any sequence
def isMatch(s, p):
    m, n = len(s), len(p)
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True
    for j in range(1, n + 1):
        if p[j-1] == "*": dp[0][j] = dp[0][j-1]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if p[j-1] == "*":
                dp[i][j] = dp[i-1][j] or dp[i][j-1]   # match more / match nothing
            elif p[j-1] == "?" or p[j-1] == s[i-1]:
                dp[i][j] = dp[i-1][j-1]
    return dp[m][n]
```

## Space optimization to O(n)

Most two-sequence DP only uses the previous row. Roll to one or two arrays:

```python
def LCS_O_n(a, b):
    if len(a) < len(b): a, b = b, a
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        curr = [0]
        for j in range(1, len(b) + 1):
            if a[i-1] == b[j-1]:
                curr.append(prev[j-1] + 1)
            else:
                curr.append(max(prev[j], curr[-1]))
        prev = curr
    return prev[-1]
```

## Gotchas

- **Pad with row 0 / col 0** for empty-prefix base cases. Initialize them per problem.
- Off-by-one: `s[i-1]` is the i-th char when DP is 1-indexed.
- For counting variants, watch out for double-counting — each transition must be exclusive.
- Edit Distance with custom ops (different cost for insert vs delete) — adjust the `min(...)` accordingly.

## Practice

- **Longest Common Subsequence** — length of LCS of two strings. *Insight:* `dp[i][j] = dp[i-1][j-1]+1` on match, else `max(dp[i-1][j], dp[i][j-1])`. [LC 1143](https://leetcode.com/problems/longest-common-subsequence/)
- **Edit Distance (Levenshtein)** — min ops to convert `a` to `b`. *Insight:* match → diagonal; mismatch → `1 + min(insert, delete, substitute)`. [LC 72](https://leetcode.com/problems/edit-distance/)
- **Distinct Subsequences** — count of `t` as subsequences in `s`. *Insight:* always `dp[i-1][j]` (skip s[i-1]); add `dp[i-1][j-1]` when chars match. [LC 115](https://leetcode.com/problems/distinct-subsequences/)
- **Interleaving String** — is `s3` an interleave of `s1` and `s2`? *Insight:* 2D boolean DP; `k = i + j - 1` is current position in s3. [LC 97](https://leetcode.com/problems/interleaving-string/)
- **Wildcard Matching** — pattern with `?` and `*`. *Insight:* `*` either matches more chars (`dp[i-1][j]`) or matches nothing (`dp[i][j-1]`). [LC 44](https://leetcode.com/problems/wildcard-matching/)
- **Regular Expression Matching** — `.` and `*` (zero-or-more of preceding). *Insight:* `*` cases — zero of preceding (`dp[i][j-2]`) or one more (`dp[i-1][j]` if char matches). [LC 10](https://leetcode.com/problems/regular-expression-matching/)
- **Shortest Common Supersequence** — shortest string with both `a` and `b` as subsequences. *Insight:* `m + n - LCS(a, b)` length; reconstruct by walking the LCS table. [LC 1092](https://leetcode.com/problems/shortest-common-supersequence/)
- **Delete Operation for Two Strings** — min deletes to make a == b. *Insight:* `m + n - 2*LCS(a, b)`. [LC 583](https://leetcode.com/problems/delete-operation-for-two-strings/)
