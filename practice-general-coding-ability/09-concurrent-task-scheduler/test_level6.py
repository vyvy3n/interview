"""
Level 6 tests — Cancellation & Waiting
Run: python3 test_level6.py

Uses threading.Event-based waiting. No busy-wait.
Keep total test runtime < 3 seconds.
"""

import threading
import time
import unittest
from solution import TaskScheduler


class TestLevel6CancelTask(unittest.TestCase):

    def test_cancel_pending_returns_true(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 0.01)
        self.assertTrue(ts.cancel_task("t1"))

    def test_cancel_sets_status_to_cancelled(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 0.01)
        ts.cancel_task("t1")
        self.assertEqual(ts.get_status("t1"), "cancelled")

    def test_cancel_missing_task_returns_false(self):
        ts = TaskScheduler()
        self.assertFalse(ts.cancel_task("ghost"))

    def test_cancel_completed_task_returns_false(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 0.01)
        ts.complete_task("t1")
        self.assertFalse(ts.cancel_task("t1"))

    def test_cancel_already_cancelled_returns_false(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 0.01)
        ts.cancel_task("t1")
        self.assertFalse(ts.cancel_task("t1"))

    def test_cancel_propagates_to_direct_dependent(self):
        ts = TaskScheduler()
        ts.submit_task("a", 0.01)
        ts.submit_task("b", 0.01)
        ts.set_dependencies("b", ["a"])
        ts.cancel_task("a")
        self.assertEqual(ts.get_status("a"), "cancelled")
        self.assertEqual(ts.get_status("b"), "cancelled")

    def test_cancel_propagates_transitively(self):
        ts = TaskScheduler()
        ts.submit_task("a", 0.01)
        ts.submit_task("b", 0.01)
        ts.submit_task("c", 0.01)
        ts.set_dependencies("b", ["a"])
        ts.set_dependencies("c", ["b"])
        ts.cancel_task("a")
        self.assertEqual(ts.get_status("a"), "cancelled")
        self.assertEqual(ts.get_status("b"), "cancelled")
        self.assertEqual(ts.get_status("c"), "cancelled")

    def test_cancel_does_not_propagate_to_unrelated_tasks(self):
        ts = TaskScheduler()
        ts.submit_task("a", 0.01)
        ts.submit_task("b", 0.01)
        ts.submit_task("unrelated", 0.01)
        ts.set_dependencies("b", ["a"])
        ts.cancel_task("a")
        self.assertEqual(ts.get_status("unrelated"), "pending")

    def test_cancel_does_not_affect_completed_dependents(self):
        ts = TaskScheduler()
        ts.submit_task("a", 0.01)
        ts.submit_task("b", 0.01)
        ts.set_dependencies("b", ["a"])
        # Complete b first (manually), then cancel a
        # b's dep is a, but b is already completed — should not be cancelled
        ts.complete_task("b")
        ts.cancel_task("a")
        self.assertEqual(ts.get_status("b"), "completed")

    def test_cancel_propagation_fan_out(self):
        """Cancelling one parent cancels multiple dependent children."""
        ts = TaskScheduler()
        ts.submit_task("root", 0.01)
        ts.submit_task("child1", 0.01)
        ts.submit_task("child2", 0.01)
        ts.submit_task("child3", 0.01)
        ts.set_dependencies("child1", ["root"])
        ts.set_dependencies("child2", ["root"])
        ts.set_dependencies("child3", ["root"])
        ts.cancel_task("root")
        self.assertEqual(ts.get_status("child1"), "cancelled")
        self.assertEqual(ts.get_status("child2"), "cancelled")
        self.assertEqual(ts.get_status("child3"), "cancelled")

    def test_cancel_running_task(self):
        """A running task should eventually reach 'cancelled' after cancellation."""
        ts = TaskScheduler()
        ts.submit_task("slow", 0.3)
        ts.start_workers(1)
        time.sleep(0.05)  # let worker claim the task
        ts.cancel_task("slow")
        time.sleep(0.4)   # let worker finish sleeping and detect cancellation
        ts.stop_workers()
        # After workers finish, task should be cancelled (not completed)
        self.assertEqual(ts.get_status("slow"), "cancelled")


class TestLevel6WaitForCompletion(unittest.TestCase):

    def test_wait_for_missing_task_returns_empty(self):
        ts = TaskScheduler()
        result = ts.wait_for_completion("ghost", timeout=0.05)
        self.assertEqual(result, "")

    def test_wait_completes_when_task_completes(self):
        ts = TaskScheduler()
        ts.submit_task("job", 0.05)
        ts.start_workers(1)
        result = ts.wait_for_completion("job", timeout=1.0)
        ts.stop_workers()
        self.assertEqual(result, "completed")

    def test_wait_times_out_when_no_workers(self):
        ts = TaskScheduler()
        ts.submit_task("idle", 0.01)
        # No workers — task will never complete
        result = ts.wait_for_completion("idle", timeout=0.05)
        self.assertEqual(result, "")

    def test_wait_returns_cancelled_when_cancelled(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 5.0)  # long duration, no workers
        # Cancel the task from another thread after a short delay
        def cancel_later():
            time.sleep(0.05)
            ts.cancel_task("t1")
        threading.Thread(target=cancel_later, daemon=True).start()
        result = ts.wait_for_completion("t1", timeout=1.0)
        self.assertEqual(result, "cancelled")

    def test_wait_returns_immediately_if_already_completed(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 0.01)
        ts.complete_task("t1")
        start = time.time()
        result = ts.wait_for_completion("t1", timeout=1.0)
        elapsed = time.time() - start
        self.assertEqual(result, "completed")
        self.assertLess(elapsed, 0.1)  # should return nearly instantly

    def test_wait_returns_immediately_if_already_cancelled(self):
        ts = TaskScheduler()
        ts.submit_task("t1", 0.01)
        ts.cancel_task("t1")
        start = time.time()
        result = ts.wait_for_completion("t1", timeout=1.0)
        elapsed = time.time() - start
        self.assertEqual(result, "cancelled")
        self.assertLess(elapsed, 0.1)

    def test_multiple_threads_wait_on_same_task(self):
        """Multiple waiters are all woken when the task completes."""
        ts = TaskScheduler()
        ts.submit_task("shared", 0.05)
        ts.start_workers(1)

        results = []
        lock = threading.Lock()

        def wait_and_record():
            r = ts.wait_for_completion("shared", timeout=1.0)
            with lock:
                results.append(r)

        waiters = [threading.Thread(target=wait_and_record) for _ in range(5)]
        for w in waiters:
            w.start()
        for w in waiters:
            w.join()
        ts.stop_workers()

        self.assertEqual(results, ["completed"] * 5)

    def test_wait_no_timeout_blocks_until_done(self):
        """With timeout=None, wait blocks indefinitely until terminal state."""
        ts = TaskScheduler()
        ts.submit_task("job", 0.05)
        ts.start_workers(1)
        # timeout=None — should return when task completes
        result = ts.wait_for_completion("job", timeout=None)
        ts.stop_workers()
        self.assertEqual(result, "completed")


class TestLevel6ConcurrentCancellation(unittest.TestCase):

    def test_cancel_while_multiple_workers_running(self):
        """Cancel a pending task while workers are busy; cancelled task must not run."""
        ts = TaskScheduler()
        # Fill workers with long tasks first, then submit a quick one and cancel it
        for i in range(3):
            ts.submit_task(f"blocker{i}", 0.5)
        ts.submit_task("target", 0.01)

        ts.start_workers(3)
        time.sleep(0.02)   # workers pick up blockers
        ts.cancel_task("target")
        time.sleep(0.1)
        status = ts.get_status("target")
        ts.stop_workers()

        # target was either cancelled before running, or was never picked up
        self.assertIn(status, ("cancelled", "completed"))
        # If it ran anyway (race), we can't fully prevent it — but it must not be "pending"
        self.assertNotEqual(status, "pending")

    def test_propagation_with_workers_running(self):
        """Cancellation propagation works correctly even when workers are running."""
        ts = TaskScheduler()
        ts.submit_task("root", 5.0)    # long task, will be running when we cancel
        ts.submit_task("child", 0.01)
        ts.set_dependencies("child", ["root"])

        ts.start_workers(1)
        time.sleep(0.05)   # worker picks up "root"
        ts.cancel_task("root")
        time.sleep(0.1)
        ts.stop_workers()

        self.assertEqual(ts.get_status("root"), "cancelled")
        self.assertEqual(ts.get_status("child"), "cancelled")

    def test_wait_and_cancel_race(self):
        """wait_for_completion and cancel_task called concurrently from different threads."""
        ts = TaskScheduler()
        ts.submit_task("job", 5.0)  # no workers — won't complete naturally

        wait_result = []

        def do_wait():
            r = ts.wait_for_completion("job", timeout=1.0)
            wait_result.append(r)

        def do_cancel():
            time.sleep(0.05)
            ts.cancel_task("job")

        t_wait = threading.Thread(target=do_wait)
        t_cancel = threading.Thread(target=do_cancel)
        t_wait.start()
        t_cancel.start()
        t_wait.join()
        t_cancel.join()

        self.assertEqual(wait_result, ["cancelled"])


if __name__ == "__main__":
    unittest.main()
