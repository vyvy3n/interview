"""Tests for Exercise 02 — Print in Order (Threading)."""

import itertools
import threading
import time
import unittest

from solution import OrderedPrinter


def _run_ordered(start_order):
    """
    Spawn threads for first/second/third in the given start_order.
    Returns the list of strings appended by each print_fn, in the order
    they were appended (which must be ["first", "second", "third"]).
    """
    log = []
    lock = threading.Lock()

    printer = OrderedPrinter()

    def make_fn(label):
        def fn():
            with lock:
                log.append(label)
        return fn

    method_map = {
        "first":  (printer.first,  make_fn("first")),
        "second": (printer.second, make_fn("second")),
        "third":  (printer.third,  make_fn("third")),
    }

    threads = [
        threading.Thread(target=method_map[name][0], args=(method_map[name][1],))
        for name in start_order
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    return log


class TestOrderedPrinterAllPermutations(unittest.TestCase):
    def test_all_six_orderings(self):
        """Every scheduling permutation must produce ['first','second','third']."""
        labels = ["first", "second", "third"]
        for perm in itertools.permutations(labels):
            with self.subTest(start_order=perm):
                result = _run_ordered(perm)
                self.assertEqual(
                    result,
                    ["first", "second", "third"],
                    msg=f"Failed with thread start order {perm}",
                )

    def test_no_deadlock(self):
        """Threads must finish within 5 seconds in the reverse order."""
        start = time.monotonic()
        result = _run_ordered(["third", "second", "first"])
        elapsed = time.monotonic() - start
        self.assertEqual(result, ["first", "second", "third"])
        self.assertLess(elapsed, 5.0, "Possible deadlock — took too long")

    def test_multiple_instances_independent(self):
        """Two OrderedPrinter instances must not share state."""
        log1, log2 = [], []
        lock = threading.Lock()

        p1 = OrderedPrinter()
        p2 = OrderedPrinter()

        def append(target, label):
            with lock:
                target.append(label)

        threads = [
            threading.Thread(target=p1.third,  args=(lambda: append(log1, "first-third"),)),
            threading.Thread(target=p1.second, args=(lambda: append(log1, "first-second"),)),
            threading.Thread(target=p1.first,  args=(lambda: append(log1, "first-first"),)),
            threading.Thread(target=p2.first,  args=(lambda: append(log2, "second-first"),)),
            threading.Thread(target=p2.third,  args=(lambda: append(log2, "second-third"),)),
            threading.Thread(target=p2.second, args=(lambda: append(log2, "second-second"),)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        self.assertEqual(log1, ["first-first", "first-second", "first-third"])
        self.assertEqual(log2, ["second-first", "second-second", "second-third"])


if __name__ == "__main__":
    unittest.main()
