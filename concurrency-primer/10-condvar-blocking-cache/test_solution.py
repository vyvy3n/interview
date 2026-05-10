"""Tests for Exercise 10 — Conditional Variable Blocking Cache."""

import threading
import time
import unittest

from solution import BlockingCache


class TestBlockingCacheBasic(unittest.TestCase):
    def test_set_and_get_immediately(self):
        cache = BlockingCache()
        cache.set("foo", 42)
        self.assertEqual(cache.wait_get("foo"), 42)

    def test_multiple_keys(self):
        cache = BlockingCache()
        cache.set("a", 1)
        cache.set("b", 2)
        self.assertEqual(cache.wait_get("a"), 1)
        self.assertEqual(cache.wait_get("b"), 2)

    def test_overwrite(self):
        """set() on an existing key should update the value."""
        cache = BlockingCache()
        cache.set("k", "old")
        cache.set("k", "new")
        self.assertEqual(cache.wait_get("k"), "new")

    def test_value_types(self):
        """Cache should work with any value type."""
        cache = BlockingCache()
        cache.set("list", [1, 2, 3])
        cache.set("none", None)
        cache.set("dict", {"x": 1})
        self.assertEqual(cache.wait_get("list"), [1, 2, 3])
        self.assertIsNone(cache.wait_get("none"))
        self.assertEqual(cache.wait_get("dict"), {"x": 1})


class TestBlockingCacheBlocking(unittest.TestCase):
    def test_reader_blocks_until_writer(self):
        """wait_get must block until set() is called."""
        cache = BlockingCache()
        result = []
        ready = threading.Event()

        def reader():
            ready.set()
            result.append(cache.wait_get("key"))

        t = threading.Thread(target=reader)
        t.start()
        ready.wait()
        time.sleep(0.05)  # ensure reader is blocking

        self.assertTrue(t.is_alive(), "Reader should still be blocked")
        cache.set("key", "hello")
        t.join(timeout=3)
        self.assertFalse(t.is_alive(), "Reader should have unblocked")
        self.assertEqual(result, ["hello"])

    def test_multiple_readers_all_unblock(self):
        """All readers waiting for the same key must be woken when it's set."""
        cache = BlockingCache()
        N = 5
        results = [None] * N
        ready = threading.Barrier(N + 1)  # N readers + main thread

        def reader(idx):
            ready.wait()
            results[idx] = cache.wait_get("shared_key")

        threads = [threading.Thread(target=reader, args=(i,)) for i in range(N)]
        for t in threads:
            t.start()

        ready.wait()  # wait until all readers are at the barrier
        time.sleep(0.05)  # let all readers reach wait_get and block

        cache.set("shared_key", 99)

        for t in threads:
            t.join(timeout=5)

        for i, r in enumerate(results):
            self.assertEqual(r, 99, f"Reader {i} got {r!r} instead of 99")

    def test_three_readers_before_writer(self):
        """Core test: 3 readers block, writer sets key, all unblock with same value."""
        cache = BlockingCache()
        results = []
        lock = threading.Lock()
        start_barrier = threading.Barrier(4)  # 3 readers + main

        def reader():
            start_barrier.wait()
            val = cache.wait_get("answer")
            with lock:
                results.append(val)

        threads = [threading.Thread(target=reader) for _ in range(3)]
        for t in threads:
            t.start()

        start_barrier.wait()  # all readers ready
        time.sleep(0.1)       # let all readers enter wait_get

        cache.set("answer", 42)
        for t in threads:
            t.join(timeout=5)

        self.assertEqual(len(results), 3)
        self.assertTrue(all(r == 42 for r in results), f"Not all got 42: {results}")


class TestBlockingCacheTimeout(unittest.TestCase):
    def test_timeout_raises(self):
        """wait_get with timeout should raise TimeoutError when key not set."""
        cache = BlockingCache()
        with self.assertRaises(TimeoutError):
            cache.wait_get("missing", timeout=0.1)

    def test_timeout_does_not_raise_if_set_in_time(self):
        """wait_get with generous timeout should succeed if writer arrives."""
        cache = BlockingCache()
        result = []

        def reader():
            result.append(cache.wait_get("k", timeout=5.0))

        def writer():
            time.sleep(0.1)
            cache.set("k", "arrived")

        t_reader = threading.Thread(target=reader)
        t_writer = threading.Thread(target=writer)
        t_reader.start()
        t_writer.start()
        t_reader.join(timeout=6)
        t_writer.join(timeout=1)

        self.assertEqual(result, ["arrived"])

    def test_timeout_expires_roughly_on_time(self):
        """TimeoutError should be raised close to the timeout value."""
        cache = BlockingCache()
        start = time.monotonic()
        try:
            cache.wait_get("never", timeout=0.2)
            self.fail("Expected TimeoutError")
        except TimeoutError:
            elapsed = time.monotonic() - start
            self.assertGreaterEqual(elapsed, 0.15)
            self.assertLess(elapsed, 1.0)


if __name__ == "__main__":
    unittest.main()
