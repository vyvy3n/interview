---
layout: ../../layouts/Layout.astro
title: Knapsack DP
---

# Knapsack DP

> State = (current item index, remaining capacity / target). For each item, decide: take it or skip.

## When to use

- "Pick a subset that maximizes value subject to a weight/budget"
- "Can we make sum / target with these items?"
- "Number of subsets summing to S"
- "Partition into K equal halves"

## The four flavors

| Problem | Each item | Use? | Loop order |
|---|---|---|---|
| **0/1 Knapsack** | take 0 or 1 | feasibility / max value | `for x in items: for w in W..x: dp[w] = ...` (capacity descending) |
| **Unbounded Knapsack** | take any count | feasibility / max value | `for x in items: for w in x..W: dp[w] = ...` (capacity ascending) |
| **Counting (combinations)** | take 0/1 each, count subsets | counting | item outer, capacity inner |
| **Counting (permutations)** | take any count, order matters | counting | capacity outer, item inner |

The loop order is the *whole game* in counting variants.

## 0/1 Knapsack — max value, each item once

```python
def knapsack(weights, values, W):
    dp = [0] * (W + 1)
    for w, v in zip(weights, values):
        for c in range(W, w - 1, -1):       # iterate capacity DESCENDING
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[W]
```

Why descending? `dp[c-w]` must reflect "before adding this item." Going descending ensures we read the old value, not the just-updated one.

## Unbounded Knapsack — max value, items can repeat

```python
def unbounded(weights, values, W):
    dp = [0] * (W + 1)
    for w, v in zip(weights, values):
        for c in range(w, W + 1):           # ASCENDING — reuse allowed
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[W]
```

Ascending lets `dp[c - w]` already include this item, enabling repeats.

## Subset Sum — can we make exactly S?

```python
def can_partition_to_sum(nums, S):
    dp = [False] * (S + 1)
    dp[0] = True
    for x in nums:
        for c in range(S, x - 1, -1):
            dp[c] = dp[c] or dp[c - x]
    return dp[S]
```

## Counting variants — combinations vs permutations

```python
# Coin Change II — number of COMBINATIONS that sum to amount (each coin unlimited use)
def change_combos(amount, coins):
    dp = [0] * (amount + 1)
    dp[0] = 1
    for coin in coins:                       # OUTER = items
        for c in range(coin, amount + 1):    # INNER = capacity, ascending
            dp[c] += dp[c - coin]
    return dp[amount]

# Combination Sum IV — number of PERMUTATIONS summing to target
def combo_sum_perms(nums, target):
    dp = [0] * (target + 1)
    dp[0] = 1
    for c in range(1, target + 1):           # OUTER = capacity
        for x in nums:                       # INNER = items
            if x <= c:
                dp[c] += dp[c - x]
    return dp[target]
```

Same recurrence, swapped loops, different answer. Memorize the rule:
- **Items outer** → each item considered once → combinations
- **Capacity outer** → at every capacity you pick fresh → permutations

## Partition Equal Subset Sum

Reduces to: "is there a subset summing to `total / 2`?" — 0/1 subset sum on `nums` with target `total // 2`.

## Min coins to make amount (Coin Change)

```python
def coinChange(coins, amount):
    INF = amount + 1
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for c in range(1, amount + 1):
        for coin in coins:
            if coin <= c:
                dp[c] = min(dp[c], dp[c - coin] + 1)
    return dp[amount] if dp[amount] != INF else -1
```

This is the *min* version of unbounded knapsack — optimization, not counting.

## Path reconstruction

To recover *which* items you picked: keep a parallel `take[i][c]` boolean and trace from `(n, W)` backward, decrementing `c -= w[i]` whenever `take[i][c]` is true.

## Gotchas

- **Loop order is the bug**: for 0/1, capacity DESC; for unbounded, capacity ASC.
- For counting, item-outer vs capacity-outer changes the answer entirely.
- Integer overflow on counting variants — use a mod or unbounded ints.
- Edge case `target = 0` usually has `dp[0] = 1` (one way: pick nothing) for counting, `dp[0] = 0` for min-cost.

## Practice

- **0/1 Knapsack** — max value within weight W, each item once. *Insight:* item outer, capacity descending; classic template. [LintCode 92](https://www.lintcode.com/problem/backpack/)
- **Coin Change** — fewest coins to make amount. *Insight:* min-version unbounded knapsack; loop coins inner. [LC 322](https://leetcode.com/problems/coin-change/)
- **Coin Change II** — count combinations to make amount. *Insight:* coins outer, amount inner — combinations not permutations. [LC 518](https://leetcode.com/problems/coin-change-ii/)
- **Combination Sum IV** — count permutations summing to target. *Insight:* target outer, nums inner — permutations. [LC 377](https://leetcode.com/problems/combination-sum-iv/)
- **Partition Equal Subset Sum** — split nums into two equal-sum subsets? *Insight:* subset-sum to `total/2`; `dp[s]` boolean. [LC 416](https://leetcode.com/problems/partition-equal-subset-sum/)
- **Target Sum** — count ways to assign +/- to make S. *Insight:* let P = sum of `+` set, N = sum of `-` set; `P - N = S`, `P + N = total` ⇒ `P = (S + total) / 2` → subset-sum count. [LC 494](https://leetcode.com/problems/target-sum/)
- **Ones and Zeroes** — max strings selectable given m zeros, n ones. *Insight:* 2D knapsack — capacity is `(m, n)`; iterate strings outer. [LC 474](https://leetcode.com/problems/ones-and-zeroes/)
- **Last Stone Weight II** — minimize remaining stone after smashing pairs. *Insight:* equivalent to "split sum closest to total/2" → subset-sum DP. [LC 1049](https://leetcode.com/problems/last-stone-weight-ii/)
- **Perfect Squares** — fewest perfect-squares summing to n. *Insight:* unbounded knapsack with items = `1, 4, 9, ..., k²`; min count. [LC 279](https://leetcode.com/problems/perfect-squares/)
