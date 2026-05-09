---
layout: ../../layouts/Layout.astro
title: Leetcode (主笔记)
---

# Binary Search

Source: 九章基础班 lec 02-binary-search-logn-algorithm

## Time Complexity

### 时间复杂度推导举例

T(n) = T(n/2) + O(1) = O(log n) 通过 O(1) 时间把规模 n 的问题变为 n / 2。T(n) 是个函数。

T(n) 

= T(n/2) + O(1)

= T(n/4) + O(1) + O(1)

= T(n/8) + O(1) + O(1) +O(1) = ... = T(1) + logn * O(1) = O(logn)

T(n) = T(n/2) + O(n) = O(n) 通过 O(n) 的时间把规模为 n 的问题变为 n / 2。

T(n) 

= T(n/2) + O(n)

= T(n/4) + O(n) + O(n/2)

= T(n/8) + O(n) + O(n/2) +O(n/4) = T(1) + (n * (1 + 1/2 + 1/4 + … + 1/n) ≈ O(2n) ≈ O(n) ???

### 常见算法时间复杂度

| 复杂度 | 可能对应的算法 | 备注 | P v.s. NP |
| --- | --- | --- | --- |
| O(1) | 位运算 | 面试鲜有 | 多项式复杂度 P 问题 |
| O(logn) | 二分法 / 倍增法 / 快速幂算法 / 辗转相除法 |  | 多项式复杂度 P 问题 |
| O(\sqrt(n)) | 分解质因数 | 几乎只有该算法 | 多项式复杂度 P 问题 |
| O(n) | 枚举法 / 双指针算法 / 单调栈算法 / KMP 算法 / Rabin Karp / Manacher's Algorithm | 线性时间复杂度 | 多项式复杂度 P 问题 |
| O(nlogn) | 快速排序 / 归并排序 / 堆排序 |  | 多项式复杂度 P 问题 |
| O(n^2) | 数组 / 枚举法 / 动态规划 / Dijkstra |  | 多项式复杂度 P 问题 |
| O(n^3) | 数组 / 枚举法 / 动态规划 / Floyd |  | 多项式复杂度 P 问题 |
| O(2^n) | 与组合有关的搜索问题: DFS / 递归 |  | NP 问题 |
| O(n!) | 与排列有关的搜索问题 |  | NP 问题 |

### 数据范围推测时间复杂度 *

- 一秒能跑的运算次数: 10^9

e.g.: n <= 1000 则 O(n^3) 的算法会 TLE ⇒ 需要比如 O(n^2) = O(10^6) 的算法

- 技巧: 用数据范围推测所需时间复杂度 ⇒ 用复杂度推测算法

e.g.: 

n = 10^7 ⇒ O(n)

n = 10^4 ~ 10^6: O(n), O(nlogn)

n = 10^3 ⇒ O(n^2)

n <= 20 ⇒ O(2^n)

## Level 1: 二分法四要点模板

- start + 1 < end ⇒ Side note: mid + 1 不会越界

- mid = start + (end - start) / 2。若 (start + end) / 2 则 start 和 end 都很大相加或溢出。

- A[mid] == / < / > target 分三种情况讨论

- A[start] or A[end] == target 根据题意选择

四要点总结通用模板: Classic Binary Search

```python
def findPosition(self, nums, target):
    if len(nums) == 0:
        return -1
    
    start, end = 0, len(nums) - 1
    # 1. 循环条件
    while start + 1 < end:
        # 2. 中值计算
        mid = (start + end) // 2
        # 3. 分三种情况讨论
        if nums[mid] < target:
            start = mid
        elif nums[mid] > target:
            end = mid
        else:
            return mid
    # 4. 结果讨论
    if nums[start] == target:
        return start
    if nums[end] == target:
        return end
    return -1
```

注释 1: start + 1 < end

Last Position of Target nums = [1,1], target = 1 使用 start < end 无论如何都会出现死循环

```
while start < end:
    mid = (0 + 1) / 2 = 0;
    if mid == target:
        start = mid
```

注释 3: 任意位置 v.s. 第一个位置 v.s. 最后一个位置

- Classic Binary Search

- First Position of Target: if nums[mid] == target: end = mid

- Last Position of Target: if nums[mid] == target: start = mid

并且首先判断 if nums[end] == target: return end

## Level 2: 二分位置之 OOXX

一般会给你一个数组, 让你找数组中第一个 / 最后一个满足某个条件的位置

i.e.: 在 OOOOOO...OOXX….XXXXXX 中第一个 X / 最后一个 O

> Q: First Bad Version

> Q: Find K Closest Elements: 二分法找到 index 后双指针找邻近 k 个

### 倍增法 Exponential Backoff

使用到倍增思想的场景: 动态数组 (ArrayList in Java, vector in C++), 网络重试

#### > Q: Search in a Big Sorted Array

### 二分搜 Rotated Array

```
递增数组：
              ↗
            ↗
          ↗
        ↗
      ↗
    ↗
  ↗
↗
旋转数组: 分成两段上升数组:
             ↗|
           ↗  |
         ↗    |
       ↗      |
     ↗        |
---------------|------------------
               |    ↗
               |  ↗
               |↗
     ↑     ↑        ↑
   start   mid       end
```

> Q: Find Minimum in Rotated Sorted Array | submission | figure

```
# 比较 mid 与 end 以确定 mid 位于两段上升数组的哪一段:
# 1.  nums[mid] < nums[end]:
#     mid 在后段上升数组中 end = mid
# 2.  nums[mid] > nums[end]:
#     mid 在前段上升数组中 start = mid
```

Follow up 1: 若有重复元素 

> Q: Find Minimum in Rotated Sorted Array II (hard)

此题区别: 存在重复元素 ⇒ 二分法无法保证时间复杂度为 O(logn) ⇒ Worst Time O(n)

证明方法: [1,1,1….,1] 里有个 0 ⇒ 此时 mid = 1 无法判断 0 在哪边 (考点: 想到 worst case)

(solution): 解法的唯一区别是 nums[mid] == nums[end] 时 end -= 1

```python
def findMin(self, nums: List[int]) -> int:
    n = len(nums)
    if n == 0: 
        return
    start, end = 0, n - 1
    while start + 1 < end:
        mid = (start + end) // 2
        if nums[mid] < nums[end]:
            end = mid
        elif nums[mid] > nums[end]:
            start = mid
        else:  # nums[mid] == nums[end]
            end -= 1
    return min(nums[start], nums[end])
```

Follow up 2: 为何不三分法

问: 三分法 log3(n) 应该比二分法 log2(n) 更快 / 时间复杂度更好 ?

答: In practice 并不是. k 分法需要 (k-1) * logk(m).

### Problems

> Q: Maximum Number in Mountain Sequence: 在先增后减的序列中找最大值

> Q: Search a 2D Matrix II

思路 1: 二分法: 做一次. 把矩阵看作 1D array ⇒ log(mn)

思路 2: 二分法: 做两次. 先二分搜索 row index 再 col index ⇒ log(m) + log(n) = log(mn)

思路 3: 双指针: zigzag 从左下角开始 Search Space Reduction ⇒ O(m + n) | submission

> Q: Search for a Range / Find First and Last Position of Element in Sorted Array: submit

> Q: Total Occurrence of Target @Google

> Q: Smallest Rectangle Enclosing black Pixels (hard) | solution

## Level 3: 二分位置之 Half Half

并无法找到一个条件形成 OOXX 的模型 ⇒ 

但可以根据判断以保留下有解的那一半或者去掉无解的一半

#### > Q: Search in Rotated Sorted Array *

# 二分法 mid 和 end 比较:
# 1. nums[mid] > nums[end]:
# mid 在第一段上升区间, 跟 target 比较:
#   1. 如果 nums[start] <= target < nums[mid] ==> end = mid
#   2. 否则 start = mid 继续二分查找. 仍是 search in rotated sorted array
# 2. nums[mid] <= nums[end]:
# mid 在第二段上升区间, 跟 target 比较:
#   1. 如果 nums[mid] < target <= nums[end] ==> start = mid
#   2. 否则 end = mid 继续二分查找. 仍是 search in rotated sorted array

(submission)

```python
def search(self, nums: List[int], target: int) -> int:
    if not nums: return -1
    start, end = 0, len(nums) - 1

    while start + 1 < end:
        mid = (end + start) // 2
        if nums[mid] == target:
            return mid
        # 在低上升段
        if nums[mid] <= nums[end]:  
            if nums[mid] < target <= nums[end]:
                start = mid
            else:
                end = mid
        # 在高上升段
        else: 
            if nums[start] <= target < nums[mid]:
                end = mid
            else:
                start = mid

    if nums[start] == target:
        return start
    if nums[end] == target:
        return end
    return -1
```

> Q: Find Peak Element

Note 1: 二分法

- 如果 mid 如果大于左右 ⇒ 找到 peek.

- 否则取大的一边 / 若两边都大于 mid 则可任取一边

Note 2: start + 1 < end ⇒ mid + 1 不会越界 ⇒ 每步可以比较 if nums[mid] > nums[mid + 1] 

- 每步可以比较 if nums[mid] > nums[mid + 1]

Note 3: 方法的正确性如何保证 

- A[0] < A[1] && A[n-2] > A[n-1] ⇒ 一定存在 peak 且范围 1 ~ len(A) - 2

- 由于二分时总选择大的一边, 则留下的部分仍然满足条件 a., i.e.: 最两边的元素都小于相邻的元素 ⇒ 仍然必存在 peak

- 二分至区间足够小 (长度为 3) ⇒ 中间元素就是 peak

> Q: Find Peak Element II (follow up)

Challenge: Solve it in O(n+m) time.

If you come up with an algorithm that you thought it is O(nlogm) or O(mlogn), can you prove it is actually O(n+m) or propose a similar but O(n+m) algorithm ??? TODO

#### > Q: Kth Smallest Element in a Sorted Matrix

思路: 二分; 计算 number of `less or equal` 再决定是否继续二分.

![](/notes/leetcode/media/image1.png)

![](/notes/leetcode/media/image2.png)

## Level 4: 二分答案

往往没有给数组让你二分. 通过猜值判断是该值否满足题意. 否则二分搜索可能解:

1. 找到可行解范围

2. 猜答案

3. 检验条件

4. 调整搜索范围

> Q: Sqrt(x) & Sqrt(x) II

> Q: Wood Cut / Cut Ribbon @FB @Google | solution

> Q: Copy Books (ctrl+f in DP)

> Q: Find The Duplicate Number ⇒ 应该用 Linked List Cycle 的快慢指针做法

> Q: Maximum Average Subarray II | solution | TODO

> Q: Koko Eating Bananas

## Log(n) 算法 Overview

二分法 \ 倍增法 \ 快速幂算法 \ 辗转相除法

> Q: Fast Power (ctrl+f)

原理: xn = xn/2 * xn/2 使得 O(n) 问题可以用 O(logn) 解决

相关: Pow(x, n) 

## 二叉树分治法 / 二分法

(ctrl+f)

> Q: Min Depth of Binary Tree (easy) @2020.02.18

三种方法：Recursion \ DFS \ BFS。注意和 Max Depth of Binary Tree 不同的地方。

> 解法 1: Recursion | Time O(n); Space O(logn) balanced tree, O(n) worst | submission

```python
def minDepth(self, root: TreeNode) -> int:
    if root == None:
        return 0 

    children = [root.left, root.right]
    if not any(children):  # if we're at leaf node
        return 1

    min_depth = float('inf')
    for child in children:
        if child != None:
            min_depth = min(self.minDepth(child), min_depth)
    return min_depth + 1
```

> 解法 2: DFS

依旧 Time O(n); Space worst O(n)

```python
def minDepth(self, root: TreeNode) -> int:
    if root == None:
        return 0
    
    stack, min_depth = [(1, root),], float('inf')
    while stack:
        depth, root = stack.pop()
        children = [root.left, root.right]
        if not any(children):
            min_depth = min(depth, min_depth)
        for child in children:
            if child:
                stack.append((depth + 1, child))
    return min_depth 
```

> 解法 3: level BFS

依旧 Time O(n); Space worst O(n) 但 better ⇒ O(n / 2)

- The drawback of the DFS approach in this case is that all nodes should be visited to ensure that the minimum depth would be found. Therefore, this results in a O(N) complexity. One way to optimize the complexity is to use the BFS strategy. We iterate the tree level by level, and the first leaf we reach corresponds to the minimum depth. As a result, we do not need to iterate all nodes.

- Time complexity : in the worst case for a balanced tree we need to visit all nodes level by level up to the tree height, that excludes the bottom level only. This way we visit N/2 nodes, and thus the time complexity is O(N).

```python
from collections import deque

def minDepth(self, root: TreeNode) -> int:
    if not root:
        return 0
    else:
        node_deque = deque([(1, root),])

    while node_deque:
        depth, root = node_deque.popleft()
        children = [root.left, root.right]
        if not any(children):
            return depth
        for child in children:
            if child:
                node_deque.append((depth + 1, child))
```

# Two Pointers

背向双指针

- Longest Palindromic Substring 的中心线枚举算法

- Find K Closest Elements

相向双指针

- Reverse 类 (较少)

- Two Sum 类 (最多)

- Partition 类 (较多): sorting

同向双指针

- 滑动窗口类 Sliding Window

- 快慢指针类 Fast & Slow Pointers, etc.

三指针算法

- Sort Colors | submission

- Valid Triangle Number | submission

## 相向双指针

算法开始, 两根指针分别位于数组 / 字符串的两端, 相向移动

典型例子: 翻转字符串问题 e.g. 三步翻转法

典型例子: 判断回文串 Valid Palindrome

- 变体: 不区分大小写且忽略非英文字母

- 变体: 允许删掉一个字母 (等价于允许插入一个) | Valid Palindrome II

  - 遍历字母看删去后是否是回文串需要 O(n2), 显然太慢

  - 应该依然按照原来算法, 但当碰到不一样的字符时, 尝试删除其中之一是否可以变成回文串. 若删去两边任一都不可以, 则非回文串 (.pdf)

典型例子: Two Sum

- 哈希表: 使用 Hashmap 记录对应数字是否出现及其下标 ⇒ Time O(n) | Space O(n)

  - e.g.: 只能使用 HashMap: Two Sum III - Data structure design

- 双指针: 复杂度主要来源于排序, 但不需要额外空间 ⇒ Time O(nlogn) | Space O(1)

  - e.g.: 双指针更快: Two Sum II - Input array is sorted

类型 1: Reverse

> Q: Valid Palindrome & II (Follow up: 可以删除一个字符)

  - 类型 2: Two Sum

+ Two Sum 计数问题

> Q: Two Sum - Less Than or Equal To Target: 参考 Valid Triangle Number

+ 三指针: loop 一个固定指针 + 双指针

> Q: 3Sum / Three Sum - Unique Pairs: submission | ATTENTION: remove duplicates

> Q: 3Sum Closest

> Q: Valid Triangle Number / Triangle Count *: solution: 一条边固定后另两个指针相向移动

> Q: 4Sum

类型 3: Partition: ctrl+f: partition

烙饼排序 Pancake Sort https://en.wikipedia.org/wiki/Pancake_sorting

睡眠排序 Sleep Sort https://rosettacode.org/wiki/Sorting_algorithms/Sleep_sort

面条排序 Spaghetti Sort https://en.wikipedia.org/wiki/Spaghetti_sort

猴子排序 Bogo Sort https://en.wikipedia.org/wiki/Bogosort

## 同向双指针

指两根指针都从头出发, 同向移动. e.g.:

- 数组去重问题 Remove duplicates in an array

- 滑动窗口问题 Window Sum

- 两数之差问题 Two Sum Difference

- 链表中点问题 Middle of Linked List

- 带环链表问题 Linked List Cycle

## 背向双指针

> Q: Palindromic Substrings

枚举所有 2N - 1 个可能对称轴: either at letter or between two letters ⇒ 背向移动两指针

# BFS

## BFS Key Points

- 问：为何 BFS 使用 Queue 作为主要的数据结构 v.s. DFS 使用 Stack？

答：以二叉树的遍历为例：

BFS 从根节点出发，然后一层一层地按顺序遍历，讲究先进先出 ⇒ queue

DFS 是一直走到头，然后一点一点地从尾部操作，讲究先进后出。

DFS 若使用递归的方法，是系统栈的调用；若使用非递归的方法，才会使用到 stack

- 问：BFS 是否需要实现分层？

注：需要分层的算法比不需要分层的算法多一个循环 & DFS分层与否的区别

- 问：(Java / C++) size=queue.size() 不可直接 for (int i = 0; i < queue.size(); i++)

答：因为 queue.size() 在 queue 被删减的过程中是值是变化的

- 问：(Python) 为何可以直接写 for i in range(len(queue)) ？

答：for _ in range(len(deque) 只在 range 生成时 evaluate 一次 len 故不需提前算 len

- Queue 采用 FIFO (first in first out) 策略的抽象数据结构. 可记录 BFS 待扩展的节点.

- Queue 内部存储元素的方式一般有两种: array & linked list

对于随机访问 get & set: array 优于 linked list. 因为 linked list 要移动指针

对于修改操作 add & remove: linked list 优于 array. 因为 array 要移动数据

- Queue 主要操作: add() / pop() / size() / empty()

## 何时使用 BFS

- 图的遍历 Traversal in Graph. e.g.: 给出无向连通图 (Undirected Connected Graph) 中的一个点, 要求找到这个图里的所有点. e.g. Clone Graph

  - 层级遍历 Level Order Traversal

    - 不仅需知道从一个点出发可以到达哪些点, 还需知道这些点分别离出发点是第几层遇到的. e.g. Binary Tree Level Order Traversal

  - 由点及面 Connected Component 找连通块

  - 拓扑排序 Topological Sorting

- 最短路径 Shortest Path in Simple Graph

  - 仅限简单图 (Simple Graph)

    - 简单图即图中每条边长度都相等

    - 大部分简单图中使用 BFS 算法时都是无向图, 面试少有有向图

- 非递归的方式找所有方案 Iteration solution for all possible results / 将在 DFS 提及

建议: 能用 BFS 一定不要用 DFS. 因为用 Recursion 实现 DFS 可能造成 Stack Overflow 而 Non-Recursion DFS 不好写.

### 最短 / 长路径算法总结

- 最短路径

  - 简单图: BFS

  - 复杂图: Dijkstra / SPFA / Floyd

- 最长路径

  - 图可以分层: Dynamic Programming

  - 不可以分层: DFS

### 复杂度: 树 v.s. 图 v.s. 矩阵 BFS

问: 图上 BFS 和树上 BFS 有什么区别

答: 图中存在环 ⇒ 同一个节点可能重复进入队列 & 注意非连通图不要漏掉某些 nodes

时间复杂度 Graph: 

- N 个点, M 条边, 且 M 最大是 O(N^2) 级别

- 图上 BFS 时间复杂度 = O(N + M), or O(M) 因为 M 一般都比 N 大 ⇒ worst O(N^2)

时间复杂度 Matrix:

- R 行 C 列 R * C 个点, R * C * 2 条边 (每个点上下左右 4 条边, 每条边被 2 个点共享)

- 矩阵上 BFS 时间复杂度 = O(R * C)

## 二叉树 BFS

### Traversal

#### > Q: Binary Tree Level Order Traversal (easy)

一个队列 BFS v.s. 两个队列 BFS v.s. DFS by 九章算法 @2019.08.27

```python
def levelOrder(self, root: TreeNode) -> List[List[int]]:
    if root == None:
        return []

    queue = [root]  # or collections.deque([root])
    order = []
    while queue:
        level = []
        for _ in range(len(queue)):
            current = queue.pop(0)     # or queue.popleft()
            level.append(current.val)  # 这里需要加 .val
            if current.left != None:
                queue.append(current.left)
            if current.right != None:
                queue.append(current.right)
        order.append(level)
    return order
```

> Q: Binary Tree Right Side View (medium)

完全是层级遍历，每层记录最后一个点即可。

#### > Q: Binary Tree Vertical Order Traversal (medium)

submission BFS | DFS | solution (用到 Queue.Queue 和 put(node, x)) @2019.08.27

思路: 此题本质还是层级遍历, 只是增加了一个纵向列信息. 每遇 left node 的列 -1, 每遇 right node 的列 +1. 最后将字典中从 min 到 max 的所有列按顺序取出来即可.

注意: Leetocde 要求 same x, same y, then smaller value comes the first ⇒ 分层 BFS

```python
def verticalTraversal(self, root: TreeNode) -> List[List[int]]:
    if root == None: return []

    results = defaultdict(list)
    queue = [(root, 0)]
    while queue:
        # level-order: smaller value comes first if w/ same x, same y
        temp = defaultdict(lambda: list())
        for _ in range(len(queue)):
            node, x = queue.pop(0)
            if node:
                temp[x].append(node.val)
                queue.append((node.left, x - 1))
                queue.append((node.right, x + 1))

        for col in temp.keys():
            results[col] += sorted(temp[col])

    return [results[i] for i in sorted(results)]
    tree = defaultdict(lambda: list())
```

相关题目

> Q: Binary Tree Zigzag Order Traversal

> Q: Convert Binary Tree to Linked Lists by Depth

### Serialization

> Q: Serialize and Deserialize Binary Tree (medium) 

思路 1: 用一维 BFS 做 serialize & 用快慢两个指针做 deserialize: solution @2019.08.28

思路 2: Recursion: submission

> Q: Serialize and Deserialize N-ary Tree: 思路

## 图 BFS

由点及面图的遍历

> Q: Clone Graph | solution: DFS & BFS

最典型 BFS 问题: 隐式图 (Implicit Graph) 最短路径

#### > Q: Word Ladder I & II

> Q: Word Ladder | submission | solution bi-directional BFS

> Q: Word Ladder II | explanation level BFS

> Q: Graph Valid Tree: 判断一个图是否是一棵树

> Q: Search Graph Nodes: 搜索图中最近值为 target 的点

> Q: Connected Component in Undirected Graph: 无向图联通块

#### > Q: Bipartite Graph *

思路: 分层 BFS / 普通 DFS / 递归 DFS @2020.03.09

注意: what if the graph is not connected?

e.g.: [[],[2,4,6],[1,4,8,9],[7,8],[1,2,8,9],[6,9],[1,5,7,8,9],[3,6,9],[2,3,4,6,9],[2,4,5,6,7,8]]

分层 BFS: submission

```python
def isBipartite(self, graph):
    sets, visited = [set(), set()], set()
    for node in range(len(graph)):
        if node in visited:
            continue
        queue = collections.deque([node])
        visited.add(node)
        level = 0
        sets[level % 2].add(node)
        while queue:
            level += 1
            for _ in range(len(queue)):  # trverse this level
                node = queue.popleft()
                visited.add(node)
                for nb in graph[node]:
                    if nb in sets[(level - 1) % 2]:
                        return False
                    sets[level % 2].add(nb)
                    if nb not in visited:
                        queue.append(nb)
    return True
```

普通 DFS: submission

```python
def isBipartite(self, graph):
    sets, visited = [set(), set()], set()    
   for node in range(len(graph)):
        if node in visited:
            continue
        stack = [node]
        sets[0].add(node)
        visited.add(node)
        while stack:
            node = stack.pop()
            visited.add(node)
            i = 0 if node in sets[0] else 1
            for nb in graph[node]:
                if nb in sets[i]:
                    return False
                sets[1 - i].add(nb)
                if nb not in visited:
                    stack.append(nb)
    return True
```

递归 DFS: submission

```python
def isBipartite(self, graph):
    color = {}
    def dfs(node):
        for nb in graph[node]:
            if nb in color:
                if color[nb] == color[node]:
                    return False
            else:
                color[nb] = 1 - color[node]
                if not dfs(nb):
                    return False
        return True

    for start in range(len(graph)):
        if start not in color:
            color[start] = 0
            if not dfs(start):
                return False
    return True
```

相关题目: Possible Bipartition | submission

```python
# 唯一的区别是需要先 build graph
graph = defaultdict(lambda: list())
for u, v in dislikes:
    graph[u].append(v)
    graph[v].append(u)
```

## 矩阵 BFS

#### > Q: Number of Big Islands *

思路分析:

- 代码难度: BFS > DFS > Union Find

- 正确性: BFS = Union Find > DFS (可能 stack overflow)

上述方式中 DFS 可能 stack overflow. e.g.: 若 1 分布如下顺序 S 形 ⇒ DFS 达到 worst 复杂度 

———————

                         | 

———————

|

———————

                         |

———————

|

———————

若时间复杂度 O(n^2) 则尽量不要 DFS. 因递归 stack 所需空间不可控, 但 BFS 队列长度可控.

可以使用带权并查集, 但不建议.

```
# 1. 从为 1 的位置开始 BFS
# 2. 在 BFS 的过程中记录经过的岛屿规模, 返回岛屿规模
# 3. 判断岛屿规模是否大于 k

# 定义队列
# 定义visited：哪些点访问过
# 遍历所有点
#     如果这个点为岛屿, 且没有访问过
#         从这个点开始 BFS, 返回规模
#         如果岛屿规模大于 k
#             合法的岛屿数量 +1 
# 返回合法岛屿数量
```

```python
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
class Solution:
    def numsofIsland(self, grid, k):
        n = len(grid)
        if n == 0: return 0
        
        m = len(grid[0])
        if m == 0: return 0
        
        visited = set()
        count = 0
        for i in range(n):
            for j in range(m):
                if grid[i][j] and (i, j) not in visited:
                    size = self.bfs(i, j, grid, visited)
                    if size >= k:
                        count += 1
        return count
        
    def bfs(self, start_x, start_y, grid, visited):
        queue = collections.deque([(start_x, start_y)])
        visited.add((start_x, start_y))
        size = 1
        while queue:
            x, y = queue.popleft()
            for direction in DIRECTIONS:
                new_x = x + direction[0]
                new_y = y + direction[1]
                if self.isvalid(new_x, new_y, grid, visited):
                    queue.append((new_x, new_y))
                    visited.add((new_x, new_y))
                    size += 1         
        return size
        
    def isvalid(self, x, y, grid, visited):
        if not 0 <= x < len(grid) or not 0 <= y < len(grid[0]):                                    
            return False 
        if not grid[x][y]:
            return False 
        if (x, y) in visited:
            return False 
        return True
```

等价题目

- Leetcode 200: Number of Islands

- Leetcode 695: Max Area of Island

##### 进阶题目

- LC 827: 改变一个格子使得岛屿面积最大

  - Making a Large Island

  - solution 用 DFS 却为何是 O(n^2)? 每个格子遍历过都标上了 index 不会第二次

- LT 434: 多次查询不同的岛屿数量

  - Number of Islands II | solution: Union Find

- LT 860: 不同形状的岛屿数量

  - Number of Distinct Islands

  - solution: 用每个点和岛屿起始点的相对位置记录岛屿形状

- LT 804: 不同形状的岛屿数量 (可以旋转)

  - Number of Distinct Islands II | solution

#### > Q: Knight Shortest Path Follow up: 房子数量较少空地数量较多, 能否进一步降低复杂度?

⇒ 考虑从每个房子开始分层 BFS: 给每个空地加上该点到这个空地的 steps

0	A	0	0	0
B	0	0	-1	D
0	C	0	0	0

BFS(A) 后得到

1	A	1	2	3
B	1	2	-1	D
0	C	3	4	5

BFS(B) 后得到

2	A	4	6	8
B	2	4	-1	D
1	C	6	8	10

注意: 需要额外 array 记录每个空地被达到的次数. 比如上例中 [2, 0] 位置是 A 不可达的, 那这个空地虽然比 optimal solution [1, 1] 位置值小, 也是不可取的.

#### > Q: Zombie in Matrix

#### > Q: Escape a Large Maze

相关题目: The Maze ⇒ 思路: 每次选择一个方向滚到头 (直到遇到 WALL) 即可

discussion & discussion

```python
def isEscapePossible(self, blocked: List[List[int]], source: List[int], target: List[int]) -> bool:
    if not blocked: return True
    blocked = set(map(tuple, blocked))  # set O(1) < list O(n)
    DIRECTOINS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    def check(blocked, source, target):
        level = 0
        queue = collections.deque([(source[0], source[1])])
        visited = set()
        while queue:
            for _ in range(len(queue)):
                x, y = queue.popleft()
                for dx, dy in DIRECTOINS:
                    x_ = x + dx
                    y_ = y + dy
                    if 0 <= x_ < 10**6 and 0 <= y_ < 10**6 and \
                        (x_, y_) not in visited and \
                        (x_, y_) not in blocked:
                        if x_ == target[0] and y_ == target[1]: 
                            return True
                        visited.add((x_, y_))
                        queue.append((x_, y_))
            level += 1
            if level == 2 * len(blocked): break
        return len(queue) != 0
    return  check(blocked, source, target) and \
            check(blocked, target, source)
```

Why check(blocked, target, source)? e.g.: this test case should be Fasle

[[10,9],[9,10],[10,11],[11,10]]
[0,0]
[10,10]

## 拓扑排序 Topological Sorting

- 入度 (In-degree): 有向图 (Directed Graph) 中指向当前节点的边的条数

- Topological Sorting 不是传统的排序算法: 一个图可能存在多个 or 不存在拓扑序

算法描述 Topological Sorting

- 统计每个点的 In-degree

- 将每个入度为 0 的点放入队列 Queue 中作为起始节点

- 不断从队列中拿出一个点: 去掉这个点的所有指向其他点的边, i.e. 其他点相应入度 - 1

- 一旦发现新的入度为 0 的点 ⇒ 丢回队列中

> Q: Topological Sorting

##### BFS 拓扑排序

```python
def topSort(self, graph):
    indegree_list = {x: 0 for x in graph}
    for node in graph:
        for neighbor in node.neighbors:
            indegree_list[neighbor] += 1
    
    order = []
    zero_indegree_nodes = [x for x in graph if indegree_list[x] == 0]
    queue = collections.deque(zero_indegree_nodes)
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in node.neighbors:
            indegree_list[neighbor] -= 1 
            if indegree_list[neighbor] == 0:
                queue.append(neighbor)
    return order
```

##### DFS 拓扑排序

```python
def topSort(self, graph): 
    indegree_list = {x: 0 for x in graph}
    for node in graph:
        for neighbor in node.neighbors:
            indegree_list[neighbor] += 1
        
    order = []
    for this_node in graph:
        if indegree_list[this_node] == 0:
            self.dfs(this_node, indegree_list, order)
    return order
    
def dfs(self, node, indegree_list, order):
    order.append(node)
    indegree_list[node] -= 1  # ==> -1, so no duplicate add to order
    for neighbor in node.neighbors:
        indegree_list[neighbor] -= 1
        if indegree_list[neighbor] == 0:
            self.dfs(neighbor, indegree_list, order)
```

> Q: Course Schedule | submission

> Q: Course Schedule II | submission | Note: return order[::-1]

#### > Q: Alien Dictionary

考点1：如何构建图

考点2：如何存储图

考点3：如何拓扑排序

相似问题: Sequence Reconstruction: 序列重构 (判断是否只有一个拓扑排序)

## 双向 Bi-directional BFS

(ctrl+f)

# DFS

DFS early reture / 剪枝:

DFS 达到指数级别时才需要考虑 early return。否则徒增代码复杂度。

BFS / Binary Search 则不需要剪枝考虑。

搜索 \ 回溯 \ 遍历 \ 分治 \ 迭代

![](/notes/leetcode/media/image3.png)

## 二叉树 DFS

- 第一类：求值 / 求路径 | e.g.: Subtree with Maximum Average

- 第二类：结构变化 | e.g.: Invert Binary Tree

- 第三类：二叉查找树 | e.g.: Valid BST / Validate Binary Search Tree

  - 非递归 (Non-recursion or Iteration) 版本的中序遍历 (Inorder Traversal)

### 题型 1: 二叉树求值 / 路径

Maximum / Minimum / Average / Sum / Paths

Easy Level Practices

> Q: Binary Tree Maximum Node

> Q: Minimum Subtree | submission | 求和最小的子树

> Q: Subtree with Maximum Average

> Q: Binary Tree Paths | DFS / DFS non-recursion / BFS | 求从 root 到叶 leaf 的所有路径

#### > Q: Lowest Common Ancestor of a Binary Tree *

```python
def lowestCommonAncestor(self, root, p, q):
    if root == p or root == q: 
        return root

    left = right = None
    if root.left: 
        left = self.lowestCommonAncestor(root.left, p, q)
    if root.right:
        right = self.lowestCommonAncestor(root.right, p, q)

    if left and right:
        return root
    else:
        return left or right
```

Follow up: 

> Q: Lowest Common Ancestor II | w/ parent pointer

> Q: Lowest Common Ancestor III | LCA is not gauranteed to exist

⇒ LCA 在 BST 上可以 iterative 求解

> Q: Lowest Common Ancestor of a Binary Search Tree: Iteration & Recursion

```python
def lowestCommonAncestor(self, root, p, q):
    while root:
        if p.val < root.val and q.val < root.val:
            root = root.left
        elif p.val > root.val and q.val > root.val:
            root = root.right
        else:
            return root
```

> Q: Smallest Subtree with all the Deepest Nodes | submission

> Q: Maximum Binary Tree

### 题型 2: 二叉树结构变化

> Q: Invert Binary Tree (easy)

#### > Q: Flattern Binary Tree to Linked List *

(submission): DFS

```python
def flatten(self, root: TreeNode) -> None:
    last = TreeNode(-1)
    stack = [root]
    while stack:
        node = stack.pop()
        last.right = node
        last.left = None  # ATTENTION: clear previous connections
        if node and node.right:
            stack.append(node.right)
        if node and node.left:
            stack.append(node.left)
        last = node
```

(submission): DFS Recursion

```python
class Solution:
    last_node = None
    def flatten(self, root: TreeNode) -> None:
        if root is None:
            return

        if self.last is not None:
            self.last.left = None
            self.last.right = root
            
        self.last = root
        right = root.right
        self.flatten(root.left)
        self.flatten(right)
```

### 题型 3: 二叉查找树 BST

#### > Q: Kth Smallest Element in BST *

solution: Recursion / Iteration

解法 1: Recursion

```python
def kthSmallest(self, root: TreeNode, k: int) -> int:
    stack = []
    while root or stack:
        while root:
            stack.append(root)
            root = root.left

        node = stack.pop()
        k -= 1
        if k == 0:
            return node.val
        root = node.right
```

解法 2: Iteration

```python
class Solution:
    def kthSmallest(self, root: TreeNode, k: int) -> int:
        self.k = k
        self.kth = None
        self.dfs(root)
        return self.kth.val
    
    def dfs(self, node):
        if node  == None: 
            return 
        
        self.dfs(node.left)
        self.k -= 1
        if self.k == 0:
            self.kth = node
            return
        self.dfs(node.right)
```

#### > Q: Validate BST

Validate Binary Search Tree: solution by leetcode

思路: 核心思想是遍历过程中维持 lower & upper 的值

注意: 中序遍历每次只 check 每个 node 左右值是否符合是不可以的: failed submission

解法 1: Recursion

```python
def isValidBST(self, root):
    def helper(node, lower, upper):
        if not node:
            return True

        val = node.val
        if val <= lower or val >= upper:
            return False
        if not helper(node.left, lower, val):
            return False
        if not helper(node.right, val, upper):
            return False
        return True

    return helper(root, float('-inf'), float('inf'))
```

解法 2: DFS

```python
def isValidBST(self, root):
    if not root:
        return True

    stack = [(root, float('-inf'), float('inf'))] 
    while stack:
        root, lower, upper = stack.pop()
        if not root:
            continue
        val = root.val
        if val <= lower or val >= upper:
            return False
        stack.append((root.right, val, upper))
        stack.append((root.left, lower, val))
    return True 
```

> Q: Closest Binary Search Tree Value

#### > Q: Binary Search Tree Iterator **

访问所有节点用时 O(n) ⇒ 均摊下来访问每个节点的时间复杂度时 O(1) | 三种 solutions

```python
# Find next node:
# if node.right != None: next 是右子树中最左边的那个点
# if node.right == None: next 是走到当前点的路径中 last 左拐的点: stack.pop

class BSTIterator:
    def __init__(self, root):
        self.stack = []
        self.curr = root

    def hasNext(self):
        return self.curr is not None or len(self.stack) > 0

    def next(self):
        while self.curr is not None:
            self.stack.append(self.curt)
            self.curr = self.curr.left
            
        self.curr = self.stack.pop()
        nxt = self.curr
        self.curr = self.curt.right
        return nxt
```

Follow up: 

- 树与分治法 (ctrl+f)

- Closest Binary Search Tree Value II (ctrl+f)

### Traversal (Pre/In/Post-Order)

BFS: level-order traversal \ DFS: pre/in/post-order traversal

#### > Q: Binary Tree Preorder Traversal

solution @2019.09.01

```python
# Recursive Solution
class Solution:
    def preorderTraversal(self, root):
        self.order = list()
        self.traverse(root)
        return self.order
        
    def traverse(self, node):
        if node == None:
            return
        self.order.append(node.val)
        self.traverse(node.left)
        self.traverse(node.right)

# Non-Recursive Solution
class Solution:
    def preorderTraversal(self, root):
        if root == None:
            return []
        stack = [root]
        order = []
        while stack:
            current = stack.pop()
            order.append(current.val)
            if current.right:
                stack.append(current.right)
            if current.left:
                stack.append(current.left)
        return order
```

0067. Binary Tree Inorder Traversal (easy) @2019.09.01

0068. Binary Tree Postorder Traversal (easy) @2019.09.01

DFS solution: return order[::-1]

#### > Q: Binary Tree Vertical Order Traversal

```python
def verticalTraversal(self, root: TreeNode) -> List[List[int]]:
    if root == None: return []
    seen = collections.defaultdict(
              lambda: collections.defaultdict(list))

    def dfs(node, col=0, row=0):
        if node:
            seen[col][row].append(node)
            dfs(node.left, col - 1, row + 1)
            dfs(node.right, col + 1, row + 1)

    dfs(root)
    ans = []
    for col in sorted(seen):
        report = []
        for row in sorted(seen[col]):
            report.extend(sorted(node.val for node in seen[col][row]))
        ans.append(report)
    return ans
```

## 组合 Combination

#### > Q: Subsets

```python
class Solution:
    def subsets(self, nums):
        self.res = []
        self.dfs(sorted(nums), [], 0) # sort required
        return self.res
    
    def dfs(self, nums, subset, i):
        if (i == len(nums)):
            self.res.append(subset)
            return

        self.dfs(nums, subset + [nums[i]], i + 1) 
        self.dfs(nums, subset + [], i + 1)
```

```python
class Solution:
    def subsets(self, nums: List[int]) -> List[List[int]]:
        self.res = []
        self.dfs(sorted(nums), [])
        return self.res

    def dfs(self, nums, subset):
        if len(nums) == 0:
            res.append(subset)
            return

        self.dfs(nums[1:], subset + [nums[0]])
        self.dfs(nums[1:], subset)
```

#### > Q: Combination Sum

```python
class Solution:
    def combinationSum(self, candidates, target):
        self.res = []
        # Case: [2,2,3], 5
        self.dfs(sorted(list(set(candidates))), [], target)
        return self.res

    def dfs(self, candidates, subset, target):
        if sum(subset) > target:
            return
        if sum(subset) == target:
            self.res.append(subset)
            return
        for i in range(len(candidates)):
            self.dfs(candidates[i:], subset + [candidates[i]], target)
```

⇒ 更快解法参考如下: 利用 pruning 优化

> Q: Combination Sum | submission | sum up to Target 可以重复使用元素

> Q: Combination Sum II | submission | sum up to Target 不可重复使用元素

> Q: Combination Sum III | submission | k 个 sum up to Target

> Q: Combination Sum IV

Requires DP: solusion

```python
def combinationSum4(self, nums: List[int], target: int) -> int:
    combs = [1] + [0] * (target)
    for i in range(target + 1):
        for num in sorted(nums):
            if i < num: break
            combs[i] += combs[i - num]
    return combs[-1]
```

> Q: Split String 

#### > Q: Palindrome Partitioning *

```python
class Solution:
    def partition(self, s):
        if not s: return [] 
        return self.help(s, {})
    
    def help(self, s, memo):
        if not s: return [[]]
        # if s in memo: return memo[s]
        
        res = []
        for i in range(1, len(s) + 1):
            prefix = s[:i]
            if prefix == prefix[::-1]:
                parts = self.help(s[i:], memo)
                for part in parts:
                    res.append([prefix] + part)
        
        # memo[s] = res
        return res
```

⇒ 如上可利用两行 memo 记忆化搜索优化

## 记忆化搜索 Memoization Search

通用 DFS 时间复杂度: O(答案个数 * 构造每个答案的时间)

记忆化搜索

- 方法: 将函数的计算结果保存下来. 下次通过访问同样的参数时直接返回保存的结果

- 作用: 通常能够将指数级别的时间复杂度降低到多项式级别

#### > Q: Wildcard Matching

(ctrl+f in DP): solution

Follow up: 

> Q: Regular Expression Matching

> Q: Word Break II: ctrl+f

## 排列 Permutation

> Q: Permutations

```python
def permute(self, nums):
    def dfs(nums, path, res):
        if len(nums) == 0:
            res.append(path)
        for i in range(len(nums)):
            dfs(nums[:i] + nums[i + 1:], path + [nums[i]], res)

    res = []
    dfs(nums, [], res)
    return res
```

> Q: Permutations II: nums 中有重复元素

```python
def permuteUnique(self, nums: List[int]) -> List[List[int]]:
    def dfs(nums, path, res):
        if len(nums) == 0:
            res.append(path)
        for i in range(len(nums)):
            if i > 0 and nums[i] == nums[i - 1]:  # 在此处理重复元素即可
                continue
            dfs(nums[:i] + nums[i + 1:], path + [nums[i]], res)

    res = []
    dfs(sorted(nums), [], res)
    return res
```

> Q: String Permutation II

> Q: N Queens

> Q: N Queens II: 问方案总数

> Q: Letter Combinations of Phone Number (ctrl+f)

## 图 Graph-based DFS

> Q: Word Ladder II: ctrl+f

> Q: Word Search II: ctrl+f in Trie / Prefix Tree

#### > Q: Word Pattern II

```python
class Solution:
    def wordPatternMatch(self, pattern, string):
        return self.dfs(pattern, string, {}, set())

    def dfs(self, pattern, string, mapping, used):
        if not pattern:
            return not string
            
        char = pattern[0]
        if char in mapping:
            word = mapping[char]
            if not string.startswith(word):
                return False
            return \
            self.dfs(pattern[1:], string[len(word):], mapping, used)
            
        for i in range(len(string)):
            word = string[:i + 1]
            if word in used:
                continue
            
            used.add(word)
            mapping[char] = word
            
            if self.dfs(pattern[1:], string[i + 1:], mapping, used):
                return True
            
            del mapping[char]
            used.remove(word)
            
        return False
```

## Problems

> Q: Concatenated Words

解法 1: DFS recursion: submission

```python
def findAllConcatenatedWordsInADict(self, words: List[str]) -> List[str]:
    d = set(words)

    def dfs(word):
        for i in range(1, len(word)):
            prefix = word[:i]
            suffix = word[i:]

            if prefix in d and suffix in d:
                return True
            if prefix in d and dfs(suffix):
                return True
            if suffix in d and dfs(prefix):
                return True

        return False

    res = []
    for word in words:
        if dfs(word):
            res.append(word)

    return res
```

解法 2: DFS iteration solution

解法 3: Trie (ctrl+f)

# Queue \ Deque

Queue 支持操作: O(1) Push / O(1) Pop / O(1) Top 

Queue 队列的基本作用是用于做 BFS

Deque 双端队列: 两端都会有 push 和 pop

> Q: Sliding Window Average from Data Stream / Moving Average from Data Stream (easy)

> Q: Sliding Window Maximum (Deque)

> Q: Sliding Window Median (Heap + Hash) (ctrl+f)

> Q: Sliding Window Unique Element Sum (Hash)

#### > Q: Sliding Window Maximum

Deque 比 DP 更高效

+ 解法 1: Deque (submisson)

- 时间 O(n): since each element is processed exactly twice - it's index added and then removed from the deque.

- 空间 O(n): since O(n - k + 1) is used for an output array and O(k) for a deque.

```python
def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
    if len(nums) == 0:
        return None

    deq = deque()
    res = []

    def update(i):
        # remove indexes of elements not from sliding window
        if deq and deq[0] == i - k:
            deq.popleft()

        # remove from deq indexes of all elements 
        # which are smaller than current element nums[i]
        while deq and nums[i] > nums[deq[-1]]:
            deq.pop()

    # Process the first k elements separately to initiate the deque.
    for i in range(k):
        update(i)
        deq.append(i)

    res.append(nums[deq[0]])

    for i in range(k, len(nums)):
        update(i)
        deq.append(i)
        res.append(nums[deq[0]])
    return res
```

+ 解法 2: DP (submisson)

- 时间 O(n): since all we do is 3 passes along the array of length N.

- 空间 O(n): to keep left and right arrays of length N, output array of length N - k + 1.

![](/notes/leetcode/media/image4.png)

```python
def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
    n = len(nums)
    if n == 0:
        return None

    left = [nums[0]] + [0] * (n - 1)
    right = [0] * (n - 1) + [nums[-1]]
    for i in range(1, n):
        # from left to right
        if i % k == 0:
            # block start
            left[i] = nums[i]
        else:
            left[i] = max(left[i - 1], nums[i])

        # from right to left
        j = n - i - 1
        if (j + 1) % k == 0:
            # block end
            right[j] = nums[j]
        else:
            right[j] = max(right[j + 1], nums[j])

    res = []
    for i in range(n - k + 1):
        res.append(max(right[i], left[i + k - 1]))
    return res
```

# Stack

支持操作: O(1) Push / O(1) Pop / O(1) Top

非递归实现 DFS 的主要数据结构

## Monotone Stack

> Q: Max Stack

> Q: Min Stack

+ 解法 1: Stack of [Value, Min] Pairs: submission

![](/notes/leetcode/media/image5.png)

![](/notes/leetcode/media/image6.png)

+ 解法 2: Two Stacks: submission

![](/notes/leetcode/media/image7.png)

+ 解法 3: Improved Two Stacks: submission

![](/notes/leetcode/media/image8.png)

## Problems

> Q: Next Greater Element I *: solution

> Q: Next Greater Element II

> Q: Next Greater Element III

| 2 | 3 | 5 | 1 | 0 | *7* | 3 |
| --- | --- | --- | --- | --- | --- | --- |

e.g.: at 7, stack = (bottom) [5, 1, 0] (top), then since

0 < 7, pop() ⇒ [0, 7]

1 < 7, pop() ⇒ [1, 7]

5 < 7, pop() ⇒ [5, 7]

> Q: Online Stock Span

Solution: to maintain a weighted stack of decreasing elements. The size of the weight will be the total number of elements skipped. 

e.g.: 11, 3, 9, 5, 6, 4, 7 ⇒ (11, weight=1), (9, weight=2), (7, weight=4).

> Q: Smallest Subsequence of Distinct Characters

TODO

Minimum Cost Tree From Leaf Values

Sum of Subarray Minimums

Online Stock Span

Score of Parentheses

Next Greater Element II

Next Greater Element I

Largest Rectangle in Histogram

Trapping Rain Water

# Hash

> Counter ⇒ Hash Table 

```python
from collections import Counter
hashmap = Counter(nums)
```

> Q: LRU Cache

解法 1: Double Linked list + hash map

解法 2: Singly Linked list + hash map

linked list -- 最近使用过的放在最后

存的是（key, value），next

hash map -- key --> 前一个linked node

get : 如果 key 在 hashmap 中不存在， 说明没有对应值， return -1

如果存在，通过hashmap 找出前一个linked node,

再找出 current linked node，

通过 prev 将 current 放到linked list 的最后

return current.value

set： 如果 key 在 hashmap 中存在， 说明已有对应值，

放到linked list最后

overwrite value

return

如果不存在，直接将 新的linkednode 放在最后

如果超过 capacity， pop 将第一个 node删除（least frenquently used）

> Q: Insert Delete GetRandom O(1): solution: HashMap + Array <==> Q: Load Balancer

> Q: Insert Delete GetRandom O(1) - Duplicates allowed (hard): TODO

> Q: First Unique Number in Data Stream: solution 允许遍历两次

> Q: First Unique Number in Data Stream II: solution (LinkedList + HashMap) 只许遍历一次

[tag] Data Stream Problems 

## Problems

> Q: Valid Anagram (easy)

> Q: Subarray Sum (easy) ⇒ Follow-up: Continuous Subarray Sum * (ctrl+f)

> Q: Copy List with Random Pointer

> Q: Longest Consecutive Sequence: submission: HashSet

> Q: Contiguous Array: solution

> Q: Longest Substring Without Repeating Characters: O(2n) HashSet / O(n) HashMap

# Heap \ Priority Queue

支持操作: O(1) Min/Max / log(n) Push / log(n) Pop

构建一个 heap 时间 O(n)

遍历一个 heap 时间 O(nlogn)

- 作为 array O(n) 遍历 heap 无法保证有序性 ⇒ 需要逐一 pop 遍历 heap ⇒

- 复杂度为 ShiftUp Heapify 的 O(nlogn)

作为数组 heap 的下标转换:

- Parent: n ⇒ Children: 2n + 1, 2n + 2

- Child: n ⇒ Parent floor(n / 2), i.e.: n - 1 // 2

## 线性时间构建 Heap

@reference / illustration

Trivial Analysis: Each call to heapify requires log(n) time, we make n such calls ⇒ O(n log n).

Tighter Bound: Each call to heapify requires time O(h) where h is the height of node i ⇒ O(n)

![](/notes/leetcode/media/image9.png)

Note: sum n · (1/2)n = (1/2) / (1 - (1/2))2 = 2

### Heapify: Shift Up O(nlogn)

```python
def shiftup(A, k):
    while k != 0:
        parent = (k - 1) // 2
        if A[k] > A[parent]:
        	break
        A[k], A[parent] = A[parent], A[k]
        k = parent

def heapify(A):
    for i in range(len(A)):
        shiftup(A, i)
```

算法思路

- 对于每个元素 A[i] 与它的父结点比大小: 如果小于父结点 ⇒ 与父结点交换

- 重复上述操作直至该点的值大于父亲

算法时间复杂度 O(nlogn)

- 对于每个元素都要遍历一遍 O(n)

- 每一个元素最多需要向根部方向交换 logn 次; 且至少底层 O(n/2) 个元素需要 O(logn)

⇒ O(nlogn) 是 tight bound

### Heapify: Shift Down O(n)

```python
def shiftdown(A, k):
    while k * 2 + 1 < len(A):
    	# Choose the min of two children
        child = k * 2 + 1
        if k * 2 + 2 < len(A) and A[child] > A[k * 2 + 2]:
            child = k * 2 + 2
        # Switch with the min child if the child is smaller
        if A[k] <= A[child]:
            break
        A[k], A[child] = A[child], A[k]
        k = child

def heapify(A): 
    for i in range(len(A) - 1, -1, -1):
        shiftdown(A, i)
```

算法思路

- 与其两个子节点中较小的一个比较: 若大于子节点 ⇒ 与子节点交换。

- 重复上述操作直至该点的值小于两个子节点 or 没有子节点

算法时间复杂度 O(n)

- 类似如上分析的 O(nlogn) 不是 tight bound ⇒ O(n) 解析如下

算法从第 n / 2 个数开始倒过来进行 siftdown i.e.: 相当于从 heap 的倒数第二层开始.

- 倒数第二层节点数 O(n / 4) 个且最多 siftdown 1 次就到底了 ⇒ O(n / 4)

- 倒数第三层节点数 O(n / 8) 个且最多 siftdown 2 次就到底了 ⇒ O(n / 8 * 2)

- 倒数第四层  ⇒ O(n / 16 * 3)

- 倒数第五层  ⇒ O(n / 32 * 4)

- …..

T(n) = O(n/4) + O(n/8 * 2) + O(n/16 * 3) ...

用 2T - T 得到

```
2 * T(n) = O(n/2) + O(n/4 * 2) + O(n/8 * 3) + O(n/16 * 4) ... 
    T(n) =          O(n/4)     + O(n/8 * 2) + O(n/16 * 3) ...

2 * T(n) - T(n) = O(n/2) +O (n/4) + O(n/8) + ...
                = O(n/2 + n/4 + n/8 + ... )
                = O(n)
```

因此得到 T(n) = 2 * T(n) - T(n) = O(n)

## 删除 / 插入操作实现

```
// 删除节点
public int Poll(){
    int top = A[0];
    swap(0, heapSize-1);  // 交换第一个和最后一个节点
    heapSize--;
    heapify(0);  // ShiftDown 维护
    return top;
}
```

https://marian5211.github.io/2017/11/18/%E3%80%90%E4%B9%9D%E7%AB%A0%E7%AE%97%E6%B3%95%E5%BC%BA%E5%8C%96%E7%8F%AD%E3%80%91%E5%A0%86Heap/

https://stomachache007.wordpress.com/2017/04/09/title2-2/#more-923

https://blog.csdn.net/BTUJACK/article/details/84190018

## Problems

> Q: Ugly Number II

+ 解法 1: HashMap + Heap ⇒ O(nlogn)

+ 解法 2: 三指针 solution ⇒ O(n)

> Q: Find Median from Data Stream (hard)

解法 1: 每次排序寻找中位数: O(n2logn)

解法 2: 类似插入排序寻找中位数: O(n2)

解法 3: K 个数的中位数需要知道第 K/2 小和第 K/2 大 ⇒ 最大堆 + 最小堆: solution

- 动态维护中位数一般都是用双堆解决

- 同理: 动态维护第 K 大数

> Q: Sliding Window Median (Heap + Hash): solution

> Q: Trapping Rain Water 2 (hard)

# Union Find

支持集合快速合并和查找操作: O(1) 合并两个集合 & O(1) 查询元素所属集合

- 查询两个元素是否在同一个集合内

- 合并两个元素所在的集合

- 查询某个元素所在集合的元素个数 (派生操作) ？？？

- 查询当前集合个数 (派生操作)

问: 并查集会不会出现环 (e.g.: A → B → C → A) ?

答: 不会. 因为检测到 root 相同就不会再增加连通操作

Example: 

> Q: Connecting Graph III / Number of Connected Components in an Undirected Graph

![](/notes/leetcode/media/image10.png)

```python
class QuickUnion(object):
    parents, count = {}, 0
    def __init__(self, nums):
        self.count = len(nums)
        self.parents = {x: x for x in nums}

    def connected(self, p, q):
        return self.find(p) == self.find(q)

    def find(self, p):
        if p == self.parents[p]:
            return p
        self.parents[p] = self.find(self.parents[p])  # path compression
        return self.parents[p]
    
    def union(self, p, q):
        if not self.connected(p, q):
            parent_q = self.find(q)
            parent_p = self.find(p)
            self.parents[parent_p] = parent_q
            self.count -= 1

qf = QuickUnion([x for x in range(10)])
edges = [(4,3), (3,8), (8,9), (9,4),
         (6,1), (6,5), (6,7), (2,1), (7,2), (5,0)]
for edge in edges:
    qf.union(edge[0], edge[1])
print("root %s" % (",").join(str(y) for x, y in qf.parents.items()))
print("count of components is: %d" % qf.count)
```

## Path Compression

```python
def find(self, p):
    while p != self.parents[p]:
        p = self.parents[p]
    return p

## With Path Compression: 将 find 过程中经过的 path 上点都指向最终 parent p
# Method 1:
def find(self, p):
    if p == self.parents[p]:
        return p
    self.parents[p] = self.find(self.parents[p])
    return self.parents[p]

# Method 2:
def find(self, p):
    path = []
    while p != self.parents[p]:
        p = self.parents[p]
        path.append(p)
    # path compression
    for x in path:
        self.parents[x] = p
    return p

# Method 3:
def find(self, p):
    x = p
    while (p != self.parents[p]):
        p = self.parents[p]
    # path compression
    while x != p:
        px = self.parents[x]
        self.parents[x] = p
        x = px
    return p
```

## Problems

> Q: Number of Islands II

解法 1: BFS (ctrl+f) 

解法 2: Union Find

```python
class Solution:
    def numIslands2(self, m, n, positions):
        ans = []
        islands = Union()
        for p in map(tuple, positions):
            if islands.add(p):
                for dx, dy in (0, 1), (0, -1), (1, 0), (-1, 0):
                    q = (p[0] + dx, p[1] + dy)
                    if q in islands.id:
                        islands.unite(p, q)
            ans += [islands.count]
        return ans

class Union(object):
    def __init__(self):
        self.id = {}
        self.sz = {}
        self.count = 0

    def add(self, p):
        if p in self.id.keys():  # Case: 3, 3, [[0,0],[0,1],[1,2],[1,2]]
            return False
        self.id[p] = p
        self.sz[p] = 1
        self.count += 1
        return True

    def root(self, i):
        while i != self.id[i]:
            self.id[i] = self.id[self.id[i]]
            i = self.id[i]
        return i

    def unite(self, p, q):
        i, j = self.root(p), self.root(q)
        if i == j:
            return
        self.id[i] = j
        self.sz[j] += self.sz[i]
        self.count -= 1
```

> Q: Frinds Circles

解法 1: DFS: solution

解法 2: Union Find 一种简化不需要定义 class 的写法

```python
def findCircleNum(self, M):
    def find(node):
        if circles[node] == node: return node
        circles[node] = find(circles[node])
        return circles[node]

    n = len(M)
    circles = {x: x for x in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            if M[i][j] == 1 and find(i) != find(j):
                circles[find(i)] = find(j)   

    return sum([1 for k, v in circles.items() if k == v])
```

> Q: Graph Valid Tree: solution

> Q: Surrounded Regions

> Q: Evaluate Division

BFS: https://leetcode.com/problems/evaluate-division/discuss/88275/Python-fast-BFS-solution-with-detailed-explantion

UF:

https://leetcode.com/problems/evaluate-division/discuss/255407/Python-Union-Find

https://leetcode.com/problems/evaluate-division/discuss/344568/Python-Union-Find

# Trie / Prefix Tree

插入和查询操作同时完成 ⇒ 查询的时间复杂度简化为 O(len of word), i.e. O(1).

## Trie v.s. Hash

Trie 的优势就在于时间复杂度. Hash 表号称 O(1) 但在计算 hash 的时候就肯定会是 O(len of key), 而且还有 collisions 问题. Trie 的缺点是空间消耗很高.

|  | Hash Table | Trie |
| --- | --- | --- |
| 查找时间复杂度 | O(1) | O(1) |
| 空间复杂度 | worse | better |

对于 a, aa, aaa, aaaa 的情况

|  | Hash Table | Trie |
| --- | --- | --- |
| 存储 | 10 个 a | 5 个节点 (根节点 + 4 个 a) |
| 可用操作 | 有/无/查询 | 有/无查询 + 前缀查询 |
| 代码量 | 1 行 | 75 ~ 100 行 |

所以选择 hash 原因是代码量小. 但是涉及到前缀查询的时候, 考虑 Trie 树.

> 什么时候更适合用 Trie 树?

一个一个字符串遍历的时候 \ 需要节约空间 \ 查找前缀

> Compressed Trie: reference

## Trie Implementation & Design

> Q: Implement Trie (Prefix Tree): 实现一个前缀树的基础题

方法 1: 用特殊字符标注单词结尾: submission

```python
class Trie:
    def __init__(self):
        self.trie = {}
 
    def insert(self, word: str) -> None:
        node = self.trie
        for c in word:
            if c not in node:
                node[c] = {}
            node = node[c]
            # 3 lines above equal to: node = node.setdefault(c, {})
        node["#"] = "#"

    def search(self, word: str) -> bool:
        node = self.trie
        for c in word:
            if c not in node:
                return None
            node = node[c]
        return "#" in node

    def startsWith(self, prefix: str) -> bool:
        return self.search(prefix) is not None
```

方法 2: 定义 Trie Node class: submission

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_word = False
        
class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        # Inserts a word into the trie.
        node = self.root
        for c in word:
            if c not in node.children:
                node.children[c] = TrieNode()
            node = node.children[c]
        node.is_word = True
        
    def search(self, word: str) -> bool:
        # Returns if the word is in the trie.
        node = self.root
        for c in word:
            node = node.children.get(c)
            if node is None:
                return None
        return node.is_word

    def startsWith(self, prefix: str) -> bool:
        # Returns if there is any word in the trie starts with prefix.
        return self.search(prefix) is not None
```

> Q: Add and Search Word - Data structure design: 把前缀树做一个简单的变形 (DFS + Trie)

> Q: Wild Card Match @谷歌面经题

e.g.: filter = [he*o, a*p] 那么 ‘hello’ 和 ‘heo’ 满足第一个 filter. ‘＊’ 可以 match 任何数量的字母.

Trie 变形: 把 word 当做 trie 节点, concatenated word 当做 path. i.e. 之前 char 对应这里 word, 之前 word 对应这里 concatenated word ⇒ 

> Q: Concatenated Words

解法 1: DFS recursion: submission (ctrl+f)

解法 2: DFS iteration solution

解法 3: Trie: solution

## Implicit Trie

> Q: Number of Matching Subsequences

解法 1: Binary Search

解法 2:  Implicit / Lazy Trie

时间: O(M + N). N is the length of S, and M is the sum of words' length.

空间: O(M)

```python
def numMatchingSubseq(self, S: str, words: List[str]) -> int:
    heads = collections.defaultdict(list)
    for w in words:
        heads[w[0]].append(iter(w[1:]))
    for c in S:
        if c in heads:
            for itr in heads.pop(c):
                heads[next(itr, None)].append(itr)
    return len(heads[None])
```

## Problems

#### > Q: Word Search II

![](/notes/leetcode/media/image11.png)

```python
def findWords(self, board, words):
    WORD_KEY = '$'

    trie = {}
    for word in words:
        node = trie
        for char in word:
            # retrieve the next node; If not found, create a empty node.
            node = node.setdefault(char, {})
        # mark the existence of a word in trie node
        node[WORD_KEY] = word

    rowNum, colNum = len(board), len(board[0])
    res = []

    def backtracking(x, y, parent):    
        char = board[x][y]
        node = parent[char]

        # check if we find a match of word
        word_match = node.pop(WORD_KEY, False)
        if word_match:
            # also we removed the matched word to avoid duplicates,
            # as well as avoiding using set() for results.
            res.append(word_match)

        # Before the EXPLORATION, mark the cell as visited, 
        # otherwise, counterexample: [["a","a"]], ["aaa"], should ret []
        board[x][y] = '#'

        # Explore the neighbors in 4 directions
        for (dx, dy) in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            x_new = x + dx
            y_new = y + dy     
            if not 0 <= x_new < rowNum or not 0 <= y_new < colNum:
                continue
            if not board[x_new][y_new] in node:
                continue
            backtracking(x_new, y_new, node)

        # End of EXPLORATION, we restore the cell
        board[x][y] = char

        # Optimization: incrementally remove matched leaf node in Trie.
        if not node:
            parent.pop(char)

    for x in range(rowNum):
        for y in range(colNum):
            if board[x][y] in trie:
                backtracking(x, y, trie)

    return res
```

![](/notes/leetcode/media/image12.png)

#### > Q: Index Pairs of a String

```
"""
Given a text string and words (a list of strings), return all index pairs [i, j] so that the substring text[i]...text[j] is in the list of words. e.g.: 
Input: text = "ababa", words = ["aba","ab"]
Output: [[0,1],[0,2],[2,3],[2,4]]

Notice that matches can overlap, see "aba" is found in [0,2] and [2,4].
"""
```

解法 1: brute-force

```python
def indexPairs(self, text: str, words: List[str]) -> List[List[int]]:
    res = []
    for word in words:
        wordLen = len(word)
        for i in range(len(text) - wordLen + 1):
            if word == text[i:i+wordLen]:
                res.append([i, i + wordLen - 1])
```

解法 2: trie (复杂度与 brute-force 相同). 此题用 trie 并无优势.

```python
def solution(text, words):
    trie = {}
    # construct trie
    for word in words:
        node = trie
        for l in word:
            if l not in node:
                node[l] = {}
            node = node[l]
        node['#'] = '#'  # indicates the end of word

    # starting from each char of text      
    res = []
    for i in range(len(text)):
        node = trie
        # search words in the trie
        for j in range(i, len(text)):
            if text[j] in node:
                node = node[text[j]]
                if '#' in node:
                    res.append((i, j))
            else:
                break
    return res
```

> Q: Maximum XOR of Two Numbers in an Array

> Q: Map Sum Pairs: submission

> Q: Word Squares: ctrl+f

# Sweep Line

@九章算法强化班 lec 04 @2020.03.18

问题特点

- 事件往往是以区间的形式存在

- 区间两端代表事件的开始和结束

- 按照区间起点排序, 起点相同的按照终点排序

扫描线法 / Sweep Line

- 定义计数器 C = 0

遇到事件开始: C += 1

遇到事件结束: C -= 1

- C 的最大值即为答案

> Q: Max Increase to Keep City Skyline | submission (ctrl+f)

> Q: Meeting Rooms <==> Merge Intervals (ctrl+f)

> Q: Meeting Rooms II <==> Number of Airplanes in the Sky (ctrl+f)

```python
def countOfAirplanes(self, intervals):
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

#### > Q: Smallest Rotation with Highest Score *

@Google AI Residency 2019 @2020.03.16

可以直接转换成基本扫描线问题 by explanation | clean explanation | submission 

TODO

#### > Q: The Skyline Problem

Explanation / Illustration: the last figure

- Sweep line naive & detailed edge cases notes: submission @2020.03.18

- Sweep line + priority queue: solution

```python
def getSkyline(self, buildings: List[List[int]]) -> List[List[int]]:
    # All possible key points
    positions = set([b[0] for b in buildings]+[b[1] for b in buildings])

    sky = [[-1,0]]  # sentinel
    active = []  # active buildings at pos
    i = 0
    for pos in sorted(positions):
        # Add the new buildings whose left side is lefter than pos
        while i < len(buildings) and buildings[i][0] <= pos:
            heappush(active, (-buildings[i][2], buildings[i][1]))
            i += 1

        # Remove the past buildings whose right side is lefter than pos
        while active and active[0][1] <= pos:
            heappop(active)

        # Pick the highest existing building at this moment
        height = -active[0][0] if active else 0
        if sky[-1][1] != height:
            sky.append([pos, height])

    return sky[1:]
```

# Dynamic Programming

- DP 基本流程: 确定状态 ⇒ 设计状态转移方程 ⇒ 确定初始态边界 ⇒ 按照一定顺序计算

- python 2D array:

a = [[0] * m for i in range(n)]

- DP 时间复杂度和什么有关

✅状态的数量

✅状态转移的代价

❌计算顺序

❌初始边界的数量

# Graph

Graph Theory Overview Playlist by William Fiset @2019.08.29

## BFS v.s. DFS (basics)

### BFS v.s. DFS Illustration

@2019.08.26

```
        0
       / \
      1   2               # BFS: 0 → 1 → 2 → 3 → 4 → 5 → 6
     /   / \
    3   4   5             # DFS: 0 → 2 → 5 → 4 → 6 → 1 → 3
       /
      6
```

BFS by Imagineer

```
    while queue:
        current = queue.pop()
        for neighbor in adjacencyList[current]:
            if not neighbor in visitedList:
                queue.insert(0, neighbor)
        visitedList.append(current)
    return visitedList
```

DFS by Imagineer

```
    while stack:
        current = stack.pop()
        for neighbor in adjacencyList[current]:
            if not neighbor in visitedVertex:
                stack.append(neighbor)
        visitedVertex.append(current)
    return visitedVertex
```

Major differences: queue 从头弹出 (更早插入的) v.s. stack 从尾弹出 (更后插入的)

### BFS v.s. DFS for Binary Tree

BFS v.s. DFS for Binary Tree from GeeksforGeeks @2019.08.26

- Breadth First Traversal (Or Level Order Traversal)

- Depth First Traversals

  - Inorder Traversal (Left-Root-Right)

  - Preorder Traversal (Root-Left-Right)

  - Postorder Traversal (Left-Right-Root)

![](/notes/leetcode/media/image13.png)

Inorder:
12 → 25 → 27 → 33 → 34 → 39 → 48 → 52 → 60 → 65 → 72 → 78 → 90
Postorder: 
12 → 27 → 25 → 34 → 48 → 39 → 33 → 60 → 72 → 90 → 78 → 65 → 52

Time Complexity & Extra Space

ps: the number of nodes \ height \ width of the tree: n \ h \ w. @reference

- Time Complexity for both BFS & DFS: O(n)

- Extra Space required is O(n) (in the worst case)

  - BFS: perfect Binary Tree ⇒ width of the highest level = ceil(n/2)

  - DFS: skewed tree ⇒ height = n

### BFS v.s. DFS for Graph

BFS v.s. DFS by WilliamFiset @2019.09.29

## Algorithms

### Dijkstra Algorithm: Shortest Path in Graph

![](/notes/leetcode/media/image14.png)

⇒ Shortest Path from A to F: F → E → C → A @reference by imagineer & code

### Minimal Spinning Tree & IDA*

Problems:

> Q: Smallest Sufficient Team

https://leetcode.com/problems/smallest-sufficient-team/discuss/334572/Python-DP-Solution

# Data Structures

数据结构的两类问题

1. 设计一个数据结构

2. 实现某个算法用到了某个/某几个数据结构

什么是数据结构: 可以认为是一个集合, 并且提供集合上的若干操作

LINEAR DATA STRUCTURE 通常用数组实现

- Queue

- Stack

- Hash

TREE DATA STRUCTURE 通常用指针

- Tree

|  | TreeMap | Heap | PriorityQueue |
| --- | --- | --- | --- |
| insert |  |  |  |
| delete |  |  |  |
| pop |  |  |  |
| find |  |  |  |
| modify |  |  |  |
| min / max |  |  |  |
| upper / lower |  |  |  |

![](/notes/leetcode/media/image15.png)

Quad Tree

KD-Tree 如何搜索

https://cloud.tencent.com/developer/article/1178474

https://zhuanlan.zhihu.com/p/45346117

https://leileiluoluo.com/posts/kdtree-algorithm-and-implementation.html

explanation: https://www.youtube.com/watch?v=ivdmGcZo6U8

Cuckoo Hashing

# Strings

ASCII Table

| 0 — 9 | 48 — 57 |
| --- | --- |
| A — Z | 65 — 90 |
| a — z | 97 — 122 |

> Q: Valid Anagram (easy) @2019.08.28 | 类似 Compare Strings (easy)

虽然 sorting O(nlogn) > Hast Table O(n) 但 average sorting 速度更快 | 复杂度分析

```python
# Sorting: Time O(nlogn); Space O(1)
def isAnagram(self, s: str, t: str) -> bool:
    if len(s) != len(t):
        return False
    return sorted(list(s)) == sorted(list(t))

# Hash Table: Time O(n); Space O(1), since there is only 26 characters
def isAnagram(self, s: str, t: str) -> bool:
    if len(s) != len(t):
        return False

    char_counter = {}
    for i in range(len(s)):
        if s[i] not in char_counter.keys():
            char_counter[s[i]] = 0
        if t[i] not in char_counter.keys():
            char_counter[t[i]] = 0
        char_counter[s[i]] += 1
        char_counter[t[i]] -= 1

    for key, val in char_counter.items():
        if val != 0:
            return False

    return True
```

> Q: Count Binary Substrings (easy) @2020.03.12

> Q: Reverse Words in a String

![](/notes/leetcode/media/image16.png)
in-place solution:

# 面试中较难 Follow Up

@九章算强化班 lec 07 @2020.03.19

- Subarray Sum & follow up

- Continuous Subarray Sum & follow up

- Partition & follow up

- Iterator & follow up

## Subarray Sum ⇒ Submatrix Sum

> Q: Subarray Sum = 0 | Time O(n)

思路: Prefix Sum + Hash Table

- 前缀和 S[j] = S[i-1] ⇒ A[i] +...+ A[j] = 0

- 哈希表 check S[j] = S[i-1]

> Q: Subarray Sum Closest | Time O(nlogn) 因为需要 sort 所有即 n 个 prefix sum 值

> Q: Submatrix Sum = 0 | Time O(n^3)

思路:  枚举上下边界 O(n^2) ⇒ 上下边界间按列求和 ⇒ 退化为一维 Subarray Sum = 0

> Q: Subarray Sum II: subarry sum in a range

TODO

A都是正整数S严格递增

每个S[j]要找到在[S[j]-end, S[j]-start]中的S[i]个数

– 同向双指针！

时间复杂度:O(N)

> Q: Minimum Size Subarray Sum

> Q: Subarray Sum Equals K: count the total number

> Q: Subarray Sum Equals K II: find the subarray w/ minimum size

> Q: Submatrices Sum = K

> Q: Matrix Block Sum

prefix range sum

304. Range Sum Query 2D - Immutable

307. Range Sum Query - Mutable

308. Range Sum Query 2D - Mutable: Premium

## Continuous Subarray Sum

> Q: Continuous Subarray Sum *: submission

![](/notes/leetcode/media/image17.png)

> Q: Continuous Subarray Sum II

solution

TODO

• 先按照Continuous Subarray Sum求出无环情况下的最大非空子数组和S 1

• 再用类似方法求出无环情况下的最小非空子数组和S 2

• 答案即为max{S 1 , total_sum – S 2 }

• 特殊情况：如果选择了最小非空子数组而它是整个数组， 那么选取无环情况下的最大非空子数组和S 1

• 时间复杂度:O(N)

> Q: Number of Subarray Sums Divisible by K

## Partition

基础 partition: 相向双指针

> Q: Partition Array

```python
def partitionArray(self, A, k):
    left, right = 0, len(A) - 1
    while left <= right:
        while left <= right and A[left] < k:
            left += 1
        while left <= right and A[right] >= k:
            right -= 1
        if left <= right:
            A[left], A[right] = A[right], A[left]
            left += 1
            right -= 1
    return left
```

> Q: Partition Array by Odd and Even (easy)

> Q: Sort Letters by Case (easy)

> Q: Interleaving Positive and Negative Numbers: solution

> Q: Sort Colors (medium) | submission

> Q: Sort Colors II

### Quick Select \ Quick Sort

(ctrl+f: Quick Sort)

#### > Q: Kth Largest Element in an Array

解法 1: PriorityQueue: submission

- 时间复杂度 O(n·logk)

- 更适合动态维护 top k

```python
def findKthLargest(self, A: List[int], k: int) -> int:
    heap = []
    for num in A:
        heapq.heappush(heap, num)
        if len(heap) > k: 
            heapq.heappop(heap)
    return heapq.heappop(heap)
```

解法 2: PriorityQueue / Heap

- 时间复杂度 O(n + k·logn): O(n) build heap + n·logn heappop()

```python
def findKthLargest(self, A: List[int], k: int) -> int:
    if not A or not 1 <= k <= len(A):
        return None
    A = [-x for x in A]
    heapq.heapify(A)
    for _ in range(k):
        res = -heapq.heappop(A)
    return res 
```

解法 3: QuickSelect: solution | submission

- 时间复杂度 O(n) ???

- 更适合静态第 k 大

```python
class Solution:
    def kthLargestElement(self, k, A):
        if not A or k < 1 or k > len(A):
            return None
        return self.partition(A, 0, len(A) - 1, len(A) - k)
        
    def partition(self, nums, start, end, k):
        # During the process, it's guaranteed start <= k <= end
        if start == end:
            return nums[k]

        left, right = start, end
        pivot = nums[(start + end) // 2]
        while left <= right:
            while left <= right and nums[left] < pivot:
                left += 1
            while left <= right and nums[right] > pivot:
                right -= 1
            if left <= right:
                nums[left], nums[right] = nums[right], nums[left]
                left, right = left + 1, right - 1
                
        # right is not bigger than left
        if k <= right:
            return self.partition(nums, start, right, k)
        if k >= left:
            return self.partition(nums, left, end, k)
        
        return nums[k]
```

> Q: Top K Frequent Elements

+ 解法 1: Heap / Counter + PriorityQueue: submission 1 & 2

+ 解法 2: Quick Sort: submission

> Q: Median of Two Sorted Arrays | solution

TODO

or directly find kth: solution

### 3-Way Partition

> Q: Wiggle Sort

#### > Q: Wiggle Sort II

solution

TODO

## Iterator

> Q: Flatten List

Recursion:

```python
class Solution(object):
    def flatten(self, nestedList):
        ret = []
        for elem in nestedList:
            if isinstance(elem, int):
                ret.append(elem)
            else:
                ret.extend(self.flatten(elem))
        return ret
```

Iteration:

```python
class Solution(object):
    def flatten(self, nestedList):
        stack = [nestedList]
        res = []
      
        while stack:
            top = stack.pop()
            if isinstance(top, list):
                for elem in reversed(top):
                    stack.append(elem)
            else:
                res.append(top)
        return res
```

#### > Q: Flatten Nested List Iterator

> Q: Flatten 2D Vector

```python
class Vector2D(object):
    def __init__(self, vec2d):
        self.vec2d = vec2d
        self.stack = []

    def next(self):
        self.flatten_next()
        return self.stack.pop()
    
    def hasNext(self):
        self.flatten_next()
        return len(self.stack) != 0
        
    def flatten_next(self):
        # "if" is not sufficient; Case: [[],[1,2],[]]
        while len(self.stack) == 0 and len(self.vec2d) > 0:
            self.stack = self.vec2d.pop(0)[::-1]
```

#### > Q: Binary Search Tree Iterator

```python
class BSTIterator:
    def __init__(self, root: TreeNode):
        self.stack = []
        while root:
            self.stack.append(root)
            root = root.left
            
    def next(self) -> int:
        if len(self.stack) == 0:
            return None
        
        node = self.stack.pop()
        curr = node.right
        while curr:
            self.stack.append(curr)
            curr = curr.left
        return node.val

    def hasNext(self) -> bool:
        return len(self.stack) != 0
```

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

![](/notes/leetcode/media/image18.png)
![](/notes/leetcode/media/image19.png)

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

![](/notes/leetcode/media/image20.png)

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

![](/notes/leetcode/media/image21.png)

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

![](/notes/leetcode/media/image22.png)

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

## 面试高频题 Ladder

# Templates

### Matrix Presum / Integral

```python
def matrixPresum(A):
    m = len(A)
    if m == 0: return
    n = len(A[0])

    for row in range(m):
        for col in range(n):
            if col == 0 and row == 0:
                pass
            elif col == 0 and row > 0:
                A[row][col] += A[row - 1][col]
            elif row == 0 and col > 0:
                A[row][col] += A[row][col - 1]
            else:
                A[row][col] += (
                    A[row][col - 1] + 
                    A[row - 1][col] -
                    A[row - 1][col - 1])
    return A
```

### Matrix Restoration / Differential

```python
def matrixRestoration(self, n, m, after):
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if i > 0:
                after[i][j] -= after[i - 1][j]
            if j > 0:
                after[i][j] -= after[i][j - 1]
            if i > 0 and j > 0:
                after[i][j] += after[i - 1][j - 1]
    return after
```

### Binary Search

```python
def findPosition(self, nums, target):
    if len(nums) == 0:
        return -1
    
    start, end = 0, len(nums) - 1
    # 1. 循环条件
    while start + 1 < end:
        # 2. 中值计算
        mid = (start + end) // 2
        # 3. 分三种情况讨论
        if nums[mid] < target:
            start = mid
        elif nums[mid] > target:
            end = mid
        else:
            return mid
    # 4. 结果讨论
    if nums[start] == target:
        return start
    if nums[end] == target:
        return end
    return -1
```

### DFS Tree

```python
def dfs(self, root, p):
    if root == None:
        return []
    
    stack = [root]
    order = []
    while stack:
        node = stack.pop()
        order.append(node.val)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    return order
```

DFS Grid

BFS Grid

# Sorting Algorithms

|  | Time | Space | Stability |
| --- | --- | --- | --- |
| 冒泡排序 Bubble Sort | O(n2) | O(1) |  |
| 快速排序 Quick Sort | Avg. O(nlogn) ~ Worst O(n2) | O(1) | No |
| 归并排序 Merge Sort | O(nlogn) | O(n) | Yes |

### Bubble Sort

比较次数 n(n-1)/2 = O(n2)

移动次数 max = 3n(n-1)/2 = O(n2)

```python
def bubble_sort(nums):
    for i in range(len(nums) - 1):         # i 循环冒泡排序进行的次数
   	 for j in range(len(nums) - i - 1):  # j 循环列表下标
   		 if nums[j] > nums[j + 1]:
   			 nums[j], nums[j + 1] = nums[j + 1], nums[j]
    return nums
```

提前结束 swap 提速

```python
def bubble_sort(nums):
    # We set swapped to True so the loop looks runs at least once
    swapped = True
    while swapped:
        swapped = False
        for i in range(len(nums) - 1):
            if nums[i] > nums[i + 1]:
                # Swap the elements
                nums[i], nums[i + 1] = nums[i + 1], nums[i]
                # Set the flag to True so we'll loop again
                swapped = True
```

### Merge Sort

每次从中间分开分别排序后合并 ⇒ 需要额外空间实现合并

```python
def mergeSort(arr):
    if len(arr) >1:
        mid = len(arr) // 2  # Finding the mid of the array
        L = arr[:mid]  # Dividing the array elements into 2 halves
        R = arr[mid:]
  
        mergeSort(L)  # Sorting the first half
        mergeSort(R)  # Sorting the second half
  
        i = j = k = 0
          
        # Copy data to temp arrays L[] and R[]
        while i < len(L) and j < len(R):
            if L[i] < R[j]:
                arr[k] = L[i]
                i+=1
            else:
                arr[k] = R[j]
                j+=1
            k+=1
          
        # Checking if any element was left
        while i < len(L):
            arr[k] = L[i]
            i+=1
            k+=1
          
        while j < len(R):
            arr[k] = R[j]
            j+=1
            k+=1
```

### Qucik Sort

从需要排序的数里面随便找出一个，然后，把比这个数小的放在这个数左边，比这个数大的放在这个数右边，一样大的和这个数放在一起，最后，左右两边各自重复上述过程，直到左边或右边只剩下一个数 (或零个数) 无法继续为止 @explanation

(选择 right 作为 pivot)

```python
def partition(array, left, right):
    i = left - 1
    for j in range(left, right):
        if array[j] <= array[right]:
            i += 1
            array[j], array[i] = array[i], array[j]
    array[i + 1], array[right] = array[right], array[i + 1]
    return i + 1

def quicksort(array, left, right):
    if left < right:
        pivot = partition(array, left, right)
        quicksort(array, left, pivot - 1)
        quicksort(array, pivot + 1, right)
```

(选择 middle 作为 pivot) TODO: why key point 2 left <= right 

```python
class Solution:
    def sortIntegers2(self, A):
        self.quickSort(A, 0, len(A) - 1)

    def quickSort(self, A, start, end):
        if start >= end:
            return
        left, right = start, end
        # key point 1: pivot is value, not index. Also, it is better to
        # choose pivot as the middle of start & end instead of start or end
        pivot = A[(start + end) // 2]

        # key point 2: every time you compare left & right, it should be
        # left <= right not left < right
        while left <= right:
   	        # key point 3: A[left] < pivot not A[left] <= pivot
            while left <= right and A[left] < pivot:
                left += 1
            while left <= right and A[right] > pivot:
                right -= 1
            if left <= right:
                A[left], A[right] = A[right], A[left]
                left += 1
                right -= 1

        self.quickSort(A, start, right)
        self.quickSort(A, left, end)
```

> Q: Sort Integers II / Sort an Array

(ctrl+f)

# Tricky

### Cycle Detection: Floyd's Tortoise and Hare

> Q: Find the Duplicate Number | solution

> Q: Find all Duplicates in an Array | reference

```python
def findDuplicates(self, nums: List[int]) -> List[int]:
    res = []
    for x in nums:
        if nums[abs(x) - 1] < 0:
            res.append(abs(x))
        else:
            nums[abs(x) - 1] *= -1
    return res
```

> Q: Linked List Cycle: two pointers: Time O(n) & Space O(1) | solution

> Q: Linked List Cycle II

解法 1: Hash Table: Time O(n) & Space O(n)

解法 2: Floyd's Tortoise and Hare: 2 phases: find intersection ⇒ find entrance

![](/notes/leetcode/media/image23.png)

### Bit Operations / Bitwise

- (1 + x) = ~x

- x & (x - 1) 可以消除最高位的 1 | Q: Number of 1 Bits

> Q: Single Number

Hast Table 需要空间 O(n) 而位运算只需要 O(1) Space

```python
def singleNumber(self, nums: List[int]) -> int:
    res = 0
    for x in nums:
        res ^= x
    return res
```

> Q: Single Number II: explanation by leetcode

![](/notes/leetcode/media/image24.png)

> Q: Counting Bits

```python
def countBits(self, num: int) -> List[int]:
    f = [0] * (num + 1)
    for i in range(1, num + 1):
        f[i] = f[i >> 1] + (i % 2)
    return f
```

> Q: Number of 1 Bits: x & (x - 1) 可以消除最高位的 1

> Q: Number of Digit One

### Reservoir Sampling Solution

> Q: Random Pick Index: solution

# Others

### Problems

#### > Q: Reach a Number (easy) @2019.08.27

- 注意要处理负数 case ⇒ 等于相应正数

- math solution by huahualeetcode

![](/notes/leetcode/media/image25.png)

#### > Q: Reaching Points (hard) @2020.02.21

```python
def reachingPoints(self, sx: int, sy: int, tx: int, ty: int) -> bool:
    # Important: whlie conditions
    while sx <= tx and sy <= ty:
        if tx > ty:
            if ty > sy:
                tx %= ty
            else:
                return (tx - sx) % ty == 0
        else:
            if tx > sx:
                ty %= tx
            else:
                return (sy - ty) % tx == 0

    return sx == tx and sy == ty
```

注意 while 循环条件： 吃

- if while sx < tx or sy < ty:

fail case: (1, 8) → … → (4, 15): fasle

- if while sx < tx and sy < ty:

fail case: (3, 3) → … → (12, 9): true

#### > Q: Merge k Sorted Lists

Solution O(nlogk): PQ / Divide & Conquer (自上向下) / 两两归并 (自下而上) || 归并 / 快速排序

### Linear Time Greedy Solutions

#### > Q: Gas Station (medium) @2020.03.06

Time O(n) & Space O(1)

```python
def canCompleteCircuit(self, gas, cost):
    total_tank, curr_tank = 0, 0
    starting_station = 0
    for i in range(len(gas)):
        total_tank += gas[i] - cost[i]
        curr_tank += gas[i] - cost[i]
        # If one couldn't get here,
        if curr_tank < 0:
            # Pick up the next station as the starting one.
            starting_station = i + 1
            # Start with an empty tank.
            curr_tank = 0
    return starting_station if total_tank >= 0 else -1
```

+ Why this works

Let's imagine the situation when total_tank >= 0 and the above algorithm returns Ns as a starting station. Algorithm directly ensures that it's possible to go from Ns to the station 0. But how to ensure the last part of the round trip from the station 0 to the station Ns?

![](/notes/leetcode/media/image26.png)

![](/notes/leetcode/media/image27.png)

![](/notes/leetcode/media/image28.png)

![](/notes/leetcode/media/image29.png)

#### > Q: Super Washing Machines (hard) @2020.03.06

思路详细解释: max( max(throughput of every washer), max(give-out of every washer) )

(python)

```python
def findMinMoves(self, machines: List[int]) -> int:
    avg = sum(machines) / len(machines)
    if avg != int(avg): 
        return -1
    avg = int(avg)
    cnt = 0
    res = 0
    for load in machines:
        cnt += load - avg;  # load-avg is "gain/lose"
        res = max(res, abs(cnt), load-avg);
    return res
```

# OA

### Sum of all elements of A left and above A[i,j]

#### > Q: Matrix Integral

Given a matrix A, return a matrix M for which every element [i,j] is the sum of all elements of A left and above A[i,j] | source @Google @2020.03.02

Considering the following matrix A:

[

  [3, 7, 1],

  [2, 4, 0],

  [9, 4, 2]

]

Compute M:

[

  [3,  10, 11],

  [5,  16, 17],

  [14, 29, 32]

]

动态规划求解

```python
def solution(A):
    m = len(A)
    if m == 0: return
    n = len(A[0])

    for row in range(m):
        for col in range(n):
            if col == 0 and row == 0:
                pass
            elif col == 0 and row > 0:
                A[row][col] += A[row - 1][col]
            elif row == 0 and col > 0:
                A[row][col] += A[row][col - 1]
            else:
                A[row][col] += (
                    A[row][col - 1] + 
                    A[row - 1][col] -
                    A[row - 1][col - 1])
    return A
```

Naive solution

```python
def Solution(A):
    # Note that we just need to 
    # add the cumulative sum up to the previous column and 
    # add the cumulative sum up to the previous row 
    # to each position [i,j]
    m = len(A)
    if m == 0: return
    n = len(A[0])

    for row in range(1, m):
        for col in range(n):
            A[row][col] += A[row - 1][col]
    for row in range(m):
        for col in range(1, n):
            A[row][col] += A[row][col - 1] 
    return A
```

#### > Q: Matrix Differential

<==> Matrix restoration

即原上题的操作 | source 1 & 2 @TuSimple OA @2020.03.02

给一个算法将 integer 矩阵 before 转换成 after. 这个算法将矩阵中每一个坐标 (x, y) (zero index based) 转换成其之前的行和列所有数的和, i.e.:

[Java]

```
int s = 0;
for (int i = 0; i <= x; i++) {
      for (int j = 0; j <= y; j++) {
            s += before[j]; 
      }
}
after[x][y]=s;
```

题目: 给定 after 求出 before

举例:

before | after

1 2    | 1  3

3 4    | 4  10

after[0][1] = 1 + 2;

after[1][1] = 1 + 2 + 3 + 4;

思路: 将上题 DP 解法的 + 都换成 - 即可

```python
def solution(A):
    m = len(A)
    if m == 0: return
    n = len(A[0])

    for row in range(m - 1, -1, -1):
        for col in range(n - 1, -1, -1):
            if col == 0 and row == 0:
                pass
            elif col == 0 and row > 0:
                A[row][col] -= A[row - 1][col]
            elif row == 0 and col > 0:
                A[row][col] -= A[row][col - 1]
            else:
                A[row][col] -= (
                    A[row][col - 1] + 
                    A[row - 1][col] -
                    A[row - 1][col - 1])
    return A
```

### Edit Distance: convert all same char at a time

#### > Q: String Transforms Into Another String (LC1153)

(hard) @2020.03.02

![](/notes/leetcode/media/image30.png)

![](/notes/leetcode/media/image31.png)

![](/notes/leetcode/media/image32.png)

(python): my submission

```python
def canConvert(self, str1: str, str2: str) -> bool:
    if str1 == str2:
        return True

    mapping = {}
    used = []
    for i in range(len(str1)):
        if str1[i] not in mapping:
            mapping[str1[i]] = str2[i]
            if str2[i] not in used:
                used.append(str2[i])
        else:
            if mapping[str1[i]] != str2[i]:
                return False

    return len(used) != 26
```

Notes:

- Case 1:

"abcdefghijklmnopqrstuvwxyz"

"bcdefghijklmnopqrstuvwxyza"

⇒ 需要 (mappings) < 26; 

- Case 2:

"abcdefghijklmnopqrstuvwxyz"

"bcdefghijklmnopqrstuvwxyzq"

⇒ 其实不是控制 (mappings) < 26 而是 

len(used) < 26 或

len(set([char for char in str2])) < 26

- Case 3:

"abcdefghijklmnopqrstuvwxyz"

"abcdefghijklmnopqrstuvwxyz"

⇒ 直接在开头判断处理

Appendix: other solutions from leetcode discussion

(python)

```python
class Solution:
    def canConvert(self, str1: str, str2: str) -> bool:
        if str1 == str2:
            return True
        m = {}
        for i in range(0, len(str1)):
            if str1[i] not in m:
                m[str1[i]] = str2[i]
            elif m[str1[i]] != str2[i]:
                return False
        return len(set([char for char in str2])) < 26
```

If a in str1 is transformed to d in str2, get all indexes of a in str1 and d in str2

if they are all not the same, transformation is not possible

If they're all the same for all the characters, then transformation is possible if str2 don't have all 26 characters. if str2 has all 26 characters, str1 should be equal to str2

(java)

```python
class Solution {
    public boolean canConvert(String str1, String str2) {
        if( str1.equals(str2)) return true;
        Map<Character, Character> map = new HashMap<>();
        for( int i =0; i < str1.length(); i++ ){
            char ch1 = str1.charAt(i);
            char ch2 = str2.charAt(i);
            if ( map.containsKey(ch1) && map.get(ch1) != ch2 ) {
                return false;
            }
            map.put(ch1, ch2);
        }
        if ( new HashSet<Character>(map.values()).size() == 26 ) {
            return false;
        }
        return true;
    }
}
```

(C): O(n) time, O(1) space, beats 100%

```
bool canConvert(char * str1, char * str2){
    char char_map[26] = { 0 };
    char char_set[26] = { 0 };
    char* cm = char_map - 'a', *cs = char_set - 'a';
    
    for (; *str1 != 0; ++str1, ++str2) {
        if (cm[*str1] != 0) {
            if (cm[*str1] != *str2) return false;
        }
        else cm[*str1] = *str2;
        cs[*str2] = 1;
    }
    for (char i = 0; i < 26; ++i) {
        if (char_set[i] == 0) return true;
    }
    for (char c = 'a'; c <= 'z'; ++c) {
        if (cm[c] != c) return false;
    }
    
    return true;
}
```

(C++): 4ms 98% O(N) solution w/ explanation

This problem is very tricky, and took me a while to figure out how to solve. But once you figure out the "catch", the coding part is very easy.

The first thing is to realize that if a character in str matches more than 1 unique characters in str2, then we cannot convert. This forms the first check, which is fairly easy to figure out based on prompt.

The second part is the catch. To get this, we need to deduce step by step how we can flip to final value:

- Each unique character in str2 can match 1 or more unique characters from str1

- The set of characters matching each unique character in str2 are mutually exclusive

- Each of these "set" can be flipped to the same character (any character in the set) without affecting any of the other sets

- This reduces the problem of flipping n characters from str1 to their respective matches in str2, with n being the number of unique characters in str2.

- Flipping can affect other sets, in the situation where the flipped value for a character is the same as the non-flipped value for some other character.

To understand 5, we can have the example str1 = "ab", str2 = "ba".

In step 4 we should end up with the following problem: [a -> b; b -> a]. Here we run into an issue, namely if we flip a first, we will get a b, and this will be affected when we try to flip b. To work around it, we need to first flip a to some unknown character x in the lowercase alphabet, flip b, then flip a.

- Reduced problem created in 4 has the form [a1 -> b1; a2 -> b2, ... an -> bn], where [a1, a2, ... an] and [b1, b2, ... bn] are both unique sets.

- If there were a conflict, then we will have something like this: [ai -> bi; aj -> bj], bi == aj, i != j. Because of 6, bi and aj just both be unique, which means that for any ai -> bi, it can conflict with at most one other aj -> bj.

- Based on 5 and 7, it will take only 1 unknown character x to resolve a conflict.

- This leads to the conclusion that when there is conflict, we need only 1 unknown character x to resolve all instances, since this character can be reused indefinitely, and conflicts do not affect each other.

- Thus, to solve this problem, we should check if there are conflicts, and if there are conflicts, make sure we have at least 1 candidate for unknown characer x (uses at most 25 out of 26 possible characters).

- It is worth noting that the condition (with conflict && uses at most 25 characters || no conflict) can be reduced to (uses at most 25 characters || strings are the same), because if there are 26 characters and no conflict then that can only mean the strings are the same.

So after all that, all we really needed was to check if the strings are the same and that str2 uses no more than 25 unique characters :).

```python
class Solution {
public:
    bool canConvert(const string& str1, const string& str2) {
        bitset<26> used2;
        vector<int> match1(26, -1);
        bool same = true;
        int size = str1.size();
        for(int i = 0 ; i < size; ++i) {
            int c1 = str1[i]-'a', c2 = str2[i]-'a';
            used2.set(c2);
            if(match1[c1] >= 0 && match1[c1] != c2) return false;
            else match1[c1] = c2;
            same &= c1 == c2;
        }
        
        return same || used2.count() < 26;
    }
};

auto gucciGang = []() {std::ios::sync_with_stdio(false);cin.tie(nullptr);cout.tie(nullptr);return 0;}()
```

#### > Q: String Transform Steps count

str1 和 str2 长度相同. 求可以把 str1 变成 str2 所需的最少步数. 若不能转换则返回 -1.

规则:  

- 每次改变字母不是只改变一个, 而是把所有相同字母都改变.

- 另外可以引入一个字符 '*' 作为中间状态.

举例:

- accs -> eeec 需要 3 步: accs -> eccs -> eees -> eeec

- abb -> baa 需要 3 步: abb -> *bb -> *aa -> baa

source @TuSimple OA @2020.03.02

```python
def solution(str1: str, str2: str) -> int:
    if str1 == str2:
        return 0

    mapping = {}
    for i in range(len(str1)):
        if str1[i] not in mapping:
            mapping[str1[i]] = str2[i]
        else:
            if mapping[str1[i]] != str2[i]:
                return -1

    used_1 = []
    used_2 = []
    for key, val in mapping.items():
        if key == val:
            continue
        if key not in used_1:
            used_1.append(key)
        if val not in used_2:
            used_2.append(val)

    if set(used_1) == set(used_2):
        return len(used_1) + 1

    return len(used_1)
```

#### > Q: Edit Distance (LC0072)

submission @2020.03.02 | non-DP solution | explanation by leetcode

D[i][j]: edit distance between the first i characters of word1 and the first j characters of word2.

If the last character is the same, i.e. word1[i] = word2[j] then

D[i][j] = 1 + min⁡(D[i - 1][j], D[i][j - 1], D[i - 1][j - 1] - 1)

and if not, i.e. word1[i] != word2[j] we have to take into account the replacement of the last character during the conversion.

D[i][j] = 1 + min⁡(D[i - 1][j], D[i][j - 1], D[i - 1][j - 1])

![](/notes/leetcode/media/image33.png)

![](/notes/leetcode/media/image34.png)
![](/notes/leetcode/media/image35.png)

Complexity Analysis

- Time: O(mn)

as it follows quite straightforward for the inserted loops.

- Space : O(mn)

since at each step we keep the results of all previous computations

(submission): python

```python
def minDistance(self, s: str, t: str) -> int:
    m = len(s)
    n = len(t)
    D = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0:
                D[i][j] = j
            elif j == 0:
                D[i][j] = i
            else:
                D[i][j] = 1 + min(
                    D[i - 1][j], 
                    D[i][j - 1], 
                    D[i - 1][j - 1] - int(s[i - 1] == t[j - 1]))
    return D[-1][-1]
```

(solution): non-DP ???

```python
def minDistance(self, word1: str, word2: str) -> int:
    heap = [(0,word1,word2)]
    seen = set()
    n = 0
    while heap:
        dis, w1, w2 = heapq.heappop(heap)
        if w1 == w2: return dis
        if not (w1,w2) in seen:
            seen.add((w1,w2))
            while w1 and w2 and w1[-1]==w2[-1]:
                w1 = w1[:-1]
                w2 = w2[:-1]
            else:
                heapq.heappush(heap,(dis+1,w1[:-1],w2))
                if w2:
                    heapq.heappush(heap,(dis+1,w1,w2[:-1]))
                if w1 and w2:
                    heapq.heappush(heap,(dis+1,w1[:-1],w2[:-1]))
```

> Q: Isomorphic Strings (LC0205) | submission

### Submatrix

#### > Q: Split a Matrix w/ Evenly 1s

(my solution: local)

source 1 & 2 & 3 LC discussion | @TuSimple OA: SDE new grad General @2020.03.05

给一个足够大的元素只有 0 和 1 的二维矩阵. 我们把这个矩阵横向切 m 次, 纵向切 n 次, 分成 (m+1) * (n+1) 块. 问: 是否有这样一种分割方法, 使每个小矩阵上 1 的总个数全部相同.

example1:

m = 1, n = 1

1 1  |  0 0
1 1  |  0 0
---- | ----
0 0  |  1 1
0 0  |  1 1

return false

example2:

m = 3, n = 1

1 0  |  0 1
---- | ----
0 1  |  1 0
---- | ----
1 0  |  0 1
---- | ----
0 1  |  1 0

return true

example3:

m = 1, n = 3

----------------
1 1 | 1 | 1 | 1 
0 0 | 1 | 1 | 1 
----------------
0 1 | 1 | 1 | 1 
1 0 | 1 | 1 | 1 
----------------

return true

思路: Time O(mn) & Space O(1) WRONG: it’s not sufficient for example 1

```
# Step 1: 
# Matrix Integral O(mn) 计算 S[i][j]: 
# sum of all elements above and left to the matrix A[i][j] 
# ⇒ 可以得到矩阵 total sum S[m - 1][n - 1].

# Step 2:
# Each col cut segment needs col_sum = S[m - 1][n - 1] / (p + 1)
# Each row cut segment needs row_sum = S[m - 1][n - 1] / (q + 1)
count = 0
for row in range(m):
    if S[row][n - 1] % row_sum == 0: count += 1
for col in range(n):
    if S[m - 1][col] % col_sum == 0: count += 1
return count == (p + 1) * (q + 1)
```

注意: 当有全 0 行或列时候特殊处理 row_cuts 和 col_cuts 的计算

思路: 需要分别找到 row_cuts 和 col_cuts 后才逐个格子 check, i.e.:

```
for i in row_cuts:
     for j in col_cuts:
        sum_ij should be total_sum / (p + 1) / (q + 1)
```

#### > Q: Submatrix w/ 1s in Each Row

source | @Amazon @2020.03.12

Given M x N matrix which contains 1s and 0s, find the largest sub matrix which contains most number of 1s; condition is that each row in the sub matrix must contain at-least one 1.

#### > Q: Largest Square w/ sum <= K *

Edge Cases:

1 5 4
5 6 4 0 3

1 1 2
2

#### > Q: Max Sum of Rectangle in a 2D matrix

This is 2D version, the extension of it’s 1D version, Kadane's Algorithm: Maximum Subarray.

2D version can be solved in O(n^3) by:

loop through i, j rows in O(n^2); take the column sum in between as 1D array, solve in O(n).

2D version equivalence:

> Q: Max Sum of Rectangle <= K (LC0363) (hard)

1D version explanation:

> Q: Maximum Subarray (easy) @2020.03.06

+ Greedy / DP: pick the locally optimal move at each step

![](/notes/leetcode/media/image36.png)
(python): Time O(n) & Space O(1)

```python
    def maxSubArray(self, nums: List[int]) -> int:
        maxSum = nums[0]
        for i in range(1, len(nums)):
            if nums[i - 1] > 0:
                nums[i] += nums[i - 1]
            maxSum = max(maxSum, nums[i])
        return maxSum
```

#### > Q: Number of Submatrices That Sum to Target (LC1074) (hard)

@2020.03.05

解答: 纯 DP 时间 O(n^4); DP + Hash Map + 前缀和可时间 O(n^3): submission | java solution

注释: 参考 leetcode 最快的 sample submisison code 优化解答 submission

思路: leetcode explanation of Subarray Sum Equals K (LC0560) (submission) 的二维拓展

- 首先对每一列计算一个 presum

- 然后对任意两个行 [j, k], 计算 j 和 k 行之间的所有数的和:

presum[i][k] - (j == 0 ? 0 : presum[i][j-1])

⇒ 任意两列 [j,k] 之间的数可形成一个临时的一维数组, 表示从第 0 行到最后一行的数 

⇒ 问题转换成: 在这个一维数组里面, 找一个连续子数组, 使其的和是 target (LC560).

类似题目: Count all sub-arrays having sum divisible by k

#### > Q: Maximal Square

(medium) submission @2020.03.05 | leetcode explanation

![](/notes/leetcode/media/image37.png)

Geometery Median @2019.10.08

https://stackoverflow.com/questions/12934213/how-to-find-out-geometric-median

https://stackoverflow.com/questions/57277247/the-point-that-minimizes-the-sum-of-euclidean-distances-to-a-set-of-n-points

### Grid DP

https://www.hackerearth.com/zh/practice/notes/dynamic-programming-problems-involving-grids/

easy

https://leetcode.com/problems/shift-2d-grid/solution/

https://www.1point3acres.com/bbs/thread-605899-1-1.html

### Problems

> Q: Copy List with Random Pointer

# 面经

TODO https://leetcode-cn.com/problems/stone-game/solution/jie-jue-bo-yi-wen-ti-de-dong-tai-gui-hua-tong-yong/

### Nuro

> Q: Add strings

Follow-up: 如果有负数怎么处理 @Nuro @2020.03.09

> Q: 一只青蛙在一个 2D grid 里, 给定起始位置, 最多能跳 K 次 (可以少于 K 次), 有多少次能跳出 grid | source @2020.03.09

BFS 跳出边界一次 count +1

### Facebook

面经

@souce

> Q: 1. Mergo Two Sorted Array (LC88)

> Q: 2. Minimum Add to Make Parentheses Valid (LC921)

加入最少的括号数让当前字符括号匹配, 不过要额外返回新的字符串: submission

@source

> Q: 2. Vertical Order Traversal of a Binary Tree (LC987)

> Q: 1. 两个顺序由小到大的序列, 找出重复的数字

Related:

> Q: Find the Duplicate Number | solution (ctrl+f)

> Q: Find all Duplicates in an Array (ctrl+f)

@source

第一题 稀蔬使量的点积

第二题 验证包含有撒种括弧的字符是否有笑

@source

> Q: 1. Validate BST / Valid Binary Search Tree (LC98)

> Q: 2. Minimum Window Substring (LC76)

Onsite Round 1

> Q: 1. 找出给定的两个数组的最小差. e.g., [3 5 7] [5 9 12] 最小差是 5 - 5 = 0: 双指针从头到尾扫一遍 O(m+n) 秒了

> Q: 2. 判断一个二叉树是不是 almost balanced (最小和最大高度差最多容忍是1): BFS 秒了

Onsite Round 2

> Q: 1. 找一个数组中最大值, 2 个最大值, 第 k 大元素. 写出找第 k 大元素的代码: partition

> Q: 2. serilize 和 deserilize a binary tree (LC)

@source

FB 高频 https://www.1point3acres.com/bbs/collection/229002

> Q: Course Schedule (LC207)

> Q: K Closest Points to Origin (LC973) solution

> Q: Integer to English Words (LC273) solution | 反过来 English words to integer @source

> Q: Three Sum / 3 Sum (LC15): solution

240

378

@source: 在职跳槽 @2020.04.07

> Q: Single Number I & II (LC136 & 137)

> Q: Lowest Common Ancestor of a Binary Search Tree (LC235)

> Q: Random Pick Index (LC398) 变体

> Q: Maximum Difference Between Node and Ancestor (LC1026): submission

> Q: 3Sum Closest (LC16)

@source

1. 利口 伊尔武，要求in-place，除了两个pointer，不能占用额外的memory。

2. 利口 吴思伞，follow-up，不能用global variable

@source

> Q: sort string by alphabet

@source

> Q: 1. diagnoal traverse 简单变体

给定 matrix

1 2 3 4

5 6 7 8

9 1 2 3

打印出

1

2 5

3 6 9

4 7 1

8 2

3

> Q: 2. Sum of Even Numbers After Queries (LC958)

@source

> Q: 1. 给一个 integer 找出 binary 值里面 1 的数量: x & (x - 1) 可以消除最高位的 1

> Q: Counting Bits

> Q: Number of 1 Bits

> Q: 2. anagram string: 两个 string 找到并返回 first matched index e.g.: "the cat", "act" → 4

> Q: Find All Anagrams in a String

@source

> Q: Merge k Sorted Lists (LC23)

### Google

> Q: Throwing eggs from a building / 扔鸡蛋问题 

@2020.04.01: ref 1 & 2

https://raw.githubusercontent.com/UmassJin/Leetcode/master/Design/%E9%9D%A2%E7%BB%8F%E5%88%86%E4%BA%AB0616.py

> Q: Binary Tree Coloring Game | Follow-up solution

### TuSimple

面经

> Q: OA Group 9: 

要把 N 个 人分成 M 个组, 左边的组人数需要小于等于右边的组. 问有多少种分法？比如 7 人 3 组, 有 4 种分法: 1|1|5, 1|2|4|, 1|3|3, 2|2|3

> Q: OA https://www.1point3acres.com/bbs/thread-604931-1-1.html

> Q: Count Unique Characters of All Substrings of a Given String (LC 828) (hard) @source

> Q: Count Binary Strings (LC 696) (easy)

> Q: N-ary tree 求给定两个 nodes 间距离 

@source 1

N-ary tree, edge 上带 weight (可以当成 edge 的长度). 给一系列 tree node 的 pair, 要求返回每个 pair 两个 node 之间的距离.

思路: 类似于 LCA, 但是由于有很多个 request, 可以预处理一下, 遍历的时候存下每个 node 的parent, O(N). 之后每次 request 时找 node 到 root 的 path, 比较path, 得到 LCA 和距离, O(h).

@source 2

用 class 自己定义了一个 N-ary tree, 每个 node 有自己的 value 和代号 (a,b,c…), 还有 list 存储了这个 node 能到达的子节点. 问给出 start 和 destination, 能否到达; 如能到达, 最短路径是什么 (node 的 value 代表 cost). 这个题我是先求的 lca, 然后再用union-find做的.

参考: LC 236. Lowest Common Ancestor of a Binary Tree

> Q: implement a hashmap 要求实现 get(key), put(key, val), delete(key), hashcode(key) (即把一个string representation hash 成一个 integer) 要求同时考虑 collision 的问题

思路: 就是用的 list + doubly linked list 写的 wrap 一个 node class, 一个 doubly linked list class with some helper functions, 最后一个 hashmap class. 本质就还是考察链表用的熟不熟

Relate? LRU Cache: Python O(1) doubly linked list + hashmap 

> Q: Given a non-empty array containing only positive integers, find if the array can be partitioned into four subsets such that the sum of elements in both subsets is equal. @source

https://leetcode.com/problems/partition-equal-subset-sum/discuss/276278/Python-DP-and-(DFS%2BMemo)

backpack

> Q LC772: Basic Calculator III

> Q: AAA -> BBB -> CCC: https://www.1point3acres.com/bbs/thread-592959-1-1.html

> Q: https://www.1point3acres.com/bbs/thread-591978-1-1.html

> Q: https://www.1point3acres.com/bbs/thread-593274-1-1.html

> Q: OA: https://www.1point3acres.com/bbs/thread-590446-1-1.html

### Citadel

OA

OA 2019 @source 1 & 2

> Q: The Jungle Book: local

> Q: Unique Sub Palindrome: local; requires O(n) Manacher's Algorithm

> Q: Longest String Chain

DP solution ⇒ TLE

需要 DFS + memoization search: solution

OA 2020 @source

OA 2019 @source

OA 2018 @source

电面

https://www.1point3acres.com/bbs/forum.php?mod=viewthread&tid=579807&ctid=228994

https://www.1point3acres.com/bbs/collection/228994

https://www.1point3acres.com/bbs/thread-596022-1-1.html

### ByteDance

高频 2019 & 2020 | job description

> Q: Robot Room Cleaner (LC489) 用 recursion 写完后要求改成 iteration @source

> Q: Binary Tree Zigzag Level Order Traversal @source

> @source

> 电面 1 Q: Find the Town Judge: solution

> 电面 2 Q: Shortest Distance from All Buildings (LC317 简化版)

Related: Build Post Office / Build Post Office II

> Q: Number of Matching Subsequences (ctrl+f) 类似题目 @source

```
# S 是一个长 string 长度 M, e.g:
# S = "applebananawatermelon"

# D 是一个字典, 有 N 个 word. 每个平均长度 L. e.g.:
# D =  ["aple", "apppple", "banana", "wtrmelon"]

# 返回: 对于每个 word, S 中是否存在同样的 sequence (中间可以隔字母, 但顺序不能变). e.g.: 
# return = [T, F, T, T]. 因为 S 中有 {a, p, l, e} 这样的 sequence 在 index {0, 1, 3, 4} 上 ⇒ T; 没 {a,p,p,p,p,l,e} ⇒ F.

# 其中 M >> L, N 并且 S 中 26 个字母出现概率均匀分布. 求复杂度较低的算法
```

@source

> Q: Top K Frequent Elements (ctrl+f)

> Q: 给你一个数组，里面有很多正整数。你每次选定一个数字，取走数组里所有和这个数字相同的数，得分是你选的数字乘以取走的个数。取完一个数字以后，这个数字加一、减一的两个数字就不能再取了。求问你按这个规则取到最后不能再取任何数字为止，可能的最大得分是多少。

@source PhD intern AI lab

> Q1: 如何在球面上均匀采样 uniformly sample

只要意识到 Gaussian 是 isotropic 的就很显然了: solution

> Q2: 连续扔骰子，扔出一个单调不减序列且最终抵达6算作成功（直接扔出6也算成功），问成功序列的期望长度是多少。出这个题的时候面试官也说这比较难，提示是可以把每个数字上停留的次数当成是一个geometric distribution。

> Q3: coding 题是算 median of stream data，面试官说是leetcode原题，只要用heap来keep前半段max和后半段的min然后适当插入就好了。最后分析一下复杂度，也不是很难算

@source

> Q1: 有个物种被创造后要 hibernate 4 天, hibernation 结束后在接下来的 4 天中每天生成一个后代, 然后永远休眠. 求在 N 天时一共生成过有多少个: solution (local)

> Q2: 一共有 N 个nodes, 给一个 N * N matrix, matrix[i][j] 代表 node i 和 node j 之间信号强度. 两个 node 之间信号强度大于某 threshold 时可联通, 在一个 network 中每个 node 可以直接或间接联通该 network 中其他 node. 求有多少个 disjoint networks ⇒ [Union Find]

> Q3: bool expression evaluation. 类似 postfix calculator: Evaluate Reverse Polish Notation

@source

> Q1: Koko Eating Bananas

> Q2: Sort List 链表归并排序. solution: merge sort

> Q3: Minimum Path Sum 要考虑负数

@source

> Q1: strings 加法, 考虑负数 (LC415)

> Q2: 设计异步的 request 处理系统, 每过 K 秒或者每积攒 N 个 request 时要对 request 进行处理. Follow-up: thread safe.

> Q3: Next Greater Node In Linked List

> Q4: Longest Substring with At Least K Repeating Characters: DFS recusion & iteration

> Q: Next Permutation @source // similar to:

> Q: Next Greater Element III

@source

> Q1: Smallest Subsequence of Distinct Characters * (ctrl+f)

> Q2: 给你两个能装水的容器和他们最大装水量，再给你一个目标水量，问最少进行多少步操作可以让其中任何一个容器装目标水量，并且要把每一步都打印出来。可以进行的操作有如下：fill 1代表把1号容易装满，empty 1代表把1号容器水都倒出来，move 1 2代表把1号容器的水移到2号容器，如果2号容器可以装下1号倒过来的水，那么操作完之后1号容器为空，如果2号容器装不下1号倒过来的水，那么操作完之后1号容器还会剩下没有倒过去的水。

https://leetcode.com/problems/water-and-jug-problem/discuss/159226/python-O(n)-time-O(1)-space...gcd-based-solution-with-explanation

solution

https://leetcode-cn.com/problems/water-and-jug-problem/solution/shui-hu-wen-ti-by-leetcode-solution/

@source

> Q1: Find First and Last Position of Element in Sorted Array

> Q2: 给无序不重复数组, 返回第 k 小的数. Note: 优化到 O(n) & (follow-up: 能否不用 PQ)

> Q: Path Sum III (LC437) @source

解法 1: O(n^2) double recursion: submission & solution

解法 2: O(n) w/ hashmap: submission & solution 1 & 2

> Q: Optimal Account Balancing @source: solution 1 & 2

@source

> Q1: Find the Smallest Divisor Given a Threshold / Koko Eating Bananas

> Q2: 有 n 个节点和 m 条路, 你可以放障碍物在节点上 block 所有过这个节点的路, 但你不能把一条路的两边节点都 block. 求能否 block 所有路, 最少放多少障碍物 block 所有路.

Solution: DFS 染色. 对 graph 每一个连在一起的部分先把一个点染成黑色, 就可以 DFS 把剩下点染成黑色或白色 (如果有冲突返回 -1), 然后这一部分需要放置的障碍物就是黑色和白色比较少颜色的节点的个数.

> Q: Jump Game @source

@source

> Q: Lemonade Change (LC860)

> Q: Gas Station (LC134)

ByteDance 国内面经

@source

> Q1: Max Consecutive Ones III

解法 1: O(n) 双指针 submission / solution

解法 2: O(nk) DP ⇒ TLE

Related: Max Consecutive Ones II: O(n): 双指针 submission 倒 3 | DP 倒 1 ⇒ 滚动数组 倒 2

> Q2: LRU Cache

> Q3: Minimum Cost For Tickets: DP = DFS w/ memoization search

@source

> Q1: Count pairs from two sorted arrays whose sum is equal to a give target: Hash O(m+n)

> Q2: Element with left side smaller and right side greater

找出数组中的 k 数, 定义: 比位置位于这个数前面的数字都大, 且比位于这个数后面的数字都小.

e.g.: [4,1,3,2,7,9,8,10,12] ⇒ k 数为 7 和 10

> Q: Longest Common Subsequence: solution DP

> Q: 博弈型 DP @source

Related: Coins in A Line // Predict the Winner <~similar~> Stone Game (LC877): solution

@source

> Q1: Add up two numbers & 口述 LRU 实现

> Q2: Three Sum & Intersection of k vectors: 分治 O(nlogn)

> Q3: 快速查找 IP ⇒ [Trie] & Friend Circle: [DFS] / [union find]

> Q4: Reverse Linked List & Find Kth Largest Number [quick sort]

> Q5: 迷宫走到终点最少步数

> Q6.1: 二叉树最大路径和 Binary Tree Maximum Path Sum (ctrl+f): submission

> Q6.2: Find Kth num in two sorted array: 应该是寻找中位数的follow up。我给了two pointers的On，要求logn，最后在提示下写出用k / 2 - 1作为边界的二分法；

> Q7.1: Trapped Rain Water

> Q7.2: 迷宫中到达终点的路径数量，只能右or下，1代表墙（follow up限制拐弯次数）

第一题用了左右两个指针；

第二题一开始是用了动态规划，加了额外条件以后用dfs，传参记录拐弯次数。还被问了在dfs情况下如何进一步提升，答用空间换时间，memo数组用来剪枝。

### Apple

@source

> Q: Permutation of numbers such that sum of two consecutive numbers is a perfect square

给一个数 n, 找出 1 到 n 的 permutation array s.t. 相邻的数相加都是 square number.

e.g.: n = 15 ⇒ [8，1，15，10，6，3，13，12，4，5，11，14，2，7，9], 
since 1 + 8 = 9 = 3 * 3, 1 + 15 = 16 =4 * 4.

Related to: Number of Squareful Arrays (hard) (LC996)

> Q2-1: Combination Sum // follow-up: 打出所有组合 / 复杂度

> Q2-2: 打印对称数组

```
e.g.: [1, 2, 3]               [1, 4, 7]
      [4, 5, 6]     -->       [2, 5, 8]
      [7, 8, 9]               [3, 6, 9]
```

Related to: Rotate Image

> Q: Flatten 2D Vector (LC251) @source

> Q: Serialize and Deserialize N-ary Tree @source

> Q: Group Anagrams @source

@source

> Q1: LFU Cache

> Q2: Longest Valid Parentheses

> Q3: Generate Parentheses

> Q: 给定一个有向图, 找出一个节点, 使得从这个节点出发, reach 到的节点总数最多. 如果有 tie 则返回其中一个即可. @source

@source: OS Performance Engineer

> Q: String Compression

Apple Performance Engineer 面试准备

mutex

# 面试笔记

Nuro

电面 Code @2020.03.09

Kadane’s Algorithm: Maximum Subarray ⇒ Follow up: Max Sum of Rectangle in a 2D matrix

电面 ML @2020.03.13

SAC on/off policy / list RL algorithms / projects

Video Onsite @2020.04.02

Design a buffer that supports read & write

Union Find: Cluster High-dim Points

TuSimple

电面 @2020.03.16: Q: Split a Matrix 问能否把一个 0-1 矩阵划分成每格有相同数量 1 (ctrl+f)

电面 @2020.03.27

![](/notes/leetcode/media/image38.png)

Google AI Residency

电面 @2020.03.19: Q: Frog Jump (LC403)

电面 Research @2020.05.07

Facebook

电面 @2020.03.20

> Q: Course Schedule & Design Question:

![](/notes/leetcode/media/image39.png)

Video Onsite @2020.04.09

Round 1:

> Q: add two floats string: “3.14” + ”12.9” → “16.04”

Round 2:

> Q: Kth Largest Element in an Array (solved by partition)

> Q: implement readLines() by an interface read4k() which reads the first 4k bits each time.

ByteDance 

电面 CV + Code @2020.05.13: Non-decreasing Array (LC665)

电面 Code @2020.05.19: number of ways to color a binary tree (local)

电面 Code @2020.05.28: build post offices (local)

HR Interview @2020.06.01: 旗下产品

在美 Office LA > NY / Mountain View. Applied ML group 30/80 人在 US, MV > Seattle.

Overall 300, SDE 过半 // AI Lab v.s. Applied ML // Lark app

国内部门交叉电面 Code @2020.06.02

Apple

电面 @2020.06.02

简历 Optimization

代码: Q: Majority Element II

1. HashMap: Time O(n) & Space O(n)

2. Sorting: Time O(nlogn) & Space O(1)

3. One-pass solution: Time O(n) & Space O(1)

# MISC

### Python

max & min

float('inf')   # max
float('-inf')  # min

2D array

```
 f = [[0] * n for _ in range(n)]
```

Ceiling Division

-(-a // b)

排序方式

```python
intervals = sorted(intervals, key = lambda x: x.start) 

dictionary ={1:"c",2:"b"}

# Sort dictionary by key:
sorted(dictionary.items(), key = lambda kv: kv[0])
# [(1, 'c'), (2, 'b')]

# Sort dictionary by value:
sorted(dictionary.items(), key = lambda kv: kv[1])
# [(2, 'b'), (1, 'c')]

# Sort only values by key:
[kv[1] for kv in sorted(self.hashtable.items(), key = lambda kv: kv[0])]
```

BFS 数据结构

visited 用 set 比 list 好。set 是一个 hashtable, 检查 if in set 时间复杂度是 O(1)。

```python
graph = defaultdict(lambda: list())
graph = defaultdict(list)
```

Dict to List: sorted by key

```
# dictionary = {0: [3, 15], -1: [9], 1: [20], 2: [7]})
lst = [dictionary[i] for i in sorted(dictionary)]
```

Dict default values

```python
dict = {'Name': 'Zara', 'Age': 7}
print "Value : %s" %  dict.setdefault('Age', None)  # out: Value : 7
print "Value : %s" %  dict.setdefault('Sex', None)  # out: Value : None
```

26 Letters

```python
list(map(chr, range(97, 123)))
list(map(chr, range(ord('a'), ord('z')+1)))
# ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

import string
string.ascii_lowercase  
# 'abcdefghijklmnopqrstuvwxyz'
```

### 算法频率 Data Structures

![](/notes/leetcode/media/image40.png)

### 算法频率

![](/notes/leetcode/media/image41.png)

http://joshuablog.herokuapp.com/Leetcode-%E6%80%BB%E7%BB%93.html

- BFS

- 模拟 (e.g.: strange sort, Integer -> Roman)

- DFS \ 二叉树 \ 基础 DP (背包 \ 序列 DP \ 坐标 DP \ 双序列 DP (LCS) \ 常见题 LIS) \ 隐式图老题 (word ladder

- 二分答案 \ 双指针 \ 前缀和 \ 排序 \ 扫描线

- 数据结构 Heap \ Quick Select \ Quick Sort \ Union Find \ Trie \ 隐式图新题

- 二分搜索 \ 进阶 DP (区间 DP \ 概率 DP) \ Monotonus Stack \ Bit Operation \ 最小生成树 MST \ Dijaska \ SPFA

- 找 bridge (tarjan)

链表是否有环

带环链表 102 103

![](/notes/leetcode/media/image42.png)

# TODO

https://leetcode.com/articles/unique-paths-iii/

https://www.lintcode.com/problem/coin-change-2/description

https://leetcode.com/problems/partition-to-k-equal-sum-subsets/solution/
