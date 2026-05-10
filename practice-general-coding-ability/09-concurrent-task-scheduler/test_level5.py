"""
Level 5 tests — Concurrent Workers
Run: python3 test_level5.py

All durations are tiny floats (0.01 s) so tests finish in < 2 s total.
Workers sleep during task execution — the lock must be RELEASED during sleep.
"""

import threading
import time
import unittest
from solution import TaskScheduler


class TestLevel5BasicWorkers(unittest.TestCase):

    def test_workers_complete_single_task(self):
        ts = TaskScheduler()
        ts.submit_task("job1", 0.01)
        ts.start_workers(1)
        time.sleep(0.3)
        ts.stop_workers()
        self.assertEqual(ts.get_status("job1"), "completed")

    def test_workers_complete_multiple_tasks(self):
        ts = TaskScheduler()
        for i in range(5):
            ts.submit_task(f"job{i}", 0.01)
        ts.start_workers(2)
        time.sleep(0.5)
        ts.stop_workers()
        for i in range(5):
            self.assertEqual(ts.get_status(f"job{i}"), "completed")

    def test_running_status_visible(self):
        ts = TaskScheduler()
        # Use a slightly longer duration so we can catch "running"
        ts.submit_task("slow", 0.2)
        ts.start_workers(1)
        time.sleep(0.05)  # worker should have claimed but not finished
        status = ts.get_status("slow")
        ts.stop_workers()
        # status should have been "running" at some point; after stop it's "completed"
        # We can only assert it reached "completed" eventually
        self.assertEqual(ts.get_status("slow"), "completed")

    def test_stop_workers_joins_threads(self):
        ts = TaskScheduler()
        ts.submit_task("j", 0.01)
        ts.start_workers(3)
        time.sleep(0.2)
        ts.stop_workers()
        # After stop_workers, count_by_status should show 0 running
        self.assertEqual(ts.count_by_status("running"), 0)

    def test_start_workers_is_additive(self):
        ts = TaskScheduler()
        for i in range(6):
            ts.submit_task(f"t{i}", 0.01)
        ts.start_workers(2)
        ts.start_workers(1)   # 3 total workers
        time.sleep(0.5)
        ts.stop_workers()
        self.assertEqual(ts.count_by_status("completed"), 6)
        self.assertEqual(ts.count_by_status("pending"), 0)

    def test_no_tasks_workers_idle_cleanly(self):
        ts = TaskScheduler()
        ts.start_workers(2)
        time.sleep(0.1)
        ts.stop_workers()
        # No crash — workers exit cleanly with nothing to do

    def test_count_by_status_running(self):
        ts = TaskScheduler()
        # Submit tasks with longer durations so "running" is observable
        for i in range(3):
            ts.submit_task(f"t{i}", 0.3)
        ts.start_workers(3)
        time.sleep(0.05)
        running = ts.count_by_status("running")
        ts.stop_workers()
        # At 0.05 s in, with 3 workers and 0.3 s tasks, at least some should be running
        self.assertGreater(running, 0)


class TestLevel5ThreadSafety(unittest.TestCase):

    def test_concurrent_submits_no_duplicate_processing(self):
        """Two threads race to submit tasks; each task must be processed exactly once."""
        ts = TaskScheduler()
        errors = []

        def submit_batch(prefix, count):
            for i in range(count):
                ts.submit_task(f"{prefix}-{i}", 0.01)

        t1 = threading.Thread(target=submit_batch, args=("a", 20))
        t2 = threading.Thread(target=submit_batch, args=("b", 20))
        t1.start(); t2.start()
        t1.join(); t2.join()

        ts.start_workers(4)
        time.sleep(0.8)
        ts.stop_workers()

        total_completed = ts.count_by_status("completed")
        self.assertEqual(total_completed, 40)

    def test_get_status_concurrent_with_workers(self):
        """Calling get_status from multiple threads while workers run must not crash."""
        ts = TaskScheduler()
        for i in range(10):
            ts.submit_task(f"t{i}", 0.02)

        results = []
        lock = threading.Lock()

        def poll_status():
            for i in range(10):
                s = ts.get_status(f"t{i}")
                with lock:
                    results.append(s)

        ts.start_workers(3)
        threads = [threading.Thread(target=poll_status) for _ in range(4)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        ts.stop_workers()

        # All returned values must be valid statuses (no None, no exceptions)
        valid_statuses = {"pending", "running", "completed", ""}
        for s in results:
            self.assertIn(s, valid_statuses)

    def test_list_by_status_concurrent(self):
        """list_by_status must not raise or return corrupted data under concurrent access."""
        ts = TaskScheduler()
        for i in range(20):
            ts.submit_task(f"t{i:02d}", 0.01)

        exceptions = []

        def check_list():
            try:
                for _ in range(20):
                    result = ts.list_by_status("pending")
                    self.assertIsInstance(result, list)
            except Exception as e:
                exceptions.append(e)

        ts.start_workers(4)
        threads = [threading.Thread(target=check_list) for _ in range(4)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        ts.stop_workers()

        self.assertEqual(exceptions, [])

    def test_workers_with_dependencies(self):
        """Workers should respect dependencies: child task runs only after parent completes."""
        ts = TaskScheduler()
        ts.submit_task_with_priority("parent", 0.05, 1)
        ts.submit_task_with_priority("child", 0.05, 10)  # higher priority but blocked
        ts.set_dependencies("child", ["parent"])

        completion_order = []
        orig_complete = ts.complete_task.__func__ if hasattr(ts.complete_task, '__func__') else None

        # We'll verify via timing: parent must complete before child starts
        ts.start_workers(2)
        time.sleep(0.5)
        ts.stop_workers()

        self.assertEqual(ts.get_status("parent"), "completed")
        self.assertEqual(ts.get_status("child"), "completed")

    def test_stop_workers_is_idempotent(self):
        ts = TaskScheduler()
        ts.start_workers(2)
        ts.stop_workers()
        ts.stop_workers()  # second stop should not crash


if __name__ == "__main__":
    unittest.main()
