"""Tests for Exercise 03 — Print in Order (asyncio)."""

import asyncio
import itertools
import unittest

from solution import AsyncOrderedPrinter


async def _run_ordered_async(start_order):
    """
    Schedule all three coroutines concurrently in the given start_order.
    Returns the log list (must be ['first', 'second', 'third']).
    """
    log = []
    printer = AsyncOrderedPrinter()

    def make_fn(label):
        def fn():
            log.append(label)
        return fn

    method_map = {
        "first":  printer.first(make_fn("first")),
        "second": printer.second(make_fn("second")),
        "third":  printer.third(make_fn("third")),
    }

    coros = [method_map[name] for name in start_order]
    await asyncio.gather(*coros)
    return log


class TestAsyncOrderedPrinter(unittest.IsolatedAsyncioTestCase):
    async def test_natural_order(self):
        result = await _run_ordered_async(["first", "second", "third"])
        self.assertEqual(result, ["first", "second", "third"])

    async def test_reverse_order(self):
        result = await _run_ordered_async(["third", "second", "first"])
        self.assertEqual(result, ["first", "second", "third"])

    async def test_all_six_permutations(self):
        labels = ["first", "second", "third"]
        for perm in itertools.permutations(labels):
            with self.subTest(start_order=perm):
                result = await _run_ordered_async(list(perm))
                self.assertEqual(
                    result,
                    ["first", "second", "third"],
                    msg=f"Failed with scheduling order {perm}",
                )

    async def test_multiple_instances_independent(self):
        """Two AsyncOrderedPrinter instances must not share event state."""
        log1, log2 = [], []

        p1 = AsyncOrderedPrinter()
        p2 = AsyncOrderedPrinter()

        await asyncio.gather(
            p1.third(lambda: log1.append("p1-third")),
            p2.first(lambda: log2.append("p2-first")),
            p1.first(lambda: log1.append("p1-first")),
            p2.third(lambda: log2.append("p2-third")),
            p1.second(lambda: log1.append("p1-second")),
            p2.second(lambda: log2.append("p2-second")),
        )

        self.assertEqual(log1, ["p1-first", "p1-second", "p1-third"])
        self.assertEqual(log2, ["p2-first", "p2-second", "p2-third"])

    async def test_no_hang(self):
        """Coroutines must finish within a reasonable timeout."""
        try:
            result = await asyncio.wait_for(
                _run_ordered_async(["third", "second", "first"]),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            self.fail("Coroutines timed out — possible deadlock")
        self.assertEqual(result, ["first", "second", "third"])


if __name__ == "__main__":
    unittest.main()
