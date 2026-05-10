"""
Level 2 tests — update / fetch_by_prefix / get_total_size
Run: python3 test_level2.py
"""

import unittest
from solution import FileCache


class TestLevel2Update(unittest.TestCase):
    def setUp(self):
        self.cache = FileCache()

    def test_update_existing_returns_true(self):
        self.cache.store("f.txt", "old")
        self.assertTrue(self.cache.update("f.txt", "new"))

    def test_update_missing_returns_false(self):
        self.assertFalse(self.cache.update("ghost.txt", "data"))

    def test_update_actually_overwrites_content(self):
        self.cache.store("f.txt", "original")
        self.cache.update("f.txt", "updated")
        self.assertEqual(self.cache.fetch("f.txt"), "updated")

    def test_update_does_not_create_new_file(self):
        self.assertFalse(self.cache.update("newfile.txt", "data"))
        self.assertEqual(self.cache.fetch("newfile.txt"), "")

    def test_update_does_not_change_size(self):
        self.cache.store("f.txt", "x")
        self.assertEqual(self.cache.size(), 1)
        self.cache.update("f.txt", "y")
        self.assertEqual(self.cache.size(), 1)

    def test_update_returns_bool(self):
        self.cache.store("f.txt", "x")
        result = self.cache.update("f.txt", "y")
        self.assertIsInstance(result, bool)

    def test_update_to_empty_string(self):
        self.cache.store("f.txt", "data")
        self.assertTrue(self.cache.update("f.txt", ""))
        self.assertEqual(self.cache.fetch("f.txt"), "")

    def test_multiple_updates_preserve_last_value(self):
        self.cache.store("f.txt", "v0")
        self.cache.update("f.txt", "v1")
        self.cache.update("f.txt", "v2")
        self.cache.update("f.txt", "v3")
        self.assertEqual(self.cache.fetch("f.txt"), "v3")


class TestLevel2FetchByPrefix(unittest.TestCase):
    def setUp(self):
        self.cache = FileCache()

    def test_fetch_by_prefix_returns_sorted_list(self):
        self.cache.store("img_cat.jpg", "c")
        self.cache.store("img_dog.jpg", "d")
        self.cache.store("img_ant.jpg", "a")
        result = self.cache.fetch_by_prefix("img_")
        self.assertEqual(result, ["img_ant.jpg", "img_cat.jpg", "img_dog.jpg"])

    def test_fetch_by_prefix_empty_prefix_returns_all(self):
        self.cache.store("z.txt", "z")
        self.cache.store("a.txt", "a")
        self.cache.store("m.txt", "m")
        result = self.cache.fetch_by_prefix("")
        self.assertEqual(result, ["a.txt", "m.txt", "z.txt"])

    def test_fetch_by_prefix_no_match_returns_empty_list(self):
        self.cache.store("foo.txt", "data")
        result = self.cache.fetch_by_prefix("bar")
        self.assertEqual(result, [])

    def test_fetch_by_prefix_exact_match_included(self):
        self.cache.store("exact", "data")
        result = self.cache.fetch_by_prefix("exact")
        self.assertEqual(result, ["exact"])

    def test_fetch_by_prefix_does_not_include_non_matching(self):
        self.cache.store("alpha.txt", "a")
        self.cache.store("beta.txt", "b")
        result = self.cache.fetch_by_prefix("alph")
        self.assertEqual(result, ["alpha.txt"])

    def test_fetch_by_prefix_returns_list_not_set(self):
        self.cache.store("f.txt", "x")
        result = self.cache.fetch_by_prefix("f")
        self.assertIsInstance(result, list)

    def test_fetch_by_prefix_empty_cache_returns_empty_list(self):
        self.assertEqual(self.cache.fetch_by_prefix("any"), [])


class TestLevel2GetTotalSize(unittest.TestCase):
    def setUp(self):
        self.cache = FileCache()

    def test_total_size_empty_cache_is_zero(self):
        self.assertEqual(self.cache.get_total_size(), 0)

    def test_total_size_single_file(self):
        self.cache.store("f.txt", "hello")
        self.assertEqual(self.cache.get_total_size(), 5)

    def test_total_size_multiple_files(self):
        self.cache.store("a.txt", "ab")     # 2
        self.cache.store("b.txt", "cdef")   # 4
        self.cache.store("c.txt", "x")      # 1
        self.assertEqual(self.cache.get_total_size(), 7)

    def test_total_size_after_update_reflects_new_content(self):
        self.cache.store("f.txt", "abc")    # 3
        self.cache.update("f.txt", "xy")    # 2
        self.assertEqual(self.cache.get_total_size(), 2)

    def test_total_size_after_remove_decreases(self):
        self.cache.store("a.txt", "aaa")   # 3
        self.cache.store("b.txt", "bb")    # 2
        self.cache.remove("a.txt")
        self.assertEqual(self.cache.get_total_size(), 2)

    def test_total_size_empty_content_contributes_zero(self):
        self.cache.store("empty.txt", "")
        self.assertEqual(self.cache.get_total_size(), 0)


class TestLevel2Integration(unittest.TestCase):
    def test_store_update_prefix_flow(self):
        cache = FileCache()
        for name in ["report_jan.txt", "report_feb.txt", "report_mar.txt", "notes.txt"]:
            cache.store(name, "initial content")
        # update one
        cache.update("report_feb.txt", "revised")
        self.assertEqual(cache.fetch("report_feb.txt"), "revised")
        # prefix search
        reports = cache.fetch_by_prefix("report_")
        self.assertEqual(reports, ["report_feb.txt", "report_jan.txt", "report_mar.txt"])
        # total size: 3 files * len("initial content")=15 + "revised"=7
        self.assertEqual(cache.get_total_size(), 15 + 15 + 7 + 15)

    def test_removed_file_excluded_from_prefix_search(self):
        cache = FileCache()
        cache.store("log_a.txt", "x")
        cache.store("log_b.txt", "y")
        cache.remove("log_a.txt")
        self.assertEqual(cache.fetch_by_prefix("log_"), ["log_b.txt"])

    def test_updated_file_not_in_prefix_search_by_content(self):
        # fetch_by_prefix returns filenames, not content
        cache = FileCache()
        cache.store("data_v1.txt", "version one")
        cache.update("data_v1.txt", "version two")
        result = cache.fetch_by_prefix("data_")
        self.assertEqual(result, ["data_v1.txt"])


if __name__ == "__main__":
    unittest.main()
