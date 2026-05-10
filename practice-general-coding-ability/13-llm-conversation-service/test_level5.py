"""
Level 5 tests — Concurrent Sessions (Threading)
Run: python3 test_level5.py
"""

import unittest
import threading
import time
from solution import ConversationService


class TestLevel5ThreadSafety(unittest.TestCase):

    def test_concurrent_add_message_no_race(self):
        """500 concurrent adds to a shared conversation must all succeed."""
        s = ConversationService()
        s.create_conversation("shared", "alice")

        def add_many():
            for _ in range(100):
                s.add_message("shared", "user", "msg", 1)

        threads = [threading.Thread(target=add_many) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()

        self.assertEqual(s.get_message_count("shared"), 500)

    def test_concurrent_add_token_count_correct(self):
        """Cumulative token count must be exact after concurrent adds."""
        s = ConversationService()
        s.create_conversation("c1", "alice")

        def add_tokens():
            for _ in range(50):
                s.add_message("c1", "user", "msg", 2)

        threads = [threading.Thread(target=add_tokens) for _ in range(4)]
        for t in threads: t.start()
        for t in threads: t.join()

        # 4 threads * 50 adds * 2 tokens = 400
        self.assertEqual(s.get_user_total_tokens("alice"), 400)

    def test_concurrent_create_same_id(self):
        """Only one of N concurrent creates for the same ID should succeed."""
        s = ConversationService()
        results = []
        lock = threading.Lock()

        def try_create():
            ok = s.create_conversation("c1", "alice")
            with lock:
                results.append(ok)

        threads = [threading.Thread(target=try_create) for _ in range(20)]
        for t in threads: t.start()
        for t in threads: t.join()

        self.assertEqual(results.count(True), 1)
        self.assertEqual(results.count(False), 19)

    def test_concurrent_delete_and_read(self):
        """Concurrent deletes and reads should not crash."""
        s = ConversationService()
        s.create_conversation("c1", "alice")
        for _ in range(10):
            s.add_message("c1", "user", "msg", 1)

        def delete():
            s.delete_conversation("c1")

        def read():
            s.get_messages("c1")

        threads = [threading.Thread(target=delete if i == 0 else read) for i in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        # No exception means pass

    def test_concurrent_fork_and_modify(self):
        """Concurrent forks and modifications should not corrupt state."""
        s = ConversationService()
        s.create_conversation("src", "alice")
        s.add_message("src", "user", "Original", 10)

        results = []
        lock = threading.Lock()

        def fork_and_add(fork_id):
            ok = s.fork_conversation("src", fork_id)
            with lock:
                results.append(ok)
            if ok:
                s.add_message(fork_id, "user", "Fork msg", 5)

        threads = [threading.Thread(target=fork_and_add, args=(f"fork-{i}",)) for i in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()

        self.assertEqual(sum(results), 10)  # All forks succeed (unique IDs)


class TestLevel5WorkerPool(unittest.TestCase):

    def test_start_workers_and_process(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.start_session_workers(2)
        q1 = s.queue_message("c1", "user", "Hello", 10)
        self.assertEqual(q1, "q_1")
        processed = s.wait_for_processed(q1, timeout=2.0)
        self.assertTrue(processed)
        s.stop_session_workers()
        self.assertEqual(s.get_message_count("c1"), 1)

    def test_queue_message_missing_conv_returns_empty(self):
        s = ConversationService()
        s.start_session_workers(1)
        q = s.queue_message("ghost", "user", "Hello", 5)
        self.assertEqual(q, "")
        s.stop_session_workers()

    def test_queue_id_increments(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.create_conversation("c2", "alice")
        s.start_session_workers(2)
        q1 = s.queue_message("c1", "user", "Msg1", 5)
        q2 = s.queue_message("c2", "user", "Msg2", 5)
        self.assertEqual(q1, "q_1")
        self.assertEqual(q2, "q_2")
        s.stop_session_workers()

    def test_wait_for_processed_timeout(self):
        s = ConversationService()
        # No workers started — items won't be processed
        s.create_conversation("c1", "alice")
        q1 = s.queue_message("c1", "user", "Hello", 5)
        result = s.wait_for_processed(q1, timeout=0.1)
        self.assertFalse(result)

    def test_wait_for_processed_unknown_id(self):
        s = ConversationService()
        result = s.wait_for_processed("q_9999", timeout=0.1)
        self.assertFalse(result)

    def test_multiple_workers_process_all(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.start_session_workers(3)

        queue_ids = []
        for i in range(15):
            q = s.queue_message("c1", "user", f"msg{i}", 5)
            queue_ids.append(q)

        for qid in queue_ids:
            result = s.wait_for_processed(qid, timeout=3.0)
            self.assertTrue(result, f"Expected {qid} to be processed")

        s.stop_session_workers()
        self.assertEqual(s.get_message_count("c1"), 15)

    def test_workers_with_budget_limit(self):
        """Workers dispatch to add_message_with_budget when limit is set."""
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.set_context_limit("c1", 20)
        s.start_session_workers(2)

        # Queue a message that's within budget
        q1 = s.queue_message("c1", "user", "Hello", 10)
        s.wait_for_processed(q1, timeout=2.0)

        # Queue another that requires dropping
        q2 = s.queue_message("c1", "user", "World", 15)
        s.wait_for_processed(q2, timeout=2.0)

        s.stop_session_workers()
        # With limit 20: after second msg, total would be 25 > 20, so oldest dropped
        msgs = s.get_messages("c1")
        self.assertIn("user:World", msgs)

    def test_stop_and_restart_workers(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.start_session_workers(2)
        q1 = s.queue_message("c1", "user", "First", 5)
        s.wait_for_processed(q1, timeout=2.0)
        s.stop_session_workers()

        # Restart
        s.start_session_workers(2)
        q2 = s.queue_message("c1", "user", "Second", 5)
        self.assertTrue(s.wait_for_processed(q2, timeout=2.0))
        s.stop_session_workers()
        self.assertEqual(s.get_message_count("c1"), 2)

    def test_start_workers_idempotent(self):
        """Calling start_session_workers multiple times should not spawn extra workers."""
        s = ConversationService()
        s.start_session_workers(2)
        s.start_session_workers(2)  # second call is no-op
        s.start_session_workers(2)  # third call is no-op
        self.assertEqual(len(s._workers), 2)
        s.stop_session_workers()

    def test_concurrent_queue_and_wait(self):
        """Multiple threads can queue and wait concurrently."""
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.start_session_workers(4)

        results = []
        lock = threading.Lock()

        def queue_and_wait():
            q = s.queue_message("c1", "user", "msg", 1)
            ok = s.wait_for_processed(q, timeout=3.0)
            with lock:
                results.append(ok)

        threads = [threading.Thread(target=queue_and_wait) for _ in range(20)]
        for t in threads: t.start()
        for t in threads: t.join()
        s.stop_session_workers()

        self.assertEqual(results.count(True), 20)
        self.assertEqual(s.get_message_count("c1"), 20)

    def test_stop_workers_joins_all(self):
        """stop_session_workers must join all threads before returning."""
        s = ConversationService()
        s.start_session_workers(3)
        s.stop_session_workers()
        # After stop, no workers should be alive
        self.assertEqual(len(s._workers), 0)


if __name__ == "__main__":
    unittest.main()
