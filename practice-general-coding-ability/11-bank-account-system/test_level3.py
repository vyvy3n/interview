"""
Level 3 tests — Scheduled Transfers
Run: python3 test_level3.py
"""

import unittest
from solution import Bank


class TestLevel3ScheduleTransfer(unittest.TestCase):

    def test_schedule_returns_sched_id(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 1000)
        sid = b.schedule_transfer("alice", "bob", 100, execute_at=10)
        self.assertEqual(sid, "sched_1")

    def test_schedule_counter_increments(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 1000)
        s1 = b.schedule_transfer("alice", "bob", 100, execute_at=10)
        s2 = b.schedule_transfer("alice", "bob", 100, execute_at=20)
        s3 = b.schedule_transfer("alice", "bob", 100, execute_at=30)
        self.assertEqual(s1, "sched_1")
        self.assertEqual(s2, "sched_2")
        self.assertEqual(s3, "sched_3")

    def test_schedule_from_missing_returns_empty(self):
        b = Bank()
        b.open_account("bob")
        result = b.schedule_transfer("ghost", "bob", 100, execute_at=10)
        self.assertEqual(result, "")

    def test_schedule_to_missing_returns_empty(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 500)
        result = b.schedule_transfer("alice", "ghost", 100, execute_at=10)
        self.assertEqual(result, "")

    def test_schedule_same_account_returns_empty(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 500)
        result = b.schedule_transfer("alice", "alice", 100, execute_at=10)
        self.assertEqual(result, "")

    def test_schedule_does_not_check_balance(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        # alice has 0 balance but scheduling should still succeed
        sid = b.schedule_transfer("alice", "bob", 9999, execute_at=10)
        self.assertNotEqual(sid, "")
        self.assertTrue(sid.startswith("sched_"))

    def test_schedule_counter_not_incremented_on_failure(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 1000)
        b.schedule_transfer("ghost", "bob", 100, 10)  # fail, counter unchanged
        sid = b.schedule_transfer("alice", "bob", 100, 10)  # first valid
        self.assertEqual(sid, "sched_1")


class TestLevel3CancelScheduled(unittest.TestCase):

    def test_cancel_returns_true(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 1000)
        sid = b.schedule_transfer("alice", "bob", 100, execute_at=10)
        self.assertTrue(b.cancel_scheduled(sid))

    def test_cancel_missing_returns_false(self):
        b = Bank()
        self.assertFalse(b.cancel_scheduled("sched_99"))

    def test_cancel_twice_returns_false(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        sid = b.schedule_transfer("alice", "bob", 100, execute_at=10)
        b.cancel_scheduled(sid)
        self.assertFalse(b.cancel_scheduled(sid))

    def test_cancel_after_execution_returns_false(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        sid = b.schedule_transfer("alice", "bob", 100, execute_at=5)
        b.tick(10)
        self.assertFalse(b.cancel_scheduled(sid))


class TestLevel3Tick(unittest.TestCase):

    def test_tick_executes_due_transfer(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.schedule_transfer("alice", "bob", 100, execute_at=10)
        count = b.tick(10)
        self.assertEqual(count, 1)
        self.assertEqual(b.get_balance("alice"), 400)
        self.assertEqual(b.get_balance("bob"), 100)

    def test_tick_executes_multiple_due(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.schedule_transfer("alice", "bob", 100, execute_at=10)
        b.schedule_transfer("alice", "bob", 50, execute_at=10)
        count = b.tick(10)
        self.assertEqual(count, 2)
        self.assertEqual(b.get_balance("alice"), 350)

    def test_tick_skips_not_yet_due(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.schedule_transfer("alice", "bob", 100, execute_at=20)
        count = b.tick(10)
        self.assertEqual(count, 0)
        self.assertEqual(b.get_balance("alice"), 500)

    def test_tick_skips_cancelled(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        sid = b.schedule_transfer("alice", "bob", 100, execute_at=10)
        b.cancel_scheduled(sid)
        count = b.tick(10)
        self.assertEqual(count, 0)
        self.assertEqual(b.get_balance("alice"), 500)

    def test_tick_skips_insufficient_funds(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 50)
        b.schedule_transfer("alice", "bob", 100, execute_at=10)
        count = b.tick(10)
        self.assertEqual(count, 0)
        self.assertEqual(b.get_balance("alice"), 50)

    def test_tick_executes_in_creation_order(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 150)
        # sched_1 and sched_2 both due at 10; only sched_1 can execute given funds
        b.schedule_transfer("alice", "bob", 100, execute_at=10)  # sched_1 runs first: 150->50
        b.schedule_transfer("alice", "bob", 100, execute_at=10)  # sched_2: 50 < 100, skipped
        count = b.tick(10)
        self.assertEqual(count, 1)
        self.assertEqual(b.get_balance("alice"), 50)

    def test_tick_does_not_re_execute(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.schedule_transfer("alice", "bob", 100, execute_at=5)
        b.tick(10)
        b.tick(20)  # already executed; must not run again
        self.assertEqual(b.get_balance("alice"), 400)

    def test_tick_records_history(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.schedule_transfer("alice", "bob", 100, execute_at=10)
        b.tick(10)
        alice_history = b.get_transaction_history("alice", 1)
        bob_history = b.get_transaction_history("bob", 1)
        self.assertEqual(alice_history, ["transfer_out:100:to_bob"])
        self.assertEqual(bob_history, ["transfer_in:100:from_alice"])

    def test_tick_returns_zero_when_nothing_executes(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        count = b.tick(100)
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
