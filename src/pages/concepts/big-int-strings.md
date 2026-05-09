---
layout: ../../layouts/Layout.astro
title: Big-Int String Math
---

# Big-Int String Math

> Add, subtract, multiply numbers given as strings — when integers don't fit in 64 bits.

## Add Strings

```python
def add_strings(a, b):
    i, j = len(a) - 1, len(b) - 1
    carry = 0
    out = []
    while i >= 0 or j >= 0 or carry:
        d = carry
        if i >= 0: d += int(a[i]); i -= 1
        if j >= 0: d += int(b[j]); j -= 1
        carry, d = divmod(d, 10)
        out.append(str(d))
    return "".join(reversed(out))
```

The `or carry` in the loop condition catches the final carry-out.

## Multiply Strings

Trick: result of `len(a) × len(b)` digits fits in `len(a) + len(b)` slots. Each digit pair `(a[i], b[j])` contributes to positions `i+j` and `i+j+1`.

```python
def multiply(a, b):
    if a == "0" or b == "0": return "0"
    n, m = len(a), len(b)
    res = [0] * (n + m)
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            mul = int(a[i]) * int(b[j])
            p1, p2 = i + j, i + j + 1
            total = mul + res[p2]
            res[p2] = total % 10
            res[p1] += total // 10
    # strip leading zeros
    s = "".join(map(str, res)).lstrip("0")
    return s or "0"
```

## Subtraction (with borrow + sign)

To subtract, borrow column-by-column:

```python
def sub_strings(a, b):           # assume a >= b, both non-negative
    i, j = len(a) - 1, len(b) - 1
    borrow = 0
    out = []
    while i >= 0:
        d = int(a[i]) - borrow - (int(b[j]) if j >= 0 else 0)
        if d < 0:
            d += 10
            borrow = 1
        else:
            borrow = 0
        out.append(str(d))
        i -= 1; j -= 1
    return "".join(reversed(out)).lstrip("0") or "0"
```

For full add-and-subtract handling negatives: dispatch on signs to call `add` or `sub` with the larger magnitude first, then prepend `-` if needed.

## Plus One Linked List

Same idea but in reverse on the list — easier to reverse the list, add 1, reverse back. Or recurse:

```python
def plus_one(head):
    def helper(node):
        if not node: return 1
        carry = helper(node.next)
        node.val += carry
        carry, node.val = divmod(node.val, 10)
        return carry
    carry = helper(head)
    if carry:
        new = ListNode(carry)
        new.next = head
        return new
    return head
```

## Gotchas

- Always handle the **final carry / borrow** outside the loop body.
- Strip leading zeros at the end, but return `"0"` (not `""`) for zero.
- For multiplication, watch the index math: `i + j` is the *higher* digit, `i + j + 1` is the lower.

## Practice

- [Add Strings](https://leetcode.com/problems/add-strings/) · [Add Binary](https://leetcode.com/problems/add-binary/)
- [Multiply Strings](https://leetcode.com/problems/multiply-strings/)
- [Plus One](https://leetcode.com/problems/plus-one/) · [Plus One Linked List](https://www.lintcode.com/problem/plus-one-linked-list/)
- [Add Two Numbers](https://leetcode.com/problems/add-two-numbers/) (linked list)
- [String to Integer (atoi)](https://leetcode.com/problems/string-to-integer-atoi/)
