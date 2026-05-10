"""
Level 2 tests — Status Reports
Run: python3 test_level2.py
"""

import unittest
from solution import TaskScheduler


class TestLevel2ListByStatus(unittest.TestCase):

    def test_list_all_pending(self):
        ts = TaskScheduler()
        ts.submit_task("banana", 2)
        ts.submit_task("apple", 1)
        ts.submit_task("cherry", 3)
        self.assertEqual(ts.list_by_status("pending"), ["apple", "banana", "cherry"])

    def test_list_returns_sorted_alphabetically(self):
        ts = TaskScheduler()
        for name in ["z", "m", "a", "b", "y"]:
            ts.submit_task(name, 1)
        self.assertEqual(ts.list_by_status("pending"), ["a", "b", "m", "y", "z"])

    def test_list_completed_empty_initially(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 1)
        self.assertEqual(ts.list_by_status("completed"), [])

    def test_list_after_completions(self):
        ts = TaskScheduler()
        ts.submit_task("c", 1)
        ts.submit_task("a", 1)
        ts.submit_task("b", 1)
        ts.complete_task("c")
        ts.complete_task("a")
        self.assertEqual(ts.list_by_status("completed"), ["a", "c"])
        self.assertEqual(ts.list_by_status("pending"), ["b"])

    def test_list_unknown_status_returns_empty(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 1)
        self.assertEqual(ts.list_by_status("running"), [])
        self.assertEqual(ts.list_by_status("foobar"), [])

    def test_list_empty_scheduler(self):
        ts = TaskScheduler()
        self.assertEqual(ts.list_by_status("pending"), [])
        self.assertEqual(ts.list_by_status("completed"), [])

    def test_list_returns_new_list(self):
        # mutating the returned list must not affect internal state
        ts = TaskScheduler()
        ts.submit_task("t1", 1)
        result = ts.list_by_status("pending")
        result.append("fake")
        self.assertEqual(ts.list_by_status("pending"), ["t1"])


class TestLevel2CountByStatus(unittest.TestCase):

    def test_count_all_pending(self):
        ts = TaskScheduler()
        ts.submit_task("a", 1)
        ts.submit_task("b", 1)
        ts.submit_task("c", 1)
        self.assertEqual(ts.count_by_status("pending"), 3)

    def test_count_completed_zero_initially(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 1)
        self.assertEqual(ts.count_by_status("completed"), 0)

    def test_count_after_completions(self):
        ts = TaskScheduler()
        for i in range(4):
            ts.submit_task(f"t{i}", 1)
        ts.complete_task("t0")
        ts.complete_task("t2")
        self.assertEqual(ts.count_by_status("completed"), 2)
        self.assertEqual(ts.count_by_status("pending"), 2)

    def test_count_unknown_status_returns_zero(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 1)
        self.assertEqual(ts.count_by_status("foobar"), 0)

    def test_count_consistent_with_list(self):
        ts = TaskScheduler()
        for i in range(6):
            ts.submit_task(f"t{i}", 1)
        ts.complete_task("t1")
        ts.complete_task("t3")
        ts.complete_task("t5")
        for status in ("pending", "completed"):
            self.assertEqual(
                ts.count_by_status(status),
                len(ts.list_by_status(status)),
            )

    def test_count_empty_scheduler(self):
        ts = TaskScheduler()
        self.assertEqual(ts.count_by_status("pending"), 0)


if __name__ == "__main__":
    unittest.main()
