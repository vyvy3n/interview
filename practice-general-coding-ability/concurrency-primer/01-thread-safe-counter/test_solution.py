"""Tests for Exercise 01 — Thread-Safe Counter."""

import threading
import unittest

from solution import Counter


class TestCounterBasic(unittest.TestCase):
    def test_initial_value(self):
        c = Counter()
        self.assertEqual(c.value(), 0)

    def test_single_increment(self):
        c = Counter()
        c.increment()
        self.assertEqual(c.value(), 1)

    def test_increment_with_delta(self):
        c = Counter()
        c.increment(5)
        self.assertEqual(c.value(), 5)

    def test_multiple_increments(self):
        c = Counter()
        for _ in range(10):
            c.increment()
        self.assertEqual(c.value(), 10)

    def test_increment_negative_delta(self):
        c = Counter()
        c.increment(10)
        c.increment(-3)
        self.assertEqual(c.value(), 7)


class TestCounterConcurrent(unittest.TestCase):
    def _run_threads(self, counter, n_threads, n_increments):
        """Spawn n_threads threads, each incrementing n_increments times."""
        threads = [
            threading.Thread(
                target=lambda: [counter.increment() for _ in range(n_increments)]
            )
            for _ in range(n_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def test_no_lost_updates_medium(self):
        """100 threads × 1000 increments = 100,000."""
        c = Counter()
        self._run_threads(c, n_threads=100, n_increments=1000)
        self.assertEqual(c.value(), 100_000)

    def test_no_lost_updates_large(self):
        """1000 threads × 1000 increments = 1,000,000.  Core requirement."""
        c = Counter()
        self._run_threads(c, n_threads=1000, n_increments=1000)
        self.assertEqual(c.value(), 1_000_000)

    def test_concurrent_reads_are_consistent(self):
        """Readers interleaved with writers should never see a negative count."""
        c = Counter()
        errors = []

        def reader():
            for _ in range(500):
                if c.value() < 0:
                    errors.append("negative value observed")

        def writer():
            for _ in range(500):
                c.increment()

        threads = (
            [threading.Thread(target=writer) for _ in range(10)]
            + [threading.Thread(target=reader) for _ in range(10)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])

    def test_multiple_counters_independent(self):
        """Two counters incremented in parallel stay independent."""
        c1, c2 = Counter(), Counter()

        def bump_c1():
            for _ in range(500):
                c1.increment()

        def bump_c2():
            for _ in range(300):
                c2.increment()

        threads = (
            [threading.Thread(target=bump_c1) for _ in range(4)]
            + [threading.Thread(target=bump_c2) for _ in range(4)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(c1.value(), 2000)
        self.assertEqual(c2.value(), 1200)


if __name__ == "__main__":
    unittest.main()
