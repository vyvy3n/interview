---
layout: ../../layouts/Layout.astro
title: Fast Power
---

# Fast Power

> Compute `a^n` (or `a^n mod m`) in O(log n) by squaring.

## Why it matters

`a^n` naively is n multiplies. Squaring exploits `a^n = (a^(n/2))^2` (if n even) or `a · a^(n-1)` (if n odd) → O(log n).

## Iterative template (handles mod)

```python
def fast_power(a, n, m=None):
    """Compute a**n, optionally modulo m."""
    result = 1
    base = a if m is None else a % m
    while n > 0:
        if n & 1:                # n is odd → multiply current bit's contribution
            result = result * base
            if m is not None: result %= m
        base = base * base       # square the base for next bit
        if m is not None: base %= m
        n >>= 1
    return result
```

## Recursive form (cleaner, easier to remember)

```python
def fast_power(a, n):
    if n == 0: return 1
    half = fast_power(a, n // 2)
    return half * half * (a if n % 2 else 1)
```

## Pow(x, n) with negative exponent

```python
def my_pow(x, n):
    if n < 0:
        x, n = 1 / x, -n
    return fast_power(x, n)
```

## Where it shows up

- **Modular exponentiation** for crypto / hashing primes.
- **Matrix exponentiation** to solve linear recurrences in O(log n) — Fibonacci, climbing stairs, Tribonacci.
- **Polynomial / string hashing**: precompute `base^i mod p`.

## Matrix exponentiation skeleton (Fibonacci in O(log n))

```python
def mat_mul(A, B, mod=None):
    n, m, p = len(A), len(B), len(B[0])
    C = [[0] * p for _ in range(n)]
    for i in range(n):
        for k in range(m):
            if A[i][k] == 0: continue
            for j in range(p):
                C[i][j] += A[i][k] * B[k][j]
                if mod: C[i][j] %= mod
    return C

def mat_pow(M, n, mod=None):
    size = len(M)
    res = [[int(i == j) for j in range(size)] for i in range(size)]   # identity
    base = M
    while n > 0:
        if n & 1:
            res = mat_mul(res, base, mod)
        base = mat_mul(base, base, mod)
        n >>= 1
    return res

def fib(n):
    if n == 0: return 0
    M = mat_pow([[1, 1], [1, 0]], n)
    return M[0][1]
```

## Gotchas

- Use `n & 1` and `n >>= 1` — bit ops make intent obvious.
- `pow(a, n, m)` is built into Python and uses fast exponentiation under the hood — use it in interviews if mod is required (still explain you know the algorithm).
- For matrix expo: identity matrix as the starting "1" of multiplication.

## Practice

- [Pow(x, n)](https://leetcode.com/problems/powx-n/)
- [Fast Power](https://www.lintcode.com/problem/fast-power/)
- [Super Pow](https://leetcode.com/problems/super-pow/) (digit-by-digit exponent)
- [Fibonacci Number](https://leetcode.com/problems/fibonacci-number/) (try matrix-power solution)
- [Count Different Palindromic Subsequences](https://leetcode.com/problems/count-different-palindromic-subsequences/) (uses mod arithmetic)
