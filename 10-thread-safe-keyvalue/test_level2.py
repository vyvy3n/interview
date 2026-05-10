"""
Level 2 tests — Bulk operations and prefix queries
Run: python3 test_level2.py
"""

import unittest
from solution import KVStore


class TestLevel2MultiGet(unittest.TestCase):
    def setUp(self):
        self.kv = KVStore()
        self.kv.put("a", "apple")
        self.kv.put("b", "banana")
        self.kv.put("c", "cherry")

    def test_multi_get_all_present(self):
        result = self.kv.multi_get(["a", "b", "c"])
        self.assertEqual(result, ["apple", "banana", "cherry"])

    def test_multi_get_preserves_order(self):
        result = self.kv.multi_get(["c", "a", "b"])
        self.assertEqual(result, ["cherry", "apple", "banana"])

    def test_multi_get_missing_returns_empty_string(self):
        result = self.kv.multi_get(["a", "missing", "b"])
        self.assertEqual(result, ["apple", "", "banana"])

    def test_multi_get_all_missing(self):
        result = self.kv.multi_get(["x", "y", "z"])
        self.assertEqual(result, ["", "", ""])

    def test_multi_get_empty_list(self):
        result = self.kv.multi_get([])
        self.assertEqual(result, [])

    def test_multi_get_duplicate_keys(self):
        result = self.kv.multi_get(["a", "a", "b"])
        self.assertEqual(result, ["apple", "apple", "banana"])

    def test_multi_get_single_key(self):
        result = self.kv.multi_get(["a"])
        self.assertEqual(result, ["apple"])

    def test_multi_get_returns_list(self):
        result = self.kv.multi_get(["a"])
        self.assertIsInstance(result, list)


class TestLevel2KeysByPrefix(unittest.TestCase):
    def setUp(self):
        self.kv = KVStore()
        self.kv.put("user:alice", "30")
        self.kv.put("user:bob", "25")
        self.kv.put("user:carol", "28")
        self.kv.put("session:xyz", "active")
        self.kv.put("config:max", "100")

    def test_prefix_matches_multiple_sorted(self):
        result = self.kv.keys_by_prefix("user:")
        self.assertEqual(result, ["user:alice", "user:bob", "user:carol"])

    def test_prefix_matches_one(self):
        result = self.kv.keys_by_prefix("session:")
        self.assertEqual(result, ["session:xyz"])

    def test_prefix_no_match_returns_empty(self):
        result = self.kv.keys_by_prefix("zzz")
        self.assertEqual(result, [])

    def test_prefix_empty_string_returns_all_sorted(self):
        result = self.kv.keys_by_prefix("")
        expected = sorted(["user:alice", "user:bob", "user:carol", "session:xyz", "config:max"])
        self.assertEqual(result, expected)

    def test_prefix_exact_key_match(self):
        result = self.kv.keys_by_prefix("user:alice")
        self.assertEqual(result, ["user:alice"])

    def test_prefix_returns_keys_not_values(self):
        result = self.kv.keys_by_prefix("user:")
        for item in result:
            self.assertIn(item, ["user:alice", "user:bob", "user:carol"])

    def test_prefix_after_delete(self):
        self.kv.delete("user:bob")
        result = self.kv.keys_by_prefix("user:")
        self.assertEqual(result, ["user:alice", "user:carol"])

    def test_prefix_sorted_alphabetically(self):
        kv = KVStore()
        kv.put("z", "last")
        kv.put("a", "first")
        kv.put("m", "middle")
        result = kv.keys_by_prefix("")
        self.assertEqual(result, ["a", "m", "z"])

    def test_prefix_returns_list(self):
        result = self.kv.keys_by_prefix("user:")
        self.assertIsInstance(result, list)


class TestLevel2Count(unittest.TestCase):
    def test_count_empty_store(self):
        kv = KVStore()
        self.assertEqual(kv.count(), 0)

    def test_count_after_puts(self):
        kv = KVStore()
        kv.put("a", "1")
        kv.put("b", "2")
        self.assertEqual(kv.count(), 2)

    def test_count_overwrite_does_not_increase(self):
        kv = KVStore()
        kv.put("a", "1")
        kv.put("a", "2")
        self.assertEqual(kv.count(), 1)

    def test_count_after_delete(self):
        kv = KVStore()
        kv.put("a", "1")
        kv.put("b", "2")
        kv.delete("a")
        self.assertEqual(kv.count(), 1)

    def test_count_delete_missing_no_change(self):
        kv = KVStore()
        kv.put("a", "1")
        kv.delete("nonexistent")
        self.assertEqual(kv.count(), 1)

    def test_count_returns_int(self):
        kv = KVStore()
        self.assertIsInstance(kv.count(), int)

    def test_count_many_keys(self):
        kv = KVStore()
        for i in range(50):
            kv.put(f"k{i}", str(i))
        self.assertEqual(kv.count(), 50)
        for i in range(25):
            kv.delete(f"k{i}")
        self.assertEqual(kv.count(), 25)


class TestLevel2BackwardsCompat(unittest.TestCase):
    """L1 operations still work."""

    def test_l1_put_get_delete_unchanged(self):
        kv = KVStore()
        kv.put("x", "hello")
        self.assertEqual(kv.get("x"), "hello")
        self.assertTrue(kv.delete("x"))
        self.assertEqual(kv.get("x"), "")


if __name__ == "__main__":
    unittest.main()
