---
layout: ../../layouts/Layout.astro
title: 面试笔记 & Logs
---

# Others

@2022.03.18

tesla

- KL

- sigmoid gradient

- dilution 0 0 0 01010111

- python basics

  - class a:__name__ = “”; given name, return class; dir()

  - decorator for memorization, fibnaic

  - yeild: given an array, write generator for diff prev-curr

amazon:

- smallest rectangle that contains the touch point

# Skoopin

Interview w/ Min Fan @2021.07.11

```python
# Question: 
# Given the radius r, return an array of points that can draw the circle centered at (0, 0) with radius r.
# i.e. drawCircle(radius: int)
# r = 10
# [0, 10] ...... [10, 0] [-10, 0]
# Note: 
# 1) 想要 display 这个圆, 返回坐标 x, y 需要都是 int 因为显示屏 pixel (x, y) 位置都是 int. ==> Necessary to round?
# 2) open-ended: How many points?

def drawCircle(r):
    results = []
    results.append((-r, 0))  # leftmost
    results.append((0, r))
    results.append((0, -r))
    results.append((r, 0))
    R2 = r ** 2
    for x in range(0 - r + 1, 0):
        y = np.sqrt(R2 - (x) ** 2)  # Note 1: sqrt(); Note 2: R2;
        y_pos = round(y)
        y_neg = -y_pos
        results.append((x, y_pos))  
        results.append((x, y_neg)) 
        results.append((-x, y_pos)) 
        results.append((-x, y_neg))
        # (-9, 5), ...,
        # (-8, 6), (-8, -6), (8, 6), (8, -6),
        # (-7, 7), (-7, -7), (7, 7), (7, -7),
        # (-6, 8), (-6, -8), (6, 8), (6, -8),
        # (-5, 9), (-5, -9), (5, 9), (5, -9),
        # (-4, 9), ...,
        # (-3, 10), ...,
        # (-2, 10), ...,
        # (-1, 10), ...,
    return results
```

Q1: 精度？沿 x 均分: range(-r, r + 1).

Q2: 如何画圆尽量精确？

y_pos = round(y) 用 round() 而不是 np.ceil()/np.floor(); 沿 y 也可以均分.

Q3: 如何验证你的函数正确？如果 unit test？需要 test 那些 cases？

可以验证是否每个点都在圆上；unit test 主要验证 r > 0.

```python
def test(r):
    results = drawCircle(r)
    for (x, y) in results:
        print (x ** 2 + y ** 2)
```

Q4: 如何优化

Note 1: R2 = r ** 2 不需要重复计算

Note 2: sqrt() 的 log(n) 复杂度太高冗杂；如何做到线性？

不用计算每个 y[n] = np.sqrt(R2 - x[n] ** 2) 都开平方; 事实上：
对每个 y[n], 只需 search [y[n-1], y[n-1] + 2 * x[n] - 1] 即可得到 y[n]; 
下一个 y[n + 1] 又是接着 y[n] search.
所以 overall 算完所有 y[n] 的计算量是 O(r) i.e. 每个 sqrt() 运算等价于线性.

Takeaways: 学习 unit test 思路 & sqrt() 具体情况下优化到线性

# Nuro

Phone Interview @2020.03.09 

How to reduce variance?

答 Advanages

这个 naive。还有什么别的方法？

我说 take min of two O-nets。他说这是 double Q leanring 吧，我说是。

Advantages 是不是 unbiased?

我说是

Why / What is importance sampling?

\sum R(t)

\sum w_i R(t_i)

\sum p(t_1) R(t_i)

\sum p(s_1|s_0, a_1)

/********************************************************************************************************/

Given an array of numbers. It can contain both +ve and -ve integers. Find the maximum sum contiguous array. Output -> Sum, Start and end index.

[1, 34,  45, 100] -> 180, 0, 3

[1,-34,- 45, 100] -> 100, 3, 3

O(n^2) contiguous array

sum(interval) up to O(n)

首先面试官分析了 straightforward 解法:

For i in range(0,n):

	For j in range(0,n):

		sum += 

⇒ O(n2)

问题: Can we do it in O(N)?

/********************************************************************************************************/

```python
def findMaxSum(nums):
    n = len(nums)
    f = [0] * n
    if len(nums) < 1:
        return -1, -1, -1
    
    maxsum = float('-inf')
    f[0] = nums[0]
    start = 0
    curr_start = 0
    for i in range(1, n):
        if nums[i - 1] > 0:
            f[i] = f[i - 1] + nums[i]
            
        else:
            f[i] = nums[i]
            curr_start = i
        if f[i] > maxsum:
            maxsum = f[i]
            # update start, end
            end = i
            start = curr_start
    return maxsum, start, end
    

nums = [1,-34,-45,100]
nums = [-3,-4, 1, 34, -3, 45, 100, -2, -4]

print(findMaxSum(nums))
```

/********************************************************************************************************/

[Follow-up] Given a 2D matrix. Find the maximum sum rectangle in the 2D matrix containing both +ve and -ve integers.

首先要求分析 straightforward 解法复杂度:

We have O(n^4) rectangles:

since each edge O(n^2) ⇒ O(n^2) *  O(n^2) =  O(n^4)

Can we use the maximum sum 1d array here?

/********************************************************************************************************/

N : cols:

M : rows

O(n^2): i, j

Array: sum_i_j[col] = sum of col, from i to j - 1

Length: n

x x x x x x x x 

x x x x x x x x 

x x x x x x x x 

x x x x x x x x 

x x x x x x x x 

x x x x x x x x 

```python
def findMaxSumMat(matrix):
    m = len(matrix)
    n = len(matrix[0])
    for i in range(m):
        for j in range(i, m):
            # interval i, j ...
```

# 3M Model

Phone Interview @2020.03.17

code logistic regression
