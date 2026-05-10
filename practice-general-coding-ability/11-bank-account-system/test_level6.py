"""
Level 6 tests — Atomic Compound Operations
Run: python3 test_level6.py

Tests verify:
  - compare_and_deposit: CAS semantics — only one winner when many threads race
  - batch_transfer: all-or-nothing atomicity
  - wait_for_balance: blocking until target reached, or timeout
"""

import threading
import time
import unittest
from solution import Bank


class TestLevel6CompareAndDeposit(unittest.TestCase):

    def test_cas_success_when_balance_matches(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        result = b.compare_and_deposit("alice", 100, 50)
        self.assertTrue(result)
        self.assertEqual(b.get_balance("alice"), 150)

    def test_cas_fails_when_balance_mismatch(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        result = b.compare_and_deposit("alice", 999, 50)
        self.assertFalse(result)
        self.assertEqual(b.get_balance("alice"), 100)

    def test_cas_no_side_effect_on_failure(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        b.compare_and_deposit("alice", 999, 50)
        self.assertEqual(b.get_balance("alice"), 100)

    def test_cas_missing_account_returns_false(self):
        b = Bank()
        result = b.compare_and_deposit("ghost", 0, 100)
        self.assertFalse(result)

    def test_cas_records_history_on_success(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        b.compare_and_deposit("alice", 100, 50)
        history = b.get_transaction_history("alice", 1)
        self.assertEqual(history, ["deposit:50"])

    def test_cas_no_history_on_failure(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        b.compare_and_deposit("alice", 999, 50)  # fail
        history = b.get_transaction_history("alice", 10)
        # Only the original deposit should be there
        self.assertEqual(history, ["deposit:100"])

    def test_cas_zero_balance(self):
        b = Bank()
        b.open_account("alice")
        # balance is 0; expect 0
        result = b.compare_and_deposit("alice", 0, 100)
        self.assertTrue(result)
        self.assertEqual(b.get_balance("alice"), 100)

    def test_cas_concurrent_only_one_wins(self):
        """100 threads all see balance=100 and try to CAS with expected=100; only ONE must succeed."""
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)

        results = []
        lock = threading.Lock()

        def try_cas():
            ok = b.compare_and_deposit("alice", 100, 1)
            with lock:
                results.append(ok)

        threads = [threading.Thread(target=try_cas) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(results.count(True), 1)
        self.assertEqual(results.count(False), 99)
        self.assertEqual(b.get_balance("alice"), 101)  # only one deposit of 1 succeeded

    def test_cas_sequential_cas_chain(self):
        """CAS can be used in a chain: each CAS expects the result of the previous one."""
        b = Bank()
        b.open_account("alice")
        # Start at 0; each step adds 10 and expects the previous result
        balance = 0
        for _ in range(10):
            ok = b.compare_and_deposit("alice", balance, 10)
            self.assertTrue(ok)
            balance += 10
        self.assertEqual(b.get_balance("alice"), 100)


class TestLevel6BatchTransfer(unittest.TestCase):

    def test_batch_basic_success(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.open_account("carol")
        b.deposit("alice", 500)
        b.deposit("bob", 300)
        ok = b.batch_transfer([("alice", "carol", 200), ("bob", "carol", 100)])
        self.assertTrue(ok)
        self.assertEqual(b.get_balance("alice"), 300)
        self.assertEqual(b.get_balance("bob"), 200)
        self.assertEqual(b.get_balance("carol"), 300)

    def test_batch_all_or_nothing_on_insufficient(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.open_account("carol")
        b.deposit("alice", 500)
        b.deposit("bob", 50)
        # bob can't cover 200; whole batch fails
        ok = b.batch_transfer([("alice", "carol", 100), ("bob", "carol", 200)])
        self.assertFalse(ok)
        self.assertEqual(b.get_balance("alice"), 500)  # unchanged
        self.assertEqual(b.get_balance("bob"), 50)      # unchanged
        self.assertEqual(b.get_balance("carol"), 0)     # unchanged

    def test_batch_missing_from_id_fails(self):
        b = Bank()
        b.open_account("bob")
        ok = b.batch_transfer([("ghost", "bob", 100)])
        self.assertFalse(ok)

    def test_batch_missing_to_id_fails(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 500)
        ok = b.batch_transfer([("alice", "ghost", 100)])
        self.assertFalse(ok)

    def test_batch_same_account_fails(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 500)
        ok = b.batch_transfer([("alice", "alice", 100)])
        self.assertFalse(ok)

    def test_batch_multiple_withdrawals_from_same_account(self):
        """Two transfers from alice; combined withdrawal must be within balance."""
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.open_account("carol")
        b.deposit("alice", 300)
        # 200 + 200 = 400 > 300 — should fail
        ok = b.batch_transfer([("alice", "bob", 200), ("alice", "carol", 200)])
        self.assertFalse(ok)
        self.assertEqual(b.get_balance("alice"), 300)

    def test_batch_multiple_withdrawals_within_balance(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.open_account("carol")
        b.deposit("alice", 500)
        ok = b.batch_transfer([("alice", "bob", 200), ("alice", "carol", 100)])
        self.assertTrue(ok)
        self.assertEqual(b.get_balance("alice"), 200)
        self.assertEqual(b.get_balance("bob"), 200)
        self.assertEqual(b.get_balance("carol"), 100)

    def test_batch_records_history(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.batch_transfer([("alice", "bob", 100)])
        alice_h = b.get_transaction_history("alice", 1)
        bob_h = b.get_transaction_history("bob", 1)
        self.assertEqual(alice_h, ["transfer_out:100:to_bob"])
        self.assertEqual(bob_h, ["transfer_in:100:from_alice"])

    def test_batch_empty_list_succeeds(self):
        b = Bank()
        ok = b.batch_transfer([])
        self.assertTrue(ok)

    def test_batch_concurrent_no_corruption(self):
        """Multiple threads doing batch transfers simultaneously; total money must be conserved."""
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 1000)
        b.deposit("bob", 1000)

        def move_forward():
            for _ in range(20):
                b.batch_transfer([("alice", "bob", 5)])

        def move_backward():
            for _ in range(20):
                b.batch_transfer([("bob", "alice", 5)])

        threads = [threading.Thread(target=move_forward) for _ in range(5)]
        threads += [threading.Thread(target=move_backward) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total = b.get_balance("alice") + b.get_balance("bob")
        self.assertEqual(total, 2000)


class TestLevel6WaitForBalance(unittest.TestCase):

    def test_wait_immediate_when_already_sufficient(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 1000)
        result = b.wait_for_balance("alice", 500, timeout=0.1)
        self.assertTrue(result)

    def test_wait_succeeds_when_deposit_arrives(self):
        b = Bank()
        b.open_account("alice")

        def delayed_deposit():
            time.sleep(0.1)
            b.deposit("alice", 500)

        writer = threading.Thread(target=delayed_deposit)
        writer.start()
        result = b.wait_for_balance("alice", 500, timeout=2.0)
        writer.join()
        self.assertTrue(result)

    def test_wait_timeout_when_never_reached(self):
        b = Bank()
        b.open_account("alice")
        # Nobody deposits; timeout after 0.1s
        result = b.wait_for_balance("alice", 9999, timeout=0.1)
        self.assertFalse(result)

    def test_wait_missing_account_returns_false(self):
        b = Bank()
        result = b.wait_for_balance("ghost", 100, timeout=0.1)
        self.assertFalse(result)

    def test_wait_zero_target_immediate(self):
        b = Bank()
        b.open_account("alice")
        # Balance is 0; target is 0: balance >= 0 is immediately true
        result = b.wait_for_balance("alice", 0, timeout=0.5)
        self.assertTrue(result)

    def test_wait_triggered_by_transfer_in(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("bob", 500)

        def delayed_transfer():
            time.sleep(0.1)
            b.transfer("bob", "alice", 300)

        writer = threading.Thread(target=delayed_transfer)
        writer.start()
        result = b.wait_for_balance("alice", 300, timeout=2.0)
        writer.join()
        self.assertTrue(result)

    def test_wait_multiple_waiters(self):
        """Multiple threads wait on the same account; all wake up when balance is deposited."""
        b = Bank()
        b.open_account("shared")
        results = []
        result_lock = threading.Lock()

        def waiter():
            ok = b.wait_for_balance("shared", 100, timeout=2.0)
            with result_lock:
                results.append(ok)

        waiters = [threading.Thread(target=waiter) for _ in range(5)]
        for w in waiters:
            w.start()

        time.sleep(0.1)
        b.deposit("shared", 200)

        for w in waiters:
            w.join()

        self.assertEqual(results.count(True), 5)

    def test_wait_exact_timeout_boundary(self):
        """Very short timeout — should return False quickly without hanging."""
        b = Bank()
        b.open_account("alice")
        start = time.monotonic()
        result = b.wait_for_balance("alice", 1000, timeout=0.05)
        elapsed = time.monotonic() - start
        self.assertFalse(result)
        self.assertLess(elapsed, 1.0)  # should not hang for 1+ seconds

    def test_wait_woken_by_batch_transfer(self):
        """wait_for_balance woken by a batch_transfer that credits the account."""
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("bob", 500)

        def delayed_batch():
            time.sleep(0.1)
            b.batch_transfer([("bob", "alice", 400)])

        writer = threading.Thread(target=delayed_batch)
        writer.start()
        result = b.wait_for_balance("alice", 400, timeout=2.0)
        writer.join()
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
