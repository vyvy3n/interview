"""
Level 2 tests — Transfers + History
Run: python3 test_level2.py
"""

import unittest
from solution import Bank


class TestLevel2Transfer(unittest.TestCase):

    def test_transfer_basic_success(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        result = b.transfer("alice", "bob", 200)
        self.assertEqual(result, 300)

    def test_transfer_updates_both_balances(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.transfer("alice", "bob", 200)
        self.assertEqual(b.get_balance("alice"), 300)
        self.assertEqual(b.get_balance("bob"), 200)

    def test_transfer_from_missing_returns_neg_one(self):
        b = Bank()
        b.open_account("bob")
        self.assertEqual(b.transfer("ghost", "bob", 100), -1)

    def test_transfer_to_missing_returns_neg_one(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        self.assertEqual(b.transfer("alice", "ghost", 50), -1)

    def test_transfer_same_account_returns_neg_one(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 500)
        self.assertEqual(b.transfer("alice", "alice", 100), -1)

    def test_transfer_insufficient_funds_returns_neg_one(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 100)
        self.assertEqual(b.transfer("alice", "bob", 200), -1)

    def test_transfer_failure_no_side_effect(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 100)
        b.deposit("bob", 50)
        b.transfer("alice", "bob", 999)  # fail
        self.assertEqual(b.get_balance("alice"), 100)
        self.assertEqual(b.get_balance("bob"), 50)

    def test_transfer_exact_balance_succeeds(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 300)
        result = b.transfer("alice", "bob", 300)
        self.assertEqual(result, 0)
        self.assertEqual(b.get_balance("bob"), 300)


class TestLevel2TransactionHistory(unittest.TestCase):

    def test_history_deposit_recorded(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        history = b.get_transaction_history("alice", 5)
        self.assertEqual(history, ["deposit:100"])

    def test_history_withdraw_recorded(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 500)
        b.withdraw("alice", 200)
        history = b.get_transaction_history("alice", 1)
        self.assertEqual(history, ["withdraw:200"])

    def test_history_newest_first(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        b.deposit("alice", 200)
        b.withdraw("alice", 50)
        history = b.get_transaction_history("alice", 3)
        self.assertEqual(history, ["withdraw:50", "deposit:200", "deposit:100"])

    def test_history_transfer_out_recorded(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.transfer("alice", "bob", 150)
        history = b.get_transaction_history("alice", 1)
        self.assertEqual(history, ["transfer_out:150:to_bob"])

    def test_history_transfer_in_recorded(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 500)
        b.transfer("alice", "bob", 150)
        history = b.get_transaction_history("bob", 1)
        self.assertEqual(history, ["transfer_in:150:from_alice"])

    def test_history_n_limits_results(self):
        b = Bank()
        b.open_account("alice")
        for i in range(5):
            b.deposit("alice", 10)
        history = b.get_transaction_history("alice", 3)
        self.assertEqual(len(history), 3)

    def test_history_n_larger_than_available(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 10)
        b.deposit("alice", 20)
        history = b.get_transaction_history("alice", 100)
        self.assertEqual(len(history), 2)

    def test_history_missing_account_returns_empty_list(self):
        b = Bank()
        result = b.get_transaction_history("ghost", 5)
        self.assertEqual(result, [])

    def test_history_no_transactions_returns_empty_list(self):
        b = Bank()
        b.open_account("alice")
        result = b.get_transaction_history("alice", 5)
        self.assertEqual(result, [])

    def test_history_failed_transfer_not_recorded(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 100)
        b.transfer("alice", "bob", 9999)  # fail
        # No history entry for the failed transfer
        self.assertEqual(b.get_transaction_history("alice", 1), ["deposit:100"])
        self.assertEqual(b.get_transaction_history("bob", 1), [])

    def test_history_is_list_type(self):
        b = Bank()
        result = b.get_transaction_history("ghost", 5)
        self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()
