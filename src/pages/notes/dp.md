---
layout: ../../layouts/Layout.astro
title: Dynamic Programming
---

# 1 Introduction

> Q: Maximum Triangle Path Sum + solutions (解答参见 exercises)

![](/notes/dp/media/image1.png)

![](/notes/dp/media/image2.png)

### Recursion v.s. DP

![](/notes/dp/media/image3.png)

解析: 确实, 两个问题都可以通过指数复杂度的递归来求解. 但是问题 A 如果使用动态规划算法, 就会变成多项式复杂度, 比递归要快很多很多. 递归导致做很多次同一个值的重复计算.

#### 递归的不可行性: 重复计算

(参见 slides: coin change)

![](/notes/dp/media/image4.png)

#### 动态规划基本流程

- DP 基本流程: 确定状态 ⇒ 设计状态转移方程 ⇒ 确定初始态边界 ⇒ 按照一定顺序计算

- python 2D array: https://snakify.org/en/lessons/two_dimensional_lists_arrays/

[[0] * m for i in range(n)]

- DP 时间复杂度和什么有关

✅状态的数量

✅状态转移的代价

❌计算顺序

❌初始边界的数量

解析：通常来说, 动态规划的时间复杂度 = 状态数 * 状态转移代价。

计算顺序是从前往后或者从后往前并不会影响动态规划的时间复杂度，但是在某些情况下会影响计算结果的正确性，初始态边界的数量只会影响初始化时间复杂度，而这一部分的时间复杂度是很低的，所以一般情况下动态规划的时间复杂度不会考虑这一部分。 

Problems

最值型动态规划: Minimum Triangle Path Sum

计数型动态规划: Unique Paths

存在型动态规划: Jump Game

### 最值型 Min Triangle Path Sum

> Q: Minimum Triangle Path Sum (medium) | submission

此题如下 bottom-up 写法较为方便; top-down 需要额外处理边界.

```python
def minimumTotal(self, triangle: List[List[int]]) -> int:
    if len(triangle) == 0 or len(triangle[0]) == 0:
        return
    for i in range(len(triangle) - 2, -1, -1):
        for j in range(i + 1): 
            triangle[i][j] += min(triangle[i + 1][j + 1], triangle[i + 1][j]) 
    return triangle[0][0]
```

也可不修改 triangle 的值而额外使用数组 dp 存储:

```python
def minimumTotal(self, triangle: List[List[int]]) -> int:
    dp = list(triangle[-1])
    for i in range(len(triangle) - 2, -1, -1):
        for j in range(i + 1):
            dp[j] = min(triangle[i][j] + dp[j], triangle[i][j] + dp[j + 1])
    return dp[0]
```

参考一种思路相同的不同写法 (submission):

```python
def minimumTotal(self, triangle: List[List[int]]) -> int:
    while len(triangle) > 1:
        level0 = triangle.pop()
        level1 = triangle.pop()
        triangle.append([min(level0[i], level0[i + 1]) + level1[i] \
                         for i in range(len(level1))])
    return triangle[0][0]
```

### 计数型 Unique Paths

#### > Q: Coin Change

状态: dp[i]: number of ways to make i

```python
def coinChange(self, coins: List[int], amount: int) -> int:
    dp = [0] + [sys.maxsize] * amount
    for i in range(1, amount + 1):
        for coin in coins:
            if (i >= coin) and (dp[i - coin] < sys.maxsize):
                dp[i] = min(dp[i], dp[i - coin] + 1)
    return dp[-1] if dp[-1] != sys.maxsize else -1
```

Note: 若 java / C++ 则需要检查 dp[i - coin] < sys.maxsize 以防止最大值 +1 后溢出

> Q: Unique Paths

![](/notes/dp/media/image5.png)

leetcode explanation

![](/notes/dp/media/image6.png)

```python
def uniquePaths(self, m: int, n: int) -> int:
    dp = [[1] * n for _ in range(m)]
    for row in range(1, m):
        for col in range(1, n):
            dp[row][col] = dp[row][col - 1] + dp[row - 1][col]
    return dp[m - 1][n - 1]  # dp[-1][-1]
```

⇒ 使用滚动数组优化空间到 O(2n)

```python
def uniquePaths(self, m: int, n: int) -> int:
    dp = [[1] * n for _ in range(2)]
    old = 0
    new = 1
    for _ in range(1, m):
        new = old
        old = 1 - new
        for col in range(1, n):
            dp[new][col] = dp[new][col - 1] + dp[old][col]
    return dp[new][-1]
```

⇒ 进一步优化到 O(n) memory: 考虑到更新顺序只依赖左边和上边的格子 ⇒ 从左开始更新行

```python
def uniquePaths(self, m: int, n: int) -> int:
    dp = [1] * n
    for i in range(1, m):
        for j in range(1, n):
            dp[j] = dp[j - 1] + dp[j]
    return dp[-1]
```

#### > Q: Unique Paths II 有障碍

暂不使用滚动数组, 仅仅额外考虑 obstacles 的简单做法

```python
def uniquePathsWithObstacles(self, obstacleGrid: List[List[int]]) -> int:
    m = len(obstacleGrid)
    n = len(obstacleGrid[0])
    dp = [[0] * n for _ in range(m)]
    for row in range(m):
        for col in range(n):
            if row == 0 and col == 0:
                dp[row][col] = 1 - obstacleGrid[row][col]
            if not obstacleGrid[row][col] == 1:
                if row > 0: dp[row][col] += dp[row - 1][col]
                if col > 0: dp[row][col] += dp[row][col - 1]
    return dp[-1][-1]
```

⇒ 滚动数组优化到 O(2n)

```python
def uniquePathsWithObstacles(self, obstacleGrid: List[List[int]]) -> int:
    m = len(obstacleGrid)
    n = len(obstacleGrid[0])
    dp = [[0] * n for _ in range(2)]
    now = 0
    old = 1
    for row in range(m):
        now = old
        old = 1 - now
        for col in range(n):
            dp[now][col] = 0
            if row == 0 and col == 0:
                dp[now][col] = 1 - obstacleGrid[row][col]
            if not obstacleGrid[row][col] == 1:
                if row > 0: dp[now][col] += dp[old][col]
                if col > 0: dp[now][col] += dp[now][col - 1]
    return dp[now][-1]
```

Summary:

- obstacle 会影响其下方或右方的 grid 的初始化:

Case 2: [[1, 0]]; Case 3: [[1], [0]];

- 需要考虑终点是否是 obstacle:

Case 4: [[0], [1]]

⇒ 同理进一步优化到 O(n)

```python
def uniquePathsWithObstacles(self, obstacleGrid: List[List[int]]) -> int:
    m = len(obstacleGrid)
    n = len(obstacleGrid[0])
    dp = [0] * n
    for row in range(m):
        for col in range(n):
            if obstacleGrid[row][col] == 1:
                    dp[col] = 0
            else:
                if row == 0 and col == 0:
                    dp[col] = 1
                elif col == 0: 
                    dp[col] = dp[col]
                elif row == 0: 
                    dp[col] = dp[col - 1]
                else: 
                    dp[col] = dp[col] + dp[col - 1]
    return dp[-1]
```

#### > Q: Unique Paths III 路径和

```python
def uniqueWeightedPaths(self, grid):
    if not grid or not grid[0]:
        return 0
    dp = [set()] * len(grid[0])
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if row == 0 and col == 0:
                dp[col].add(grid[row][col])
            else:
                temp = set()
                if row > 0:
                    temp = temp.union(
                        set([v + grid[row][col] for v in dp[col]]))
                if col > 0:
                    temp = temp.union(
                        set([v + grid[row][col] for v in dp[col - 1]]))
                dp[col] = temp
    return sum(dp[-1])
```

Unique Paths

> Q: Unique Paths: 右下方向 

> Q: Unique Paths II: 右下方向 + 障碍物

> Q: Unique Paths III (lintcode): 右下方向 + 所有可行路径经过的格子值求和

> Q: Unique Paths III (leetcode): 四个方向 + 可经过所有非障碍物格子的路径计数 ⇒ DFS

### 存在型 Jump Game

> Q: Jump Game (medium) | DP 时间 O(n^2) & 空间 O(n)

注释：可参考 leetcode 答案区分 bottom-up 和 top-down 两种 & Greedy 时间空间都 O(n).

```python
def canJump(self, nums: List[int]) -> bool:
    n = len(nums)
    can = [0] * (n - 1) + [1]
    for i in range(n - 2, -1, -1):
        can[i] = max(can[i: i + nums[i] + 1])
    return can[0] == 1
```

* MUCH faster solution: Greedy

```python
def canJump(self, nums):
    stepsLeft = 0
    for num in nums[-1]:
        stepsLeft = max(stepsLeft - 1, num)
        if not stepsLeft:
            return False
    return True
```

#### > Q: Jump Game 拓展讨论 *

@source: leetcode solution

Usually, solving and understanding a dynamic programming problem is a 4 step process:

- Start with the recursive backtracking solution ⇒ DFS + backtracking ⇒ TLE

- Optimize by a memo table (top-down DP) ⇒ DFS + memoization search ⇒ TLE

- Remove the need for recursion (bottom-up DP) ⇒ DP (see above)

- Apply final tricks to reduce time / memory complexity ⇒ here, Greedy (see above)

Solution 1: DFS w/o Memoization Search

Time O(2^n) & Space O(n): recursion requires additional memory for stack frames ==> TLE

```python
class Solution:
    def canJump(self, nums):
        return self.canJumpFromPos(0, nums)
        
    def canJumpFromPos(self, pos, nums):
        if pos == len(nums) - 1:
            return True
        furthest_pos = min(pos + nums[pos], len(nums) - 1)
        for next_pos in range(pos + 1, furthest_pos + 1):
            if self.canJumpFromPos(next_pos, nums):
                return True
        return False
```

Solution 2: DFS w/ Memoization Search

Time O(2^n) & Space O(2n) = O(n) ⇒ TLE

Space: First n originates from recursion. Second n comes from the usage of the memo table. 

```python
class Solution:
    def canJump(self, nums):
        memo = ["Unkown"] * (len(nums) - 1) + ["Good"]
        return self.canJumpFromPos(0, nums, memo)
        
    def canJumpFromPos(self, pos, nums, memo):
        if memo[pos] != "Unkown":
            return True if memo[pos] == "Good" else False
    
        furthest_pos = min(pos + nums[pos], len(nums) - 1)
        next_pos = None
        for next_pos in range(pos + 1, furthest_pos + 1):
            if self.canJumpFromPos(next_pos, nums, memo):
                memo[next_pos] = "Good"
                return True
        if next_pos:
            memo[next_pos] = "Bad"
        return False
```

#### > Q: Jump Game II

Solution 1: my stupid DP ⇒ Time O(n^2)

```python
def jump(self, nums: List[int]) -> int:
    n = len(nums)
    steps = [0] * n
    for i in range(n - 2, -1, -1):
        if nums[i] == 0:
            steps[i] = sys.maxsize
        else:
            steps[i] = min(steps[i + 1: i + nums[i] + 1]) + 1
    return steps[0]
```

Solution 2: Time O(n)

The idea is to maintain two pointers left and right, where left is initialized as 0 and right as nums[0]. So points between 0 and nums[0] are the ones you can reach by using just 1 jump.

Next, we want to find points I can reach using 2 jumps, so our new left will be set equal to right, and our new right will be set equal to the farest point we can reach by two jumps.

```python
def jump(self, nums: List[int]) -> int:
    if len(nums) <= 1: return 0
    left, right = 0, nums[0]
    steps = 1
    while right < len(nums) - 1:
        steps += 1
        furthest = max(i + nums[i] for i in range(left, right + 1))
        left, right = right, furthest
    return steps
```

![](/notes/dp/media/image7.png)
![](/notes/dp/media/image8.png)
> Exercises

方案 A：设定 f[i][j] 表示从 (i, j) 的点往下走能得到的最大数字之和  ⇒ 从下到上计算

方案 B：设定 f[i][j] 表示走到 (i, j) 能够得到的最大数字之和 ⇒ 从上到下计算

> Assignments

> Q: Maximum Product Subarray (medium) | submission

```python
def maxProduct(self, nums: List[int]) -> int:
    n =  len(nums)
    if n == 0: return
    f = [nums[0]] * n
    g = [nums[0]] * n
    for i in range(1, n):
        f[i] = max(nums[i], nums[i] * f[i - 1], nums[i] * g[i - 1])
        g[i] = min(nums[i], nums[i] * f[i - 1], nums[i] * g[i - 1])
    return max(f)
```

# 2 初探 & 坐标型 & 位操作型 DP

> 坐标型 Q: Unique Paths II

> 序列型 Q: Paint House

> 划分型 Q: Decode Ways | submission

### 划分型 Decode Ways *

```python
def numDecodings(self, s):
    n = len(s)
    if n == 0: return 0
    
    # f[i]: 数字串 s[0...i-1] 解密成字母串有 f[i] 种方式
    f = [1] + [0] * n  # f[0] = 1

    for i in range(1, n + 1):
        # last one digit --> letter
        if (s[i - 1] != "0"):
            f[i] += f[i - 1]
        # last two digit --> letter
        if (i >= 2) and (10 <= int(s[i - 2: i]) <= 26):
            f[i] += f[i - 2]
    return f[n]
```

注释:

- 循环中的初始化 f[i] = 0 保证了一旦出现 “00” 则后续所有 f[i] 为 0

e.g.: Case: s = ”1920011” 需要返回 0

- 10 <= int(s[i - 2: i]) <= 26

### 坐标型 Grids

#### > Q: Minimum Path Sum

```python
def minPathSum(self, grid):
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if row == 0 and col > 0:
                grid[row][col] += grid[row][col - 1]
            if col == 0 and row > 0:
                grid[row][col] += grid[row - 1][col]
            if row > 0 and col > 0:
                grid[row][col] += min(grid[row][col - 1], 
                                      grid[row - 1][col])
    return grid[-1][-1] 
```

##### + 路径打印

```python
def minPathSum(self, grid: List[List[int]]) -> int:
    m, n = len(grid), len(grid[0])
    pi = [[""] * n for _ in range(m)]
    # pi[i][j] = "U" if grid[i][j] comes from grid[i - 1][j], from Up
    # pi[i][j] = "L" if grid[i][j] comes from grid[i][j - 1], from Left

    for row in range(m):
        for col in range(n):
            if row == 0 and col > 0:
                grid[row][col] += grid[row][col - 1]
                pi[row][col] = "L"
            if col == 0 and row > 0:
                grid[row][col] += grid[row - 1][col]
                pi[row][col] = "U"
            if row > 0 and col > 0:
                if grid[row][col - 1] < grid[row - 1][col]:
                    grid[row][col] += grid[row][col - 1]
                    pi[row][col] = "L"
                else:
                    grid[row][col] += grid[row - 1][col]
                    pi[row][col] = "U"

    # Retrieve the path
    row = m - 1
    col = n - 1
    path = []
    for _ in range(m + n - 2, -1, -1):
        path.append((row, col))
        if pi[row][col] == "U":
            row -= 1
        else:
            col -= 1
    # print(path[::-1])

    return grid[-1][-1]
```

##### + 空间优化: 滚动数组

(trivial; please refer to Unique Paths & Unique Paths II)

#### > Q: Bomb Enemy

solution

### 位操作 Counting Bits

```python
def countBits(self, num):
    f = [0] * (num + 1)
    for i in range(1, num + 1):
        # f[i] = f[i & i-1] + 1  # or
        f[i] = f[i >> 1] + (i % 2)
    return f
```

> Assignment: Longest Increasing Continuous Subsequence | solution

# 3 序列型 DP

### 状态序列型

#### > Q: Digital Flip

题目：给定一个 01 构成的数组 [0,1,0,0,1,0,0,1,1,1,0,1,1,1,1,0]。你可以翻转 1 变成 0 或者翻转 0 变成 1。请问最少翻转多少次可以使得数组满足以下规则：1 的后面可以是 1 或者 0，而 0 的后面必须是 0。

思路 1：记录整个数字 1 的个数，然后枚举 0 和 1 的分界点，维护最小转次数。时间 O(n)。

思路 2：动态规划。时间 O(n)。

- 用 f[i][0] 表示 A[i-1] 变成 0 的情况下, 前 i 位最少翻转多少个能满足要求

- 用 f[i][1] 表示 A[i-1] 变成 1 的情况下, 前 i 位最少翻转多少个能满足要求

![](/notes/dp/media/image9.png)

![](/notes/dp/media/image10.png)

注释: A 也是不错的方法

```python
def flipDigit(self, nums):
    n = len(nums)
    if n <= 1:
        return 0
    f = [[0] * 2 for _ in range(n + 1)]
    # f[i][j]: number of flips needed if (all before nums[i]) == j
    f[0][0] = 0
    f[0][1] = 0
    for i in range(1, n + 1):
        for j in [0, 1]:
            f[i][j] = float('inf')
            for k in [0, 1]:
                turn = (nums[i - 1] != k)
                if not (k == 0 and j == 1):
                    f[i][j] = min(f[i][j], f[i - 1][k] + turn)
    return min(f[n][0], f[n][1])
```

DP w/ 滚动数组: quickest

```python
def flipDigit(self, nums):
    if not nums or len(nums) == 0: 
        return 0
    num0 = 0 # flip current to 0, minimum flip numbers including previous to follow the rules
    num1 = 0 # flip current to 1, minimum flip numbers including previous to follow the rules
    for n in nums:
        if n == 0: 
            num0 = min(num0, num1)
            num1 = num1 + 1
        if n == 1:
            num0 = min(num0, num1) + 1
            num1 = num1
    return min(num1, num0)
```

#### > Q: Paint House II

如下推导 Naive DP: O(NK^2) ⇒ TLE

![](/notes/dp/media/image11.png)

时间优化:

- 分别记录下 f[i-1][1], …, f[i-1][K] 中的最小值 f[i-1][a] 和次小值 f[i-1][b]

- 则对于 j=1,2,3,…,a-1, a+1,…,K, f[i][j] = f[i-1][a] + cost[i-1][j]

- f[i][a] = f[i-1][b] + cost[i-1][a]

⇒ 时间复杂度降为O(NK)

```python
def minCostII(self, costs):
    if not costs: return 0
    if not costs[0]: return 0
    N = len(costs)
    K = len(costs[0])

    for i in range(1, N):
        # Find 1st & 2nd minimum among f[i-1][0], ..., f[i - 1][K - 1]
        a = -1  # 1st minimum
        b = -1  # 2nd minimum
        for k in range(K):
            if (a == -1) or (costs[i - 1][k] < costs[i - 1][a]):
                b = a  # old minimum is now 2nd minimum
                a = k  # new minimum is f[i-1][k]
            else:
                if (b == -1) or (costs[i - 1][k] < costs[i - 1][b]):
                    b = k

        # Update costs
        for k in range(K):
            if k != a:
                costs[i][k] += costs[i - 1][a]
            else:
                costs[i][k] += costs[i - 1][b]

    return min(costs[-1])
```

##### + 路径打印

```python
def minCostII(self, costs):
    if not costs: return 0
    if not costs[0]: return 0
    N = len(costs)
    K = len(costs[0])

    # pi[i][j] = k: means f[i][j] chooses f[i-1][k] as the color
    pi = [[0] * (K) for _ in range(N)]
    
    # Update costs[i][j] as: min total cost to paint house i as color j
    for i in range(1, N):
        # Find 1st & 2nd minimum among f[i-1][0], ..., f[i - 1][K - 1]
        a = -1  # 1st minimum
        b = -1  # 2nd minimum
        for k in range(K):
            if (a == -1) or (costs[i - 1][k] < costs[i - 1][a]):
                b = a  # old minimum is now 2nd minimum
                a = k  # new minimum is f[i-1][k]
            else:
                if (b == -1) or (costs[i - 1][k] < costs[i - 1][b]):
                    b = k

        # Update costs
        for k in range(K):
            if k != a:
                costs[i][k] += costs[i - 1][a]
                pi[i][k] = a
            else:
                costs[i][k] += costs[i - 1][b]
                pi[i][k] = b
    
    # Find the minimum color of the last house
    mink = 0
    for k in range(K):
        if costs[N - 1][k] < costs[N - 1][mink]:
            mink = k

    # Loop back to get the color of all houses
    color = [0] * N
    c = mink
    for i in range(N - 1, -1, -1):
        color[i] = c
        c = pi[i][c]
        print("House " + str(i) + " is color " + str(color[i]))
    
    return costs[-1][mink]
```

> Q: Best Time to Buy and Sell Stock | solution: Greedy

题意: 只能进行一次股票买卖

```python
def maxProfit(self, prices):
    res = 0
    buy = 0
    out = 0
    min_i = 0
    for i in range(n = len(prices)):
        if prices[i] < prices[min_i]:
            min_i = i
        if prices[i] - prices[min_i] >= res:
            res = prices[i] - prices[min_i]
            buy = min_i
            out = i
    return res
```

> Q: Best Time to Buy and Sell Stock II | solution: Greedy

题意: 允许任意多次股票买卖

解法: Greedy. 只要今天的价格比明天的价格低 ⇒ 今天买明天卖 ⇒ Time O(n) & Space O(1)

#### > Q: Best Time to Buy and Sell Stock III

题意: 最多只能两次股票买卖

##### + 解法 1: 空手套白狼

思路参考 by Tin: 把状态设置成每个阶段的获利 (解法 2) 很不利于思考 ⇒ 转换思考方位: 只关注你的股票账户的现金数会。

此题可理解为：你账户里的现金最多有四种状态：1. 第一次满仓，2. 第一次清仓，3. 第二次满仓，4. 第二次清仓。分别用 h1，s1，h2，s2 代表。 h 是 hold，s 是 sold。

这里我们用空手套白狼的手法，即借钱买股票，因为反正知道股票的未来价格，稳定赚钱。

第一次满仓时，是借钱买股票，那天买，就欠那天价格数的钱，目标是用最低价格买进，所以要孜孜以求的把它置为最小，求反就是 max ⇒ h1 = max(h1, -price)

满仓的初始值设为股票最高价的负数，也就是你最多需要借那么多钱。直接就是 -inf 太糙。

第一次清仓时，你账户里的现金应该是当天卖掉股票的成交价格冲抵你的余额 (欠的钱)。这还要和以前的最优的 (余额最高) 的额度比，没以前高，就别清仓了 ⇒ s1 = max(s1, price + h1)

可直接扩展为 k 次买卖解法。

(submission)

```python
def maxProfit(self, prices: List[int]) -> int:
    h1 = h2 = - max(prices)  # float('-inf') 
    s1 = s2 = 0 
    for price in prices:
        h1 = max(h1, - price) 
        s1 = max(s1,   price + h1)
        h2 = max(h2, - price + s1)
        s2 = max(s2,   price + h2)
    return s2
```

##### + 解法 2: 普通 DP

submission | Time O(n); Space O(n) 滚动数字优化到 O(1), i.e.: O(k), k = 2.

```python
def maxProfit(self, P):
    n = len(P)
    if n <= 1: return 0
        
    nos = 2 * 2 + 1  # num of stages

    # f[i][j]: 前 i 天 (第 i-1 天结束后) 处在 stage j 的最大获利
    f = [[0] * (nos + 1) for _ in range(2)]
    for j in range(2, nos + 1):
        f[0][j] = - float('inf')  # impossible

    new = 0
    old = 1
    for i in range(1, n + 1):
        new = old
        old = 1 - new
        for j in range(1, nos + 1, 2):
            f[new][j] = f[old][j]
            if (j > 1) and (i > 1) and (f[old][j - 1] != -float('inf')):
                f[new][j] = max(
                    f[new][j], f[old][j - 1] + P[i - 1] - P[i - 2])
        
        for j in range(2, nos + 1, 2):
            f[new][j] = f[old][j - 1]
            if (i > 1) and (f[old][j] != - float('inf')):
                f[new][j] = max(
                    f[new][j], f[old][j] + P[i - 1] - P[i - 2])
    
    return max(f[new][1::2])
```

+ 解法 3: ???

(solution)

```python
def maxProfit(self, prices):
    n = len(prices)
    if n <= 1:
        return 0
    p1 = [0] * n
    p2 = [0] * n
    
    minV = prices[0]
    for i in range(1,n):
        minV = min(minV, prices[i]) 
        p1[i] = max(p1[i - 1], prices[i] - minV)
    
    maxV = prices[-1]
    for i in range(n-2, -1, -1):
        maxV = max(maxV, prices[i])
        p2[i] = max(p2[i + 1], maxV - prices[i])
    
    res = 0
    for i in range(n):
        res = max(res, p1[i] + p2[i])
    return res
```

#### > Q: Best Time to Buy and Sell Stock IV

题意: 最多只能 k 次股票买卖

参考: discussion from lintcode

+ 解法 1: 空头套白狼 (参考上题)

注意要特殊处理 k >= n / 2 的情形。否则 TLE。

(submission)

```python
def maxProfit(self, k: int, prices: List[int]) -> int:
    n = len(prices)
    if k >= n / 2:
        return self.quickSolve(n, prices)
    if k == 0:
        return 0

    dp = [0] * (2 * k)
    dpmin = - max(prices) 
    for i in range(0, 2 * k, 2):
        dp[i] = dpmin

    for price in prices:
        dp[0] = max(dp[0], - price) 
        for i in range(1, 2 * k):
            dp[i] = max(dp[i], dp[i - 1] + price * [-1, 1][i % 2])
        # h1 = max(h1, - price)
        # s1 = max(s1,   price + h1) 
        # h2 = max(h2, - price + s1)
        # s2 = max(s2,   price + h2)
    return dp[-1]

def quickSolve(self, n, prices):
    sum = 0
    for x in range(n - 1):
        if prices[x + 1] > prices[x]:
            sum += prices[x + 1] - prices[x]
    return sum
```

+ 解法 2: 普通 DP

(submission)

+ 解法 3: ???

(solution):

```python
def maxProfit(self, k, prices):
    size = len(prices)
    if k >= size / 2:
        return self.quickSolve(size, prices)
    dp = [None] * (2 * k + 1)
    dp[0] = 0
    for i in range(size):
        for j in range(min(2 * k, i + 1) , 0 , -1):
            dp[j] = max(dp[j], dp[j - 1] + prices[i] * [1, -1][j % 2])
    return max(dp)

def quickSolve(self, size, prices):
    sum = 0
    for x in range(size - 1):
        if prices[x + 1] > prices[x]:
            sum += prices[x + 1] - prices[x]
    return sum      
```

### 状态序列型总结

序列 + 状态 Dynamic Programming

- 动态规划最后一步的选择依赖于前一步的某种状态

- 初始化: f[0] 代表前 0 个元素 / 前 0 天的情况

与坐标型动态规划区别 ?

- 计算时: f[i] 代表前 i 个元素 (即元素 0 ~ i-1) 的某种性质

![](/notes/dp/media/image12.png)

### 最长序列型

#### > Q: Longest Increasing Subsequence

##### + 解法 0: O(2^n) Brute Force: DFS ⇒ TLE

```python
class Solution:
    def lengthOfLIS(self, nums: List[int]) -> int:
        self.n = len(nums)
        return self.lenOfLIS(nums, float('-inf'), 0)
    
    def lenOfLIS(self, nums, prev, cur_pos):
        if curr_pos == self.n:
            return 0
        taken = 0
        if nums[cur_pos] > prev:
            taken = 1 + self.lenOfLIS(nums, nums[cur_pos], cur_pos + 1)
        not_taken = self.lenOfLIS(nums, prev, cur_pos + 1)
        return max(taken, not_taken)
```

##### + 解法 1: O(n^2) Naive DP

f[j] 表示以 a[j] 结尾的最长上升子序列的长度:

- 枚举前面所有小于自己的数字 j ⇒ f[i] = max{f[j]} + 1

- 如果没有比自己小的 ⇒ f[i] = 1

![](/notes/dp/media/image13.png)

(submission): too slow, DO NOT use

```python
def longestIncreasingSubsequence(self, nums):
    n = len(nums)
    if n <= 1: return n

    f = [1] * n
    for i in range(1, n):
        for j in range(i):
            if nums[j] < nums[i]:
                f[i] = max(f[i], f[j] + 1)
    return max(f)
```

##### + 解法 2: O(nlogn) 二分法 *

思路: tails[k] 存储 “以该数为结尾的 LIS 长度为 k” 的数。若有多个位置, 以这些位置为结尾的 LIS 长度都为 k, 则这些数字中最小的一个存在 tails[k] 中。i.e.:

 tails[k] = nums[i], where f[i] == k 

则 B 数组严格递增。且索引值 k 表示 LIS 长度也严格递增。

⇒ 可以在 B 数组中进行二分查找: 

- 对于每个位置 i 寻找所有 j < i s.t. A[j] < A[i] 且在 B 中索引值 k 最大的 j

- f[i] = f[j] + 1

注释: java 还可使用 TreeSet 实现 O(nlogn)。

解释 from leetcode discussion:

tails: array storing the smallest tail of all increasing subsequences with length i+1 in tails[i].

e.g.: say we have nums = [4,5,6,3], then all the available increasing subsequences are:

```
len = 1 : [4], [5], [6], [3]   => tails[0] = 3
len = 2 : [4, 5], [5, 6]       => tails[1] = 5
len = 3 : [4, 5, 6]            => tails[2] = 6
```

We can easily prove that tails is a increasing array. Therefore it is possible to do a binary search in tails array to find the one needs update. Each time we only do one of the two:

(1) if x is larger than all tails, append it, increase the size by 1

(2) if tails[i-1] < x <= tails[i], update tails[i]

(submisson)

```python
def lengthOfLIS(self, nums: List[int]) -> int:
    # tails: the smallest tail of all IS with length i+1 in tails[i].
    tails = [0] * len(nums)
    size = 0
    for x in nums:
        i, j = 0, size
        while i != j:
            m = (i + j) // 2
            if tails[m] < x:
                i = m + 1
            else:
                j = m
        tails[i] = x
        size = max(i + 1, size)
    return size
```

> 相关题目: Number of Longest Increasing Subsequence

![](/notes/dp/media/image14.png)
> Exercises

解析：4 次。交换的方法不唯一, e.g.: 得到 A=[0,4,5,7,10,11,19,20], B=[4,7,8,10,11,14,17,18].

![](/notes/dp/media/image15.png)

解析: 0 1 1 0。如果他已经是有序的了，那么不需要交换的 f[i][0] 就应该是等于前面一个不交换的，也就是 f[i-1][0]。如果他是可以交换的，那么这一次不交换的话说明前一次要交换，也就是 f[i][0]=f[i-1][1]，但是如果两个条件都满足的情况下，就应该取这两种情况的最小值，也就是 f[i][0]=min(f[i-1][0], f[i-1][1])。

![](/notes/dp/media/image16.png)

![](/notes/dp/media/image17.png)

![](/notes/dp/media/image18.png)

A. 在状态转移方程里面已经写明了可以不交换和可以交换成功的两个条件, 如果保证有解, 那么就会满足两个条件至少成立其中之一, 所以只需要遍历一遍判断是否有其中之一成立即可。

C. 我们已经把数组中元素初始化为 Integer.MAX_VALUE, 而如果交换不出我们要求的结果转移方程里面两个 if 是无法进入的, 那么 f 数组在断层的那里开始后面都是大于等于 Integer.MAX_VALUE。

![](/notes/dp/media/image19.png)

> Assignment: Russian Doll Envelopes | solution 

要求: 实现 O(nlogn) 而非 O(n^2)

思路: 信封按照长度从小到大排序 (相同长度按宽度从大到小) 后找宽度的 Longest Increasing Subsequence

# 4 划分型 & 博弈型 & 背包型 DP

### 划分型

#### > Q: Perfect Squares

![](/notes/dp/media/image20.png)
思路: 设 f[i] 表示 i 最少被分成几个完全平方数之和

```python
def numSquares(self, n):
    dp = [0] + [float('inf')] * n
    for i in range(1, n + 1):
        for j in range(int(i ** 0.5) + 1):
            dp[i] = min(dp[i], dp[i - j * j] + 1)
    return dp[-1]
```

> Follow-ups

- 有多少种方式把 N 表示成完全平方数之和 (1 2 + 2 2 和 2 2 + 1 2 属于不同的方式）

- 能不能把 N 表示成恰好 K 个完全平方数之和

![](/notes/dp/media/image21.png)

解析：f[i][k] 表示的是数字 i 可以拆分成 k 的方案数，它就应该是所有 i - j * j 的并且由 k-1 个数组成的方案数之和。结果就是拆分成 1,2,3...k 个数的方案数之和。

#### > Q: Palindrome Partitioning II

![](/notes/dp/media/image22.png)

```python
def minCut(self, s):
    n = len(s)
    f = []
    # p[i][j]: s[i...j] is a palindrome
    p = [[False for x in range(n)] for x in range(n)]

    for i in range(n + 1):
        f.append(n - 1 - i)  # the last one f[n] = -1

    for i in reversed(range(n)):
        for j in range(i, n):
            if (s[i] == s[j] and (j - i < 2 or p[i + 1][j - 1])):
                p[i][j] = True
                f[i] = min(f[i], f[j + 1] + 1)
    return f[0]
```

#### > Q: Copy Books *

submission

```
public int copyBooks(int[] A, int K) {
    int N = A.length;  // num of books
    
    // Special cases
    if (N == 0) return 0;
    if (K > N) K = N;
    
    // f[k][j]: time for first k copiers to finish first j books
    int f[][] = new int[K+1][N+1];
    int k, j, i, s;
    
    // Initialization
    for (j = 1; j <= N; ++j) {
        f[0][j] = Integer.MAX_VALUE;
    }
    
    // First k copiers
    for (k = 1; k <= K; ++k) {
        f[k][0] = 0;  // Initialization for f[k][0] can be done here

        // To finish first i books
        for (i = 1; i <= N; ++i) {
            f[k][i] = Integer.MAX_VALUE;
            // s = A[j] + ... + A[i-1], to be calcuated
            s = 0;  
            for (j = i; j > 0; --j) {
                // Update s: s += A[j-1]
                s += A[j-1];  // time for j-th book
                
                if (f[k-1][j-1] != Integer.MAX_VALUE) {
                    f[k][i] = Math.min(
                        f[k][i], 
                        Math.max(f[k-1][j-1], s));
                }
            }
        }
    }
    return f[K][N];
}
```

Alternatively, change the place to calcuate s, i.e.:

```
        for (i = 1; i <= N; ++i) {
            f[k][i] = Integer.MAX_VALUE;
            // s = A[j] + ... + A[i-1], to be calcuated
            s = 0;  
            for (j = i; j >= 0; --j) {
                
                if (f[k-1][j] != Integer.MAX_VALUE) {
                    f[k][i] = Math.min(f[k][i], Math.max(f[k-1][j], s));
                }
            
                // Update s: s += A[j-1]
                if (j > 0) {
                    s += A[j-1];  // time for j-th book
                }
            }
        }
```

### 博弈型 Coins in A Line

思路参考 slides \ python 解法使用了滚动数组

```python
def firstWillWin(self, n):
    dp = [False, True]
    if n < 2:
        return dp[n]
    
    now, old = 0, 0
    for i in range(n - 1):
        now = old
        old = 1 - now
        dp[now] = dp[old] == False or dp[now] == False

    return dp[now]
```

### 背包型 [可行] I

> Quick Notes

- 背包问题所用数组一定有一个维度和背包最大承重 m 有关.

- 背包问题重量都是整数. 若不是整数, 比如有两位小数, 则乘以 100 直至整数.

> Q: Backpack | submission

- 是 A[i - 1] 不是 A[i]

- size[i][w]: whether first i items can make w weights

(python)

```python
def backPack(self, m, A):
    n = len(A)
    
    # f[i][w]: whether first i items can make w weight
    # 使用滚动数组
    f = [[True] + [False] * m for _ in range(2)]
    
    now, old = 0, 0
    maxSize = 0
    for i in range(n):
        now = old
        old = 1 - now
        for w in range(m + 1):
            # Case 1: using item A[i-1]
            if w >= A[i]:
                f[now][w] = f[old][w] or f[old][w - A[i]]
            
            # Case 2: not using item A[i-1]
            else:
                f[now][w] = f[old][w]
            
            # Update the maximum size
            if (i == n - 1) and f[now][w]:
                maxSize = max(w, maxSize)

    return maxSize
```

(java)

```
public int backPack(int m, int[] A) {
    int n = A.length;
    
    if (n == 0 | m == 0) {
        return 0;
    }
    
    // size[i][w]: whether first i items can make w weights
    boolean[][] size = new boolean [n + 1][m + 1];
    int i, w, maxSize = 0;

    // Initialization
    size[0][0] = true;
    for (i = 1; i <= m; ++i) {
        size[0][i] = false;
    }
    
    for (i = 1; i <= n; ++i) {
        for (w = 0; w <= m; ++w) {
            // Case 1: using item A[i-1]
            if (w - A[i - 1] >= 0) {
                size[i][w] = size[i - 1][w] || size[i - 1][w - A[i-1]];
            } 
            // Case 2: not using item A[i-1]
            else {
                size[i][w] = size[i - 1][w];
            }
            
            // Update the maximum size
            if (i == n && size[i][w] == true) {
                maxSize = w;
            }
        }
    }
    return maxSize;
```

### 背包型 [计数] V & VI

#### > Q: Backpack V * 无重复

题意: 求 N 个物品 A0 ,..., AN-1 有多少种组合加起来是 Target. 每个 Ai 只能用一次.

解析: 

- 只更改 Backpack 问题中的 initialization 和 transition function (Solutoin 1) ⇒ TLE

- 滚动数组优化到 Memory O(2W) (Solutoin 2)

- 可进一步优化到 Memory O(W) (Solutoin 3)

Solutoin 1 (Memory Limit Exceed):

```python
def backPackV(self, nums, W):
    N = len(nums)
    # numWays[i][w]: number of ways that i items can make weight w
    numWays = [[0] * (W + 1) for _ in range(N + 1)]
    for i in range(N):
        numWays[i][0] = 1

    for w in range(1, W):
        numWays[0][w] = 0

    for i in range(1, N+1):
        for w in range(1, W + 1):
            if (w - nums[i - 1]) >= 0:
                numWays[i][w] = numWays[i - 1][w] + \
                                numWays[old][w - nums[i - 1]]
            else:
                numWays[i][w] = numWays[i - 1][w]
    
    return numWays[N][W]
```

Solutoin 2:

```python
def backPackV(self, nums, W):
    N = len(nums)
    # numWays[i][w]: number of ways that i items can make weight w
    numWays = [[1] + [0] * W for _ in range(2)]

    new = 0
    for i in range(1, N + 1):
        old = new
        new = 1 - old
        for w in range(1, W + 1):
            if (w - nums[i - 1]) >= 0:
                numWays[new][w] = numWays[old][w] + \
                                  numWays[old][w - nums[i - 1]]
            else:
                numWays[new][w] = numWays[old][w]
    
    return numWays[new][W]
```

Solution 3 **:

```python
def backPackV(self, A, m):
    n = len(A)
    # f[i][w]: number of ways that i items can make weight w
    f = [1] + [0] * m

    for i in range(1, n + 1):
        for w in range(m, A[i - 1] -1, -1):
            f[w] += f[w - A[i - 1]]
    
    return f[-1]
```

#### > Q: Backpack VI 可重复

题意: 求 N 个物品 A0 ,..., AN-1 有多少种组合加起来是 Target. 每个 Ai 可以用多次.

解析: 思路可类比 Coin Challenge 类似 \ 稍微修改 backpack V 即可

```python
def backPackVI(self, A, m):
    n = len(A)
    # f[i][w]: number of ways that i items can make weight w
    f = [1] + [0] * m

    for w in range(m + 1):
        for i in range(n):
            if w >= A[i]:
                f[w] += f[w -A[i]]

    return f[-1]
```

> 课后检测

![](/notes/dp/media/image23.png)

- 状态转移：如果按照上一题的子问题求解，那么对应的状态转移方程是什么?（sum[i]表示拿走前 i 个硬币时总价值，f[i] 表示拿走前i个硬币时先手获得的最大价值。

⇒ 解析：我们拿走第 i 个硬币的最大价值就应该是拿到 i 的时候硬币总价值减去对手拿的在加上我们自己拿的硬币的价值。并且我们根据上一题的子问题来遍历的话最后一个拿的硬币是 0 号硬币，然后是 1 号硬币，所以需要我们从后往前遍历。

```
     sum[i] = sum[i+1] + values[i];
     f[i] = max(
         sum[i+1] - f[i+1] + values[i], //拿一个硬币
         sum[i+2] - f[i+2] + values[i] + values[i+1] //拿两个硬币
     );
```

- 上题中的初始态正确的是什么？

```
     f[n] = sum[n] = 0;
     f[n-1] = sum[n-1] = values[n-1];
```

- 选如上初始状态后循环顺序是: 从 n - 2 到 0

- 结合上面四个题目的选项和答案，我们最后需要怎么判断先手获胜呢？两种方式：

![](/notes/dp/media/image24.png)

```
     f[0] > sum[0] / 2
     f[0] > sum[0] - f[0]
```

解析：

1. 前面我们说到sum为硬币的总价值，f 为先手获得的最大价值，那么后手获得的最大价值就是sum[0] - f[0]，我们要判断谁赢只需要根据题目意思比较一下先手和后手谁获得价值大就行。

2. sum[0] / 2 表示总价值的二分之一，如果先手获得的价值已经大于一半了，那么肯定是先手获胜。

# 5 背包型 & 区间型 DP

### 背包型 [最值] II & III

#### 考虑价值 + 打印路径 *

> Q: Backpack II | submission

```python
def backPackII(self, m, A, V):
    n = len(A)
    if n == 0:
        return 0
    
    # f[i][w]: the max value of first i items with weight w
    f = [[0] * (m + 1) for _ in range(n + 1)]
    
    # f[0][w]: cannot make >0 weight with 0 item
    for w in range(1, n + 1):
        f[0][w] = -1
        
    for i in range(1, n + 1):
        for w in range(m + 1):
            f[i][w] = f[i - 1][w]
            if (w >= A[i - 1]) and (f[i - 1][w - A[i - 1]] >= 0):
                f[i][w] = max(
                    f[i][w], f[i - 1][w - A[i - 1]] + V[i - 1])
    return max(f[n])
```

这里状态 f[i][w] 表示前 i 个物品拼出容量 w 时, 得到的最大总价值. 容量 w 未必能拼得出来. 不过, 我们可以做一点点小小的变动, 就可避免最后的循环, 直接返回 f[n][m], 你能想到怎么做吗?

打印路径

e.g.:

Input

10

[2,3,5,7]

[1,5,2,4]

Expected

9

Stdout (print(f))

[0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]

[0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0]

[0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1]

[0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1]

Weight: 7 , Value: 4

Weight: 3 , Value: 5

(python)

```python
def backPackII(self, m, A, V):
    n = len(A)
    if n == 0:
        return 0
    
    # f[i][w]: the max value of first i items with weight w
    f = [[0] * (m + 1) for _ in range(n + 1)]
    # selected[i][w]: whether selected to make f[i][w]
    selected = [[0] * (m + 1) for _ in range(n)]
    
    # f[0][w]: cannot make >0 weight with 0 item
    for w in range(1, m + 1):
        f[0][w] = -1
    
    maxv = 0
    for i in range(1, n + 1):
        for w in range(m + 1):
            f[i][w] = f[i - 1][w]
            if (w >= A[i - 1]) and (f[i - 1][w - A[i - 1]] >= 0):
                candidate = f[i - 1][w - A[i - 1]] + V[i - 1]
                if f[i][w] < candidate:
                    f[i][w] = candidate
                    # update whether selected
                    selected[i - 1][w] = 1

                # update max value
                if f[i][w] > maxv:
                    weight = w  # weight corresponds to max value
                    maxv = f[i][w]
    
    for line in selected:
        print(line)

    for i in range(n - 1, -1, -1):
        if selected[i][weight] == 1:
            weight -= A[i]
            print("Weight:", A[i], ", Value:", V[i])

    return maxv
```

#### 考虑价值 + 可以重复 **

> Q: Backpack III | submission

如果每个物品都从取 0 还是 k 个遍历算一遍则 Time O(nm^2) 会超时 (解法如下)

```python
def backPackIII(self, A, V, m):
    n = len(A)
    if n == 0: return 0
    
    F = [[0] * (m + 1) for _ in range(n + 1)]
    # BUG 1: No need to init as -1
    # for w in range(1, m + 1):
    #     F[0][w] = -1
        
    for i in range(1, n + 1):
        for w in range(m + 1):
            F[i][w] = F[i - 1][w]
            k = 1
            # BUG 2: >= instead of >;
            # otherwise A = [1], V = [2], m = 10 gives 9
            while w >= k * A[i - 1] and F[i - 1][w - k*A[i - 1]] >= 0):
                F[i][w] = max(
                    F[i][w], F[i - 1][w - k * A[i - 1]] + k * V[i - 1])
                k += 1
```

时间优化? 主要改变是 F[i][w] = max(F[i][w], F[i][w - A[i - 1]] + V[i - 1]) 是 F[i][w - A[i - 1]] 而不是 F[i - 1][w - A[i - 1]] 。这样可以减少重复计算。

⇒ 优化 Time O(nm^2) 到 O(nm)

```python
def backPackIII(self, A, V, m):
    n = len(A)
    if n == 0: return 0
    
    F = [[0] * (m + 1) for _ in range(n + 1)]

    # NOTE: the below init in optional for this method
    # for w in range(1, m + 1):
    #     F[0][w] = -1

    for i in range(1, n + 1):
        for w in range(m + 1):
            F[i][w] = F[i - 1][w]
            if (w >= A[i - 1]) and (F[i][w - A[i - 1]] >= 0):
                F[i][w] = max(
                    F[i][w], F[i][w - A[i - 1]] + V[i - 1])

    return max(F[n])    
```

⇒ 优化 Memory 到一个一维数组 O(m) | ATTENTIONS: 顺序从左往右 (与之前题相反)

```python
def backPackIII(self, A, V, m):
    n = len(A)
    if n == 0: return 0
    
    F = [0] * (m + 1)
        
    for i in range(1, n + 1):
        for w in range(A[i - 1], m + 1):
           if F[w - A[i - 1]] >= 0:
                F[w] = max(F[w], F[w - A[i - 1]] + V[i - 1])
                
    return max(F)
```

Note: for w in range(A[i - 1], m + 1) 从 A[i - 1] 开始可以减少时间

![](/notes/dp/media/image25.png)

解析：既然每个物品有一定的数量, 那么我们完全可以把它们看成不同的物品, 然后按照 Backpack II 的算法来解决. 只不过速度可能更慢一点而已. 但是 Backpack III 的优化算法是固然不可行的, 因为物品数量有限, 不能无限地取用.

### 背包型总结

### 可行性背包: Backpack

  - 题面：要求不超过Target时能拼出的最大重量

  - 记录f[i][w] = 前 i 个物品能不能拼出重量 w

- 计数型背包: Backpack V, Backpack VI

  - 题面：要求有多少种方式拼出重量Target

  - 记录f[i][w] = 前 i 个物品有多少种方式拼出重量 w

- 最值型背包: Backpack II, Backpack III

  - 题面：要求能拼出的最大价值

  - 记录f[i][w] = 前 i 个 / 种物品拼出重量 w 能得到的最大价值

- 关键点

  - 最后一步

    - 最后一个背包内的物品是哪个

    - 最后一个物品有没有进背包

  - 数组大小和最大承重Target有关

- 空间优化

### 动态规划两种思路

#### > 递推方法

- 顺序: 自下而上 bottom-up, i.e.: f[0], f[1], …, f[N]

- 优势: 在某些条件下可以做空间优化, 但记忆化搜索则必须存储所有 f 值

#### > 记忆化搜索

- 顺序: 自上而下 top-down, i.e.: f(N), f(N-1), …

- 优势: 程序编写一般比较简单

- 注意: 记得 calc 算好每个值后要 return

![](/notes/dp/media/image26.png)

解析：一般来说, 动态规划的时间复杂度 = 状态的数量 * 状态转移的时间. 无论是递推还是记忆化搜索, 使用相同的状态定义和状态转移方程, 所以时空复杂度相同. C 属于迷惑选项, 即使是使用递归, 子问题被计算出来的顺序也是从小的状态到大的状态, 遵从状态转移方程.

### 区间型

区间型动态规划的特殊之处: 初始化和计算顺序都是按照区间长度

#### > Q: Longest Palindromic Subsequence

此题三种解法参考:

- 基于中心点枚举的算法 O(n^2)

- 动态规划 O(n^2)

  - 自下而上: 递推

  - 自上而下: 记忆化搜索

- Manancher's Algorithm O(n)

动态规划解法 (递推)

![](/notes/dp/media/image27.png)

submission: java & python

```python
def longestPalindromeSubseq(self, s: str) -> int:
    n = len(s)
    if n <= 1:
        return n

    # f[i][j]: longest palindromic subsequence in s[i: j + 1]
    f = [[0] * n for _ in range(n)]

    for i in range(n):
        f[i][i] = 1

    for i in range(n - 1):
        f[i][i + 1] = int(s[i] == s[i + 1]) + 1

    for length in range(3, n + 1):
        # [i...i + length - 1]
        # i + length - 1 < n ==> i < n - length + 1 ==> i <= n - length
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                f[i][j] = max(f[i + 1][j], f[i][j - 1], 
                              f[i + 1][j - 1] + 2)
            else:
                f[i][j] = max(f[i + 1][j], f[i][j - 1])

    return f[0][n - 1]
```

动态规划解法 (记忆化搜索) 求解上题 | solution java

注意: 以下三处 ATTENTION 内容是记忆化搜索关键点

```python
class Solution {
    char[] s;
    int n = 0;
    int[][] f;
    
    void calc(int i, int j) {
        // compute f[i][j]
        if (f[i][j] != -1) {
            // ATTENTION 2:
            // if has been calculated, return directly (use memory)
            return;
        }
        // calc will be called no more than (3n * n + 1) times
        // -------------------------------------------------------------
        // If the program continues below, this means that: 
        // f[i][j] has not been calculated. 
        // This happens only n * n times.
        
        if (i == j) {
            f[i][i] = 1;
            return;  // REMEMBER to return HERE
        }
        
        if (i + 1 == j) {
            f[i][i + 1] = (s[i] == s[i + 1]) ? 2 : 1;
            return;  // REMEMBER to return HERE
        }
        
        // ATTENTION 3: recursion
        calc(i + 1, j);  // f[i + 1][j] is computed;
        calc(i, j - 1);
        calc(i + 1, j - 1);
        
        f[i][j] = Math.max(f[i + 1][j], f[i][j - 1]);
        if (s[i] == s[j]) {
             f[i][j] = Math.max(f[i][j], f[i + 1][j - 1] + 2);
        }
    }

    public int longestPalindromeSubseq(String ss) {
        s = ss.toCharArray();
        n = s.length;
        if (n <= 1) {
            return n;
        }
    
        f = new int[n][n];
        // ATTENTION 1: initialization, clear memory
        int i, j;
        for (i = 0; i < n; ++i) {
            for (j = i; j < n; ++j) {
                f[i][j] = -1;  // f[i][j] has not been calculated yet
            }
        }
        
        calc(0, n - 1);
        return f[0][n - 1];
    }
}
```

#### > Q: Coins in a Line III 博弈型

(hard)

题意: 给定一个序列 a[0], a[1], …, a[N-1], 两个玩家 Alice 和 Bob 轮流取数, 每人每次只能取第一个数或最后一个数. 双方都用最优策略, 使得自己的数字和尽量比对手大. 问先手是否必胜?

例子: [1, 5, 233, 7] ⇒ True 因为先手取走 1, 无论后手取哪个, 先手都能取走 233.

题型判断: “每个人每次只能取第一个数或最后一个数” ⇒ 剩下的是个区间 ⇒ 区间型

如果这句话是 “每个人可以随便取走一个数” 那就不是区间型问题了.

思路 (参见 slides): 设 f[i][j] 为一方在面对 a[i..j] 这些数字时, 能得到的最大的与对手的数字差.

![](/notes/dp/media/image28.png)

(java): solution 倒 1 submission

```
    int n = A. length;
    if (n == 0) {
        return true;
    }

    int[][] f = new int[n][n];
    int i, j, len;
    // len -- 1

    for (i = 0; i < n; ++i) {
        f[i][i] = A[i];
    }
    
    for (len = 2; len <= n; ++len) {
        for (i = 0; i <= n - len; ++i) {
            j = i + len - 1;
            // A[i...j]
            f[i][j] = Math.max(A[i] - f[i + 1][j], A[j] - f[i][j - 1]);
        }
    }
    return f[0][n - 1] >= 0;
}
```

#### > Q: Sramble String

解法参考

- DFS + 剪枝: Divide & Conquer

- 动态规划: 递推 or 记忆化搜索

(java): DP 递推 solution

```
public boolean isScramble(String s, String t) {
    int m = s.length();
    int n = t.length();
    if (m != n) {
        return false;
    }
    // f[i][j][k]: 表示 s1 能否通过变换成为 t1
    // s1 为 s 从字符 i 开始的长度为 k 的子串
    // t1 为 t 从字符 j 开始的长度为 k 的子串
    boolean[][][] f = new boolean[n][n][n + 1];
    int i, j, w, len;
    
    // len = 1
    for (i = 0; i < n; ++i) {
        for (j = 0; j < n; ++j) {
            f[i][j][1] = (s.charAt(i) == t.charAt(j));
        }
    }

    for (len = 2; len <= n; ++len) {
        for (i = 0; i <= n - len; ++i) {  // s[i...i + len - 1]
            for (j = 0; j <= n - len; ++j) {  // t[j...j + len - 1]
                // break into s1 (length w) and s2 (length (len - w))
                for (w = 1; w < len; ++w) {  // note: 0 < w < len
                    // no swap: s1 --> t1, s2 --> t2
                    if (f[i][j][w] && f[i + w][j + w][len - w]) {
                        f[i][j][len] = true;
                        break;
                    }
                    // swap: s1 --> t2, s2 --> t1
                    if (f[i][j + len - w][w] && f[i + w][j][len - w]) {
                        f[i][j][len] = true;
                        break;
                    }
                }
            }
        }
    }
    return f[0][0][n];
}
```

(java): DP 记忆化搜索 solution

```python
class Solution {
    boolean[][][] f, done;  // done: denote whether f[i][j][len] computed
    int n;
    String s, t;
    
    void calc(int i, int j, int len) {
        if (done[i][j][len]) {
            return;
        }
    
        // len = 1
        if (len == 1) {
            f[i][j][len] = (s.charAt(i) == t.charAt(j));
            return;
        }

        // 枚举在何处 cut s into s1 and s2
        // break into s1 (has length w) and s2 (has length (len - w))
        for (int w = 1; w < len; ++w) {  // note: 0 < w < len
            // no swap
            // s1 --> t1, s2 --> t2
            calc(i, j, w);
            calc(i + w, j + w, len - w);
            if (f[i][j][w] && f[i + w][j + w][len - w]) {
                f[i][j][len] = true;
                break;
            }
            // swap
            calc(i, j + len - w, w);
            calc(i + w, j, len - w);
            if (f[i][j + len - w][w] && f[i + w][j][len - w]) {
                f[i][j][len] = true;
                break;
            }
        }
        done[i][j][len] = true;  // f[i][j][len] has been computed
    }
    
    public boolean isScramble(String ss, String tt) {
        int m;
        s = ss;
        t = tt;
        m = s.length();
        n = t.length();
        if (m != n) {
            return false;
        }

        int i, j, len;
        // f[i][j][k]: 表示 s1 能否通过变换成为 t1
        // s1 为 s 从字符 i 开始的长度为 k 的子串
        // t1 为 t 从字符 j 开始的长度为 k 的子串
        f = new boolean[n][n][n + 1];
        done = new boolean[n][n][n + 1];
        for (len = 1; len <= n; ++len) {
            for (i = 0; i <= n - len; ++i) {  // s[i...i + len - 1]
                for (j = 0; j <= n - len; ++j) {  // t[j...j + len - 1]
                    // f[i][j][len] not computed yet
                    done[i][j][len] = false;
                }
            }
        }  

        calc(0, 0, n);
        return f[0][0][n];
    }
}
```

> Exercises

![](/notes/dp/media/image29.png)

解析：最优的策略是先拿走 1, 得 20 分, 剩下 [4, 5, 10]; 然后拿走 5, 得 200 分, 剩下 [4, 10]; 然后拿走 4, 得 40 分, 剩下 [10]; 最终拿走 10, 得 10 分. 共计 20 + 200 + 40 + 10 = 270分.

![](/notes/dp/media/image30.png)

解析：枚举出所有的情况固然是可以的, 只不过时间复杂度变成了阶乘级别. 而动态规划可以在多项式时间复杂度内解决这个问题.

![](/notes/dp/media/image31.png)

![](/notes/dp/media/image32.png)

解析：还记得区间型动态规划的一个要点吗? "倒着". 要解决状态 f[i][j], 我们的决策其实是倒着来的, 我们要枚举的是这个区间的元素最后拿走的是哪个, 拿走这个获得的分数就是这个元素的值乘这个区间两边的元素, 也就是 arr[i-1] 和 arr[j+1], 特殊地, 如果 arr[i - 1] 或 arr[j + 1] 越界, 那应该使用 1, 如果 f[i][j] 中 i > j, 应该得到 0.

![](/notes/dp/media/image33.png)

解析：按照上面的思路，我们的初始化，就应该是拿走第i个元素的得分，就是说f[i][i]的得分，那么根据题目描述拿走一个元素的得分是左边的元素 * 该元素 * 右边的元素，所以f[i][i] = arr[i - 1] * arr[i] * arr[i + 1]。

> Assignments

#### > Q: Burst Balloons (hard)

题意: 给定 N 个气球, 每个气球上都标有一个数字 a[1] , a[2] , …, a[N]. 要求扎破所有气球. 扎破第 i 个气球可以获得 a[left] * a[i] * a[right] 枚金币.

- left 和 right 是与 i 相邻的下标

- 扎破气球i以后，left和right就变成相邻的气球

求最多获得的金币数 (设 a[0] = a[N+1] = 1).

思路: 观察最后被扎破的气球, 分为左右两个区间. f[i][j] 设为为扎破 i + 1 ~ j - 1 号气球, 最多获得的金币数. 枚举在这段 (i + 1 ~ j - 1) 中最后扎破的气球 k 是哪一个:

f[i][j] = max{i < k < j} { f[i][k] + f[k][j] + a[i] * a[k] * a[j] }

类似: LintCode 1694 Monster Hunter

# 6 双序列 DP

![](/notes/dp/media/image34.png)

### > Q: Longest Common Subsequence

(java)

![](/notes/dp/media/image35.png)

![](/notes/dp/media/image36.png)
![](/notes/dp/media/image37.png)
![](/notes/dp/media/image38.png)
打印最长公共子序列

### > Q: Interleaving String

![](/notes/dp/media/image39.png)

滚动数组优化

![](/notes/dp/media/image40.png)

### > Q: Edit Distance

![](/notes/dp/media/image41.png)

也可滚动数组优化

![](/notes/dp/media/image42.png)

解析: 正确. 这时前三个决策或许会与第四个决策一样, 但是绝对不会比第四个决策更优. 与 LCS 的情况类似, 同样是贪心.

### > Q: Regular Expression Matching

![](/notes/dp/media/image43.png)

![](/notes/dp/media/image44.png)

### > Q: Wildcard Matching

![](/notes/dp/media/image45.png)

![](/notes/dp/media/image46.png)

### > Q: Ones and Zeroes 双背包型

双背包问题: 0 和 1 分别是一个背包问题

此题可以滚动数组

![](/notes/dp/media/image47.png)

![](/notes/dp/media/image48.png)
![](/notes/dp/media/image49.png)

![](/notes/dp/media/image50.png)

> Exercises

![](/notes/dp/media/image51.png)

![](/notes/dp/media/image52.png)

解析: 但是 A 时间复杂度 O(2^N) 效率很低.

![](/notes/dp/media/image53.png)

![](/notes/dp/media/image54.png)

### > Q: Distinct Subsequence 计数型

状态: f[i][j]: B 前 j 个字符 B[0..j-1] 在 A 前 i 个字符 A[0..i-1] 中出现多少次

转移: f[i][j] = f[i-1][j-1] | A[i-1] == B[j-1] + f[i-1][j]

submission: Memory O(mn)

```python
def numDistinct(self, s: str, t: str) -> int:
    m, n = len(s), len(t)
    f = [[0] * (n + 1) for _ in range(m + 1)]
    f[0][0] = 1
    for i in range(1, m + 1):
        for j in range(n + 1):
            f[i][j] += f[i - 1][j]
            if s[i - 1] == t[j - 1] and j != 0:
                f[i][j] += f[i - 1][j - 1]
    return f[-1][-1]
```

submission: 滚动数组优化 ⇒ Memory O(n)

```python
def numDistinct(self, s: str, t: str) -> int:
    m, n = len(s), len(t)
    cur = [1] + [0] * n
    for i in range(1, m + 1):
        pre = cur[:]
        for j in range(1, n + 1):
            if s[i - 1] == t[j - 1]:
                cur[j] += pre[j - 1]
    return cur[-1]
```

# 7 难题专场

> 课前练习

![](/notes/dp/media/image55.png)

解析: 错误. 简单反例, 当 start = 3, end = 4 时, mid = 3, 如果 nums[mid] < target 则会一直 start = mid= 3 从而陷入死循环.

![](/notes/dp/media/image56.png)

![](/notes/dp/media/image57.png)

解析：

- m 次 i 到 j 的遍历，时间复杂度 O(m*(j-i))，最坏情形 j-i=n ⇒ worst Time O(m*n).

- 构造树状数组 Time O(nlogn)，每一次查询 Time O(logn) ⇒ Time O(nlogn+mlogn).

- 构造线段树 Time O(nlogn)，每一次查询 Time O(logn) ⇒ O(nlogn+mlogn).

- 求一遍前缀和 Time O(n)，查询时 Time O(1) 只需  sum[j]-sum[i-1] ⇒ Time O(n+m).

### > Q: Rogue Knight Sven

```python
def getNumberOfWays(self, N, M, limit, cost):
    if N == 0: return 0

    # F[n][m]: num of ways to: 
    # get to planet n with holding m coins now (i.e. used M - m coins)
    F = [[0] * (M + 1) for _ in range(N + 1)]
    # for m in range(m): F[0][m] = 0    
    F[0][M] = 1
    
    for n in range(1, N + 1):
        for m in range(M + 1):
            F[n][m] = 0
            if m + cost[n] > M:
                continue
            for k in range(max(n - limit, 0), n):
                # Sven jumps from planet k to i
                F[n][m] += F[k][m + cost[n]]
    return sum(F[N])
```

#### > 时间优化: 前缀和

```python
def getNumberOfWays(self, N, M, limit, cost):
    if N == 0:
        return 0
    
    # F[n][m]: num of ways to: 
    # get to planet n with holding m coins now (i.e. used M-m coins)
    F = [[0] * (M + 1) for _ in range(N + 1)]
    summ = [[0] * (M + 1) for _ in range(N + 1)]
    
    F[0][M] = 1
    summ[0][M] = 1
    
    for n in range(1, N + 1):
        for m in range(M + 1):
            # Sven is at planet i w/ j coins, AFTER paying cost[m] coins
            F[n][m] = 0
            summ[n][m] = summ[n - 1][m]
            if m + cost[n] > M:
                continue
            
            F[n][m] = summ[n - 1][m + cost[n]]
            if n - limit - 1 >= 0:
                F[n][m] -= summ[n - limit - 1][m + cost[n]]
    
            summ[n][m] += F[n][m]
            
    return sum(F[N])
```

![](/notes/dp/media/image58.png)

### > Q: K-Sum

与背包问题的不同: 要求正好 k 个数

![](/notes/dp/media/image59.png)

![](/notes/dp/media/image60.png)
滚动数组优化

![](/notes/dp/media/image61.png)

![](/notes/dp/media/image62.png)
### > Q: Longest Increasing Subsequence

![](/notes/dp/media/image63.png)
![](/notes/dp/media/image64.png)

![](/notes/dp/media/image65.png)
> Exercises

解析: 5. 我们选择的信封为 [5,7]->[8,9]->[13,11]->[14,17]->[18,19].

![](/notes/dp/media/image66.png)

解析: 我们只需对其中一维进行排序, 这样另外一维就可以转换成为一个最长上升子序列.

![](/notes/dp/media/image67.png)

解析: 首先对 w 从小到大. 然后因为要 w, h都大于前一个信封的 w, h 故 h 应从大到小. 这样我们只需要对 h 求一次最长上升子序列就可以得到答案了. 同理w, h 排序对调也可.

### > Q: Surplus Value Backpack

剩余价值背包

![](/notes/dp/media/image68.png)

![](/notes/dp/media/image69.png)

记忆化搜索

![](/notes/dp/media/image70.png)

![](/notes/dp/media/image71.png)

![](/notes/dp/media/image72.png)

![](/notes/dp/media/image73.png)

![](/notes/dp/media/image74.png)

### > Q: Maximal Square

![](/notes/dp/media/image75.png)

![](/notes/dp/media/image76.png)
> Exercises

解析: 如果每个 * 号各表示 1 个字符，那么 ** 就有 9 * 9 = 81 种可能性. 如果 ** 整体表示一个字符, 那么就只有 11-26 (20 不算) 这里的 15 个数字 ⇒ 96 = 81 + 15.

![](/notes/dp/media/image77.png)

解析: 只考虑一个字符时, 0 无法解码成字母, 1-9 应该是等同的都是转化成为 1 个字母, * 号是 1-9 的任意一个故有 9 种可能性.

![](/notes/dp/media/image78.png)

解析: 2* 只考虑两个数字解码成字母只有 21, 22, 23, 24, 25, 26; 27-99 都不能转换成为字母.

![](/notes/dp/media/image79.png)

解析: 

- 不同位置相乘. 比如第一个字母有 9 种可能性, 第二个字母有 6 种可能性

⇒ 总共 6 * 9 = 54 种.

- 相同位置相加. 这个位置单独一个位置只考虑一个字符有 9, 考虑两个字符有 6 种

⇒ 总共 9 + 6 = 15 种.

- 所以说 cnt1 和 cnt2 的情况要相加; 而 f[i-1] 和 cnt1, cn2 应该相乘.

> Assignment

### > Q: Decode Ways II

# 8 Ladder

![](/notes/dp/media/image80.png)

![](/notes/dp/media/image81.png)

![](/notes/dp/media/image82.png)

![](/notes/dp/media/image83.png)

![](/notes/dp/media/image84.png)
![](/notes/dp/media/image85.png)

![](/notes/dp/media/image86.png)
