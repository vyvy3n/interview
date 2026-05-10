"""
Exercise 08 — FizzBuzz Multithreaded

Four threads collaborate to print the FizzBuzz sequence in order.
Thread A → "fizz", Thread B → "buzz", Thread C → "fizzbuzz", Thread D → number.

Allowed imports: threading (stdlib only)
"""

import threading
from typing import Callable


class FizzBuzz:
    def __init__(self, n: int) -> None:
        self._n = n
        self._current = 1
        # TODO: add a threading.Condition shared by all four methods
        raise NotImplementedError

    def fizz(self, print_fn: Callable[[str], None]) -> None:
        """Print 'fizz' for each multiple of 3 (not 15) up to n."""
        raise NotImplementedError

    def buzz(self, print_fn: Callable[[str], None]) -> None:
        """Print 'buzz' for each multiple of 5 (not 15) up to n."""
        raise NotImplementedError

    def fizzbuzz(self, print_fn: Callable[[str], None]) -> None:
        """Print 'fizzbuzz' for each multiple of 15 up to n."""
        raise NotImplementedError

    def number(self, print_fn: Callable[[int], None]) -> None:
        """Print the integer for each number not divisible by 3 or 5."""
        raise NotImplementedError
