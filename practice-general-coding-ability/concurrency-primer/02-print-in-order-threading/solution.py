"""
Exercise 02 — Print in Order (Threading)

Guarantee first() → second() → third() regardless of thread scheduling order.

Allowed imports: threading (stdlib only)
"""

import threading
from typing import Callable


class OrderedPrinter:
    def __init__(self) -> None:
        # TODO: create threading.Event objects to coordinate ordering
        self._first_done = threading.Event()
        self._second_done = threading.Event()

    def first(self, print_fn: Callable[[], None]) -> None:
        """Run print_fn, then signal that first is done."""
        print_fn()
        self._first_done.set()

    def second(self, print_fn: Callable[[], None]) -> None:
        """Wait for first to finish, run print_fn, then signal second is done."""
        self._first_done.wait()
        print_fn()
        self._second_done.set()

    def third(self, print_fn: Callable[[], None]) -> None:
        """Wait for second to finish, then run print_fn."""
        self._second_done.wait()
        print_fn()
