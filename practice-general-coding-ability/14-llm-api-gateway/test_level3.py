"""
Level 3 tests — Token-bucket rate limiting (lazy refill)
Run: python3 test_level3.py
"""

import unittest
from solution import LLMGateway


class TestSetTierLimits(unittest.TestCase):
    def test_set_tier_limits_returns_true(self):
        gw = LLMGateway()
        self.assertTrue(gw.set_tier_limits("free", 1000, 100))

    def test_set_tier_limits_applies_to_existing_users(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.set_tier_limits("free", 500, 50)
        remaining = gw.get_remaining_tokens_at("alice", now=0)
        self.assertEqual(remaining, 500)

    def test_set_tier_limits_caps_current_tokens_at_new_max(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        # alice starts with default max = 1_000_000
        gw.set_tier_limits("free", 200, 10)
        remaining = gw.get_remaining_tokens_at("alice", now=0)
        self.assertEqual(remaining, 200)

    def test_set_tier_limits_applies_to_future_users(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 300, 30)
        gw.register_user("alice", "free")
        remaining = gw.get_remaining_tokens_at("alice", now=0)
        self.assertEqual(remaining, 300)

    def test_set_tier_limits_only_affects_matching_tier(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        gw.register_user("bob", "build")
        gw.set_tier_limits("free", 400, 0)
        # bob's tier is "build", should not be affected
        bob_remaining = gw.get_remaining_tokens_at("bob", now=0)
        self.assertEqual(bob_remaining, 1_000_000)


class TestHandleRequestAt(unittest.TestCase):
    def test_accepted_when_tokens_available(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        result = gw.handle_request_at("alice", "hello", 500, now=0)
        self.assertEqual(result, "ok")

    def test_rate_limited_when_insufficient_tokens(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 100, 0)
        gw.register_user("alice", "free")
        result = gw.handle_request_at("alice", "big", 200, now=0)
        self.assertEqual(result, "rate_limited")

    def test_missing_user_returns_empty_string(self):
        gw = LLMGateway()
        result = gw.handle_request_at("ghost", "p", 100, now=0)
        self.assertEqual(result, "")

    def test_tokens_deducted_on_accept(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 300, now=0)
        self.assertEqual(gw.get_remaining_tokens_at("alice", now=0), 700)

    def test_tokens_not_deducted_on_rate_limit(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 100, 0)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 200, now=0)
        self.assertEqual(gw.get_remaining_tokens_at("alice", now=0), 100)

    def test_request_count_incremented_on_ok(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 100, now=0)
        self.assertEqual(gw.get_request_count("alice"), 1)

    def test_request_count_not_incremented_on_rate_limit(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10, 0)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 100, now=0)  # rate limited
        self.assertEqual(gw.get_request_count("alice"), 0)

    def test_total_tokens_used_incremented_on_ok(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 300, now=0)
        self.assertEqual(gw.get_total_tokens_used("alice"), 300)

    def test_refill_happens_before_check(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 100)  # refill 100/sec
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 900, now=0)   # 1000 → 100
        result = gw.handle_request_at("alice", "p", 300, now=2)  # refill +200 → 300, deduct 300 → 0
        self.assertEqual(result, "ok")

    def test_refill_capped_at_max_tokens(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 500)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 1000, now=0)  # drain to 0
        remaining = gw.get_remaining_tokens_at("alice", now=100)  # refill: min(1000, 50000) = 1000
        self.assertEqual(remaining, 1000)

    def test_same_timestamp_no_refill(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 100)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 500, now=5)   # 1000 → 500
        remaining = gw.get_remaining_tokens_at("alice", now=5)  # elapsed=0, no refill
        self.assertEqual(remaining, 500)

    def test_handle_request_no_timestamp_still_works(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10, 0)  # tiny bucket
        gw.register_user("alice", "free")
        # L1 handle_request ignores rate limits
        result = gw.handle_request("alice", "p", 10000)
        self.assertEqual(result, "ok")


class TestGetRemainingTokensAt(unittest.TestCase):
    def test_full_bucket_at_start(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        self.assertEqual(gw.get_remaining_tokens_at("alice", now=0), 1000)

    def test_missing_user_returns_neg1(self):
        gw = LLMGateway()
        self.assertEqual(gw.get_remaining_tokens_at("ghost", now=0), -1)

    def test_triggers_refill(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 50)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 1000, now=0)  # drain to 0
        remaining = gw.get_remaining_tokens_at("alice", now=4)  # +200
        self.assertEqual(remaining, 200)


class TestUpdateUserTier(unittest.TestCase):
    def test_update_tier_returns_true(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.set_tier_limits("scale", 5000, 200)
        gw.register_user("alice", "free")
        self.assertTrue(gw.update_user_tier("alice", "scale", now=0))

    def test_update_tier_missing_user_returns_false(self):
        gw = LLMGateway()
        self.assertFalse(gw.update_user_tier("ghost", "scale", now=0))

    def test_update_tier_new_limits_applied(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.set_tier_limits("scale", 5000, 200)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 500, now=0)   # 1000 → 500
        gw.update_user_tier("alice", "scale", now=0)
        remaining = gw.get_remaining_tokens_at("alice", now=0)
        # Refill at old rate first (0): still 500. New max = 5000, cap(500, 5000) = 500
        self.assertEqual(remaining, 500)

    def test_update_tier_refills_before_switching(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 100)
        gw.set_tier_limits("build", 500, 0)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 1000, now=0)  # drain to 0
        gw.update_user_tier("alice", "build", now=5)     # refill 5*100=500 → min(1000,500)=500, then new max=500
        remaining = gw.get_remaining_tokens_at("alice", now=5)
        self.assertEqual(remaining, 500)

    def test_update_tier_caps_tokens_at_new_max(self):
        gw = LLMGateway()
        gw.set_tier_limits("scale", 5000, 0)
        gw.set_tier_limits("free", 100, 0)
        gw.register_user("alice", "scale")
        # alice has 5000 tokens; downgrade to free (max=100)
        gw.update_user_tier("alice", "free", now=0)
        remaining = gw.get_remaining_tokens_at("alice", now=0)
        self.assertEqual(remaining, 100)


if __name__ == "__main__":
    unittest.main()
