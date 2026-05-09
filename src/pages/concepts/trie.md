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

- [Implement Trie (Prefix Tree)](https://leetcode.com/problems/implement-trie-prefix-tree/)
- [Add and Search Word — Data Structure Design](https://leetcode.com/problems/design-add-and-search-words-data-structure/)
- [Word Search II](https://leetcode.com/problems/word-search-ii/)
- [Replace Words](https://leetcode.com/problems/replace-words/)
- [Word Squares](https://www.lintcode.com/problem/word-squares/)
- [Maximum XOR of Two Numbers in an Array](https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/) (binary trie)
