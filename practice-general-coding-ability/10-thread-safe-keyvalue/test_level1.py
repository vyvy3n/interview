"""
Level 1 tests — Basic put / get / delete
Run: python3 test_level1.py
"""

import unittest
from solution import KVStore


class TestLevel1PutGet(unittest.TestCase):
    def setUp(self):
        self.kv = KVStore()

    def test_put_then_get(self):
        self.kv.put("key", "value")
        self.assertEqual(self.kv.get("key"), "value")

    def test_get_missing_returns_empty_string(self):
        self.assertEqual(self.kv.get("nonexistent"), "")

    def test_put_overwrites_existing(self):
        self.kv.put("k", "first")
        self.kv.put("k", "second")
        self.assertEqual(self.kv.get("k"), "second")

    def test_put_returns_none(self):
        result = self.kv.put("k", "v")
        self.assertIsNone(result)

    def test_multiple_independent_keys(self):
        self.kv.put("a", "1")
        self.kv.put("b", "2")
        self.kv.put("c", "3")
        self.assertEqual(self.kv.get("a"), "1")
        self.assertEqual(self.kv.get("b"), "2")
        self.assertEqual(self.kv.get("c"), "3")

    def test_overwrite_does_not_affect_other_keys(self):
        self.kv.put("x", "original")
        self.kv.put("y", "untouched")
        self.kv.put("x", "updated")
        self.assertEqual(self.kv.get("y"), "untouched")

    def test_empty_string_value(self):
        # Storing an empty string is valid
        self.kv.put("k", "")
        self.assertEqual(self.kv.get("k"), "")


class TestLevel1Delete(unittest.TestCase):
    def setUp(self):
        self.kv = KVStore()

    def test_delete_existing_returns_true(self):
        self.kv.put("k", "v")
        self.assertTrue(self.kv.delete("k"))

    def test_delete_missing_returns_false(self):
        self.assertFalse(self.kv.delete("nope"))

    def test_delete_removes_key(self):
        self.kv.put("k", "v")
        self.kv.delete("k")
        self.assertEqual(self.kv.get("k"), "")

    def test_delete_twice_returns_false_second_time(self):
        self.kv.put("k", "v")
        self.kv.delete("k")
        self.assertFalse(self.kv.delete("k"))

    def test_delete_only_removes_target_key(self):
        self.kv.put("a", "1")
        self.kv.put("b", "2")
        self.kv.delete("a")
        self.assertEqual(self.kv.get("b"), "2")

    def test_put_after_delete_works(self):
        self.kv.put("k", "v1")
        self.kv.delete("k")
        self.kv.put("k", "v2")
        self.assertEqual(self.kv.get("k"), "v2")

    def test_delete_returns_bool_not_string(self):
        self.kv.put("k", "v")
        result = self.kv.delete("k")
        self.assertIsInstance(result, bool)
        self.assertEqual(self.kv.delete("k"), False)
        self.assertIsInstance(self.kv.delete("k"), bool)


class TestLevel1StressSequence(unittest.TestCase):
    def test_interleaved_operations(self):
        kv = KVStore()
        kv.put("name", "alice")
        self.assertEqual(kv.get("name"), "alice")
        kv.put("name", "bob")
        self.assertEqual(kv.get("name"), "bob")
        self.assertEqual(kv.get("missing"), "")
        self.assertTrue(kv.delete("name"))
        self.assertFalse(kv.delete("name"))
        self.assertEqual(kv.get("name"), "")

    def test_many_keys(self):
        kv = KVStore()
        for i in range(200):
            kv.put(f"key{i}", f"val{i}")
        for i in range(200):
            self.assertEqual(kv.get(f"key{i}"), f"val{i}")
        for i in range(200):
            self.assertTrue(kv.delete(f"key{i}"))
        for i in range(200):
            self.assertEqual(kv.get(f"key{i}"), "")


if __name__ == "__main__":
    unittest.main()
