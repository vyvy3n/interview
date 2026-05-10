"""
Level 4 tests — Dependencies
Run: python3 test_level4.py
"""

import unittest
from solution import TaskScheduler


class TestLevel4SetDependencies(unittest.TestCase):

    def test_set_deps_valid(self):
        ts = TaskScheduler()
        ts.submit_task("a", 1)
        ts.submit_task("b", 1)
        self.assertTrue(ts.set_dependencies("b", ["a"]))

    def test_set_deps_missing_task_id(self):
        ts = TaskScheduler()
        ts.submit_task("a", 1)
        self.assertFalse(ts.set_dependencies("ghost", ["a"]))

    def test_set_deps_missing_dep(self):
        ts = TaskScheduler()
        ts.submit_task("b", 1)
        self.assertFalse(ts.set_dependencies("b", ["ghost"]))

    def test_set_deps_empty_list_clears_deps(self):
        ts = TaskScheduler()
        ts.submit_task("a", 1)
        ts.submit_task("b", 1)
        ts.set_dependencies("b", ["a"])
        self.assertTrue(ts.set_dependencies("b", []))  # clears deps

    def test_set_deps_replaces_previous(self):
        ts = TaskScheduler()
        ts.submit_task("a", 1)
        ts.submit_task("b", 1)
        ts.submit_task("c", 1)
        ts.set_dependencies("c", ["a"])
        # replace: now c depends on b only
        self.assertTrue(ts.set_dependencies("c", ["b"]))
        ts.complete_task("b")
        # c should now be runnable (b completed), even though a is still pending
        self.assertEqual(ts.get_next_runnable(), "c")

    def test_direct_cycle_rejected(self):
        ts = TaskScheduler()
        ts.submit_task("a", 1)
        ts.submit_task("b", 1)
        ts.set_dependencies("b", ["a"])
        # a -> b would create cycle a <-> b
        self.assertFalse(ts.set_dependencies("a", ["b"]))

    def test_transitive_cycle_rejected(self):
        ts = TaskScheduler()
        ts.submit_task("a", 1)
        ts.submit_task("b", 1)
        ts.submit_task("c", 1)
        ts.set_dependencies("b", ["a"])
        ts.set_dependencies("c", ["b"])
        # trying to make a depend on c would create a -> b -> c -> a cycle
        self.assertFalse(ts.set_dependencies("a", ["c"]))

    def test_multiple_deps_allowed(self):
        ts = TaskScheduler()
        ts.submit_task("a", 1)
        ts.submit_task("b", 1)
        ts.submit_task("c", 1)
        self.assertTrue(ts.set_dependencies("c", ["a", "b"]))


class TestLevel4GetNextRunnable(unittest.TestCase):

    def test_no_pending_tasks_returns_empty(self):
        ts = TaskScheduler()
        self.assertEqual(ts.get_next_runnable(), "")

    def test_task_with_no_deps_is_runnable(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 1)
        self.assertEqual(ts.get_next_runnable(), "t1")

    def test_task_blocked_by_pending_dep(self):
        ts = TaskScheduler()
        ts.submit_task("a", 1)
        ts.submit_task("b", 1)
        ts.set_dependencies("b", ["a"])
        # only a is runnable; b is blocked
        self.assertEqual(ts.get_next_runnable(), "a")

    def test_task_unblocked_after_dep_completes(self):
        ts = TaskScheduler()
        ts.submit_task("a", 1)
        ts.submit_task("b", 1)
        ts.set_dependencies("b", ["a"])
        ts.complete_task("a")
        self.assertEqual(ts.get_next_runnable(), "b")

    def test_priority_respected_among_runnable(self):
        ts = TaskScheduler()
        ts.submit_task_with_priority("a", 1, 5)
        ts.submit_task_with_priority("b", 1, 10)
        ts.submit_task_with_priority("c", 1, 7)
        # all have no deps — b has highest priority
        self.assertEqual(ts.get_next_runnable(), "b")

    def test_tie_broken_by_submission_order(self):
        ts = TaskScheduler()
        ts.submit_task_with_priority("x", 1, 5)
        ts.submit_task_with_priority("y", 1, 5)
        self.assertEqual(ts.get_next_runnable(), "x")

    def test_chain_of_dependencies(self):
        ts = TaskScheduler()
        ts.submit_task("build", 1)
        ts.submit_task("test", 1)
        ts.submit_task("deploy", 1)
        ts.set_dependencies("test", ["build"])
        ts.set_dependencies("deploy", ["test"])

        self.assertEqual(ts.get_next_runnable(), "build")
        ts.complete_task("build")
        self.assertEqual(ts.get_next_runnable(), "test")
        ts.complete_task("test")
        self.assertEqual(ts.get_next_runnable(), "deploy")
        ts.complete_task("deploy")
        self.assertEqual(ts.get_next_runnable(), "")

    def test_multiple_deps_all_must_complete(self):
        ts = TaskScheduler()
        ts.submit_task("a", 1)
        ts.submit_task("b", 1)
        ts.submit_task("c", 1)
        ts.set_dependencies("c", ["a", "b"])

        # c blocked until both a and b done
        ts.complete_task("a")
        self.assertEqual(ts.get_next_runnable(), "b")  # c still blocked; b is next
        ts.complete_task("b")
        self.assertEqual(ts.get_next_runnable(), "c")

    def test_get_next_runnable_is_read_only(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 1)
        ts.get_next_runnable()
        ts.get_next_runnable()
        self.assertEqual(ts.get_status("t1"), "pending")

    def test_get_next_task_ignores_deps(self):
        # get_next_task (L3) must still ignore dependencies
        ts = TaskScheduler()
        ts.submit_task_with_priority("a", 1, 1)
        ts.submit_task_with_priority("b", 1, 10)
        ts.set_dependencies("b", ["a"])
        # get_next_task ignores deps: b has higher priority
        self.assertEqual(ts.get_next_task(), "b")
        # get_next_runnable respects deps: b is blocked
        self.assertEqual(ts.get_next_runnable(), "a")


if __name__ == "__main__":
    unittest.main()
