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
        # TODO: create an asyncio.Semaphore with `rate` initial tokens
        raise NotImplementedError

    async def acquire(self) -> None:
        """
        Block until a rate-limit slot is available, then return.
        Schedule a background task to release the slot after 1 second.
        """
        raise NotImplementedError
