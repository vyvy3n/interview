---
layout: ../../layouts/Layout.astro
title: Cheatsheet (核心模板)
---

```python
class Node:
    def __init__(self, key= None, value = None):
        self.key, self.val = key, value
        self.prev, self.next = None, None
class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.hash = {}
        self.head = Node(-1, -1)  # dummy, 1st start at self.head.next
        self.tail = Node(-1, -1)  # dummy node
        self.tail.prev = self.head
        self.head.next = self.tail
    def get(self, key: int) -> int:
        if key not in self.hash: return -1
        node = self.hash[key]
        self.remove_node(node)
        self.add_to_tail(node)
        return node.val
    def put(self, key: int, value: int) -> None:
        if key in self.hash:
            node = self.hash[key]
            node.val = value
            self.remove_node(node)
        else:
            if len(self.hash) == self.capacity:
                self.pop_head()
            node = Node(key, value)
        self.add_to_tail(node)
        self.hash[key] = node
    def remove_node(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev    
        node.next = None
        node.prev = None
    def add_to_tail(self, node):
        node.prev = self.tail.prev
        node.next = self.tail
        node.prev.next = node
        self.tail.prev = node
    def pop_head(self):
        print("pop",self.head.next.key)
        del self.hash[self.head.next.key]
        self.head.next = self.head.next.next
        self.head.next.prev = self.head
```

# Heapify

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

```
2 * T(n) = O(n/2) + O(n/4 * 2) + O(n/8 * 3) + O(n/16 * 4) ... 
    T(n) =          O(n/4)     + O(n/8 * 2) + O(n/16 * 3) ...
2 * T(n) - T(n) = O(n/2) +O (n/4) + O(n/8) + ...
                = O(n/2 + n/4 + n/8 + ... )
                = O(n)
```

# Union Find

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

# Topo Sort

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
        for neigbhor in node.neighbors:
            indegree_list[neighbor] -= 1 
            if indegree_list[neighbor] == 0:
                queue.append(neighbor)
    return order
```

##### DFS 拓扑排序

```python
def topSort(self, graph): 
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

```python
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

```python
def kthSmallest(self, matrix: List[List[int]], k: int) -> int:
    n = len(matrix)
    start, end = matrix[0][0], matrix[n - 1][n - 1]

    while start < end:  # ATTENTION
        mid = (start + end) // 2
        smaller, larger = (matrix[0][0], matrix[n - 1][n - 1])
        count, smaller, larger = self.countLessEqual(matrix, mid, smaller, larger)

        if count == k:
            return smaller
        if count < k:
            start = larger  # search higher
        else:
            end = smaller  # search lower
    return start

def countLessEqual(self, matrix, mid, smaller, larger):
    count, n = 0, len(matrix)
    row, col = n - 1, 0
    while row >= 0 and col < n:
        if matrix[row][col] > mid:
            larger = min(larger, matrix[row][col])
            row -= 1
        else:
            smaller = max(smaller, matrix[row][col])
            count += row + 1
            col += 1
    return count, smaller, larger
```

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

# Partition

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

```python
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

```python
def solve(self, num1: str, num2: str) -> str:
    len1 = len(num1)
    len2 = len(num2)
    if len1 == 0 and len2 == 0: return ""
    if len1 == 0: return num2
    if len2 == 0: return num1
    if num1[0] == "-":
        if num2[0] == "-":  # - (abs(num1) + abs(num2))
            return "-" + self.addStrings(num1[1:], num2[1:], len1 - 1, len2 - 1)
        else:               # num2 - num1
            return self.subStrings(num2, num1[1:], len2, len1 - 1)
    else:
        if num2[0] == "-":  # num1 - num2
            return self.subStrings(num1, num2[1:], len1, len2 - 1)
        else:               # num1 + num2
            return self.addStrings(num1, num2, len1, len2)
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
def subStrings(self, num1, num2, len1, len2) -> str:
    # return string of num1 - num2
    res = ""
    carry = 0
    prev_borrow = 0
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
    while res[0] == "0":
        res = res[1:]
    return res
```

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

# DFS backtracking

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

# 分层 BFS

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
