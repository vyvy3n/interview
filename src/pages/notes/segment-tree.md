---
layout: ../../layouts/Layout.astro
title: Segment Tree
---

# 1 线段树

线段树和树状数组

对于求区间和的问题，可选方法有：暴力 \ 前缀和 \ 后缀和 \ 线段数

关于维护一个序列的问题 e.g.: 给定一个整数序列，每次操作会修改序列某个位置上的数，或是询问你序列中某个区间内所有数的和。

|  | 修改时间 | 查询时间 | 空间 |
| --- | --- | --- | --- |
| 暴力 | O(1) | O(n) | O(1) |
| 前缀和数组 | O(n) | O(1) | O(n) |
| 线段树 | O(logn) | O(logn) | O(n) |

区间的长度：左边上取整, 右边下取整。

区间下标值：左边下取整, 右边上取整。

e.g.: [1, 10] 区间左节点是 [1, 5] ⇐ floor((1 + 10) / 2) = 5

![](/notes/segment-tree/media/image1.png)

![](/notes/segment-tree/media/image2.png)

线段树的构造

线段树单点修改的递归结束条件是：start == end

# 2 线段树实战

### 查询 Interval Sum

> Q: Interval Sum | solution 倒 4 submission

若 n 为数组长度, m 为查询次数:

- 暴力求和 O(mn)

- 树状数组 / 线段树查询区间和 O(mlogn)

- 前缀和数组 O(m + n)

e.g.:

![](/notes/segment-tree/media/image3.png)

coding:

```python
/**
 * Definition of Interval:
 * public classs Interval {
 *     int start, end;
 *     Interval(int start, int end) {
 *         this.start = start;
 *         this.end = end;
 *     }
 * }
 */

public class Solution {
    /**
     * @param A: An integer list
     * @param queries: An query list
     * @return: The result list
     */
    public List<Long> intervalSum(int[] A, List<Interval> queries) {
        List<Long> ret = new ArrayList<>();
        SegmentTree tree = new SegmentTree(A);
        for (Interval i : queries) {
            ret.add(tree.querySum(i.start, i.end));
        }
        return ret;
    }
}

class SegmentTreeNode {
    public long sum;
    public int start, end;
    public SegmentTreeNode left, right;
    public SegmentTreeNode(int start, int end) {
        this.start =  start;
        this.end = end;
        sum = 0;
        left = null;
        right = null;
    }
}

// 封装类 segment tree
class SegmentTree {
    private int size;
    private SegmentTreeNode root;
    
    private SegmentTreeNode buildTree(int start, int end, int[] A) {
        SegmentTreeNode node = new SegmentTreeNode(start, end);
        if (start == end) {
            node.sum = A[start];
            return node;
        }
        int mid = (start + end) / 2;
        node.left = buildTree(start, mid, A);
        node.right = buildTree(mid + 1, end, A);
        node.sum = node.left.sum + node.right.sum;
        return node;
    }
    
    public SegmentTree(int[] A) {
        size = A.length;
        root = buildTree(0, size - 1, A);
    }
    
    // 在 node 节点下，查询原数组 [start, end] 区间和
    private long querySum(SegmentTreeNode node, int start, int end) {
        // ATTENTION: 查询和构造 node 不同. 终止条件不是 start == end
        if (node.start == start && node.end == end) {
            return node.sum;
        }
        
        // ATTENTION: 查询时候 node.start + node.end 而不是 start + end
        int mid = (node.start + node.end) / 2;
        long leftSum = 0, rightSum = 0;
        
        if (start <= mid) {
            leftSum = querySum(node.left, start, Math.min(mid, end));
        }
        if (end >= mid + 1) {
            rightSum = querySum(node.right, Math.max(mid + 1, start), end);
        }
        
        return leftSum + rightSum;
    }
    
    // 外界要调用的查询函数 public
    public long querySum(int start, int end) {
        // 查询是需要节点信息的. 在此定义重载函数
        return querySum(root, start, end);
    }
}
```

### 查询 + 修改 Interval Sum II

> Q: Interval Sum II | solution 倒一 submission

注意: modify 不需要返回值. (java) 但 start == end 时需要 return;

### 拓展题目 Count of Smaller Num

> Q: Count of Smaller Number | solution

若 n 为数组长度, m 为查询次数, k 为数组最大值:

- 暴力求解 O(mn): 每次遍历数组

- 树状数组 / 线段树 O(mlogk): 比如题目中最大值 k = 10000

- 二分法 O(nlogn + mlogn): 首先排序需 nlogn, 之后 m 次查询 mlogn

- 前缀和数组 O(m + n + k): 时间线性是最优的. 但无法解决 follow-up 问题.

线段树解法思路:

- 数组 B: B[i] 表示 i 这个值出现了几次 (题目中数组范围 0 ~ 10000)

- 查询比 x 小的元素的个数相当于 B 的 x - 1 前缀和: B[0] + … + B[x - 1]

- 使用线段树维护 B 数组

- class SegmentTree

```
    SegmentTree(int size)
    QuerySum(int start, int end)
    modify(int index, int val)
```

> Q: Count of Smaller Number before itself | solution

若 n 为数组长度, k 为数组最大值:

- 暴力求解 O(n^2)

- 树状数组 / 线段树 O(mlogk)

线段树解法思路:

- 数组 B: B[i] 表示数组 A 当前元素之前 i 出现了几次

> 两题对比: 线段树定义完全一样. 调用求解方式有所不同.

Count of Smaller Number:

```python
public class Solution {
    public List<Integer> countOfSmallerNumber(int[] A, int[] queries) {
        int[] B = new int[10001];  // 0 ~ 10000
        for (int i : A) {
            B[i]++;
        }
        
        SegmentTree tree = new SegmentTree(10001);
        for (int i = 0; i <= 10000; i++) {
            tree.modify(i, B[i]);
        }
        
        List<Integer> ret = new ArrayList<>();
        for (int i : queries) {
            if (i == 0) {
                ret.add(0);
            }
            else {
                ret.add(tree.querySum(0, i - 1));
            }
        }
        return ret;
    }
}
```

Count of Smaller Number before itself:

```python
public class Solution {
    public List<Integer> countOfSmallerNumberII(int[] A) {
        int[] B = new int[10001];  // 0 ~ 10000
        SegmentTree tree = new SegmentTree(10001);
        List<Integer> ret = new ArrayList<>();
        for (int i : A) {
            if (i == 0) {
                ret.add(0);
            }
            else {
                ret.add(tree.querySum(0, i - 1));
            }
            B[i]++;
            tree.modify(i, B[i]);
        }
        return ret;
    }
}
```

### 基础练习 Build & Query & Modify

> Q: Segment Tree Build II

> Q: Segment Tree Build

> Q: Segment Tree Query II

> Q: Segment Tree Modify

Notes: 选好左右子树操作后记得更新根节点信息

root.max = Math.max(root.left.max, root.right.max);

> Q: Segment Tree Query

Notes: right 需要 mid + 1 \\ 两边都取 Math.min() / Math.max()

leftMax = this.query(node.left, start, Math.min(mid, end));
// ...
rightMax = this.query(node.right, Math.max(start, mid + 1), end);

# 3 树状数组

树状数组是通过前缀和思想，用来完成单点更新和区间查询的数据结构。它比之线段树，所用空间更小 (Segment Tree 需要指针和 node)，速度更快。

构建和查询

树状数组理解参见 slides

![](/notes/segment-tree/media/image4.png)

![](/notes/segment-tree/media/image5.png)

![](/notes/segment-tree/media/image6.png)

### lowbit(x): return x & (-x);

- num & (-num) == 2 ^ k

- e.g.: 10001010 的补码是 01110110

### > Q: Range Sum | solution

```python
public class NumArray {
    private int[] arr, bit;

    public NumArray(int[] nums) {
        arr = new int[nums.length];
        bit = new int[nums.length + 1];
        
        for (int i = 0; i < nums.length; i++) {
            update(i, nums[i]);
        }
    }
    
    public void update(int index, int val) {
        int delta = val - arr[index];
        arr[index] = val;
        
        for (int i = index + 1; i <= arr.length; i = i + lowbit(i)) {
            bit[i] += delta;
        }
    }
    
    public int getPrefixSum(int index) {
        int sum = 0;
        for (int i = index + 1; i > 0; i = i - lowbit(i)) {
            sum += bit[i];
        }
        return sum;
    }
    
    private int lowbit(int x) {
        return x & (-x);
    }

    public int sumRange(int left, int right) {
        return getPrefixSum(right) - getPrefixSum(left - 1);
    }
}
```

课后问答题

![](/notes/segment-tree/media/image7.png)

![](/notes/segment-tree/media/image8.png)

![](/notes/segment-tree/media/image9.png)

![](/notes/segment-tree/media/image10.png)

![](/notes/segment-tree/media/image11.png)

![](/notes/segment-tree/media/image12.png)

若求区间 (i, j) 的区间和 rangeSum(i, j)

- 使用前缀和时，rangeSum(i, j) = sum(j) - sum(i)，时间复杂度为O(1)。

- 使用线段树时，需要从根向下搜索，找到所有包含且仅包含 (i, j) 中元素的区间和，所有的深度最大为树的高度，时间复杂度为 O(log n)。

- 使用树状数组，根据公式 sum(i) = sum(i - lowbit(i)) + C[i]，使用树状数组求前缀和的时间复杂度为 O(log n)。区间和 rangeSum(i, j) = sum(j) - sum(i)，求区间和的操作可以转换为求两次前缀和，因此时间复杂度也是 O(log n)。

# 4 树状数组实战

### 查询 Interval Sum

![](/notes/segment-tree/media/image13.png)
> Q: Interval Sum | solution 倒数第五个 submission

```python
public class Solution {
    /**
     * @param A: An integer list
     * @param queries: An query list
     * @return: The result list
     */
    public List<Long> intervalSum(int[] A, List<Interval> queries) {
        List<Long> ret = new ArrayList<>();
        BinaryIndexTree tree = new BinaryIndexTree(A);
        for (Interval i : queries) {
            if (i.start == 0) {
                ret.add(tree.prefixSum(i.end));
            }
            else {
                ret.add(tree.prefixSum(i.end) - 
                        tree.prefixSum(i.start - 1));
            }
        }
        return ret;
    }
}

class BinaryIndexTree {
    private long[] a;
    private int size;
    private int lowbit(int x) {
        return x & (-x);
    }
    
    public BinaryIndexTree(int[] A) {
        size = A.length;
        a = new long[size + 1];
        for (int i = 0; i < size; i++) {
            add(i, A[i]);
        }
    }
        
    // A[index] += val
    public void add(int index, int val) {
        index++;
        while (index <= size) {
            a[index] += val;
            index += lowbit(index);
        }
    }
    
    // A[0] + ... + A[index]
    public long prefixSum(int index) {
        index++;
        long ret = 0;
        while (index > 0) {
            ret += a[index];
            index -= lowbit(index);
        }
        return ret;
    }
}
```

### 查询 + 修改 Interval Sum II

> Q: Interval Sum II | solution 倒二 submission

### 拓展题目 Count of Smaller Num

> Q: Count of Smaller Number | solution

> Q: Count of Smaller Number before itself | solution

```
public List<Integer> countOfSmallerNumberII(int[] A) {
    int max = -1;
    
    for (int i : A) {
        max = Math.max(max, i);
    }
    
    BinaryIndexTree tree = new BinaryIndexTree(max + 1);
    
    List<Integer> ret = new ArrayList<>();
    for (int i = 0; i < A.length; i++) {
        if (i == 0) {
            ret.add(0);
        }
        else {
            ret.add(tree.prefixSum(A[i] - 1));
        }
        // B[A[i]]++
        tree.add(A[i], 1);
    }
    return ret;
}
```

其中循环部分还可如下写:

```
    for (int i : A) {
        if (i == 0) {
            ret.add(0);
        }
        else {
            ret.add(tree.prefixSum(i - 1));
        }
        tree.add(i, 1);
    }
```

### 基础练习 Build & Query & Modify

> Q: Segment Tree Build II

> Q: Segment Tree Build

> Q: Segment Tree Query II

> Q: Segment Tree Modify

> Q: Segment Tree Query
