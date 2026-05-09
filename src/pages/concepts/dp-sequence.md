---
layout: ../../layouts/Layout.astro
title: Sequence DP
---

# Sequence DP

> 1D state over a sequence: `dp[i]` summarizes the answer for the first `i` (or up to position `i`).

## When to use

- "Best / count / can-we ending at index i"
- Each position depends on a few previous positions
- Often O(n) or O(n²) time, O(n) → O(1) space with rolling

## Common state shapes

| Pattern | `dp[i]` means |
|---|---|
| Reach / count | ways to land on / number of ways to reach `i` |
| Cumulative best | optimal value considering first `i` elements |
| Choose / skip | `dp[i] = max(dp[i-1], dp[i-2] + val[i])` |
| Multi-state | `dp[i][k]` — k tracks an extra dimension (count, color, holding stock?) |

## Climbing Stairs / Fibonacci shape

```python
def climbStairs(n):
    if n <= 2: return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b
```

## House Robber — choose / skip

```python
def rob(nums):
    prev = curr = 0
    for x in nums:
        prev, curr = curr, max(curr, prev + x)
    return curr
```

`prev` = best up to `i-2`; `curr` = best up to `i-1`. After processing `x`, `curr` = best up to `i`.

## Decode Ways — partition counting

Given `"226"`, count decodings (`A=1..Z=26`):

```python
def numDecodings(s):
    if not s or s[0] == "0": return 0
    n = len(s)
    dp = [0] * (n + 1)
    dp[0] = dp[1] = 1
    for i in range(2, n + 1):
        if s[i-1] != "0":
            dp[i] += dp[i-1]                       # use 1 digit
        two = int(s[i-2:i])
        if 10 <= two <= 26:
            dp[i] += dp[i-2]                       # use 2 digits
    return dp[n]
```

State: `dp[i]` = ways to decode the first `i` chars.

## Longest Increasing Subsequence (LIS)

### O(n²) DP

```python
def LIS(nums):
    dp = [1] * len(nums)
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp) if dp else 0
```

### O(n log n) — patience-sort trick

Maintain `tails[k]` = smallest possible tail of an increasing subsequence of length `k+1`. For each `x`, binary-search-replace; final length of `tails` is the answer.

```python
import bisect
def LIS(nums):
    tails = []
    for x in nums:
        i = bisect.bisect_left(tails, x)
        if i == len(tails): tails.append(x)
        else:               tails[i] = x
    return len(tails)
```

`tails` itself is *not* a valid LIS — only its length is meaningful.

## Multi-state per index — Paint House II

`k` colors, `n` houses, no two adjacent the same color, minimize cost:

```python
def minCostII(costs):
    if not costs: return 0
    n, k = len(costs), len(costs[0])
    dp = costs[0][:]
    for i in range(1, n):
        # min and 2nd-min of previous row, with their indices
        m1 = m2 = -1
        for j in range(k):
            if m1 == -1 or dp[j] < dp[m1]:
                m2, m1 = m1, j
            elif m2 == -1 or dp[j] < dp[m2]:
                m2 = j
        dp = [costs[i][j] + (dp[m2] if j == m1 else dp[m1]) for j in range(k)]
    return min(dp)
```

Trick: at each row, you only need the *two smallest* values of the previous row → O(nk) instead of O(nk²).

## Stock-trading family

`dp[i][k][holding]`: at day `i`, with at most `k` transactions used, holding (0/1).

```python
# Best Time to Buy and Sell Stock III — at most 2 transactions
def maxProfit(prices):
    if not prices: return 0
    n = len(prices)
    K = 2
    dp = [[[0, -float("inf")] for _ in range(K+1)] for _ in range(n+1)]
    for i in range(1, n+1):
        for k in range(K, 0, -1):
            dp[i][k][0] = max(dp[i-1][k][0], dp[i-1][k][1] + prices[i-1])  # not holding
            dp[i][k][1] = max(dp[i-1][k][1], dp[i-1][k-1][0] - prices[i-1])# holding
    return dp[n][K][0]
```

For unlimited K (LC 122), greedy "sum of every up-move" is optimal.

## Gotchas

- **Pad the array** by 1 (`dp[0]` as the empty-prefix base) so transitions don't special-case `i = 0`.
- For LIS-style, `dp[i]` includes index `i` itself — final answer is `max(dp)`, not `dp[-1]`.
- For multi-state DP, name your dimensions in code comments — easy to get confused.
- Counting DP: order of loops matters when reuse is allowed (combinations vs permutations).

## Practice

- **Climbing Stairs** — ways to climb n with steps of 1 or 2. *Insight:* `dp[n] = dp[n-1] + dp[n-2]` Fibonacci. [LC 70](https://leetcode.com/problems/climbing-stairs/)
- **House Robber** — max non-adjacent sum. *Insight:* `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`. [LC 198](https://leetcode.com/problems/house-robber/)
- **House Robber II** — circular variant. *Insight:* run House Robber twice — once excluding first, once excluding last. [LC 213](https://leetcode.com/problems/house-robber-ii/)
- **Decode Ways** — number of decodings of digit string. *Insight:* at each i, contribute `dp[i-1]` if 1-digit valid + `dp[i-2]` if 2-digit valid. [LC 91](https://leetcode.com/problems/decode-ways/)
- **Longest Increasing Subsequence** — length of LIS. *Insight:* O(n²) DP per index, OR O(n log n) patience sort with `bisect_left`. [LC 300](https://leetcode.com/problems/longest-increasing-subsequence/)
- **Paint House II** — min cost with k colors, no adjacent same. *Insight:* track first-min and second-min of previous row → O(nk). [LC 265](https://leetcode.com/problems/paint-house-ii/)
- **Best Time to Buy and Sell Stock III** — at most 2 transactions. *Insight:* `dp[k][hold]` 2D state; `k` decreases when you *buy* (or *sell* — pick one). [LC 123](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iii/)
- **Best Time to Buy and Sell Stock IV** — at most k transactions. *Insight:* same as III with general k. If k ≥ n/2, degenerate to "unlimited" (LC 122). [LC 188](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iv/)
- **Word Break** — can string be split into dict words? *Insight:* `dp[i] = any(dp[j] and s[j:i] in dict)`. [LC 139](https://leetcode.com/problems/word-break/)
- **Maximum Subarray (Kadane)** — max contiguous sum. *Insight:* `dp[i] = max(nums[i], dp[i-1] + nums[i])`; track max. [LC 53](https://leetcode.com/problems/maximum-subarray/)
