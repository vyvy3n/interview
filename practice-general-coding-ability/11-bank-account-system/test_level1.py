"""
Level 1 tests — Account Lifecycle
Run: python3 test_level1.py
"""

import unittest
from solution import Bank


class TestLevel1OpenAccount(unittest.TestCase):

    def test_open_account_returns_true_for_new(self):
        b = Bank()
        self.assertTrue(b.open_account("alice"))

    def test_open_multiple_accounts(self):
        b = Bank()
        self.assertTrue(b.open_account("alice"))
        self.assertTrue(b.open_account("bob"))
        self.assertTrue(b.open_account("carol"))

    def test_open_duplicate_returns_false(self):
        b = Bank()
        b.open_account("alice")
        self.assertFalse(b.open_account("alice"))

    def test_open_duplicate_does_not_reset_balance(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 500)
        b.open_account("alice")  # should be no-op
        self.assertEqual(b.get_balance("alice"), 500)

    def test_open_account_initial_balance_is_zero(self):
        b = Bank()
        b.open_account("alice")
        self.assertEqual(b.get_balance("alice"), 0)

    def test_open_account_returns_bool(self):
        b = Bank()
        result = b.open_account("alice")
        self.assertIsInstance(result, bool)


class TestLevel1GetBalance(unittest.TestCase):

    def test_get_balance_missing_returns_neg_one(self):
        b = Bank()
        self.assertEqual(b.get_balance("ghost"), -1)

    def test_get_balance_returns_int_not_none(self):
        b = Bank()
        result = b.get_balance("nobody")
        self.assertIsInstance(result, int)
        self.assertEqual(result, -1)

    def test_get_balance_new_account_is_zero(self):
        b = Bank()
        b.open_account("alice")
        self.assertEqual(b.get_balance("alice"), 0)

    def test_get_balance_after_deposit(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 300)
        self.assertEqual(b.get_balance("alice"), 300)

    def test_get_balance_zero_not_same_as_missing(self):
        b = Bank()
        b.open_account("alice")
        # alice exists with balance 0 — must return 0, not -1
        self.assertEqual(b.get_balance("alice"), 0)
        self.assertEqual(b.get_balance("bob"), -1)


class TestLevel1Deposit(unittest.TestCase):

    def test_deposit_returns_new_balance(self):
        b = Bank()
        b.open_account("alice")
        self.assertEqual(b.deposit("alice", 100), 100)

    def test_deposit_accumulates(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        result = b.deposit("alice", 50)
        self.assertEqual(result, 150)

    def test_deposit_missing_account_returns_neg_one(self):
        b = Bank()
        self.assertEqual(b.deposit("ghost", 100), -1)

    def test_deposit_missing_no_side_effect(self):
        b = Bank()
        b.deposit("ghost", 100)
        # account should not be created
        self.assertEqual(b.get_balance("ghost"), -1)

    def test_deposit_does_not_affect_other_accounts(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 200)
        self.assertEqual(b.get_balance("bob"), 0)


class TestLevel1Withdraw(unittest.TestCase):

    def test_withdraw_returns_new_balance(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 500)
        self.assertEqual(b.withdraw("alice", 200), 300)

    def test_withdraw_to_zero(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        self.assertEqual(b.withdraw("alice", 100), 0)

    def test_withdraw_insufficient_funds_returns_neg_one(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        self.assertEqual(b.withdraw("alice", 200), -1)

    def test_withdraw_insufficient_balance_unchanged(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        b.withdraw("alice", 999)
        self.assertEqual(b.get_balance("alice"), 100)

    def test_withdraw_missing_account_returns_neg_one(self):
        b = Bank()
        self.assertEqual(b.withdraw("ghost", 50), -1)

    def test_withdraw_exact_balance_succeeds(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 75)
        self.assertEqual(b.withdraw("alice", 75), 0)

    def test_withdraw_sequence(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 1000)
        b.withdraw("alice", 300)
        b.withdraw("alice", 200)
        self.assertEqual(b.get_balance("alice"), 500)


if __name__ == "__main__":
    unittest.main()
