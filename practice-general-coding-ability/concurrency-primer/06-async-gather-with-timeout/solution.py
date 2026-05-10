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
    if not coros:
        return []

    # asyncio.wait expects Tasks, not bare coroutines (problem gotcha #1).
    tasks = [asyncio.create_task(c) for c in coros]

    # Wait until every task has finished OR the wall timeout elapses.
    _, pending = await asyncio.wait(tasks, timeout=timeout)

    # Slow tasks are still in ``pending`` — cancel them (gotcha #2).
    for t in pending:
        t.cancel()

    # Let cancelled tasks run their cleanup / absorb CancelledError (gotcha #3).
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)

    # Build results in the same order as ``coros`` (gotcha #4: index = order).
    out: list = []
    for t in tasks:
        if t.cancelled():
            out.append(TIMEOUT_SENTINEL)
        else:
            exc = t.exception()
            if exc is not None:
                out.append(TIMEOUT_SENTINEL)
            else:
                out.append(t.result())
    return out
