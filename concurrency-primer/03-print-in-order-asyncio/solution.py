"""
Exercise 03 — Print in Order (asyncio)

Same as Exercise 02, but using asyncio coroutines instead of threads.

Allowed imports: asyncio (stdlib only)
"""

import asyncio
from typing import Callable


class AsyncOrderedPrinter:
    def __init__(self) -> None:
        self._first_done = asyncio.Event()
        self._second_done = asyncio.Event()

    async def first(self, print_fn: Callable[[], None]) -> None:
        """Run print_fn, then signal that first is done."""
        print_fn()
        self._first_done.set()

    async def second(self, print_fn: Callable[[], None]) -> None:
        """Wait for first to finish, run print_fn, then signal second is done."""
        await self._first_done.wait()
        print_fn()
        self._second_done.set()

    async def third(self, print_fn: Callable[[], None]) -> None:
        """Wait for second to finish, then run print_fn."""
        await self._second_done.wait()
        print_fn()
