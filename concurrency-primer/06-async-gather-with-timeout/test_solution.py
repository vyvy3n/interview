"""Tests for Exercise 06 — Async Gather with Timeout."""

import asyncio
import unittest

from solution import TIMEOUT_SENTINEL, gather_with_timeout


async def fast(value, delay=0.05):
    await asyncio.sleep(delay)
    return value


async def slow(value, delay=5.0):
    await asyncio.sleep(delay)
    return value


class TestGatherWithTimeoutBasic(unittest.IsolatedAsyncioTestCase):
    async def test_all_fast(self):
        """All coroutines complete before timeout — no sentinels."""
        coros = [fast(i) for i in range(5)]
        result = await gather_with_timeout(coros, timeout=1.0)
        self.assertEqual(result, list(range(5)))

    async def test_all_slow(self):
        """All coroutines exceed timeout — all sentinels."""
        coros = [slow(i) for i in range(3)]
        result = await gather_with_timeout(coros, timeout=0.1)
        self.assertEqual(result, [TIMEOUT_SENTINEL] * 3)

    async def test_mixed(self):
        """
        Fast coroutines get their values; slow ones get TIMEOUT_SENTINEL.
        Input: [fast(0), slow(1), fast(2), slow(3), fast(4)]
        Expected: [0, TIMEOUT_SENTINEL, 2, TIMEOUT_SENTINEL, 4]
        """
        coros = [
            fast(0),
            slow(1),
            fast(2),
            slow(3),
            fast(4),
        ]
        result = await gather_with_timeout(coros, timeout=0.5)
        self.assertEqual(result[0], 0)
        self.assertIs(result[1], TIMEOUT_SENTINEL)
        self.assertEqual(result[2], 2)
        self.assertIs(result[3], TIMEOUT_SENTINEL)
        self.assertEqual(result[4], 4)

    async def test_order_preserved(self):
        """Result order must match input order regardless of completion order."""
        # Coroutines with different delays — slower ones have smaller indices.
        coros = [
            fast(0, delay=0.3),
            fast(1, delay=0.1),
            fast(2, delay=0.2),
        ]
        result = await gather_with_timeout(coros, timeout=1.0)
        self.assertEqual(result, [0, 1, 2])

    async def test_empty_input(self):
        result = await gather_with_timeout([], timeout=1.0)
        self.assertEqual(result, [])


class TestGatherWithTimeoutCleanup(unittest.IsolatedAsyncioTestCase):
    async def test_timed_out_coroutines_are_cancelled(self):
        """
        Slow coroutines must be cancelled (not just abandoned), so no tasks
        linger after gather_with_timeout returns.
        """
        cancelled_flags = []

        async def cancellable(idx):
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                cancelled_flags.append(idx)
                raise

        coros = [cancellable(i) for i in range(3)]
        result = await gather_with_timeout(coros, timeout=0.1)

        # Give event loop a tick to process cancellations
        await asyncio.sleep(0)

        self.assertEqual(result, [TIMEOUT_SENTINEL] * 3)
        self.assertEqual(
            sorted(cancelled_flags),
            [0, 1, 2],
            "All slow coroutines should have received CancelledError",
        )

    async def test_no_exception_raised(self):
        """gather_with_timeout must not raise even when all coros time out."""
        coros = [slow(i) for i in range(5)]
        try:
            result = await gather_with_timeout(coros, timeout=0.05)
        except Exception as e:
            self.fail(f"gather_with_timeout raised unexpectedly: {e}")
        self.assertEqual(len(result), 5)


if __name__ == "__main__":
    unittest.main()
