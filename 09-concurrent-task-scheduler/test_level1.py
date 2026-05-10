"""
Level 1 tests — Submit & Complete
Run: python3 test_level1.py
"""

import unittest
from solution import TaskScheduler


class TestLevel1SubmitTask(unittest.TestCase):

    def test_submit_returns_true_for_new_task(self):
        ts = TaskScheduler()
        self.assertTrue(ts.submit_task("t1", 5))

    def test_submit_multiple_new_tasks(self):
        ts = TaskScheduler()
        self.assertTrue(ts.submit_task("a", 1))
        self.assertTrue(ts.submit_task("b", 2))
        self.assertTrue(ts.submit_task("c", 3))

    def test_submit_duplicate_returns_false(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 5)
        self.assertFalse(ts.submit_task("t1", 5))

    def test_submit_duplicate_different_duration_still_false(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 5)
        self.assertFalse(ts.submit_task("t1", 99))

    def test_submit_sets_status_to_pending(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 5)
        self.assertEqual(ts.get_status("t1"), "pending")

    def test_submit_completed_task_duplicate_still_false(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 1)
        ts.complete_task("t1")
        self.assertFalse(ts.submit_task("t1", 1))


class TestLevel1GetStatus(unittest.TestCase):

    def test_get_status_missing_returns_empty_string(self):
        ts = TaskScheduler()
        self.assertEqual(ts.get_status("ghost"), "")

    def test_get_status_pending(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 3)
        self.assertEqual(ts.get_status("t1"), "pending")

    def test_get_status_completed(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 3)
        ts.complete_task("t1")
        self.assertEqual(ts.get_status("t1"), "completed")

    def test_get_status_empty_string_not_none(self):
        ts = TaskScheduler()
        result = ts.get_status("nope")
        self.assertIsInstance(result, str)
        self.assertEqual(result, "")


class TestLevel1CompleteTask(unittest.TestCase):

    def test_complete_pending_returns_true(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 2)
        self.assertTrue(ts.complete_task("t1"))

    def test_complete_changes_status_to_completed(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 2)
        ts.complete_task("t1")
        self.assertEqual(ts.get_status("t1"), "completed")

    def test_complete_missing_returns_false(self):
        ts = TaskScheduler()
        self.assertFalse(ts.complete_task("ghost"))

    def test_complete_already_completed_returns_false(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 2)
        ts.complete_task("t1")
        self.assertFalse(ts.complete_task("t1"))

    def test_complete_does_not_affect_other_tasks(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 1)
        ts.submit_task("t2", 1)
        ts.complete_task("t1")
        self.assertEqual(ts.get_status("t2"), "pending")

    def test_multiple_tasks_lifecycle(self):
        ts = TaskScheduler()
        for i in range(5):
            ts.submit_task(f"task{i}", i + 1)
        for i in range(5):
            self.assertTrue(ts.complete_task(f"task{i}"))
        for i in range(5):
            self.assertEqual(ts.get_status(f"task{i}"), "completed")


if __name__ == "__main__":
    unittest.main()
