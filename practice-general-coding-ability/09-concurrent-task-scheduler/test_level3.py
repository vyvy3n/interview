"""
Level 3 tests — Priorities
Run: python3 test_level3.py
"""

import unittest
from solution import TaskScheduler


class TestLevel3SubmitWithPriority(unittest.TestCase):

    def test_submit_with_priority_returns_true(self):
        ts = TaskScheduler()
        self.assertTrue(ts.submit_task_with_priority("t1", 1, 10))

    def test_submit_with_priority_duplicate_returns_false(self):
        ts = TaskScheduler()
        ts.submit_task_with_priority("t1", 1, 10)
        self.assertFalse(ts.submit_task_with_priority("t1", 1, 5))

    def test_submit_with_priority_sets_pending(self):
        ts = TaskScheduler()
        ts.submit_task_with_priority("t1", 1, 7)
        self.assertEqual(ts.get_status("t1"), "pending")

    def test_submit_task_defaults_to_priority_zero(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 1)                          # priority 0
        ts.submit_task_with_priority("t2", 1, 1)         # priority 1 — should be next
        self.assertEqual(ts.get_next_task(), "t2")

    def test_negative_priority_is_valid(self):
        ts = TaskScheduler()
        ts.submit_task_with_priority("low", 1, -100)
        ts.submit_task("normal", 1)                      # priority 0
        self.assertEqual(ts.get_next_task(), "normal")


class TestLevel3GetNextTask(unittest.TestCase):

    def test_empty_returns_empty_string(self):
        ts = TaskScheduler()
        self.assertEqual(ts.get_next_task(), "")

    def test_single_pending_task(self):
        ts = TaskScheduler()
        ts.submit_task_with_priority("t1", 1, 5)
        self.assertEqual(ts.get_next_task(), "t1")

    def test_highest_priority_wins(self):
        ts = TaskScheduler()
        ts.submit_task_with_priority("low", 1, 1)
        ts.submit_task_with_priority("high", 1, 99)
        ts.submit_task_with_priority("mid", 1, 50)
        self.assertEqual(ts.get_next_task(), "high")

    def test_tie_broken_by_submission_order(self):
        ts = TaskScheduler()
        ts.submit_task_with_priority("first", 1, 5)
        ts.submit_task_with_priority("second", 1, 5)
        ts.submit_task_with_priority("third", 1, 5)
        self.assertEqual(ts.get_next_task(), "first")

    def test_tie_broken_by_submission_order_not_alphabetical(self):
        ts = TaskScheduler()
        ts.submit_task_with_priority("z", 1, 5)  # submitted first
        ts.submit_task_with_priority("a", 1, 5)  # submitted second
        # submission order: z before a — z wins despite being lexicographically after
        self.assertEqual(ts.get_next_task(), "z")

    def test_get_next_task_is_read_only(self):
        ts = TaskScheduler()
        ts.submit_task_with_priority("t1", 1, 5)
        ts.get_next_task()
        ts.get_next_task()
        # still pending after two calls
        self.assertEqual(ts.get_status("t1"), "pending")
        self.assertEqual(ts.get_next_task(), "t1")

    def test_get_next_task_updates_after_completion(self):
        ts = TaskScheduler()
        ts.submit_task_with_priority("a", 1, 10)
        ts.submit_task_with_priority("b", 1, 5)
        self.assertEqual(ts.get_next_task(), "a")
        ts.complete_task("a")
        self.assertEqual(ts.get_next_task(), "b")

    def test_all_completed_returns_empty(self):
        ts = TaskScheduler()
        ts.submit_task_with_priority("t1", 1, 1)
        ts.complete_task("t1")
        self.assertEqual(ts.get_next_task(), "")

    def test_mixed_positive_zero_negative_priorities(self):
        ts = TaskScheduler()
        ts.submit_task_with_priority("neg", 1, -5)
        ts.submit_task_with_priority("zero", 1, 0)
        ts.submit_task_with_priority("pos", 1, 5)
        self.assertEqual(ts.get_next_task(), "pos")
        ts.complete_task("pos")
        self.assertEqual(ts.get_next_task(), "zero")
        ts.complete_task("zero")
        self.assertEqual(ts.get_next_task(), "neg")

    def test_large_number_of_tasks(self):
        ts = TaskScheduler()
        for i in range(100):
            ts.submit_task_with_priority(f"t{i:03d}", 1, i)
        # t099 has priority 99 — the highest
        self.assertEqual(ts.get_next_task(), "t099")


if __name__ == "__main__":
    unittest.main()
