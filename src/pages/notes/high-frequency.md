---
layout: ../../layouts/Layout.astro
title: Leetcode 高频题
---

# 面试高频题

## 各大厂高频题

@2020.03.08

Facebook onsite ⾼频题

> Q: Number of Ways to Stay in the Same Place After Some Steps

解法 1: DFS 暴力求解是 O(3^n) 指数级复杂度 BUT 远远不如 DP 高效 ⇒ TLE | submission

```python
def numWays(self, steps, arrLen):
    self.arrlen = arrLen
    return self.dfs(steps, 0)
def dfs(self, steps, cur_pos):
    if cur_pos < 0 or cur_pos >= self.arrlen: return 0
    if steps == 0: return cur_pos == 0
    if cur_pos > steps: return 0   # ATTENTION: this is necessary
    if cur_pos == steps: return 1  # Note: optional, but improves a lot
    return \
        self.dfs(steps - 1, cur_pos - 1) + \
        self.dfs(steps - 1, cur_pos + 1) + \
        self.dfs(steps - 1, cur_pos)
```

解法 2: DP O(n^2): w/o 滚动数组 (submision) | w/ 滚动数组 (submission)

```python
def numWays(self, steps, arrlen):
    # dp[i][j]: reach index (j - 1) by exactly (i + 1) steps
    dp = [[0] * (min(steps, arrlen) + 2) for i in range(steps)]
    dp[0][1] = 1
    dp[0][2] = 1
    for i in range(1, steps):
        for j in range(1, min(arrlen, steps - i) + 1):
            dp[i][j] = dp[i - 1][j - 1] + dp[i - 1][j + 1] + dp[i-1][j]
    return dp[steps - 1][1] % (10**9 + 7)
```

Microsoft 电⾯⾼频题

> Q: Merge Intervals

```python
def merge(self, intervals):
    intervals = sorted(intervals, key=lambda x: x.start)  # 注意排序方法
    result = []
    for interval in intervals:
        if len(result) == 0 or result[-1].end < interval.start:
            result.append(interval)
        else:
            result[-1].end = max(interval.end, result[-1].end)
    return result
```

> Q: Max Increase to Keep City Skyline | submission

> Q: Meeting Rooms <==> Merge Intervals

#### > Q: Meeting Rooms II: 扫描线法

```python
def minMeetingRooms(self, intervals):
    scan = defaultdict(lambda: 0)
    for interval in intervals:
        scan[interval.start] += 1
        scan[interval.end] -= 1
    
    ongoing = 0
    res = 0
    for key in sorted(scan.keys()):
        ongoing += scan[key]
        res = max(res, ongoing)
    return res
```

> Q: Number of Airplanes in the Sky <==> Meeting Rooms II

扫描线法: 定义计数器 C = 0

– 遇到起飞事件: C += 1

– 遇到降落事件: C -= 1

⇒ C 的最大值即为答案

> Q: Smallest Rotation with Highest Score (hard) (ctrl+f) 扫描线

Amazon OA ⾼频题

#### > Q: Shortest path to the destination: 分层 BFS **

等价题目 Shortest Path in Binary Matrix

思路:

```python
# 分层 BFS: 
# 1. 定义队列
# 2. 把起点放进去
# 3. 定义 visited 表示每个点是都被访问过
# 4. 记录起点已经被访问过
#
# 开始 BFS:
# 当前队列为空
#   把当前队列中的元素弹出
#     判断是否已经到达终点, if ture:
#       返回移走的步数
#     判段周围元素是否可以加入队列, if true:
#       加入到队列
#       记录该点已经被访问过
# 走的步数 += 1

class MapType:
    ROAD = 0
    WALL = 1
    DEST = 2  # Destination

class Solution:
    def shortestPath(self, targetMap):
        if len(targetMap) == 0 or len(targetMap[0]) == 0: return -1
        m, n = len(targetMap), len(targetMap[0])
        start = (0, 0)
        queue = collections.deque()
        queue.append(start)
        visited = set()
        visited.add(start)
        
        def isValid(x, y):
            if not (0 <= x < m and 0 <= y < n):
                return False
            if targetMap[x][y] == MapType.WALL:
                return False
            # When there's a dead cycle: [[0,0,1,0],[0,1,2,0],[1,1,0,1]]
            if (x, y) in visited:
                return False
            return True
        
        steps = 0
        DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        while queue:
            k = len(queue)
            for _ in range(k):
                x, y = queue.popleft()
                if targetMap[x][y] == MapType.DEST:
                    return steps
                        
                for delta_x, delta_y in DIRECTIONS:
                    x_ = x + delta_x
                    y_ = y + delta_y
                    if isValid(x_, y_):
                        if targetMap[x_][y_] == MapType.DEST:
                            return steps + 1
                        queue.append((x_, y_))
                        visited.add((x_, y_))
            steps += 1
        return -1
```

此题总结

code:

- 常数的写法

- 方向的写法 DIRECTIONS

- 用 isValid 函数 check 点是否合法

algorithm:

- BFS 时间复杂度 O(V + E): V 是节点个数, E 是边的个数

Google OA ⾼频题

#### > Q: Pen Box: 双指针

notes: jiuzhang

可选方法: Presum / Sliding Window / DFS

暴力做法: 找出所有有效的区间, 判断这些区间两两是否重合. 如果不重合与 ans 比较谁大.

⇒ O(n^2) 个区间 ⇒ 两两比较则 O(n^4) 复杂度 ⇒ 不可取

用 Sliding Window 找有效区间

能否找到⼀个最短的有效区间 ? 

如何扩展到两个区间 ?

相关题目: Two Sum (Hash Map) + Best Time to Buy and Sell Stock III (DP / 枚举隔板位置)

# 枚举隔板的位置
# lmin[i]: 前 i 个盒子 (include) 中的最小有效区间长度. 不需 lmin[n]
# rmin[i]: 第 i 个盒子 (include) 后的最小有效区间长度. 不需 rmin[0]
# res = min(res, lmin[i] + rmin[i + 1])
# 如何求左半部分的最小值 ? 双指针

(submission)

```python
def minimumBoxes(self, boxes, target):
    n = len(boxes)
    if n < 2: return -1
    if target == 0: return 0
    
    # lmin[i]: 前 i 个盒子 (include) 中的最小有效区间长度. 不需 lmin[n]
    lmin = [float('inf')] * n
    left = 0
    cur_sum = 0
    for right in range(n - 1):
        cur_sum += boxes[right]
        while left < right and cur_sum > target:
            cur_sum -= boxes[left]
            left += 1
        
        if right == 0:
            if cur_sum == target:
                lmin[right] = 1
            continue
        
        if cur_sum < target:
            lmin[right] = lmin[right - 1]
        
        if cur_sum == target:
            while boxes[left] == 0:
                left += 1
            lmin[right] = min(lmin[right - 1], right - left + 1)

    # rmin[i]: 第 i 个盒子 (include) 后的最小有效区间长度. 不需 rmin[0]
    rmin = [float('inf')] * n
    right = n - 1
    cur_sum = 0
    for left in range(n - 1, 0, -1):
        cur_sum += boxes[left]
        while left < right and cur_sum > target:
            cur_sum -= boxes[right]
            right -= 1
        
        if left == n - 1:
            if cur_sum == target:
                lmin[left] = 1
            continue
        
        if cur_sum < target:
            rmin[left] = rmin[left + 1]
        
        if cur_sum == target:
            while boxes[right] == 0:
                right -= 1
            rmin[left] = min(rmin[left + 1], right - left + 1)

    # res = min(ans, lmin[i] + rmin[i + 1])
    res = float('inf')
    for i in range(n - 1):
        res = min(res, lmin[i] + rmin[i + 1])
        
    return res if res < float('inf') else -1
```

## 基础算法和数据结构 I

减少时间复杂度技巧

- LintCode 645. 识别名⼈ ⇒ 减少冗余操作

- LintCode 654. 稀疏矩阵乘法 ⇒ 改变数据存储⽅式

- LintCode 140. 快速幂 ⇒ 合并重复操作

常考高精度问题

- LintCode 904. Plus one

### 减少时间复杂度

#### 1. 减少冗余操作

Facebook / Microsoft ⾼频题

##### > Q: Find the Celebrity <==> Find the Town Judge

思路 1 (浪费了部分问询信息): submission 倒 5

# 对于⼀个⼈ i 枚举其他⼈ j:
#   若 i knows j 或 j not knows i: 则 i 必然不是名⼈, break
#   否则继续⽐较

⇒ 问题: 那我们在这个过程中能否也判断出 j 的性质 ?

⇒ 思路 2:

在⼀次询问 knows(a,b) 中：思路 1 只利用了答案为 True 的情况。如果为 False 呢 ?

```python
knows(a, b) == True  : ==> a 不可能是名⼈
knows(a, b) == False : ==> b 不可能是名⼈
```

⇒ 每次询问我们可以确定⼀个⼈不是名⼈

⇒ 做 n - 1 次询问后只有 1 个⼈⽆法确定是否是名⼈

```python
def findCelebrity(self, n):
    cand = 0  # candidate that might be celebrity
    # 两两判断 n - 1 次
    for i in range(1, n):
        if Celebrity.knows(cand, i):
            # candidate knows i ==> i might be celebrity
            # otherwise, candidate might still be celebrity
            cand = i

    # Check if the final candicate is the celebrity
    for i in range(n):
        if cand == i:
            continue
        if Celebrity.knows(cand, i) or not Celebrity.knows(i, cand): 
            return -1
    return cand
```

相关题目: Alien dictionary (ctrl+f)

#### 2. 改变数据存储⽅式

Facebook 电⾯⾼频题

##### > Q: Sparse Matrix Multiplication

注释: 非稀疏矩阵的暴力做法 O(n^3) | 算法导论里的优化方式可以达到 O(n^(8/3))

```python
def multiply(self, A, B):
    # A: n x m
    # B: m x k
    # C: n x k ⇐ C = A * B
    n = len(A) 
    m = len(A[0])
    k = len(B[0])
    
    # n 行, 每行存 (index, value): O(N^2) time
    # Here, 常数级别的非零元素 ==> O(1) memory
    row_vector = [
            [
                (j, A[i][j])
                for j in range(m)
                if A[i][j] != 0 
            ]
            for i in range(n)
        ]

    # 同理处理 B 的列向量 O(N^2) time
    col_vector = [
            [
                (i, B[i][j])
                for i in range(m)
                if B[i][j] != 0
            ]
            for j in range(k)
        ]
    
    # O(N^2)
    C = [
        [
            self.multi(row, col)
            for col in col_vector
        ]    
        for row in row_vector
    ]
    
    return C

# O(1)
def multi(self, row, col):
    i, j = 0, 0  # two pointers
    ans = 0 # C[i][j]
        
    while i < len(row) and j < len(col):
        index1, val1 = row[i]
        index2, val2 = col[j]
        if index1 < index2:
            i += 1 
        elif index1 > index2:
            j += 1 
        else:
            ans += val1 * val2
            i += 1 
            j += 1 

    return ans
```

> Q: Build Post Office II: 根据空地和房⼦的数量选择算法 (ctrl+f)

#### 3. 合并重复操作

合并重复操作以降低问题规模. e.g.: n → n / 2 → n / 4 → n / 8 → n / 16 ⇒  O(logn) 

##### > Q: Fast Power

如何实现 O(logn) ? ⇒ 利用平⽅关系 xn = xn/2 * xn/2  ⇒ 递归每次减少⼀半问题规模

如何支持负数幂次 ? ⇒ x = 1 / x, n = - n | Pow(x, n)

```
# a ^ n % b
# e.g.: n = 5 = (101)2 ⇒ a^5 % b = a^(101)2 % b = [a^(100)2 * a&(1)2] % b
# ⇒ 对 n 做二进制转换后每遇到 1 时乘以对应的 a 的幂次
# Note 1: 需要 a^1, a^(10)2, a^(100)2 ... 也就是 a^1, a^2, a^4 ...
#         递归 a = a * a 即可依次计算 a 的如上所有 2 的指数级幂次
# Note 2: 随时可 % b 避免 overflow ⇐  ((m % b) * (n % b)) % b = (mn % b)
```

```python
def fastPower(self, a, b, n):
    ans = 1
    while n > 0:
        if n % 2 == 1:
            ans = (ans * a) % b  # 每遇到 1 时乘以对应的 a 的幂次
        a = a * a % b  # 递归依次计算 a 的所有 2 的指数级幂次
        n = n // 2
    return ans % b
```

该方法同理可做矩阵快速乘法:

> Q: Fabonacci Number II | solution by Matrix Fast Power | solution by jiuzhang

### 常考高精度问题

#### 链表问题

- 高精度: 模拟两个很大很大的数相加 / 字符串带小数问题

- 快慢指针: 判断链表是否有环

- reverse / delete node / add node

链表求和

- 倒序存储数字: Add Two Number | submission

- 顺序存储数字: Add Two Number II

相关问题

##### > Q: Add Strings w/ Negative Values

Follow up: 处理负数 submission

```python
def addStrings(self, num1, num2, len1, len2) -> str:
    res = ""
    carry = 0
    for i in range(1, max(len1, len2) + 1):
        digit = int(num1[-i] if i <= len1 else 0) + \
                int(num2[-i] if i <= len2 else 0) + carry
        carry = digit // 10
        res = str(digit % 10) + res

    # ATTENTION: Remember the last carry
    if carry != 0:
        res = str(carry) + res
    return res
```

> Q: Subtract Strings

```python
def subStrings(self, num1, num2, len1, len2) -> str:
    res, carry, prev_borrow = "", 0, 0
    for i in range(1, max(len1, len2) + 1):
        dig1 = num1[-i] if i <= len1 else 0
        dig2 = num2[-i] if i <= len2 else 0
        # Note: when to borrow? Need to consider prev_borrow
        curr_borrow = 1 if int(dig1) < (int(dig2) + prev_borrow) else 0
        digit = int(dig1) - int(dig2) + curr_borrow * 10 - prev_borrow
        prev_borrow = curr_borrow
        res = str(digit) + res

    if prev_borrow != 0:
        res = str(int(res[0]) - 10) + res[1:]
    while res[0] == "0": res = res[1:]
    return res
```

##### > Q: Multiply Strings

```python
def multiply(self, num1: str, num2: str) -> str:
    product = [0] * (len(num1) + len(num2))
    pos = len(product) - 1
    for n1 in reversed(num1):
        tempPos = pos
        for n2 in reversed(num2):
            product[tempPos] += int(n1) * int(n2)
            product[tempPos - 1] += product[tempPos] // 10
            product[tempPos] %= 10
            tempPos -= 1
        pos -= 1

    pt = 0
    while pt < len(product) - 1 and product[pt] == 0:
        pt += 1
    return ''.join(map(str, product[pt:]))
```

##### > Q: Plus One Linked List

explanation by leetcode

```python
def plusOne(self, head):
    sentinel = ListNode(0)
    sentinel.next = head

    node = sentinel
    if node.val != 9:
        not_nine = node
    
    while node.next:
        node = node.next
        if node.val != 9:
            not_nine = node
    
    not_nine.val += 1
    not_nine = not_nine.next
    while not_nine:
        not_nine.val = 0
        not_nine = not_nine.next
    return sentinel if sentinel.val == 1 else sentinel.next
```

#### 除法带余数

(非高频)

> Q: Fraction to Recurring Decimal | solution

> Q: Divide Two Integers

> Q: Wood Cut / Cut Ribbon @FB @Google | solution 二分法 

## 基础算法和数据结构 II

### 前缀和 Prefix Sum

@2020.03.14

> Q: Matrix Differential (ctrl+f)

> Q: Best Time to Buy and Sell Stock (ctrl+f in DP)

前缀最小值, 枚举卖出日期

后缀最大值, 枚举买入日期

Facebook ⾼频题

#### > Q: Product of Array Except Self

数组除了⾃身的乘积 

思路 1: 求出整个数组的积, 然后分别除以这个数

思路 2: 前缀和数组. 用一个数组记录前缀积 nums[0] * nums[1] *...*nums[i-1], 再记录后缀积 nums[i+1] * ... * nums[n-1]. 将这两个数相乘即可获得 res[i].

思路 2: naive solution

```python
# 1. 定义两个数组表示前缀积和后缀积
# 2. for 循环每个位置, 把前半部分和后半部分乘起来
 
def productExceptSelf(self, nums):
    n = len(nums)
    if n == 0: return []

    prefix = [nums[0]] + [0] * (n - 1)  # 前缀积
    for i in range(1, n):
        prefix[i] = prefix[i - 1] * nums[i]

    suffix = [0] * (n - 1) + [nums[-1]]  # 后缀积
    for i in range(n - 2, -1, -1):
        suffix[i] = suffix[i + 1] * nums[i]
   
    output = [1] * n
    for i in range(n):
        if i != 0:
            output[i] *= prefix[i - 1]
        if i != n - 1:
            output[i] *= suffix[i + 1]
    return output
```

思路 2: 优化 Meomry 到 O(1) (Note: output 不算算法的 memroy)

```python
# 1. 初始化 output as ones
# 2. 从前往后 for, output[i] *= prefix, prefix: 前 i - 1 个元素的乘积
# 2. 从前往后 for, output[i] *= suffix, suffix: 第 i - 1 后元素的乘积

def productExceptSelf(self, nums):
    n = len(nums)
    if n == 0: 
        return []
    output = [1] * n
    
    # 从前往后处理前缀积
    prefix = 1
    for i in range(n):  
        output[i] *= prefix
        prefix *= nums[i]

    # 从后往前处理后缀积
    suffix = 1
    for i in range(n - 1, -1, -1):  
        output[i] *= suffix
        suffix *= nums[i]
    return output
```

思路 2: 上述 O(1) 解法的进一步写法优化

```python
def productExceptSelf(self, nums):
    n = len(nums)
    if n == 0: return []
    
    output = [1] * n
    prefix = 1
    suffix = 1
    for i in range(n):  
        output[i] *= prefix
        prefix *= nums[i]
        output[n - i - 1] *= suffix
        suffix *= nums[n - i - 1]
    return output
```

### 哈希表 Hash Table

@2020.03.14

Facebook ⾼频题

#### > Q: Subarray Sum Equals K II

长度最小的和为 K 的子数组

思路 0: brute-force O(n^3): O(n^2) 个 subarry 各需要 O(n) 求和 ⇒ TLE

思路 1: 前缀和优化 O(n^2) = O(n^2) * O(1) ⇒ TLE

```python
def subarraySumEqualsKII(self, nums, k):
    n = len(nums)
    if n == 0: return -1

    for i in range(1, n):
        nums[i] += nums[i - 1]  # nums is now prefix sum
        
    res = sys.maxsize
    for i in range(n):
        for j in range(i, n):
            if nums[j] - (nums[i - 1] if i > 0 else 0) == k:
                res = min(res, j - i + 1)
    return res
```

思路 2: Hash Table 优化

```python
def subarraySumEqualsKII(self, nums, k):
    n = len(nums)
    if n == 0: return -1

    for i in range(1, n):
        nums[i] += nums[i - 1]  # nums is now prefix sum
        
    hashmap = {0: -1}  # Case: [1 2], 3
    res = sys.maxsize
    for i in range(n):
        offset = nums[i] - k
        if offset in hashmap:
            res = min(res, i - hashmap[offset])
        hashmap[nums[i]] = i
    return res
```

Related:

Subarray Sum Equals K  ⇒ Follow up: Number of Submatrices That Sum to Target (ctrl+f)

Roblox 高频题

#### > Q: Find Words

解法 0: 联系 Merge two sorted arrays 通过双指针判断每个单词是否是 str 的⼦序列

⇒ check 每个单词的复杂度是 O(n)

解法 1: Hash Table

str="bcokdok"

dict=[“book","code","tag"]

‘b’ : {0}

‘c’ : {1}

‘o’ : {2,7}

‘k’ : {3,10} 

‘d’ : {4}

每次找到当前 letter 的位置 i 后, 只需要 (二分查找) check 下一个 letter 是否存在 i 之后的位置, 把指针移动到这个位置并继续 check 即可.

e.g.: “book”: “b”, index 0 → “o”, find 2 > 0 → “o”, find 7 > 2 → “k”, find 10 > 7 ⇒ True

⇒ check 每个单词的复杂度是 O(logn)

进一步优化:

上述解法 1 的复杂度为何还是有 logn 项?

因为找下一个位置时需要在⼀个许多数值的 list ⾥找最接近某个数的数字 ⇒ logn 二分查找

我们真的⽤得到这么多数字吗? 

e.g.: 若当前位置为 3, 下⼀个字⺟所在的位置有 [0,5,8] ⇒ 其实只需记录最近的单词位置即 5

解法 2:

预处理出每个单词的后⼀个任意单词的位置, e.g.:

next_pos[1][o] = 2

next_pos[1][k] = 3

next_pos[1][d] = 4

从后往前循环以预处理生成 next_pos. 大小是 len(str) * 26 

⇒ check 每个单词的复杂度是 O(1)

解法 1:

```python
class Solution:
    def findWords(self, str, dict):
        # Create a hash table of 26 letters, 
        # where each element stores indices of that letter in str.
        indices = {}
        for letter in list(map(chr, range(97, 123))):
            indices[letter] = []
        for i, letter in enumerate(str):
            indices[letter].append(i)
        
        # Traverse each word to find if it exists in str
        res = []
        for word in dict:
            if self.checkWord(indices, word):
                res.append(word)
        return res
    
    def checkWord(self, indices, word):
        if len(word) == 0:
            return False
        
        index = -1
        for letter in word:
            if len(indices[letter]) == 0:
                return False
            if index == -1:
                index = indices[letter][0]
            else:
                found, index = self.findNextIdex(letter, index, indices)
                if not found:
                    return False
        return True
    
    def findNextIdex(self, letter, index, indices):
        for i in indices[letter]:
            if i > index:
                index = i
                return True, index
        return False, -1
```

## 高效 BFS

@2020.03.15

BFS 如何存储 visited 信息?

A. 二维数组 / List

B. Hash Set

C. Hash Map: Map(point → dist): e.g.: submission 倒 1

D. 改变 grid 的值 ⇐ 这样代码风格不好

方法优劣排序: C > B > A > D

运行时间长短: D < A < B < C

### 基础典型 BFS 拓展

#### > Q: Knight Shortest Path

没有障碍物 / 上下左右都可走

Question: Minimum Knight Moves

Given an infinite chessboard, find min no. of steps for a knight to reach from origin to (x, y).

Follow-up:

A list of forbidden coordinates are introduced where knight can’t reach. Handle this in your code. Make sure the infinite loop is handled since the board is infinite.

Solutions: DP \ O(1) math \ O(n) BFS only two directions at a time

#### > Q: Knight Shortest Path II

有障碍物 / 只能从左到右走

##### Follow up 1: 打印路径

Note 1: 只需要一个 dictionary 记住每个 point 的 last_point 即可

Note 2: 路径输出要翻转顺序 path.reverse()

```python
DIRECTIONS = [(2, 1), (-2, 1), (1, 2), (-1, 2)]

class Solution:
    def shortestPath2(self, grid):
        n = len(grid)
        if n == 0: return -1
        m = len(grid[0])
        if m == 0: return -1
            
        queue = collections.deque()
        dist = {}
        last_point = {}
        
        queue.append((0, 0))
        dist[(0, 0)] = 0
        last_point = {(0, 0): (-1, -1)}  # Note 1
        while queue:
            x, y = queue.popleft()
            for dx, dy in DIRECTIONS:
                x_ = x + dx
                y_ = y + dy
                if self.isvalid(x_, y_, grid, dist):
                    queue.append((x_, y_))
                    dist[(x_, y_)] = dist[(x, y)] + 1
                    last_point[(x_, y_)] = (x, y)
            # if 有传送门: check 另一端点是否 self.isvalid()

        if (n - 1, m - 1) in dist:
            path = self.find_path(grid, n, m, last_point)
            print(path)
            return dist[(n - 1, m - 1)]
        return -1
    
    def isvalid(self, x, y, grid, dist):
        if not (0 <= x < len(grid) and 0 <= y < len(grid[0])):
            return False
        if grid[x][y] == 1 or (x, y) in dist
            return False
        return True
        
    def find_path(self, grid, n, m, last_point):
        curr_point = (n - 1, m - 1)
        path = []
        while curr_point in last_point:
            path.append(curr_point)
            curr_point = last_point[curr_point]
        path.reverse()  # Note 2
        return path
```

##### Follow up 2: 传送门

传送门类: 需要 check 跳转 / 传送到的点是否 valid

具体参考: Modern Ludo I (ctrl+f)

##### Follow up 3: 字典序最⼩的最短路径

字典序最小: 两个 path 逐个 point 对比, 直到有不同的 point, 其中值小的在前.

e.g.: 6 x 5 的 gird 中:

[(0, 0), (2, 1), (0, 2), (2, 3), (4, 4)]

比如下 path 字典序更小 (排在更前)

[(0, 0), (2, 1), (4, 2), (2, 3), (4, 4)]

```python
DIRECTIONS = [(2, 1), (-2, 1), (1, 2), (-1, 2)]
import heapq

class Solution:
    def shortestPath2(self, grid):
        n = len(grid)
        if n == 0: return -1
        m = len(grid[0])
        if m == 0: return -1
            
        queue = []
        dist = {}
        last_point = {}
        
        heapq.heappush(queue, (0, 0))
        dist[(0, 0)] = 0
        last_point = {(0, 0): (-1, -1)}
        while queue:
            x, y = heapq.heappop(queue)
            for dx, dy in DIRECTIONS:
                x_ = x + dx
                y_ = y + dy
                if self.isvalid(x_, y_, grid, dist, dist[(x, y)]):
                    heapq.heappush(queue, (x_, y_))
                    dist[(x_, y_)] = dist[(x, y)] + 1
                    last_point[(x_, y_)] = (x, y)

        if (n - 1, m - 1) in dist:
            path = self.find_path(grid, n, m, last_point)
            print(path)
            return dist[(n - 1, m - 1)]
        return -1
    
    def isvalid(self, x, y, grid, dist, last_dist):
        if not (0 <= x < len(grid) and 0 <= y < len(grid[0])):
            return False
        if grid[x][y] == 1:
            return False
        if (x, y) in dist and dist[(x, y)] <= last_dist + 1:
            return False
        return True
    
    def find_path(self, grid, n, m, last_point):
        curr_point = (n - 1, m - 1)
        path = []
        while curr_point in last_point:
            path.append(curr_point)
            curr_point = last_point[curr_point]
        path.reverse()
        return path
```

##### Follow up 4: 双向 BFS *

```python
# Bi-directional BFS
DIRECTIONS = [(2, 1), (-2, 1), (1, 2), (-1, 2)]
class Solution:
    def shortestPath2(self, grid):
        if grid == [[]] or len(grid) == 0:
            return -1
        m, n = len(grid), len(grid[0])

        if grid[0][0] or grid[m - 1][n - 1]:
            return -1    
        if m == 1 and n == 1:
            return 0

        queue_A = collections.deque()
        visited_A = [[False for i in range(n)] for j in range(m)]
        queue_A.append([0,0])
        visited_A[0][0] = True

        queue_B = collections.deque()
        visited_B = [[False for i in range(n)] for j in range(m)]
        queue_B.append([m - 1, n - 1])
        visited_B[m - 1][n - 1] = True

        queue = collections.deque()
        res = 0
        sign = 0  # flag deciding which BFS queue to use
        while queue_A and queue_B:
            # expand the shorter queue
            if len(queue_A) <= len(queue_B):
                queue = queue_A
                visited_curr = visited_A
                visited_other = visited_B
                sign = 1
            else : 
                queue = queue_B
                visited_curr = visited_B
                visited_other = visited_A
                sign = -1
            
            res += 1
            for _ in range(len(queue)):
                x, y = queue.popleft()
                for dx, dy in DIRECTIONS:
                    newx = x + sign * dx
                    newy = y + sign * dy
                    if self.isValid(newx, m, newy, n, grid):
                        if visited_other[newx][newy]:
                            return res
                      if not visited_curr[newx][newy]:
                            queue.append([newx, newy])
                            visited_curr[newx][newy] = True
        return -1
        
    def isValid(self, x, m, y, n, grid):
        if x < 0 or x >= m or y < 0 or y >= n:
            return False
        if grid[x][y] == 1:
            return False
        return True
```

思考: 双向 BFS 在这道题中是否提速 / 减少时间复杂度？

在本题中是求最短路径, visited 过的不会再次 visit, 复杂度本身就是 O(n). 

⇒ 双向 BFS 没有什么提高

思考: 什么时候双向 BFS 有用?

e.g.: 在如下格子中求左上角到右下角经过的 path 上格子值和为 target 的所有 paths

常规 BFS ⇒ O(2^{2n}), 因为如图粉色 zigzag 需要 2n 步才可达右下角

双向 BFS ⇒ O(2^n) * 2, 完全降到原来的 sqrt() ⇒ 显著提速

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

#### > Q: Snakes and Ladders

有传送门

#### > Q: Walls and Gates *

正常 BFS: submission 倒 1

##### 反向思路 BFS

```python
def wallsAndGates(self, rooms):
    INF = 2147483647
    if not rooms or not rooms[0]:
        return
    n, m = len(rooms), len(rooms[0])
    toFill = [
        (i, j) for i in range(n) for j in range(m) if rooms[i][j]==INF]
    steps = 0
    while toFill:
        notFilled = []
        for i, j in toFill:
            for di, dj in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
                r = i + di
                c = j + dj
                if 0 <= r < n and 0 <= c < m and rooms[r][c] == steps:
                    rooms[i][j] = 1 + steps
                    break
            if rooms[i][j] == INF:
                notFilled.append((i, j))
        if len(notFilled) == len(toFill):
            return
        toFill = notFilled
        steps += 1
```

### 隐式图 BFS

#### > Q: Word Ladder

(ctrl+f)

#### > Q: Sliding Puzzle II

时间复杂度 ? 3 ^ (移动总步数)

如何估计 ? 状态数量是 9! ⇒ 可以用作估计状态 upper bound

```python
DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

class Solution:
    def minMoveStep(self, init_state, final_state):
        st, ed = "", ""
        visited, queue = set(), []
        for i in range(3):
            for j in range(3):
                st += str(init_state[i][j])
                ed += str(final_state[i][j])
        queue.append(st)
        visited.add(st)
        steps = 0
        while queue:
            siz = len(queue)
            for i in range(siz):
                curr = queue.pop(0)
                if curr == ed:
                    return steps
                pos = curr.find('0')
                x, y = pos // 3, pos % 3
                for dx, dy in DIRECTIONS:
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < 3 and 0 <= ny < 3):
                        continue
                    newpos = 3 * nx + ny  # 与 0 要交换的 grid 位置
                    a, b = max(newpos, pos), min(newpos, pos)
                    new = curr[0: b] + curr[a] + curr[b + 1: a] + \
                          curr[b] + curr[a + 1:]
                    if not new in visited:
                        queue.append(new)
                        visited.add(new)
            steps += 1
        return -1
```

### 一维 BFS

#### > Q: Modern Ludo I *

传送门问题 & 一维 1D BFS & Note: DP 做更简单

Note 1: 存在连续 connections, e.g: connections = [ [3, 5], [5, 7], [7, 9] ]

Note 2: 可能一个点有多个 connections, e.g: connections = [ [3, 5], [3, 7], [3, 9] ]

Note 3: 可能一个 connection 不如另一个 connection 快, e.g.:

15
[[7, 9], [8, 14]]

```python
def modernLudo(self, length, connections):
    queue = collections.deque([1])
    dist = {1: 0}

    transport = {}
    for u, v in connections:
        transport.setdefault(u, set()).add(v)  # Note 2
    
    while queue:
        x = queue.popleft()
        # check connections & Note 1
        if x in transport:
            for next_trans in transport[x]:
                # # Note 3: no need if connection is longer
                if next_trans in dist and dist[next_trans] < dist[x]:
                    continue                 
                queue.append(next_trans)
                dist[next_trans] = dist[x]
        
        for dx in range(1, 7):
            newx = x + dx
            if newx <= length and not newx in dist:
                queue.append(newx)
                dist[newx] = dist[x] + 1

    return dist[length]
```

> Q: Serialize and Deserialize Binary Tree (ctrl+f)

一维 BFS 做 serialize & 用快慢两个指针做 deserialize: solution | Recusion submission

## 树与分治法

### 构建 Binary Search Tree

```python
class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None


def createBST(nums):
    root = None
    for num in nums:
        root = insert(root, num)
    return root


def insert(root, x):
    if not root:
        return TreeNode(x)
    if x == root.val:
        raise ValueError("Value {} already exists in the BST".format(x))
    if x < root.val:
        root.left = insert(root.left, x)
    else:
        root.right = insert(root.right, x)
    return root


def inorder(root):
    if not root: 
        return
    inorder(root.left)
    print(root.val)
    inorder(root.right)


if __name__ == '__main__':
    nums = [1, 2, 3, 4, 5, 6, 7]
    inorder(createBST(nums))
```

### 二叉树分治法主要思想

主要思想: 将问题分解成左右两个子树上的 sub-problem @source

![](/notes/high-frequency/media/image1.png)
![](/notes/high-frequency/media/image2.png)

简单分治法题目 Easy Level / Templates

#### Tempate 1: one root

```python
def solve(root):
    if not root: return ...
    if f(root): return ...
    l = solve(root.left)
    r = solve(root.right)
    return g(root, l, r)
```

> Q: Maximum Depth of Binary Tree

```python
def maxDepth(self, root):
    if root == None: return 0
    l = self.maxDepth(root.left)
    r = self.maxDepth(root.right)
    return 1 + max(l, r)
```

> Q: Path Sum

```python
def hasPathSum(self, root: TreeNode, k: int) -> bool:
    if not root: return False
    if not (root.left or root.right): return root.val == k
    l = self.hasPathSum(root.left, k - root.val)
    r = self.hasPathSum(root.right, k - root.val)
    return l or r
```

> Q: Minimum Depth of Binary Tree (ctrl+f)

```python
def minDepth(self, root: TreeNode) -> int:
    if not root: return 0
    if not root.left and not root.right: return 1
    l = self.minDepth(root.left
    r = self.minDepth(root.right)
    if root.left == None: return r + 1
    if root.right == None: return l + 1
    return min(l, r) + 1
```

#### Tempate 2: two roots

```python
def solve(p, q):
    if not p and not q: return ...
    if f(p, q): return ...
    c1 = solve(p.child, q.child)
    c2 = solve(p.child, q.child)
    return g(p, q, c1, c2)
```

> Q: Symmetric Tree \ Same Tree

```python
def mirror(p, q):
    if not p and not q: return True
    if not p or not q: return False
    l = self.mirror(p.left, q.right)
    r = self.mirror(q.left, p.right)
    return p.val == q.val and r and l
```

> Q: Flip Equivalent Binary Trees

```python
def flipEquiv(self, p: TreeNode, q: TreeNode) -> bool:
    if not p and not q: return True
    if not p or not q: return False
    n1 = self.flipEquiv(p.left, q.left)     # not flip
    n2 = self.flipEquiv(p.right, q.right)   # not flip
    s1 = self.flipEquiv(p.left, q.right)    # flip
    s2 = self.flipEquiv(p.right, q.left)    # flip
    return p.val == q.val and ((n1 and n2) or (s1 and s2))
```

### 二叉树分治法

#### > Q: Binary Tree Maximum Path Sum

粉色和紫色是各自节点所在 max sum path

但是到 A 处连起来的绿色 max sum path 并没完全包含粉色和紫色, 而利用了以 B 和 C 节点 为端点 max sum chain (B: B → D → I; C: C → F) 

⇒

递归时需要每次返回以改节点为端点的 max sum chian 

经过改节点的 max sum path 用 global 变量 keep update 即可

```
            A
          /   \
         /     \
        /       \
       /	     \
      B	      C	
    /   \       /   \
  D	    E	   F	   G
 / \     / \
H   I	  J   K
```

submission

```python
class Solution:
    def maxPathSum(self, root: TreeNode) -> int:
        self.maxsum = -sys.maxsize
        self.dfs(root)
        return self.maxsum
    
    def dfs(self, node):
        if node == None: 
            return 0
        
        l_chain = self.dfs(node.left)
        r_chain = self.dfs(node.right)
        self.maxsum = max(self.maxsum, l_chain + r_chain + node.val)
        return max(max(l_chain, r_chain) + node.val, 0)
```

#### > Q: House Robber III

由于不能选择相邻节点, 故对于每个当前节点, 需要分两种请款讨论: 是否包含当前节点 ?

思考 1: 由于分两种情况 ⇒ 如何避免如下 O(2^n) 指数级复杂度 ? 

```python
# 如何确定 left 和 right 是否被选入
# 如果左或右选了 ⇒ 根不能选
# 如果左和右没选 ⇒ 根可以选

def dfs(self, root, included):
    self.dfs(root.left, False, curr_sum)
    self.dfs(root.left, True, curr_sum + root.val)
    self.dfs(root.right, False, curr_sum)
    self.dfs(root.right, True, curr_sum + root.val)
    ......
```

思考 2: 此题不能 level BFS 去选择只要那些层. 反例:

```
      1	 
    /   \     
   2    100  
 /
100 
```

submission

```python
class Solution:
    def rob(self, root: TreeNode) -> int:
        return max(self.dfs(root))
        
    def dfs(self, node):
        if node == None:
            return 0, 0
        
        l_in, l_not_in = self.dfs(node.left)
        r_in, r_not_in = self.dfs(node.right)
        
        node_in = l_not_in + r_not_in + node.val
        node_not_in = max(l_in, l_not_in) + max(r_in, r_not_in)
        return node_in, node_not_in
```

#### > Q: Convert BST to Greater Tree

思路: 反中序遍历 | solution

```
# 定义累计求和变量 sum = 0.
# 按照右中左顺序依次访问每个节点 (反中根遍历)
#     更新累计求和变量 sum = sum + 当前节点的值
#     更新当前节点的值 = sum
```

```python
class Solution:
    def convertBST(self, root: TreeNode) -> TreeNode:
        self.sum = 0
        return self.dfs(root)
        
    def dfs(self, node):
        if node:
            self.dfs(node.right)
            self.sum += node.val
            node.val = self.sum
            self.dfs(node.left)
        return node
```

#### > Q: Binary Tree Upside Down

思考: 先翻转当前节点再递归 OR 先递归再翻转当前节点? 怎样做使得上下节点互不影响

注意: 修改 children 之后需要清除之前 children ⇒ prevent CYCLE

![](/notes/high-frequency/media/image3.png)

> Q: Find Leaves of Binary Tree | submission

#### > Q: Inorder Successor in BST *

首先理解中序遍历节点 p 的 successor 的位置:

- if p.right != None: 则后继是其 p.right 中最左端的节点

- if p.right == None: 则后继是其祖先节点右子树中最左端的节点

易理解的 straight-forward 写法

```python
# 节点 p 的 predecessor 有两种情况:
# Case 1: 若存在 node.right ==> 是它的右⼉⼦的左左左左左......⼉⼦
# Case 2: 不存在 node.right ==> 是最近的右⽗亲 (p 在这个⽗亲的左⼦树中)
def inorderSuccessor(self, root, p):
    if not root:
        return None
    
    # 循环 p 的过程中维持其最近的右⽗亲
    lowest_right_father = None
    while root != p:
        if root < p.val:
            lowest_right_father = root
            root = root.right
        else:
            root = root.left
    
    # Case 2:
    if not root.right:
        return lowest_right_father
        
    # Case 1: the left-most node in right child
    son = root.right
    while son:
        ans = son
        son = son.right
    return ans
```

1. 使用递归实现:

- if root.val <= p.val: 答案在右子树中 ⇒ 递归查找右子树

- if root.val >  p.val: 答案在左子树中 ⇒ 递归查找左子树 ⇒ 得到查找结果 left

  - 若能找到则是它一定是 answer. 因为左子树的中的元素都 < root.val, i.e.:

if left != None: return left

  - 若找不到则 root 本身是 answer, i.e.:

if left == None: return root

- Note: 递归中暂存左子树递归查找的结果 left 相当于循环实现中维护的祖先节点.

2. 使用循环实现:

- 查找该节点, 并在该过程中维护上述性质的祖先节点

- 查找到后, 如果该节点有右子节点, 则后继在其右子树内; 否则后继就是维护的祖先节点

解法 1: 递归

```python
def inorderSuccessor(self, root, p):
    if root == None: return None
    if root.val <= p.val:
        return self.inorderSuccessor(root.right, p)
    left = self.inorderSuccessor(root.left, p)
    if left != None:
        return left
    else:
        return root
```

解法 2: 循环

```python
def inorderSuccessor(self, root, p):
    if not root or not p:
        return
    res = None 
    while root:
        if root.val <= p.val:
            root = root.right 
        else:
            res = root
            root = root.left
    return res 
```

> Q: Inorder Predecessor in BST | submission

#### > Q: Closest Binary Search Tree Value II **

(optional)

解法 1: brute-force: Time O(n) & Space O(n)

用 inorder traversal 后找到第一个 >= target 的位置 index. 从 index-1 和 index 出发双指针

解法 2: 算是 simulation 解法

```python
# 最优算法: 时间 O(k + logn) & 空间 O(logn)

# getStack() => 在假装插入 target 的时候, 一路经过的所有节点放到 stack 里, 用于 iterate
# moveUpper(stack) => 根据 stack 挪动到 next node
# moveLower(stack) => 根据 stack 挪动到 prev node
# 有了这些函数后就可以把整个树当作一个数组一样来处理:
# - i++ 的时候要用 moveUpper
# - i-- 的时候要用 moveLower

class Solution:
    def closestKValues(self, root, target, k):
        if root is None or k == 0:
            return []
            
        lower_stack = self.get_stack(root, target)
        upper_stack = list(lower_stack)
        if lower_stack[-1].val < target:
            self.move_upper(upper_stack)
        else:
            self.move_lower(lower_stack)
        
        result = []
        for i in range(k):
            if self.is_lower_closer(lower_stack, upper_stack, target):
                result.append(lower_stack[-1].val)
                self.move_lower(lower_stack)
            else:
                result.append(upper_stack[-1].val)
                self.move_upper(upper_stack)
        return result
        
    def get_stack(self, root, target):
        stack = []
        while root:
            stack.append(root)
            if target < root.val:
                root = root.left
            else:
                root = root.right
        return stack
        
    def move_upper(self, stack):
        if stack[-1].right:
            node = stack[-1].right
            while node:
                stack.append(node)
                node = node.left
        else:
            node = stack.pop()
            while stack and stack[-1].right == node:
                node = stack.pop()
                
    def move_lower(self, stack):
        if stack[-1].left:
            node = stack[-1].left
            while node:
                stack.append(node)
                node = node.right
        else:
            node = stack.pop()
            while stack and stack[-1].left == node:
                node = stack.pop()
                
    def is_lower_closer(self, lower_stack, upper_stack, target):
        if not lower_stack:
            return False
        if not upper_stack:
            return True
        return target - lower_stack[-1].val < upper_stack[-1].val-target
```

### 隐式树分治法

#### > Q: Word Break

![](/notes/high-frequency/media/image4.png)

思路: 上图 code 会被计算两次 ⇒ memoization search ⇒ 注意初始化 memo = {"": [""]}  

记忆化搜索复杂度 ? 

考虑极端例子 e.g.: ‘aaaaaaaaaa’, [‘a’, ‘aa’, ‘aaa’, ‘aaaa’]

⇒ DFS w/o memo: 指数级

⇒ DFS w/ memo: O(mn)

```python
# 判断当前字符串是否可以被拆
#     枚举每个字符: 判断是否可以成为下一个字符串
#         如果可以 --> 判断剩下的部分是否能被拆分

class Solution:
    def wordBreak(self, s, wordDict):
        return self.dfs(0, s, wordDict, memo)
        
    def dfs(self, start_index, s, wordDict, memo):
        # dfs: 返回 s[start_index:] 是否可以被 dictionary 里的单词组成

        if s[start_index:] in memo:  # 记忆化搜索
            return memo[s[start_index:]]
        if start_index == len(s):  # 递归的出口
            return True

        for word in wordDict:
            n = len(word)
            if start_index + n > len(s):
                continue
            if s[start_index:start_index + n] != word:
                continue
            if self.dfs(start_index + n, s, wordDict, memo):
                memo[s[start_index:]] = True
                return True
        memo[s[start_index:]] = False
        return False
```

> Q: Word Break II *

相关: Word Break 只要求判断是否可分 | submission

```python
class Solution:
    def wordBreak(self, s: str, wordDict: List[str]) -> List[str]:
        return self.dfs(s, set(wordDict), {"": [""]})
    
    def dfs(self, s, wordDict, memo):
        if s in memo:
            return memo[s]
            
        res = []
        for i in range(1, len(s) + 1):
            s1 = s[:i]
            s2 = s[i:]
            if s1 in wordDict:
                s2_list = self.dfs(s2, wordDict, memo)
                for s2_str in s2_list:
                    if s2_str == "":
                        res.append(s1)
                    else:
                        res.append(s1 + " " + s2_str)
        memo[s] = res
        return res
```

#### > Q: Scramble String *

解法: DFS (below) \ DP \ DP w/ memo (ctrl+f in DP)

```python
def isScramble(self, s1: str, s2: str) -> bool:
    if len(s1) != len(s2) or sorted(s1) != sorted(s2):
        return False
    if len(s1) <= 3 or s1 == s2:
        return True

    f = self.isScramble 
    for i in range(1, len(s1)):
        if  (f(s1[:i], s2[:i]) and f(s1[i:], s2[i:])) or \
            (f(s1[:i], s2[len(s1) - i:]) and f(s1[i:], s2[:len(s1)-i])):
            return True
    return False
```

### Problems

> Q: Validate Binary Search Tree (ctrl+f)

> Q: Search Range in Binary Search Tree | submission

> Q: Flatten Binary Tree to Linked List * (ctrl+f)

> Q: Balanced Binary Tree * | iterative & recursive

## 高效 DFS

Naive intro-level example / practice

> Q: Generating Parentheses

```python
# 枚举所有的方法
# 递归的定义
# res -> 存所有方案
# path -> 路径: 存放当前放左右括号的方式
# 左、右括号的剩余数量

# 递归的出口:
# 用完了所有左括号和右括号 ✔️
# 在某个瞬间右括号多于左括号 x

# 递归的拆解:
# 1. 左括号
# 2. 右括号

def generateParenthesis(self, n: int) -> List[str]:
    if n == 0:
        return []

    res = []
    self.dfs(n, n, "", res)
    return res

def dfs(self, l, r, path, res):
    # 左括号剩余数量, 右括号剩余数量, 当前选择的括号 / 路径, 答案数组
    if l == 0 and r == 0:
        res.append(path)  # list 必须 [:] 来 copy; 这里字符串不用 [:] 也可
    if r < l:
        return

    if l > 0:
        self.dfs(l - 1, r, path + "(", res)
    if r > 0:
        self.dfs(l, r - 1, path + ")", res)
```

### 枚举型 DFS 模拟嵌套 for 循环

枚举型 DFS == 嵌套 for loop | Note: for 循环的问题在于层数不定 / 层数太多 ⇒ DFS 解决

#### > Q: Letter Combinations of a Phone Number

solution 1: 嵌套 for loop 的高效写法 (naive)

```python
def letterCombinations(self, digits: str) -> List[str]:
    chr = ["","","abc","def","ghi", "jkl", "mno", "pqrs", "tuv", "wxyz"]
    res = []
    for i in range(0, len(digits)):
        num = int(digits[i])
        tmp = []
        for j in range(0, len(chr[num])):
            if len(res):
                for k in range(0, len(res)):
                    tmp.append(res[k] + chr[num][j])
            else:
                tmp.append(str(chr[num][j]))
        res = copy.copy(tmp)
    return res
```

solution 2: 枚举型 DFS

```python
def letterCombinations(self, digits: str) -> List[str]:
    self.chars = ["", "", "abc", \
                  "def", "ghi", "jkl", "mno", "pqrs", "tuv", "wxyz"]
    res = []
    if not digits or len(digits) == 0:
        return res

    self.dfs(0, "", digits, res)
    return res

def dfs(self, idx, string, digits, res):
    # exit condition of DFS
    if idx == len(digits):
        res.append(string)
        return

    for ch in self.chars[int(digits[idx])]:
        self.dfs(idx + 1, string + ch, digits, res)
```

### 剪枝 + 回溯 Backtracking

#### > Q: Factorization

思路: 需要模拟如下层数不定的 for loop

```
for a in range(2, n + 1):
    for b in range(a, n / a + 1):
        for c in range(a, n / a / b + 1):
            ...
```

DFS 无剪枝 ⇒ TLE

```python
# 枚举所有的可能因子: 判断当前数字是否被该因子整除
# 1. 递归的出口: 当前数字为 1
# 2. 递归的拆解: 使用不小于之前的因子和数字去整除目标数字
# 3. 递归的定义: path, res, 当前数字 n, 之前的因子是多少

class Solution:
    def getFactors(self, n):
        res = []
        self.backtracking(2, n, [], res)
        return res
      
    def backtracking(self, start, remain, path, res):
        if remain == 1:
            if len(path) > 1:  # 防止 n = 10, path = [10] 的情况
                res.append(path[:])  
            return
        
        for factor in range(start, remain + 1):
            if remain % factor == 0:
                path.append(factor)
                self.dfs(factor, remain // factor, path, res)
                path.pop()
```

DFS + 剪枝

```python
class Solution:
    def getFactors(self, n):
        res = []
        self.backtracking(2, n, [], res)
        return res
      
    def backtracking(self, start, remain, path, res):
        if remain == 1:
            if len(path) > 1:
                res.append(path[:])  # ATTENTION 1
            return
        
        for factor in range(start, int(math.sqrt(remain)) + 1):
            if remain % factor == 0:
                path.append(factor)
                self.dfs(factor, remain // factor, path, res)
                path.pop()

        # ATTENTION 2
        path.append(remain)
        self.dfs(remain, 1, path, res)
        path.pop()
```

ATTENTION:

- 加入 res 里一定要使用 copy.copy(): res.append(path[:])

- 剪枝加入后需要特殊处理最后一个 factor = remain 的情况

> Q: Robot Room Cleaner | solution | submission: recursion 倒 1 & iteration 倒 2

#### > Q: Word Squares *

![](/notes/high-frequency/media/image5.png)

N: number of words \ L: length of each word | explanation by leetcode

- 思路 0: brute-force ⇒ Time O(N^5): 最长单词长度为 5

- 思路 1: DFS + backtracking ⇒ TLE

- 思路 2: DFS + backtracking + 剪枝 ⇒ TLE (上图)

- 思路 3: DFS + backtracking + 剪枝 + Prefix Hash Table ⇒ ✔️

  - 时间 O(N · 26L)

  - 空间 O(NL) = O(NL + NL / 2)

O(NL): values of hashtable, where we store L times all words in hashtable.

O(NL / 2): keys of the hashtable, which include all prefixes of all words.

  - Reduce time of retrieving a list of words with a given prefix from O(N) to O(1)

  - BUT: requires extra space for Prefix Hash Table

- 思路 4: DFS + backtracking + 剪枝 + Trie ⇒ ✔️

##### 思路 3: DFS + backtracking + 剪枝 + Prefix Hash Table

```python
class Solution:
    def wordSquares(self, words):
        if len(words) == 0: return []
        self.words = words
        self.N = len(words[0])
        self.build_prefix_hash(self.words)

        res = []
        for word in words:
            self.backtracking(1, [word], res)
        return res

    def backtracking(self, step, squares, res):
        if step == self.N:
            res.append(squares[:])
            return
        prefix = ''.join([word[step] for word in squares])
        for candidate in self.get_words_by_prefix(prefix):
            squares.append(candidate)
            self.backtracking(step + 1, squares, res)
            squares.pop()

    def build_prefix_hash(self, words):
        self.prefix_hash = {}
        for word in words:
            for prefix in (word[:i] for i in range(1, len(word))):
                self.prefix_hash.setdefault(prefix, set()).add(word)

    def get_words_by_prefix(self, prefix):
        if prefix in self.prefix_hash:
            return self.prefix_hash[prefix]
        else:
            return set([])
```

##### 思路 4: DFS + backtracking + 剪枝 + Trie

TODO

#### > Q: Expression Add Operators (hard)

注意: 允许 "0" 但 "03" 是不合法的, i.e.: "1*2*(03)" 是不合法的

e.g.: Input: "1203", 6 ⇒ Output: ["1+2+0+3","1+2-0+3"] 不包括 "1*2*(03)"

```python
# num: remaining num string
# tmp: temporally string with operators added
# cur: current result of "temp" string
# last: last multiply-level number in "tmp". If next operator is "multiply", "cur" and "last" will be updated

def addOperators(self, num, target):
    def dfs(idx, tmp, cur, last, res):
        if idx == len(num):
            if cur == target:
                res.append(tmp)
            return
        for i in range(idx, len(num)):
            x = int(num[idx: i + 1])
            if idx == 0:
                dfs(i + 1, str(x), x, x, res)
            else:
                dfs(i + 1, tmp + "+" + str(x), cur + x, x, res)
                dfs(i + 1, tmp + "-" + str(x), cur - x, -x, res)
                dfs(i + 1, tmp + "*" + str(x), cur - last + last * x, 
                    last * x, res)
            # ATTENTION: "0" is not allowed as a beginning of a digit
            # e.g.: Input: "1203", 6 ⇒ Output: ["1+2+0+3","1+2-0+3"]
            # i.e.: allow "0", not "03" ⇒ "1*2*(03)" is invalid.
            if x == 0:
                break
    res = []
    dfs(0, "", 0, 0, res)
    return res
```

### 结合 DFS + BFS: 最短所有方案

求最短路径 ⇒ BFS

求所有方案 ⇒ DFS

求最短的所有方案 ⇒ BFS + DFS

#### > Q: Word Ladder II

```python
class Solution:
    def findLadders(self, start, end, wordList):
        if end not in wordList:
            return []
        
        # BFS: the distance from each word to the End Word
        indexes = self.build_indexes(set(wordList + [start] + [end]))
        distance = self.bfs(end, indexes)
        
        # Return False if there is no available path
        if start not in distance:
            return []
        
        # DFS: find all paths that moves closer to End Word at each step
        # Then these paths are guaranteed to be shortest.
        results = []
        self.dfs(start, end, distance, indexes, [start], results)
        return results

    def build_indexes(self, wordList):
        indexes = collections.defaultdict(lambda: set())
        for word in wordList:
            for i in range(len(word)):
                key = word[:i] + '*' + word[i + 1:]
                indexes[key].add(word)
        return indexes

    def bfs(self, end, indexes):
        distance = {end: 0}
        queue = deque([end])
        while queue:
            word = queue.popleft()
            for next_word in self.get_next_words(word, indexes):
                if next_word not in distance:
                    distance[next_word] = distance[word] + 1
                    queue.append(next_word)
        return distance

    def get_next_words(self, word, indexes):
        words = []
        for i in range(len(word)):
            key = word[:i] + '*' + word[i + 1:]
            for w in indexes.get(key, []):
                words.append(w)
        return words
                        
    def dfs(self, curt, target, distance, indexes, path, results):
        if curt == target:
            results.append(list(path))
            return
        
        for word in self.get_next_words(curt, indexes):
            # Choose to move only when the next one is closer
            if distance[word] != distance[curt] - 1:
                continue
            path.append(word)
            self.dfs(word, target, distance, indexes, path, results)
            path.pop()
```

### Problems

> Q: Sudoku Solver

https://www.lintcode.com/problem/sudoku

> Q: N-Queens

https://www.lintcode.com/problem/n

> Q: N-Queens II

https://www.lintcode.com/problem/n-ii
