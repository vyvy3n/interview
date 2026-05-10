"""Tests for Exercise 04 — Bounded Blocking Queue."""

import threading
import time
import unittest
from collections import Counter as Multiset

from solution import BoundedQueue


class TestBoundedQueueBasic(unittest.TestCase):
    def test_put_and_get_single(self):
        q = BoundedQueue(5)
        q.put(42)
        self.assertEqual(q.get(), 42)

    def test_fifo_order(self):
        q = BoundedQueue(5)
        for i in range(5):
            q.put(i)
        result = [q.get() for _ in range(5)]
        self.assertEqual(result, list(range(5)))

    def test_capacity_one(self):
        """Queue of capacity 1 should allow put after get."""
        q = BoundedQueue(1)
        q.put("a")
        self.assertEqual(q.get(), "a")
        q.put("b")
        self.assertEqual(q.get(), "b")

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            BoundedQueue(0)


class TestBoundedQueueBlocking(unittest.TestCase):
    def test_get_blocks_on_empty(self):
        """get() must block until a producer puts an item."""
        q = BoundedQueue(2)
        result = []

        def consumer():
            result.append(q.get())  # blocks until item available

        t = threading.Thread(target=consumer)
        t.start()
        time.sleep(0.05)  # give consumer time to block
        self.assertTrue(t.is_alive(), "consumer should still be blocking")
        q.put("hello")
        t.join(timeout=2)
        self.assertFalse(t.is_alive(), "consumer should have unblocked")
        self.assertEqual(result, ["hello"])

    def test_put_blocks_when_full(self):
        """put() must block when the queue is at capacity."""
        q = BoundedQueue(2)
        q.put(1)
        q.put(2)
        blocked = threading.Event()
        unblocked = threading.Event()

        def producer():
            blocked.set()
            q.put(3)
            unblocked.set()

        t = threading.Thread(target=producer)
        t.start()
        blocked.wait(timeout=2)
        time.sleep(0.05)
        self.assertFalse(unblocked.is_set(), "producer should still be blocked")
        q.get()  # make room
        unblocked.wait(timeout=2)
        self.assertTrue(unblocked.is_set(), "producer should have unblocked")
        t.join(timeout=2)


class TestBoundedQueueConcurrent(unittest.TestCase):
    def test_producer_consumer_correctness(self):
        """5 producers + 5 consumers, 1000 items.  All consumed exactly once."""
        N_ITEMS = 1000
        N_THREADS = 5
        CAPACITY = 10
        ITEMS_PER_PRODUCER = N_ITEMS // N_THREADS

        q = BoundedQueue(CAPACITY)
        produced = list(range(N_ITEMS))
        consumed = []
        lock = threading.Lock()

        def producer(start):
            for i in range(start, start + ITEMS_PER_PRODUCER):
                q.put(i)

        def consumer():
            for _ in range(ITEMS_PER_PRODUCER):
                item = q.get()
                with lock:
                    consumed.append(item)

        producers = [
            threading.Thread(target=producer, args=(i * ITEMS_PER_PRODUCER,))
            for i in range(N_THREADS)
        ]
        consumers = [threading.Thread(target=consumer) for _ in range(N_THREADS)]

        all_threads = producers + consumers
        for t in all_threads:
            t.start()
        for t in all_threads:
            t.join(timeout=30)

        self.assertEqual(len(consumed), N_ITEMS, "wrong number of items consumed")
        self.assertEqual(
            Multiset(consumed),
            Multiset(produced),
            "consumed items don't match produced items",
        )

    def test_capacity_never_exceeded(self):
        """Track queue size manually; it must never exceed capacity."""
        CAPACITY = 5
        q = BoundedQueue(CAPACITY)
        size = [0]
        max_observed = [0]
        size_lock = threading.Lock()

        def producer():
            for _ in range(200):
                q.put(1)
                with size_lock:
                    size[0] += 1
                    if size[0] > max_observed[0]:
                        max_observed[0] = size[0]

        def consumer():
            for _ in range(200):
                q.get()
                with size_lock:
                    size[0] -= 1

        threads = (
            [threading.Thread(target=producer) for _ in range(3)]
            + [threading.Thread(target=consumer) for _ in range(3)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        self.assertLessEqual(
            max_observed[0],
            CAPACITY,
            f"queue size exceeded capacity: {max_observed[0]} > {CAPACITY}",
        )


if __name__ == "__main__":
    unittest.main()
