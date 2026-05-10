"""
Exercise 09 — Async Semaphore Fetcher

Fetch all URLs concurrently, but cap concurrency at max_concurrent.
Simulate each fetch with asyncio.sleep(0.1).

Allowed imports: asyncio (stdlib only)
"""

import asyncio


async def fetch_all(urls: list[str], max_concurrent: int) -> list[str]:
    """
    "Fetch" each URL concurrently, throttled to max_concurrent at a time.

    Args:
        urls:           list of URL strings.
        max_concurrent: maximum simultaneous fetches.

    Returns:
        list of f"result:{url}" strings, in the same order as urls.
    """
    # No work — avoid gather() edge cases and match tests for empty input.
    if not urls:
        return []

    # -------------------------------------------------------------------------
    # Why an asyncio.Semaphore?
    # -------------------------------------------------------------------------
    # A semaphore is a shared counter of "permits". ``async with sem`` takes one
    # permit on entry and returns it on exit. If none are free, the coroutine
    # waits until another coroutine exits its ``async with`` block.
    #
    # Starting value = max_concurrent  →  at most that many coroutines can be
    # inside the ``async with sem`` block at the same time. That caps how many
    # simulated HTTP fetches overlap (problem goal + tests that measure peak).
    # -------------------------------------------------------------------------
    sem = asyncio.Semaphore(max_concurrent)

    async def fetch_one(url: str) -> str:
        """
        One simulated fetch for a single URL.

        Why a nested helper (not one acquire for the whole batch)?
        ------------------------------------------------------------
        The limit must be *per in-flight fetch*. Each URL needs its own
        ``async with sem`` around only its sleep+return. If you acquired the
        semaphore once for all URLs, you would serialize everything (gotcha #2).
        """
        # ``async with`` = acquire before sleep, release after, even on errors.
        # Manual acquire()/release() is easy to get wrong on exceptions.
        async with sem:
            # Stand in for real I/O (DNS, TCP, TLS, response body). ``await``
            # yields so other fetch_one tasks can run — up to ``max_concurrent``
            # of them can be past ``async with sem`` at once.
            await asyncio.sleep(0.1)
            return f"result:{url}"

    # -------------------------------------------------------------------------
    # Why asyncio.gather?
    # -------------------------------------------------------------------------
    # ``gather`` schedules every ``fetch_one(u)`` coroutine on the event loop
    # immediately. They all *start*, but the semaphore ensures only
    # ``max_concurrent`` enter the ``async with`` body at a time; the rest wait
    # on the semaphore until a slot frees up.
    #
    # Order: when you pass awaitables positionally like gather(a, b, c), the
    # returned list matches that same order — same as input URL order here
    # (problem gotcha #4). So result[i] always corresponds to urls[i].
    # -------------------------------------------------------------------------
    return list(await asyncio.gather(*(fetch_one(u) for u in urls)))
