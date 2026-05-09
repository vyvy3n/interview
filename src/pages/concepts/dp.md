---
layout: ../../layouts/Layout.astro
title: Dynamic Programming
---

# Dynamic Programming

> Memoize overlapping subproblems. Turn an exponential recursion into polynomial.

## Recursion vs DP — when does DP help?

DP is recursion *plus* a table that remembers what you've already computed. It only helps when the recursion **revisits** the same subproblem many times.

![](/notes/dp/media/image3.png)

If subproblems don't overlap (e.g. each subtree visited once in a tree D&C), recursion is already optimal — DP adds no value.

## The four-step DP recipe

| Step | What you decide |
|---|---|
| **State** | What does `dp[i]` (or `dp[i][j]`) represent? |
| **Transition** | How do you build `dp[i]` from earlier states? |
| **Initial / boundary** | What are the base cases at the edges? |
| **Computation order** | Which order over states satisfies all dependencies? |

Time complexity = (number of states) × (cost per transition).

## Three DP "flavors" — what is the answer?

| Flavor | What you compute | Examples |
|---|---|---|
| **最值型 / Optimization** | min or max over all options | min path sum, longest increasing subsequence, edit distance |
| **计数型 / Counting** | number of ways | unique paths, decode ways, coin change ways |
| **存在型 / Existence** | boolean — can it be done? | jump game, word break |

Same skeleton; only the combine operator changes (`min`, `+`, `or`).

## Eight DP topologies — pick the matching page

For interview problems, the first thing to recognize is the *shape* of the state space:

| Shape | Page | Quick tell |
|---|---|---|
| 1D over a sequence | [Sequence DP](/concepts/dp-sequence) | "best/count up to index i" |
| 2D over a grid | [Grid / Coordinate DP](/concepts/dp-grid) | walking on a board |
| State = (item index, capacity) | [Knapsack DP](/concepts/dp-knapsack) | budget / weight constraint |
| Sub-interval `[l, r]` | [Interval DP](/concepts/dp-interval) | merging adjacent groups, palindromes |
| Two strings / sequences | [Two-Sequence DP](/concepts/dp-two-sequence) | LCS, edit distance |
| Tree subtree DP | [Tree D&C](/concepts/tree-divide-conquer) | answer at node ← children |
| Bitmask of subset | bitmask DP | "visited subset" of small N |
| Game / minimax | game DP | turn-based, both play optimally |

## Top-down vs bottom-up

```python
# Top-down: recursion + memo (closer to natural problem statement)
@cache
def f(state):
    if base: return ...
    return combine(f(sub1), f(sub2), ...)

# Bottom-up: iterate states in dependency order
dp = init
for state in order:
    dp[state] = combine(dp[prev_states])
return dp[goal]
```

- **Top-down**: easier when state space is sparse or order is hard to see.
- **Bottom-up**: usually faster (no recursion overhead), enables space optimization (rolling array).

## Space optimization: rolling arrays

When `dp[i]` depends only on `dp[i-1]` (or a few earlier rows), drop dimensions:

```python
# dp[i] only needs dp[i-1]  →  keep two arrays, alternate
prev, curr = ..., ...
for i in range(1, n):
    curr = transition(prev)
    prev, curr = curr, prev  # or: just keep one and overwrite carefully
```

Cuts O(n²) memory to O(n), or O(n) to O(1).

## Recognition cues — "is this DP?"

- "Optimal X over all configurations" + overlapping subproblems
- "Number of ways to ..."
- "Can you reach / achieve ..."
- The greedy answer fails on small adversarial inputs
- You can describe the answer in terms of "the answer for a smaller version"

## Common pitfalls

- **State that doesn't capture enough info** — if two states with the same `dp[i]` need different futures, your state is incomplete.
- **Wrong iteration order** — dependencies not satisfied when you read them.
- **Off-by-one on boundaries** — pad arrays with a 0-row/0-col so transitions don't have edge checks.
- **Re-counting in counting problems** — order matters: for "permutations" iterate items inner; for "combinations" outer.

## Practice (cross-cutting)

- **Climbing Stairs** — ways to climb n steps taking 1 or 2. *Insight:* `dp[i] = dp[i-1] + dp[i-2]` — Fibonacci. The "hello world" of DP. [LC 70](https://leetcode.com/problems/climbing-stairs/)
- **House Robber** — max sum from non-adjacent picks. *Insight:* `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`. [LC 198](https://leetcode.com/problems/house-robber/)
- **Coin Change** — fewest coins to make amount. *Insight:* `dp[a] = 1 + min(dp[a - c] for c in coins)`. [LC 322](https://leetcode.com/problems/coin-change/)
- **Triangle (Min Path Sum)** — bottom-up sum. *Insight:* `dp[j] = min(dp[j], dp[j+1]) + tri[i][j]` from last row up. [LC 120](https://leetcode.com/problems/triangle/)
