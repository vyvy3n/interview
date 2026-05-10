"""
Exercise 03 — Print in Order (asyncio)

Same as Exercise 02, but using asyncio coroutines instead of threads.

Allowed imports: asyncio (stdlib only)
"""

import asyncio
from typing import Callable


class AsyncOrderedPrinter:
    def __init__(self) -> None:
        # TODO: create asyncio.Event objects to coordinate ordering
        raise NotImplementedError

    async def first(self, print_fn: Callable[[], None]) -> None:
        """Run print_fn, then signal that first is done."""
        raise NotImplementedError

    async def second(self, print_fn: Callable[[], None]) -> None:
        """Wait for first to finish, run print_fn, then signal second is done."""
        raise NotImplementedError

    async def third(self, print_fn: Callable[[], None]) -> None:
        """Wait for second to finish, then run print_fn."""
        raise NotImplementedError
