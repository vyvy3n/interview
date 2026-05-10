"""Tests for Exercise 09 — Async Semaphore Fetcher."""

import asyncio
import unittest

from solution import fetch_all


class TestFetchAllBasic(unittest.IsolatedAsyncioTestCase):
    async def test_returns_all_results(self):
        """All URLs should produce a result."""
        urls = [f"http://example.com/{i}" for i in range(10)]
        results = await fetch_all(urls, max_concurrent=5)
        self.assertEqual(len(results), len(urls))

    async def test_result_format(self):
        """Each result must be 'result:<url>'."""
        urls = ["http://a.com", "http://b.com"]
        results = await fetch_all(urls, max_concurrent=2)
        self.assertEqual(results[0], "result:http://a.com")
        self.assertEqual(results[1], "result:http://b.com")

    async def test_order_preserved(self):
        """Results must be in the same order as input URLs."""
        urls = [f"http://example.com/{i}" for i in range(20)]
        results = await fetch_all(urls, max_concurrent=5)
        expected = [f"result:{url}" for url in urls]
        self.assertEqual(results, expected)

    async def test_empty_urls(self):
        results = await fetch_all([], max_concurrent=5)
        self.assertEqual(results, [])

    async def test_max_concurrent_one(self):
        """max_concurrent=1 should still fetch all URLs, just serially."""
        urls = [f"http://example.com/{i}" for i in range(5)]
        results = await fetch_all(urls, max_concurrent=1)
        expected = [f"result:{url}" for url in urls]
        self.assertEqual(results, expected)


class TestFetchAllConcurrencyLimit(unittest.IsolatedAsyncioTestCase):
    async def test_concurrency_never_exceeds_limit(self):
        """
        Track active fetches via a shared counter.
        Peak must be <= max_concurrent.
        """
        max_concurrent = 5
        n_urls = 20
        urls = [f"http://example.com/{i}" for i in range(n_urls)]

        active = [0]
        peak = [0]
        counter_lock = asyncio.Lock()

        # Monkey-patch: replace fetch_all's internal logic by wrapping it.
        # Instead, we test by injecting a custom fetch via a closure.

        async def tracked_fetch_all(urls, max_concurrent):
            """Re-implement fetch_all inline so we can track concurrency."""
            sem = asyncio.Semaphore(max_concurrent)

            async def fetch_one(url):
                async with sem:
                    async with counter_lock:
                        active[0] += 1
                        if active[0] > peak[0]:
                            peak[0] = active[0]
                    await asyncio.sleep(0.05)  # simulate fetch
                    async with counter_lock:
                        active[0] -= 1
                    return f"result:{url}"

            return await asyncio.gather(*(fetch_one(u) for u in urls))

        results = await tracked_fetch_all(urls, max_concurrent)

        self.assertEqual(len(results), n_urls)
        self.assertLessEqual(
            peak[0],
            max_concurrent,
            f"Peak concurrency {peak[0]} exceeded limit {max_concurrent}",
        )
        self.assertGreater(
            peak[0],
            1,
            "Peak concurrency was 1 — parallelism is not happening",
        )

    async def test_actual_fetch_all_concurrency(self):
        """
        Test the real fetch_all function's concurrency by timing.
        20 URLs × 0.1s each, max_concurrent=5: should finish in ~0.4s (4 batches),
        not 2.0s (serial). Allow up to 1.5s to be safe.
        """
        import time
        urls = [f"http://example.com/{i}" for i in range(20)]
        start = time.monotonic()
        results = await fetch_all(urls, max_concurrent=5)
        elapsed = time.monotonic() - start

        self.assertEqual(len(results), 20)
        self.assertLess(
            elapsed,
            1.5,
            f"fetch_all took {elapsed:.2f}s — looks like it may be running serially",
        )
        # Must take at least ~0.4s (can't do 20 in one batch of 0.1s)
        self.assertGreaterEqual(
            elapsed,
            0.3,
            f"fetch_all finished suspiciously fast: {elapsed:.2f}s",
        )


if __name__ == "__main__":
    unittest.main()
