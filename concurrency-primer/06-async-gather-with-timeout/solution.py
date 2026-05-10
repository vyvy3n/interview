"""
Exercise 06 — Async Gather with Timeout

Implement gather_with_timeout: like asyncio.gather but returns TIMEOUT_SENTINEL
for coroutines that do not finish within the timeout.

Allowed imports: asyncio (stdlib only)
"""

import asyncio

# Sentinel returned in place of a timed-out coroutine's result.
TIMEOUT_SENTINEL = object()


async def gather_with_timeout(coros: list, timeout: float) -> list:
    """
    Run all coroutines concurrently.  Return a list whose i-th element is
    either the result of coros[i] or TIMEOUT_SENTINEL if it did not finish
    within `timeout` seconds.

    Args:
        coros:   list of coroutines (not yet started).
        timeout: seconds to wait before cancelling slow coroutines.

    Returns:
        list of length len(coros), in input order.
    """
    raise NotImplementedError
