"""Tests for Exercise 05 — Async Rate Limiter."""

import asyncio
import time
import unittest

from solution import RateLimiter


class TestRateLimiterBasic(unittest.IsolatedAsyncioTestCase):
    async def test_single_acquire_returns(self):
        """A single acquire() must return promptly."""
        limiter = RateLimiter(rate=5)
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 0.5, "single acquire() took too long")

    async def test_within_rate_returns_immediately(self):
        """Calling acquire() <= rate times should return without sleeping."""
        rate = 5
        limiter = RateLimiter(rate=rate)
        start = time.monotonic()
        for _ in range(rate):
            await limiter.acquire()
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 0.5, f"{rate} acquires within rate should be fast")


class TestRateLimiterTiming(unittest.IsolatedAsyncioTestCase):
    async def test_rate_2_per_sec_10_calls(self):
        """
        10 calls at rate=2/sec.
        First 2 free, then groups of 2 each second → at least 4 seconds total.
        Allow up to 6.5 seconds for slow machines.
        """
        rate = 2
        n_calls = 10
        limiter = RateLimiter(rate=rate)

        start = time.monotonic()
        await asyncio.gather(*(limiter.acquire() for _ in range(n_calls)))
        elapsed = time.monotonic() - start

        # ceil((n_calls - rate) / rate) = ceil(8/2) = 4 seconds minimum
        self.assertGreaterEqual(
            elapsed,
            3.8,
            f"Rate limiting too fast: {elapsed:.2f}s (expected >= 3.8s)",
        )
        self.assertLess(
            elapsed,
            7.0,
            f"Rate limiting too slow: {elapsed:.2f}s",
        )

    async def test_rate_5_per_sec_10_calls(self):
        """
        10 calls at rate=5/sec.
        First 5 free, next 5 wait ~1 second → ~1 second total.
        """
        rate = 5
        n_calls = 10
        limiter = RateLimiter(rate=rate)

        start = time.monotonic()
        await asyncio.gather(*(limiter.acquire() for _ in range(n_calls)))
        elapsed = time.monotonic() - start

        self.assertGreaterEqual(elapsed, 0.8)
        self.assertLess(elapsed, 3.0)

    async def test_concurrent_callers_do_not_exceed_rate(self):
        """
        Track timestamps of when each acquire() returns.
        In any 1-second window, at most `rate` calls should have completed.
        """
        rate = 3
        n_calls = 9
        limiter = RateLimiter(rate=rate)
        timestamps = []
        lock = asyncio.Lock()

        async def call():
            await limiter.acquire()
            async with lock:
                timestamps.append(time.monotonic())

        await asyncio.gather(*(call() for _ in range(n_calls)))

        # Check: in any 1.05s window, count <= rate
        timestamps.sort()
        for i, ts in enumerate(timestamps):
            window = [t for t in timestamps if ts <= t <= ts + 1.05]
            self.assertLessEqual(
                len(window),
                rate + 1,  # +1 for timing jitter on the boundary
                f"Too many calls in 1s window starting at index {i}: {len(window)}",
            )


if __name__ == "__main__":
    unittest.main()
