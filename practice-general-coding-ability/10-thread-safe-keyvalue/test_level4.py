"""
Level 4 tests — Capacity cap and LRU eviction
Run: python3 test_level4.py
"""

import unittest
from solution import KVStore


class TestLevel4SetCapacity(unittest.TestCase):
    def setUp(self):
        self.kv = KVStore()

    def test_set_capacity_returns_zero_when_not_over(self):
        self.kv.put("a", "1")
        self.kv.put("b", "2")
        evicted = self.kv.set_capacity(5)
        self.assertEqual(evicted, 0)
        self.assertEqual(self.kv.count(), 2)

    def test_set_capacity_equal_to_count_no_eviction(self):
        self.kv.put("a", "1")
        self.kv.put("b", "2")
        evicted = self.kv.set_capacity(2)
        self.assertEqual(evicted, 0)

    def test_set_capacity_evicts_lru(self):
        # Insert a, b, c in order — a is LRU (lowest stamp)
        self.kv.put("a", "1")
        self.kv.put("b", "2")
        self.kv.put("c", "3")
        evicted = self.kv.set_capacity(2)
        self.assertEqual(evicted, 1)
        self.assertEqual(self.kv.count(), 2)
        # "a" should be gone (LRU)
        self.assertEqual(self.kv.get("a"), "")
        # "b" and "c" should remain
        self.assertEqual(self.kv.get("b"), "2")
        self.assertEqual(self.kv.get("c"), "3")

    def test_set_capacity_evicts_multiple(self):
        for i in range(5):
            self.kv.put(f"k{i}", str(i))
        evicted = self.kv.set_capacity(2)
        self.assertEqual(evicted, 3)
        self.assertEqual(self.kv.count(), 2)

    def test_set_capacity_returns_int(self):
        result = self.kv.set_capacity(10)
        self.assertIsInstance(result, int)

    def test_set_capacity_returns_eviction_count(self):
        for i in range(10):
            self.kv.put(f"k{i}", str(i))
        count = self.kv.set_capacity(3)
        self.assertEqual(count, 7)


class TestLevel4LRUOrdering(unittest.TestCase):
    def test_get_updates_access_order(self):
        kv = KVStore()
        kv.put("a", "1")  # a is LRU after this
        kv.put("b", "2")
        kv.put("c", "3")  # c is MRU

        # Access "a" — now "b" should be LRU
        kv.get("a")

        kv.set_capacity(2)  # evict 1 — should evict "b" (now LRU)
        self.assertEqual(kv.get("b"), "")
        self.assertEqual(kv.get("a"), "1")
        self.assertEqual(kv.get("c"), "3")

    def test_put_evicts_lru_when_at_capacity(self):
        kv = KVStore()
        kv.set_capacity(3)
        kv.put("a", "1")
        kv.put("b", "2")
        kv.put("c", "3")
        # At capacity. Adding "d" should evict "a" (LRU)
        kv.put("d", "4")
        self.assertEqual(kv.count(), 3)
        self.assertEqual(kv.get("a"), "")
        self.assertEqual(kv.get("d"), "4")

    def test_overwrite_does_not_evict(self):
        kv = KVStore()
        kv.set_capacity(2)
        kv.put("a", "1")
        kv.put("b", "2")
        # Overwrite "a" — should NOT evict anything (size unchanged)
        kv.put("a", "updated")
        self.assertEqual(kv.count(), 2)
        self.assertEqual(kv.get("a"), "updated")
        self.assertEqual(kv.get("b"), "2")

    def test_overwrite_updates_access_stamp(self):
        kv = KVStore()
        kv.set_capacity(2)
        kv.put("a", "1")  # a: oldest
        kv.put("b", "2")
        kv.put("a", "new_a")  # overwrite a → a is now MRU
        # Adding "c" should evict "b" (now LRU), not "a"
        kv.put("c", "3")
        self.assertEqual(kv.get("b"), "")
        self.assertEqual(kv.get("a"), "new_a")
        self.assertEqual(kv.get("c"), "3")

    def test_no_capacity_set_store_grows_unbounded(self):
        kv = KVStore()
        for i in range(500):
            kv.put(f"k{i}", str(i))
        self.assertEqual(kv.count(), 500)

    def test_get_at_hit_updates_lru(self):
        kv = KVStore()
        kv.put_with_ttl("a", "1", ttl=100, now=0)
        kv.put("b", "2")
        kv.put("c", "3")
        # "a" was inserted first; access it via get_at to update its stamp
        kv.get_at("a", now=1)
        # "b" should now be LRU
        kv.set_capacity(2)
        self.assertEqual(kv.get("b"), "")  # evicted
        self.assertEqual(kv.get_at("a", now=1), "1")
        self.assertEqual(kv.get("c"), "3")

    def test_get_miss_does_not_update_lru(self):
        kv = KVStore()
        kv.put("a", "1")
        kv.put("b", "2")
        # Miss on "x" — should not affect LRU order
        kv.get("x")
        kv.set_capacity(1)
        # "a" is still LRU — should be evicted
        self.assertEqual(kv.get("a"), "")
        self.assertEqual(kv.get("b"), "2")

    def test_sequential_eviction_correctness(self):
        kv = KVStore()
        kv.set_capacity(3)
        kv.put("1", "a")
        kv.put("2", "b")
        kv.put("3", "c")
        kv.get("1")        # 1 is now MRU; LRU is "2"
        kv.put("4", "d")   # evict LRU ("2")
        self.assertEqual(kv.get("2"), "")
        kv.get("3")        # MRU now "3"; LRU is "1"
        kv.put("5", "e")   # evict LRU ("1")
        self.assertEqual(kv.get("1"), "")
        self.assertEqual(kv.count(), 3)


class TestLevel4BackwardsCompat(unittest.TestCase):
    def test_ttl_and_lru_coexist(self):
        kv = KVStore()
        kv.set_capacity(2)
        kv.put_with_ttl("temp", "v", ttl=5, now=0)
        kv.put("perm", "p")
        # At capacity; adding another evicts "temp" (LRU)
        kv.put("new", "n")
        self.assertEqual(kv.count(), 2)
        self.assertEqual(kv.get("perm"), "p")
        self.assertEqual(kv.get("new"), "n")


if __name__ == "__main__":
    unittest.main()
