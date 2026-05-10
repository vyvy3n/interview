"""
Level 6 tests — Atomic Compound Operations
Run: python3 test_level6.py
"""

import unittest
import threading
import time
from solution import ConversationService


class TestLevel6CompareAndSwapMessage(unittest.TestCase):

    def test_swap_basic(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Original", 10)
        result = s.compare_and_swap_message("c1", 0, "Original", "Updated", 20)
        self.assertTrue(result)
        self.assertEqual(s.get_messages("c1"), ["user:Updated"])

    def test_swap_wrong_expected_returns_false(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Original", 10)
        result = s.compare_and_swap_message("c1", 0, "Wrong", "Updated", 20)
        self.assertFalse(result)
        self.assertEqual(s.get_messages("c1"), ["user:Original"])

    def test_swap_missing_conv_returns_false(self):
        s = ConversationService()
        self.assertFalse(s.compare_and_swap_message("ghost", 0, "content", "new", 10))

    def test_swap_invalid_index_returns_false(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 5)
        self.assertFalse(s.compare_and_swap_message("c1", 5, "Hello", "World", 5))
        self.assertFalse(s.compare_and_swap_message("c1", -1, "Hello", "World", 5))

    def test_swap_adjusts_token_total(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 10)  # total = 10
        s.compare_and_swap_message("c1", 0, "Hello", "World", 5)  # 10 - 10 + 5 = 5
        self.assertEqual(s.get_user_total_tokens("alice"), 5)

    def test_swap_no_side_effect_on_mismatch(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 10)
        s.compare_and_swap_message("c1", 0, "Wrong", "New", 99)
        # Token count unchanged
        self.assertEqual(s.get_user_total_tokens("alice"), 10)

    def test_concurrent_cas_exactly_one_wins(self):
        """Only one of N concurrent CAS calls should succeed."""
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Original", 10)

        results = []
        lock = threading.Lock()

        def try_swap():
            ok = s.compare_and_swap_message("c1", 0, "Original", "Swapped", 20)
            with lock:
                results.append(ok)

        threads = [threading.Thread(target=try_swap) for _ in range(100)]
        for t in threads: t.start()
        for t in threads: t.join()

        self.assertEqual(results.count(True), 1)
        self.assertEqual(results.count(False), 99)
        self.assertEqual(s.get_messages("c1"), ["user:Swapped"])

    def test_swap_middle_message(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "A", 5)
        s.add_message("c1", "assistant", "B", 10)
        s.add_message("c1", "user", "C", 8)
        result = s.compare_and_swap_message("c1", 1, "B", "B-updated", 15)
        self.assertTrue(result)
        msgs = s.get_messages("c1")
        self.assertEqual(msgs[1], "assistant:B-updated")
        # Token total: 5 + 10 + 8 = 23; swap B(10)->B-updated(15): 23 - 10 + 15 = 28
        self.assertEqual(s.get_user_total_tokens("alice"), 28)


class TestLevel6BatchAddMessages(unittest.TestCase):

    def test_batch_add_no_limit(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        count = s.batch_add_messages("c1", [("user", "A", 5), ("assistant", "B", 10)])
        self.assertEqual(count, 2)
        self.assertEqual(s.get_message_count("c1"), 2)

    def test_batch_add_missing_conv(self):
        s = ConversationService()
        self.assertEqual(s.batch_add_messages("ghost", [("user", "A", 5)]), -1)

    def test_batch_add_with_limit_fits(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.set_context_limit("c1", 30)
        count = s.batch_add_messages("c1", [("user", "A", 10), ("assistant", "B", 15)])
        self.assertEqual(count, 2)
        # 10+15=25 <= 30
        self.assertEqual(s.get_message_count("c1"), 2)

    def test_batch_add_reject_batch_exceeds_limit(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.set_context_limit("c1", 20)
        s.add_message("c1", "user", "Existing", 10)
        # Batch sum = 25 > limit 20 -> reject all
        count = s.batch_add_messages("c1", [("user", "X", 15), ("user", "Y", 10)])
        self.assertEqual(count, -1)
        # State unchanged — still 1 message
        self.assertEqual(s.get_message_count("c1"), 1)

    def test_batch_add_drops_existing_to_fit(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Old1", 10)
        s.add_message("c1", "assistant", "Old2", 10)
        s.set_context_limit("c1", 25)
        # Current total = 20; batch sum = 15; 20+15=35 > 25
        # Drop oldest to make room: drop Old1 (10), 10+15=25 <= 25 — fits
        count = s.batch_add_messages("c1", [("user", "New1", 8), ("assistant", "New2", 7)])
        self.assertEqual(count, 2)
        msgs = s.get_messages("c1")
        self.assertIn("assistant:Old2", msgs)
        self.assertIn("user:New1", msgs)
        self.assertIn("assistant:New2", msgs)
        self.assertNotIn("user:Old1", msgs)

    def test_batch_add_atomic_all_or_nothing(self):
        """If batch is rejected, no partial messages are added."""
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.set_context_limit("c1", 10)
        result = s.batch_add_messages("c1", [("user", "A", 5), ("assistant", "B", 6)])
        # Batch sum 11 > 10 — reject all
        self.assertEqual(result, -1)
        self.assertEqual(s.get_message_count("c1"), 0)

    def test_batch_add_empty_list(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        count = s.batch_add_messages("c1", [])
        self.assertEqual(count, 0)

    def test_batch_add_updates_token_total(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.batch_add_messages("c1", [("user", "A", 5), ("assistant", "B", 10)])
        self.assertEqual(s.get_user_total_tokens("alice"), 15)

    def test_batch_add_messages_in_order(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.batch_add_messages("c1", [("user", "First", 5), ("assistant", "Second", 10)])
        msgs = s.get_messages("c1")
        self.assertEqual(msgs, ["user:First", "assistant:Second"])


class TestLevel6WaitForMessageCount(unittest.TestCase):

    def test_wait_already_satisfied(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Hello", 5)
        result = s.wait_for_message_count("c1", 1, timeout=0.1)
        self.assertTrue(result)

    def test_wait_missing_conv(self):
        s = ConversationService()
        result = s.wait_for_message_count("ghost", 1, timeout=0.1)
        self.assertFalse(result)

    def test_wait_timeout_expires(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        result = s.wait_for_message_count("c1", 5, timeout=0.1)
        self.assertFalse(result)

    def test_wait_notified_by_add_message(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")

        def delayed_add():
            time.sleep(0.1)
            s.add_message("c1", "user", "Hello", 5)

        writer = threading.Thread(target=delayed_add)
        writer.start()
        result = s.wait_for_message_count("c1", 1, timeout=2.0)
        writer.join()
        self.assertTrue(result)

    def test_wait_notified_by_batch_add(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")

        def delayed_batch():
            time.sleep(0.1)
            s.batch_add_messages("c1", [("user", "A", 5), ("assistant", "B", 10)])

        writer = threading.Thread(target=delayed_batch)
        writer.start()
        result = s.wait_for_message_count("c1", 2, timeout=2.0)
        writer.join()
        self.assertTrue(result)

    def test_wait_multiple_threads(self):
        """Multiple threads waiting for the same conversation count."""
        s = ConversationService()
        s.create_conversation("c1", "alice")

        results = []
        lock = threading.Lock()

        def wait_for_target():
            ok = s.wait_for_message_count("c1", 3, timeout=3.0)
            with lock:
                results.append(ok)

        waiters = [threading.Thread(target=wait_for_target) for _ in range(5)]
        for t in waiters: t.start()

        time.sleep(0.05)
        s.add_message("c1", "user", "A", 5)
        s.add_message("c1", "user", "B", 5)
        s.add_message("c1", "user", "C", 5)

        for t in waiters: t.join()
        self.assertEqual(results.count(True), 5)

    def test_wait_notified_by_queue_worker(self):
        """Workers processing queued messages notify wait_for_message_count."""
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.start_session_workers(2)

        def add_via_queue():
            time.sleep(0.05)
            q = s.queue_message("c1", "user", "Queued msg", 5)
            s.wait_for_processed(q, timeout=2.0)

        writer = threading.Thread(target=add_via_queue)
        writer.start()

        result = s.wait_for_message_count("c1", 1, timeout=3.0)
        writer.join()
        s.stop_session_workers()
        self.assertTrue(result)

    def test_wait_zero_target_immediately_true(self):
        s = ConversationService()
        s.create_conversation("c1", "alice")
        result = s.wait_for_message_count("c1", 0, timeout=0.1)
        self.assertTrue(result)

    def test_concurrent_cas_and_wait(self):
        """wait_for_message_count should work while CAS is occurring."""
        s = ConversationService()
        s.create_conversation("c1", "alice")
        for i in range(3):
            s.add_message("c1", "user", f"msg{i}", 5)

        def try_swap_repeatedly():
            for _ in range(50):
                s.compare_and_swap_message("c1", 0, "msg0", "msg0", 5)

        swappers = [threading.Thread(target=try_swap_repeatedly) for _ in range(3)]
        for t in swappers: t.start()

        result = s.wait_for_message_count("c1", 3, timeout=1.0)
        for t in swappers: t.join()
        self.assertTrue(result)  # already has 3 messages

    def test_cas_then_wait_sees_updated_content(self):
        """After CAS succeeds, get_messages returns the updated content."""
        s = ConversationService()
        s.create_conversation("c1", "alice")
        s.add_message("c1", "user", "Original", 10)
        s.compare_and_swap_message("c1", 0, "Original", "Swapped", 5)

        # wait_for_message_count already satisfied (1 >= 1)
        result = s.wait_for_message_count("c1", 1, timeout=0.1)
        self.assertTrue(result)
        self.assertEqual(s.get_messages("c1"), ["user:Swapped"])


if __name__ == "__main__":
    unittest.main()
