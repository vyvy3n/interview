"""
Exercise 09 — Async Semaphore Fetcher

Fetch all URLs concurrently, but cap concurrency at max_concurrent.
Simulate each fetch with asyncio.sleep(0.1).

Allowed imports: asyncio (stdlib only)
"""

import asyncio


async def fetch_all(urls: list, max_concurrent: int) -> list:
    """
    "Fetch" each URL concurrently, throttled to max_concurrent at a time.

    Args:
        urls:           list of URL strings.
        max_concurrent: maximum simultaneous fetches.

    Returns:
        list of f"result:{url}" strings, in the same order as urls.
    """
    raise NotImplementedError
