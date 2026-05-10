"""
Exercise 05 — Async Rate Limiter

Implement a rate limiter: at most `rate` acquire() calls allowed per second.

Allowed imports: asyncio (stdlib only)
"""

import asyncio


class RateLimiter:
    def __init__(self, rate: int) -> None:
        """
        Args:
            rate: maximum number of acquire() calls allowed per second.
        """
        self._rate = rate
        # ``rate`` concurrent slots; each successful acquire returns one slot
        # after ``asyncio.sleep(1.0)`` in a background task (see problem.md).
        self._sem = asyncio.Semaphore(rate)

    async def _sleep_then_release(self) -> None:
        # try:
            await asyncio.sleep(1.0)
        # finally:
            self._sem.release()

        # Why try / finally around release()
        # Not required for the tests or for the “happy path” where sleep(1.0) runs to completion. 
        # If nothing ever cancels the task, sleep finishes, then release() runs — same as without try/finally.

    async def acquire(self) -> None:
        """
        Block until a rate-limit slot is available, then return.
        Schedule a background task to release the slot after 1 second.
        """
        await self._sem.acquire()
        asyncio.create_task(self._sleep_then_release())
