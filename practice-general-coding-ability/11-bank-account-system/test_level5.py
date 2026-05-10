"""
Level 5 tests — Concurrent Operations (Threading)
Run: python3 test_level5.py

Tests verify:
  - Thread-safe deposits/withdrawals (no lost updates)
  - Thread-safe transfers (no double-spend)
  - Background scheduler fires tick automatically
  - advance_time works for manual clock advancement
  - start_scheduler is idempotent (only one bg thread allowed)
  - stop_scheduler joins the thread properly
"""

import threading
import time
import unittest
from solution import Bank


class TestLevel5AdvanceTime(unittest.TestCase):

    def test_advance_time_executes_due_transfers(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.schedule_transfer("alice", "bob", 100, execute_at=5)
        count = b.advance_time(5)
        self.assertEqual(count, 1)
        self.assertEqual(b.get_balance("alice"), 400)
        self.assertEqual(b.get_balance("bob"), 100)

    def test_advance_time_accumulates_clock(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 600)
        b.schedule_transfer("alice", "bob", 100, execute_at=3)
        b.schedule_transfer("alice", "bob", 100, execute_at=7)
        b.advance_time(3)  # clock = 3, first executes
        self.assertEqual(b.get_balance("bob"), 100)
        b.advance_time(4)  # clock = 7, second executes
        self.assertEqual(b.get_balance("bob"), 200)

    def test_advance_time_returns_executed_count(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 1000)
        b.schedule_transfer("alice", "bob", 100, execute_at=10)
        b.schedule_transfer("alice", "bob", 100, execute_at=10)
        count = b.advance_time(10)
        self.assertEqual(count, 2)

    def test_advance_time_zero_does_not_execute(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.schedule_transfer("alice", "bob", 100, execute_at=0)
        # clock starts at 0; advance_time(0) -> clock = 0 -> tick(0) should execute
        count = b.advance_time(0)
        # execute_at=0 <= clock=0, so it runs
        self.assertEqual(count, 1)


class TestLevel5Scheduler(unittest.TestCase):

    def test_scheduler_auto_executes_transfer(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.schedule_transfer("alice", "bob", 100, execute_at=5)
        b.start_scheduler(check_interval=0.01)
        time.sleep(0.3)  # scheduler ticks 5+ times within 0.3s
        b.stop_scheduler()
        self.assertEqual(b.get_balance("alice"), 400)
        self.assertEqual(b.get_balance("bob"), 100)

    def test_scheduler_is_idempotent(self):
        b = Bank()
        b.start_scheduler(check_interval=0.05)
        b.start_scheduler(check_interval=0.05)  # second call must not crash or add extra thread
        b.stop_scheduler()
        # If this completes without hanging, only one thread was running

    def test_stop_scheduler_joins(self):
        b = Bank()
        b.start_scheduler(check_interval=0.01)
        time.sleep(0.05)
        b.stop_scheduler()
        # After stop, no background activity; verify by checking state is stable
        b.open_account("x")
        b.deposit("x", 100)
        before = b.get_balance("x")
        time.sleep(0.1)
        after = b.get_balance("x")
        self.assertEqual(before, after)

    def test_scheduler_can_restart_after_stop(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.start_scheduler(check_interval=0.01)
        time.sleep(0.1)
        b.stop_scheduler()
        # Schedule a new transfer and restart
        b.schedule_transfer("alice", "bob", 200, execute_at=b._clock + 3)
        b.start_scheduler(check_interval=0.01)
        time.sleep(0.2)
        b.stop_scheduler()
        self.assertEqual(b.get_balance("bob"), 200)

    def test_stop_no_scheduler_is_noop(self):
        b = Bank()
        b.stop_scheduler()  # must not crash


class TestLevel5ThreadSafety(unittest.TestCase):

    def test_concurrent_deposits_no_lost_updates(self):
        """100 threads each deposit $10 into the same account; final balance must be $1000."""
        b = Bank()
        b.open_account("shared")

        def deposit_many():
            for _ in range(10):
                b.deposit("shared", 10)

        threads = [threading.Thread(target=deposit_many) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(b.get_balance("shared"), 1000)

    def test_concurrent_withdrawals_no_overdraft(self):
        """Multiple threads try to withdraw from same account; no negative balance."""
        b = Bank()
        b.open_account("pot")
        b.deposit("pot", 1000)

        def try_withdraw():
            for _ in range(5):
                b.withdraw("pot", 50)

        threads = [threading.Thread(target=try_withdraw) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Balance should be >= 0 (some withdrawals may have been refused)
        balance = b.get_balance("pot")
        self.assertGreaterEqual(balance, 0)

    def test_concurrent_transfers_no_lost_money(self):
        """Transfer money back and forth concurrently; total money must be conserved."""
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.deposit("bob", 500)

        def alice_to_bob():
            for _ in range(50):
                b.transfer("alice", "bob", 1)

        def bob_to_alice():
            for _ in range(50):
                b.transfer("bob", "alice", 1)

        t1 = threading.Thread(target=alice_to_bob)
        t2 = threading.Thread(target=bob_to_alice)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        total = b.get_balance("alice") + b.get_balance("bob")
        self.assertEqual(total, 1000)

    def test_concurrent_open_same_account_only_one_succeeds(self):
        """Race to open the same account; exactly one must succeed."""
        b = Bank()
        results = []
        lock = threading.Lock()

        def try_open():
            ok = b.open_account("contested")
            with lock:
                results.append(ok)

        threads = [threading.Thread(target=try_open) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(results.count(True), 1)
        self.assertEqual(results.count(False), 19)

    def test_concurrent_get_balance_does_not_crash(self):
        """get_balance called from many threads simultaneously must not raise."""
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        errors = []

        def read_balance():
            for _ in range(50):
                try:
                    b.get_balance("alice")
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=read_balance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])

    def test_concurrent_advance_time_no_double_execution(self):
        """Multiple threads calling advance_time concurrently; each transfer executes at most once."""
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.schedule_transfer("alice", "bob", 100, execute_at=0)

        counts = []
        lock = threading.Lock()

        def do_advance():
            c = b.advance_time(1)
            with lock:
                counts.append(c)

        threads = [threading.Thread(target=do_advance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # The transfer should execute exactly once total
        self.assertEqual(sum(counts), 1)
        self.assertEqual(b.get_balance("bob"), 100)


if __name__ == "__main__":
    unittest.main()
