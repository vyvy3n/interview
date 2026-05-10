"""
Level 2 tests — Usage tracking + reports
Run: python3 test_level2.py
"""

import unittest
from solution import LLMGateway


class TestTopKUsersByTokens(unittest.TestCase):
    def _setup(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.register_user("bob", "build")
        gw.register_user("carol", "free")
        gw.register_user("dave", "scale")
        gw.handle_request("alice", "p", 500)
        gw.handle_request("bob",   "p", 300)
        gw.handle_request("carol", "p", 100)
        # dave: 0 tokens
        return gw

    def test_top1_by_tokens(self):
        gw = self._setup()
        result = gw.top_k_users_by_tokens(1)
        self.assertEqual(result, [("alice", 500)])

    def test_top3_by_tokens_ordered_desc(self):
        gw = self._setup()
        result = gw.top_k_users_by_tokens(3)
        self.assertEqual(result, [("alice", 500), ("bob", 300), ("carol", 100)])

    def test_top_k_exceeds_user_count_returns_all(self):
        gw = self._setup()
        result = gw.top_k_users_by_tokens(10)
        self.assertEqual(len(result), 4)

    def test_top_k_zero_returns_empty(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        self.assertEqual(gw.top_k_users_by_tokens(0), [])

    def test_tie_broken_by_user_id_alphabetical(self):
        gw = LLMGateway()
        gw.register_user("zara", "free")
        gw.register_user("alice", "free")
        gw.handle_request("zara", "p", 100)
        gw.handle_request("alice", "p", 100)
        result = gw.top_k_users_by_tokens(2)
        # Both have 100 tokens — alphabetical: alice < zara
        self.assertEqual(result[0][0], "alice")
        self.assertEqual(result[1][0], "zara")

    def test_zero_token_users_included(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        result = gw.top_k_users_by_tokens(1)
        self.assertEqual(result, [("alice", 0)])


class TestTopKUsersByRequests(unittest.TestCase):
    def _setup(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.register_user("bob", "build")
        gw.register_user("carol", "free")
        gw.handle_request("alice", "p", 10)
        gw.handle_request("alice", "p", 10)
        gw.handle_request("alice", "p", 10)
        gw.handle_request("bob", "p", 10)
        gw.handle_request("bob", "p", 10)
        gw.handle_request("carol", "p", 10)
        return gw

    def test_top1_by_requests(self):
        gw = self._setup()
        result = gw.top_k_users_by_requests(1)
        self.assertEqual(result, [("alice", 3)])

    def test_top2_by_requests_ordered_desc(self):
        gw = self._setup()
        result = gw.top_k_users_by_requests(2)
        self.assertEqual(result, [("alice", 3), ("bob", 2)])

    def test_tie_broken_alphabetically_requests(self):
        gw = LLMGateway()
        gw.register_user("zara", "free")
        gw.register_user("alice", "free")
        gw.handle_request("zara", "p", 10)
        gw.handle_request("alice", "p", 10)
        result = gw.top_k_users_by_requests(2)
        self.assertEqual(result[0][0], "alice")
        self.assertEqual(result[1][0], "zara")

    def test_top_k_zero_returns_empty_requests(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        self.assertEqual(gw.top_k_users_by_requests(0), [])

    def test_top_k_returns_correct_format(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.handle_request("alice", "p", 10)
        result = gw.top_k_users_by_requests(1)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], tuple)
        self.assertEqual(len(result[0]), 2)


class TestGetUsersInTier(unittest.TestCase):
    def test_users_in_tier_sorted_alphabetically(self):
        gw = LLMGateway()
        gw.register_user("carol", "free")
        gw.register_user("alice", "free")
        gw.register_user("bob", "free")
        result = gw.get_users_in_tier("free")
        self.assertEqual(result, ["alice", "bob", "carol"])

    def test_users_in_tier_filters_correctly(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.register_user("bob", "build")
        gw.register_user("carol", "free")
        self.assertEqual(gw.get_users_in_tier("build"), ["bob"])
        self.assertEqual(gw.get_users_in_tier("free"), ["alice", "carol"])

    def test_users_in_nonexistent_tier_returns_empty(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        self.assertEqual(gw.get_users_in_tier("scale"), [])

    def test_empty_gateway_tier_query_returns_empty(self):
        gw = LLMGateway()
        self.assertEqual(gw.get_users_in_tier("free"), [])


class TestGetTotalRequests(unittest.TestCase):
    def test_total_requests_zero_initially(self):
        gw = LLMGateway()
        self.assertEqual(gw.get_total_requests(), 0)

    def test_total_requests_sums_all_users(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.register_user("bob", "build")
        gw.handle_request("alice", "p", 10)
        gw.handle_request("alice", "p", 10)
        gw.handle_request("bob", "p", 10)
        self.assertEqual(gw.get_total_requests(), 3)

    def test_total_requests_excludes_failed_requests(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.handle_request("alice", "p", 10)
        gw.handle_request("ghost", "p", 10)  # missing user
        self.assertEqual(gw.get_total_requests(), 1)

    def test_total_requests_no_users_zero(self):
        gw = LLMGateway()
        gw.handle_request("ghost", "p", 10)
        self.assertEqual(gw.get_total_requests(), 0)


if __name__ == "__main__":
    unittest.main()
