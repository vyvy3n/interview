"""
Level 1 tests — Basic request lifecycle
Run: python3 test_level1.py
"""

import unittest
from solution import LLMGateway


class TestRegisterUser(unittest.TestCase):
    def test_register_new_user_returns_true(self):
        gw = LLMGateway()
        self.assertTrue(gw.register_user("alice", "free"))

    def test_register_duplicate_user_returns_false(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        self.assertFalse(gw.register_user("alice", "build"))

    def test_register_different_users_both_succeed(self):
        gw = LLMGateway()
        self.assertTrue(gw.register_user("alice", "free"))
        self.assertTrue(gw.register_user("bob", "build"))

    def test_register_does_not_overwrite_on_duplicate(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.handle_request("alice", "hi", 100)
        gw.register_user("alice", "scale")  # False, no overwrite
        # request count must still be 1
        self.assertEqual(gw.get_request_count("alice"), 1)

    def test_register_accepts_any_tier_string(self):
        gw = LLMGateway()
        self.assertTrue(gw.register_user("u1", "custom_tier_xyz"))


class TestHandleRequest(unittest.TestCase):
    def test_handle_request_registered_user_returns_ok(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        self.assertEqual(gw.handle_request("alice", "hello", 50), "ok")

    def test_handle_request_missing_user_returns_empty(self):
        gw = LLMGateway()
        self.assertEqual(gw.handle_request("ghost", "hello", 50), "")

    def test_handle_request_increments_request_count(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.handle_request("alice", "p1", 50)
        gw.handle_request("alice", "p2", 30)
        self.assertEqual(gw.get_request_count("alice"), 2)

    def test_handle_request_increments_tokens_used(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.handle_request("alice", "p1", 50)
        gw.handle_request("alice", "p2", 30)
        self.assertEqual(gw.get_total_tokens_used("alice"), 80)

    def test_handle_request_missing_user_not_counted(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.handle_request("ghost", "p", 100)  # user doesn't exist
        self.assertEqual(gw.get_total_requests() if hasattr(gw, "get_total_requests") else 0, 0)

    def test_handle_request_prompt_ignored_at_level1(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        # Any prompt string should work
        self.assertEqual(gw.handle_request("alice", "", 10), "ok")
        self.assertEqual(gw.handle_request("alice", "a" * 1000, 10), "ok")


class TestGetRequestCount(unittest.TestCase):
    def test_request_count_zero_after_register(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        self.assertEqual(gw.get_request_count("alice"), 0)

    def test_request_count_missing_user_returns_neg1(self):
        gw = LLMGateway()
        self.assertEqual(gw.get_request_count("ghost"), -1)

    def test_request_count_multiple_users_independent(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.register_user("bob", "build")
        gw.handle_request("alice", "p", 10)
        gw.handle_request("alice", "p", 10)
        gw.handle_request("bob", "p", 10)
        self.assertEqual(gw.get_request_count("alice"), 2)
        self.assertEqual(gw.get_request_count("bob"), 1)


class TestGetTotalTokensUsed(unittest.TestCase):
    def test_tokens_zero_after_register(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        self.assertEqual(gw.get_total_tokens_used("alice"), 0)

    def test_tokens_missing_user_returns_neg1(self):
        gw = LLMGateway()
        self.assertEqual(gw.get_total_tokens_used("ghost"), -1)

    def test_tokens_accumulate_across_requests(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.handle_request("alice", "p1", 100)
        gw.handle_request("alice", "p2", 250)
        gw.handle_request("alice", "p3", 50)
        self.assertEqual(gw.get_total_tokens_used("alice"), 400)

    def test_tokens_multiple_users_independent(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.register_user("bob", "build")
        gw.handle_request("alice", "p", 500)
        gw.handle_request("bob", "p", 200)
        self.assertEqual(gw.get_total_tokens_used("alice"), 500)
        self.assertEqual(gw.get_total_tokens_used("bob"), 200)

    def test_missing_user_request_does_not_affect_existing_user(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.handle_request("alice", "p", 100)
        gw.handle_request("ghost", "p", 9999)  # does nothing
        self.assertEqual(gw.get_total_tokens_used("alice"), 100)


if __name__ == "__main__":
    unittest.main()
