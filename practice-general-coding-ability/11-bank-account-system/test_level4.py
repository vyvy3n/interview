"""
Level 4 tests — Interest + Account Merging
Run: python3 test_level4.py
"""

import unittest
from solution import Bank


class TestLevel4ApplyInterest(unittest.TestCase):

    def test_interest_basic(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 1000)
        result = b.apply_interest(500)  # 5%
        self.assertEqual(result["alice"], 1050)

    def test_interest_updates_balance(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 1000)
        b.apply_interest(1000)  # 10%
        self.assertEqual(b.get_balance("alice"), 1100)

    def test_interest_multiple_accounts(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 1000)
        b.deposit("bob", 2000)
        result = b.apply_interest(1000)  # 10%
        self.assertEqual(result["alice"], 1100)
        self.assertEqual(result["bob"], 2200)

    def test_interest_result_sorted_alphabetically(self):
        b = Bank()
        b.open_account("charlie")
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 100)
        b.deposit("bob", 200)
        b.deposit("charlie", 300)
        result = b.apply_interest(1000)
        self.assertEqual(list(result.keys()), ["alice", "bob", "charlie"])

    def test_interest_zero_balance_stays_zero(self):
        b = Bank()
        b.open_account("alice")
        # balance is 0 — interest should be 0
        result = b.apply_interest(5000)
        self.assertEqual(result["alice"], 0)

    def test_interest_truncates_integer_division(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 1)
        # 1 * 300 // 10000 = 0 (not 0.03 rounded up)
        result = b.apply_interest(300)
        self.assertEqual(result["alice"], 1)

    def test_interest_truncates_large(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 999)
        # 999 * 100 // 10000 = 9 (not 10)
        result = b.apply_interest(100)
        self.assertEqual(result["alice"], 1008)  # 999 + 9 = 1008

    def test_interest_zero_rate(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 1000)
        result = b.apply_interest(0)
        self.assertEqual(result["alice"], 1000)

    def test_interest_returns_dict(self):
        b = Bank()
        b.open_account("alice")
        b.deposit("alice", 100)
        result = b.apply_interest(1000)
        self.assertIsInstance(result, dict)


class TestLevel4MergeAccounts(unittest.TestCase):

    def test_merge_basic(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 300)
        b.deposit("bob", 200)
        result = b.merge_accounts("alice", "bob")
        self.assertTrue(result)
        self.assertEqual(b.get_balance("alice"), 500)

    def test_merge_absorbed_is_removed(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.merge_accounts("alice", "bob")
        self.assertEqual(b.get_balance("bob"), -1)

    def test_merge_missing_survivor_returns_false(self):
        b = Bank()
        b.open_account("bob")
        self.assertFalse(b.merge_accounts("ghost", "bob"))

    def test_merge_missing_absorbed_returns_false(self):
        b = Bank()
        b.open_account("alice")
        self.assertFalse(b.merge_accounts("alice", "ghost"))

    def test_merge_same_account_returns_false(self):
        b = Bank()
        b.open_account("alice")
        self.assertFalse(b.merge_accounts("alice", "alice"))

    def test_merge_history_ordering(self):
        """Absorbed history goes BEFORE survivor's in the combined list (absorbed entries are older)."""
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("bob", 100)      # bob history: [deposit:100]
        b.deposit("alice", 200)    # alice history: [deposit:200]
        b.merge_accounts("alice", "bob")
        history = b.get_transaction_history("alice", 10)
        # alice's deposit (more recent) comes first; bob's deposit (absorbed) comes after
        self.assertEqual(history[0], "deposit:200")
        self.assertEqual(history[1], "deposit:100")

    def test_merge_reanchors_scheduled_from_id(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.open_account("carol")
        b.deposit("bob", 500)
        sid = b.schedule_transfer("bob", "carol", 200, execute_at=10)
        b.merge_accounts("alice", "bob")
        # bob is absorbed into alice; the transfer's from_id should now be "alice"
        count = b.tick(10)
        self.assertEqual(count, 1)
        self.assertEqual(b.get_balance("carol"), 200)

    def test_merge_reanchors_scheduled_to_id(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.open_account("carol")
        b.deposit("carol", 500)
        sid = b.schedule_transfer("carol", "bob", 100, execute_at=10)
        b.merge_accounts("alice", "bob")
        # bob is absorbed into alice; the transfer's to_id should now be "alice"
        count = b.tick(10)
        self.assertEqual(count, 1)
        self.assertEqual(b.get_balance("alice"), 100)

    def test_merge_balance_combined(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        b.deposit("alice", 1000)
        b.deposit("bob", 777)
        b.merge_accounts("alice", "bob")
        self.assertEqual(b.get_balance("alice"), 1777)

    def test_merge_returns_bool(self):
        b = Bank()
        b.open_account("alice")
        b.open_account("bob")
        result = b.merge_accounts("alice", "bob")
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()
