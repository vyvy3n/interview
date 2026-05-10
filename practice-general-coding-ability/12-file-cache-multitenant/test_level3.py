"""
Level 3 tests — set_capacity + LRU eviction
Run: python3 test_level3.py
"""

import unittest
from solution import FileCache


class TestLevel3SetCapacity(unittest.TestCase):
    def setUp(self):
        self.cache = FileCache()

    def test_set_capacity_no_eviction_needed_returns_zero(self):
        self.cache.store("a.txt", "A")
        self.cache.store("b.txt", "B")
        evicted = self.cache.set_capacity(5)
        self.assertEqual(evicted, 0)

    def test_set_capacity_exact_count_returns_zero(self):
        self.cache.store("a.txt", "A")
        self.cache.store("b.txt", "B")
        evicted = self.cache.set_capacity(2)
        self.assertEqual(evicted, 0)

    def test_set_capacity_evicts_excess(self):
        for i in range(5):
            self.cache.store(f"f{i}.txt", f"v{i}")
        evicted = self.cache.set_capacity(3)
        self.assertEqual(evicted, 2)
        self.assertEqual(self.cache.size(), 3)

    def test_set_capacity_evicts_all_returns_count(self):
        self.cache.store("a.txt", "A")
        self.cache.store("b.txt", "B")
        evicted = self.cache.set_capacity(0)
        self.assertEqual(evicted, 2)
        self.assertEqual(self.cache.size(), 0)

    def test_set_capacity_returns_int(self):
        self.cache.store("f.txt", "data")
        result = self.cache.set_capacity(10)
        self.assertIsInstance(result, int)

    def test_capacity_enforced_on_new_stores(self):
        self.cache.set_capacity(3)
        for i in range(5):
            self.cache.store(f"f{i}.txt", f"v{i}")
        self.assertEqual(self.cache.size(), 3)


class TestLevel3LRUOrder(unittest.TestCase):
    def setUp(self):
        self.cache = FileCache()

    def test_lru_evicts_oldest_accessed_first(self):
        # Store 3 files in order: a, b, c
        # LRU order (oldest first): a, b, c
        self.cache.store("a.txt", "A")
        self.cache.store("b.txt", "B")
        self.cache.store("c.txt", "C")
        # Evict down to 2 — should remove "a.txt" (oldest)
        self.cache.set_capacity(2)
        self.assertEqual(self.cache.fetch("a.txt"), "")
        self.assertNotEqual(self.cache.fetch("b.txt"), "")
        self.assertNotEqual(self.cache.fetch("c.txt"), "")

    def test_fetch_refreshes_lru(self):
        self.cache.store("a.txt", "A")
        self.cache.store("b.txt", "B")
        self.cache.store("c.txt", "C")
        # Touch "a.txt" to refresh it — now LRU order: b, c, a
        self.cache.fetch("a.txt")
        # Evict down to 2 — should remove "b.txt"
        self.cache.set_capacity(2)
        self.assertEqual(self.cache.fetch("b.txt"), "")
        self.assertNotEqual(self.cache.fetch("a.txt"), "")
        self.assertNotEqual(self.cache.fetch("c.txt"), "")

    def test_update_refreshes_lru(self):
        self.cache.store("a.txt", "A")
        self.cache.store("b.txt", "B")
        self.cache.store("c.txt", "C")
        # Touch "a.txt" via update — LRU order: b, c, a
        self.cache.update("a.txt", "A-updated")
        # Evict down to 2 — should remove "b.txt"
        self.cache.set_capacity(2)
        self.assertEqual(self.cache.fetch("b.txt"), "")
        self.assertNotEqual(self.cache.fetch("a.txt"), "")

    def test_fetch_by_prefix_does_not_refresh_lru(self):
        self.cache.store("x.txt", "X")
        self.cache.store("y.txt", "Y")
        self.cache.store("z.txt", "Z")
        # fetch_by_prefix should NOT protect "x.txt" from eviction
        self.cache.fetch_by_prefix("x")
        # Evict down to 2 — "x.txt" was stored first; prefix search didn't refresh it
        self.cache.set_capacity(2)
        self.assertEqual(self.cache.fetch("x.txt"), "")

    def test_new_store_evicts_lru_when_at_capacity(self):
        self.cache.set_capacity(3)
        self.cache.store("a.txt", "A")
        self.cache.store("b.txt", "B")
        self.cache.store("c.txt", "C")
        # Adding a 4th file should evict "a.txt" (LRU)
        self.cache.store("d.txt", "D")
        self.assertEqual(self.cache.fetch("a.txt"), "")
        self.assertEqual(self.cache.fetch("d.txt"), "D")
        self.assertEqual(self.cache.size(), 3)

    def test_update_evicts_lru_when_would_exceed_capacity(self):
        # update doesn't add a new file so no eviction should happen
        self.cache.set_capacity(2)
        self.cache.store("a.txt", "A")
        self.cache.store("b.txt", "B")
        # Update does NOT trigger eviction (same file count)
        self.cache.update("a.txt", "new-A")
        self.assertEqual(self.cache.size(), 2)
        self.assertEqual(self.cache.fetch("a.txt"), "new-A")

    def test_lru_chain_multiple_evictions(self):
        # Store 5, set capacity to 2 — 3 must be evicted in LRU order
        for i in range(5):
            self.cache.store(f"f{i}.txt", "v")
        # Touch f4, f3 to make them recent (f0 is oldest, then f1, f2)
        self.cache.fetch(f"f4.txt")
        self.cache.fetch(f"f3.txt")
        evicted = self.cache.set_capacity(2)
        self.assertEqual(evicted, 3)
        # f0, f1, f2 should be gone
        for i in range(3):
            self.assertEqual(self.cache.fetch(f"f{i}.txt"), "", f"f{i}.txt should be evicted")
        # f3, f4 should remain
        self.assertNotEqual(self.cache.fetch("f3.txt"), "")
        self.assertNotEqual(self.cache.fetch("f4.txt"), "")

    def test_store_after_capacity_enforced_respects_limit(self):
        self.cache.set_capacity(2)
        self.cache.store("a.txt", "A")
        self.cache.store("b.txt", "B")
        self.cache.store("c.txt", "C")  # evicts a
        self.cache.store("d.txt", "D")  # evicts b
        self.assertEqual(self.cache.size(), 2)
        self.assertEqual(self.cache.fetch("c.txt"), "C")
        self.assertEqual(self.cache.fetch("d.txt"), "D")


class TestLevel3Integration(unittest.TestCase):
    def test_capacity_set_after_fills(self):
        cache = FileCache()
        for i in range(10):
            cache.store(f"f{i}.txt", "data")
        # All 10 in, set capacity to 5
        evicted = cache.set_capacity(5)
        self.assertEqual(evicted, 5)
        self.assertEqual(cache.size(), 5)
        # The 5 most recently stored (f5-f9) should remain
        for i in range(5, 10):
            self.assertNotEqual(cache.fetch(f"f{i}.txt"), "", f"f{i}.txt should still exist")

    def test_l1_l2_methods_still_work_after_set_capacity(self):
        cache = FileCache()
        cache.store("log.txt", "entry1")
        cache.store("readme.txt", "desc")
        cache.set_capacity(5)
        # L1 methods
        self.assertEqual(cache.fetch("log.txt"), "entry1")
        self.assertTrue(cache.remove("log.txt"))
        self.assertEqual(cache.size(), 1)
        # L2 methods
        cache.update("readme.txt", "updated desc")
        self.assertEqual(cache.get_total_size(), len("updated desc"))
        self.assertEqual(cache.fetch_by_prefix("read"), ["readme.txt"])


if __name__ == "__main__":
    unittest.main()
