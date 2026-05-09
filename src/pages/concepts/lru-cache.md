---
layout: ../../layouts/Layout.astro
title: LRU Cache
---

# LRU Cache

> Hash + doubly linked list. `get` / `put` in O(1).

## The data structure

- **Hash map**: `key → node` for O(1) lookup.
- **Doubly linked list**: nodes ordered by recency. Most-recently-used at the tail (or head — pick one).
- Two **dummy sentinels** so insert/remove never check for None.

## Operations

- `get(k)`: hash lookup → if hit, move node to tail, return value.
- `put(k, v)`: if key exists, update + move to tail. If new and at capacity, pop head; insert at tail.

## Implementation

```python
class Node:
    __slots__ = ("key", "val", "prev", "next")
    def __init__(self, key=0, val=0):
        self.key, self.val = key, val
        self.prev = self.next = None

class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.map = {}                     # key → Node
        self.head = Node()                # dummy: head.next is LRU
        self.tail = Node()                # dummy: tail.prev is MRU
        self.head.next = self.tail
        self.tail.prev = self.head

    # --- list helpers -----------------------------------------
    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_to_tail(self, node):
        node.prev = self.tail.prev
        node.next = self.tail
        self.tail.prev.next = node
        self.tail.prev = node

    # --- API --------------------------------------------------
    def get(self, key):
        if key not in self.map: return -1
        node = self.map[key]
        self._remove(node)
        self._add_to_tail(node)           # mark MRU
        return node.val

    def put(self, key, val):
        if key in self.map:
            node = self.map[key]
            node.val = val
            self._remove(node)
            self._add_to_tail(node)
            return
        if len(self.map) == self.cap:
            lru = self.head.next
            self._remove(lru)
            del self.map[lru.key]
        node = Node(key, val)
        self.map[key] = node
        self._add_to_tail(node)
```

## Why both structures?

- Hash alone: O(1) lookup but no order.
- Linked list alone: O(1) insert/remove given the node, but **finding the node** is O(n).
- Together: hash gives the node pointer in O(1); list lets you re-link in O(1).

## Pythonic shortcut: `OrderedDict`

```python
from collections import OrderedDict
class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.od = OrderedDict()
    def get(self, key):
        if key not in self.od: return -1
        self.od.move_to_end(key)         # mark MRU
        return self.od[key]
    def put(self, key, val):
        if key in self.od:
            self.od.move_to_end(key)
        self.od[key] = val
        if len(self.od) > self.cap:
            self.od.popitem(last=False)  # pop LRU
```

In an interview, write the explicit doubly-linked version unless asked otherwise — it shows you know the data structure.

## Gotchas

- **Store the key inside the node**, not just the value — you need it to delete from the hash on eviction.
- Sentinels (`head`, `tail`) eliminate every "if node is first/last" branch.
- For `put` on an existing key, **update value AND move-to-end** — easy to forget the move.

## Variants

- **LFU**: track usage count too. Two-level dict: `count → OrderedDict of nodes`.
- **TTL cache**: add `expires_at`; lazily evict on access.
- **Thread-safe LRU**: wrap each method with a lock.

## Practice

- [LRU Cache](https://leetcode.com/problems/lru-cache/)
- [LFU Cache](https://leetcode.com/problems/lfu-cache/)
- [Design In-Memory File System](https://leetcode.com/problems/design-in-memory-file-system/)
- [All O`one Data Structure](https://leetcode.com/problems/all-oone-data-structure/)
