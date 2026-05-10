"""
Level 1 tests — Basic file ops (single-tenant, no constraints)
Run: python3 test_level1.py
"""

import unittest
from solution import FileCache


class TestLevel1Store(unittest.TestCase):
    def setUp(self):
        self.cache = FileCache()

    def test_store_new_file_returns_true(self):
        self.assertTrue(self.cache.store("readme.txt", "hello"))

    def test_store_duplicate_returns_false(self):
        self.cache.store("readme.txt", "hello")
        self.assertFalse(self.cache.store("readme.txt", "world"))

    def test_store_duplicate_does_not_overwrite(self):
        self.cache.store("f.txt", "original")
        self.cache.store("f.txt", "overwrite")
        self.assertEqual(self.cache.fetch("f.txt"), "original")

    def test_store_empty_content_allowed(self):
        self.assertTrue(self.cache.store("empty.txt", ""))
        self.assertEqual(self.cache.fetch("empty.txt"), "")

    def test_store_multiple_distinct_files(self):
        self.assertTrue(self.cache.store("a.txt", "aaa"))
        self.assertTrue(self.cache.store("b.txt", "bbb"))
        self.assertTrue(self.cache.store("c.txt", "ccc"))


class TestLevel1Fetch(unittest.TestCase):
    def setUp(self):
        self.cache = FileCache()

    def test_fetch_existing_returns_content(self):
        self.cache.store("f.txt", "hello world")
        self.assertEqual(self.cache.fetch("f.txt"), "hello world")

    def test_fetch_missing_returns_empty_string(self):
        self.assertEqual(self.cache.fetch("nonexistent.txt"), "")

    def test_fetch_returns_string_not_none(self):
        result = self.cache.fetch("missing.txt")
        self.assertIsInstance(result, str)

    def test_fetch_after_store_returns_correct_content(self):
        self.cache.store("doc.txt", "content here")
        self.assertEqual(self.cache.fetch("doc.txt"), "content here")

    def test_fetch_does_not_affect_other_files(self):
        self.cache.store("a.txt", "A")
        self.cache.store("b.txt", "B")
        self.cache.fetch("a.txt")
        self.assertEqual(self.cache.fetch("b.txt"), "B")


class TestLevel1Remove(unittest.TestCase):
    def setUp(self):
        self.cache = FileCache()

    def test_remove_existing_returns_true(self):
        self.cache.store("f.txt", "data")
        self.assertTrue(self.cache.remove("f.txt"))

    def test_remove_missing_returns_false(self):
        self.assertFalse(self.cache.remove("ghost.txt"))

    def test_remove_deletes_file(self):
        self.cache.store("f.txt", "data")
        self.cache.remove("f.txt")
        self.assertEqual(self.cache.fetch("f.txt"), "")

    def test_remove_twice_second_returns_false(self):
        self.cache.store("f.txt", "data")
        self.cache.remove("f.txt")
        self.assertFalse(self.cache.remove("f.txt"))

    def test_remove_returns_bool_not_string(self):
        self.cache.store("f.txt", "data")
        result = self.cache.remove("f.txt")
        self.assertIsInstance(result, bool)

    def test_remove_only_affects_target_file(self):
        self.cache.store("a.txt", "A")
        self.cache.store("b.txt", "B")
        self.cache.remove("a.txt")
        self.assertEqual(self.cache.fetch("b.txt"), "B")

    def test_store_after_remove_works(self):
        self.cache.store("f.txt", "v1")
        self.cache.remove("f.txt")
        self.assertTrue(self.cache.store("f.txt", "v2"))
        self.assertEqual(self.cache.fetch("f.txt"), "v2")


class TestLevel1Size(unittest.TestCase):
    def setUp(self):
        self.cache = FileCache()

    def test_size_empty_cache_is_zero(self):
        self.assertEqual(self.cache.size(), 0)

    def test_size_after_one_store(self):
        self.cache.store("f.txt", "x")
        self.assertEqual(self.cache.size(), 1)

    def test_size_after_duplicate_store_unchanged(self):
        self.cache.store("f.txt", "x")
        self.cache.store("f.txt", "y")
        self.assertEqual(self.cache.size(), 1)

    def test_size_after_remove_decrements(self):
        self.cache.store("f.txt", "x")
        self.cache.remove("f.txt")
        self.assertEqual(self.cache.size(), 0)

    def test_size_tracks_multiple_files(self):
        for i in range(10):
            self.cache.store(f"f{i}.txt", "data")
        self.assertEqual(self.cache.size(), 10)

    def test_size_remove_nonexistent_unchanged(self):
        self.cache.store("f.txt", "x")
        self.cache.remove("ghost.txt")
        self.assertEqual(self.cache.size(), 1)


class TestLevel1Integration(unittest.TestCase):
    def test_full_lifecycle(self):
        cache = FileCache()
        self.assertEqual(cache.size(), 0)
        self.assertTrue(cache.store("notes.txt", "my notes"))
        self.assertEqual(cache.fetch("notes.txt"), "my notes")
        self.assertFalse(cache.store("notes.txt", "overwrite attempt"))
        self.assertEqual(cache.fetch("notes.txt"), "my notes")
        self.assertEqual(cache.size(), 1)
        self.assertTrue(cache.remove("notes.txt"))
        self.assertEqual(cache.fetch("notes.txt"), "")
        self.assertEqual(cache.size(), 0)
        self.assertFalse(cache.remove("notes.txt"))

    def test_many_files(self):
        cache = FileCache()
        for i in range(100):
            cache.store(f"file{i:03d}.txt", f"content-{i}")
        self.assertEqual(cache.size(), 100)
        for i in range(100):
            self.assertEqual(cache.fetch(f"file{i:03d}.txt"), f"content-{i}")
        for i in range(50):
            self.assertTrue(cache.remove(f"file{i:03d}.txt"))
        self.assertEqual(cache.size(), 50)


if __name__ == "__main__":
    unittest.main()
