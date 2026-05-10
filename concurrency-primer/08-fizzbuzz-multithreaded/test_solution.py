"""Tests for Exercise 08 — FizzBuzz Multithreaded."""

import threading
import unittest

from solution import FizzBuzz


def _expected_sequence(n):
    result = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            result.append("fizzbuzz")
        elif i % 3 == 0:
            result.append("fizz")
        elif i % 5 == 0:
            result.append("buzz")
        else:
            result.append(i)
    return result


def _run_fizzbuzz(n, timeout=10):
    output = []
    lock = threading.Lock()

    fb = FizzBuzz(n)

    def record(value):
        with lock:
            output.append(value)

    threads = [
        threading.Thread(target=fb.fizz,     args=(lambda: record("fizz"),)),
        threading.Thread(target=fb.buzz,     args=(lambda: record("buzz"),)),
        threading.Thread(target=fb.fizzbuzz, args=(lambda: record("fizzbuzz"),)),
        threading.Thread(target=fb.number,   args=(lambda v: record(v),)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=timeout)

    alive = [t for t in threads if t.is_alive()]
    if alive:
        raise TimeoutError(f"{len(alive)} thread(s) still alive after {timeout}s")

    return output


class TestFizzBuzzCorrectness(unittest.TestCase):
    def test_n30(self):
        output = _run_fizzbuzz(30)
        expected = _expected_sequence(30)
        self.assertEqual(output, expected, f"Got: {output}\nExpected: {expected}")

    def test_n1(self):
        output = _run_fizzbuzz(1)
        self.assertEqual(output, [1])

    def test_n15(self):
        output = _run_fizzbuzz(15)
        expected = _expected_sequence(15)
        self.assertEqual(output, expected)

    def test_n100(self):
        output = _run_fizzbuzz(100)
        expected = _expected_sequence(100)
        self.assertEqual(output, expected)

    def test_no_deadlock(self):
        """All threads must terminate within the timeout."""
        try:
            _run_fizzbuzz(60, timeout=10)
        except TimeoutError as e:
            self.fail(str(e))

    def test_exact_count(self):
        """Output length must equal n."""
        n = 30
        output = _run_fizzbuzz(n)
        self.assertEqual(len(output), n, f"Expected {n} items, got {len(output)}")

    def test_fizzbuzz_positions(self):
        """Check specific positions in n=30 output."""
        output = _run_fizzbuzz(30)
        # 1-indexed: position 3 → "fizz", 5 → "buzz", 15 → "fizzbuzz", 7 → 7
        self.assertEqual(output[2],  "fizz")      # index 2 = number 3
        self.assertEqual(output[4],  "buzz")      # index 4 = number 5
        self.assertEqual(output[14], "fizzbuzz")  # index 14 = number 15
        self.assertEqual(output[6],  7)           # index 6 = number 7


if __name__ == "__main__":
    unittest.main()
