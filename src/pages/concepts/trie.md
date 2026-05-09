---
layout: ../../layouts/Layout.astro
title: Trie / Prefix Tree
---

# Trie / Prefix Tree

> Tree of characters. `insert` and `lookup` in O(len(word)) — independent of dictionary size.

## When to use

- Prefix queries / autocomplete
- Word search in a grid (avoid re-checking dead branches with prefix-prune)
- Streaming: add words and look them up over time
- IP routing / longest-prefix match

## Trie vs hash

- Hash: O(len) for hashing the key + collisions.
- Trie: same O(len) but **prefix queries are free** and you can prune mid-word.
- Trie costs more memory unless words share prefixes.

## Template (dict-based — shortest)

```python
class Trie:
    def __init__(self):
        self.root = {}

    def insert(self, word):
        node = self.root
        for c in word:
            node = node.setdefault(c, {})
        node["#"] = True               # end-of-word sentinel

    def search(self, word):
        node = self._walk(word)
        return bool(node and node.get("#"))

    def starts_with(self, prefix):
        return self._walk(prefix) is not None

    def _walk(self, s):
        node = self.root
        for c in s:
            if c not in node: return None
            node = node[c]
        return node
```

## Template (class-based — clearer when extending)

```python
class TrieNode:
    __slots__ = ("children", "is_word")
    def __init__(self):
        self.children = {}
        self.is_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
    def insert(self, word):
        node = self.root
        for c in word:
            if c not in node.children:
                node.children[c] = TrieNode()
            node = node.children[c]
        node.is_word = True
```

## Word search in grid (Trie-pruned DFS)

Build a trie of all words; DFS the grid only following children that exist in the current trie node. Mark word in trie when found, then *delete* the leaf to avoid duplicates.

```python
def find_words(board, words):
    root = build_trie(words)
    rows, cols = len(board), len(board[0])
    res = []
    def dfs(r, c, node, path):
        ch = board[r][c]
        nxt = node.children.get(ch)
        if not nxt: return
        path.append(ch)
        if nxt.is_word:
            res.append("".join(path))
            nxt.is_word = False     # dedupe
        board[r][c] = "#"
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != "#":
                dfs(nr, nc, nxt, path)
        board[r][c] = ch
        path.pop()
    for r in range(rows):
        for c in range(cols):
            dfs(r, c, root, [])
    return res
```

## Variants

- **Compressed trie / radix tree**: collapse single-child chains. Less memory, more code.
- **Suffix trie / suffix array**: for substring queries.
- **Wildcard search** (`.` matches any): recurse into all children when the query char is `.`.

## Gotchas

- End-of-word marker: pick a sentinel (`"#"` or `is_word: bool`) and stick with it — easy to mix up.
- Don't forget to **walk back up** to clean state in DFS (or trie traversal won't recover).
- For huge alphabets (Unicode), use a dict, not a fixed-size array.

## Practice

- **Implement Trie (Prefix Tree)** — `insert`, `search`, `startsWith`. *Insight:* mark end-of-word with a sentinel (`is_word: bool` or `"#"` key). [LC 208](https://leetcode.com/problems/implement-trie-prefix-tree/)
- **Add and Search Word (with `.` wildcard)** — `search` may contain `.` matching any char. *Insight:* DFS at each `.` over all current children; otherwise normal trie walk. [LC 211](https://leetcode.com/problems/design-add-and-search-words-data-structure/)
- **Word Search II** — find all dictionary words present in a grid (4-dir adjacency). *Insight:* build trie of dictionary; DFS each grid cell, only following children that exist in trie. Mark words found and prune leaves. [LC 212](https://leetcode.com/problems/word-search-ii/)
- **Replace Words** — replace each word in a sentence by its shortest dictionary root prefix. *Insight:* insert all roots; for each word, walk the trie and stop at the first end-of-word. [LC 648](https://leetcode.com/problems/replace-words/)
- **Word Squares** — build NxN grids where row[i] == col[i]. *Insight:* DFS row-by-row; the next row must start with the column-prefix above; trie indexed by prefix yields candidates fast. [LintCode 634](https://www.lintcode.com/problem/word-squares/)
- **Maximum XOR of Two Numbers in an Array** — max `a ^ b` over pairs. *Insight:* binary trie of 32-bit ints; greedily descend toward the opposite bit at each level to maximize XOR. [LC 421](https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/)
