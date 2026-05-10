"""Tests for Exercise 07 — Readers-Writers Lock."""

import threading
import time
import unittest

from solution import RWLock


class TestRWLockBasic(unittest.TestCase):
    def test_single_reader(self):
        lock = RWLock()
        lock.read_acquire()
        lock.read_release()

    def test_single_writer(self):
        lock = RWLock()
        lock.write_acquire()
        lock.write_release()

    def test_multiple_sequential_readers(self):
        lock = RWLock()
        for _ in range(5):
            lock.read_acquire()
            lock.read_release()

    def test_multiple_sequential_writers(self):
        lock = RWLock()
        for _ in range(5):
            lock.write_acquire()
            lock.write_release()


class TestRWLockConcurrency(unittest.TestCase):
    def _run_readers_writers(self, n_readers, n_writers, hold_time=0.02):
        """
        Run n_readers and n_writers concurrently.
        Returns (max_concurrent_readers, writer_overlap_detected).
        """
        lock = RWLock()
        active_readers = [0]
        active_writers = [0]
        max_readers = [0]
        writer_overlap = [False]
        counter_lock = threading.Lock()

        def reader():
            lock.read_acquire()
            try:
                with counter_lock:
                    active_readers[0] += 1
                    if active_writers[0] > 0:
                        writer_overlap[0] = True
                    if active_readers[0] > max_readers[0]:
                        max_readers[0] = active_readers[0]
                time.sleep(hold_time)
                with counter_lock:
                    active_readers[0] -= 1
            finally:
                lock.read_release()

        def writer():
            lock.write_acquire()
            try:
                with counter_lock:
                    active_writers[0] += 1
                    if active_readers[0] > 0:
                        writer_overlap[0] = True
                time.sleep(hold_time)
                with counter_lock:
                    active_writers[0] -= 1
            finally:
                lock.write_release()

        threads = (
            [threading.Thread(target=reader) for _ in range(n_readers)]
            + [threading.Thread(target=writer) for _ in range(n_writers)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        return max_readers[0], writer_overlap[0]

    def test_multiple_concurrent_readers_allowed(self):
        """At some point, at least 2 readers must be active simultaneously."""
        max_r, overlap = self._run_readers_writers(n_readers=10, n_writers=0)
        self.assertGreater(max_r, 1, "Expected concurrent readers but only ever 1 active")
        self.assertFalse(overlap)

    def test_writer_excludes_readers(self):
        """A writer must never be active simultaneously with any reader."""
        _, overlap = self._run_readers_writers(n_readers=10, n_writers=2)
        self.assertFalse(overlap, "Writer and reader were active at the same time!")

    def test_no_deadlock(self):
        """All threads must finish within the timeout."""
        max_r, overlap = self._run_readers_writers(n_readers=10, n_writers=2, hold_time=0.01)
        # If we reach here, no deadlock. Also check correctness.
        self.assertFalse(overlap)

    def test_only_one_writer_at_a_time(self):
        """Two writers must never overlap."""
        lock = RWLock()
        active_writers = [0]
        overlap_detected = [False]
        w_lock = threading.Lock()

        def writer():
            lock.write_acquire()
            try:
                with w_lock:
                    active_writers[0] += 1
                    if active_writers[0] > 1:
                        overlap_detected[0] = True
                time.sleep(0.02)
                with w_lock:
                    active_writers[0] -= 1
            finally:
                lock.write_release()

        threads = [threading.Thread(target=writer) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.assertFalse(overlap_detected[0], "Multiple writers were active simultaneously!")


if __name__ == "__main__":
    unittest.main()
