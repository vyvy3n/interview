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
        self._cond = threading.Condition()

    def fizz(self, print_fn: Callable[[str], None]) -> None:
        """Print 'fizz' for each multiple of 3 (not 15) up to n."""
        with self._cond:
            while self._current <= self._n:
                c = self._current
                if c % 3 == 0 and c % 15 != 0:
                    print_fn("fizz")
                    self._current += 1
                    self._cond.notify_all()
                else:
                    self._cond.wait()

    def buzz(self, print_fn: Callable[[str], None]) -> None:
        """Print 'buzz' for each multiple of 5 (not 15) up to n."""
        with self._cond:
            while self._current <= self._n:
                c = self._current
                if c % 5 == 0 and c % 15 != 0:
                    print_fn("buzz")
                    self._current += 1
                    self._cond.notify_all()
                else:
                    self._cond.wait()

    def fizzbuzz(self, print_fn: Callable[[str], None]) -> None:
        """Print 'fizzbuzz' for each multiple of 15 up to n."""
        with self._cond:
            while self._current <= self._n:
                c = self._current
                if c % 15 == 0:
                    print_fn("fizzbuzz")
                    self._current += 1
                    self._cond.notify_all()
                else:
                    self._cond.wait()

    def number(self, print_fn: Callable[[int], None]) -> None:
        """Print the integer for each number not divisible by 3 or 5."""
        with self._cond:
            while self._current <= self._n:
                c = self._current
                if c % 3 != 0 and c % 5 != 0:
                    print_fn(c)
                    self._current += 1
                    self._cond.notify_all()
                else:
                    self._cond.wait()
