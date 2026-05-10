"""
Level 4 tests — Per-prompt response caching
Run: python3 test_level4.py
"""

import unittest
from solution import LLMGateway


class TestHandleCachedRequestBasic(unittest.TestCase):
    def setUp(self):
        self.gw = LLMGateway()
        self.gw.set_tier_limits("free", 10_000, 0)
        self.gw.register_user("alice", "free")
        self.gw.register_user("bob", "free")

    def test_cache_miss_accepted_returns_ok(self):
        result = self.gw.handle_cached_request("alice", "What is AI?", "AI is...", 100, now=0)
        self.assertEqual(result, "ok")

    def test_cache_hit_returns_cached_response(self):
        self.gw.handle_cached_request("alice", "What is AI?", "AI is...", 100, now=0)
        result = self.gw.handle_cached_request("bob", "What is AI?", "different", 999, now=0)
        self.assertEqual(result, "AI is...")

    def test_cache_hit_does_not_deduct_tokens(self):
        self.gw.handle_cached_request("alice", "prompt", "response", 1000, now=0)
        before = self.gw.get_remaining_tokens_at("bob", now=0)
        self.gw.handle_cached_request("bob", "prompt", "other", 9999, now=0)
        after = self.gw.get_remaining_tokens_at("bob", now=0)
        self.assertEqual(before, after)

    def test_cache_miss_rate_limited_returns_rate_limited(self):
        self.gw.set_tier_limits("tiny", 50, 0)
        self.gw.register_user("carol", "tiny")
        result = self.gw.handle_cached_request("carol", "expensive", "resp", 100, now=0)
        self.assertEqual(result, "rate_limited")

    def test_cache_miss_rate_limited_does_not_write_cache(self):
        self.gw.set_tier_limits("tiny", 50, 0)
        self.gw.register_user("carol", "tiny")
        self.gw.handle_cached_request("carol", "expensive", "resp", 100, now=0)
        self.assertEqual(self.gw.get_cache_size(), 0)

    def test_missing_user_returns_empty_string(self):
        result = self.gw.handle_cached_request("ghost", "p", "r", 10, now=0)
        self.assertEqual(result, "")

    def test_cache_is_global_any_user_can_hit(self):
        # alice caches, carol (different tier) gets it for free
        self.gw.set_tier_limits("tiny", 50, 0)
        self.gw.register_user("carol", "tiny")
        self.gw.handle_cached_request("alice", "shared prompt", "shared resp", 50, now=0)
        result = self.gw.handle_cached_request("carol", "shared prompt", "other", 9999, now=0)
        self.assertEqual(result, "shared resp")

    def test_same_user_cache_hit(self):
        self.gw.handle_cached_request("alice", "repeat", "the answer", 100, now=0)
        result = self.gw.handle_cached_request("alice", "repeat", "different", 100, now=0)
        self.assertEqual(result, "the answer")


class TestGetCacheSize(unittest.TestCase):
    def test_cache_size_zero_initially(self):
        gw = LLMGateway()
        self.assertEqual(gw.get_cache_size(), 0)

    def test_cache_size_increases_on_miss(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.handle_cached_request("alice", "p1", "r1", 10, now=0)
        gw.handle_cached_request("alice", "p2", "r2", 10, now=0)
        self.assertEqual(gw.get_cache_size(), 2)

    def test_cache_size_does_not_increase_on_hit(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.handle_cached_request("alice", "p1", "r1", 10, now=0)
        gw.handle_cached_request("alice", "p1", "r1", 10, now=0)  # hit
        self.assertEqual(gw.get_cache_size(), 1)

    def test_cache_size_does_not_increase_on_rate_limit(self):
        gw = LLMGateway()
        gw.set_tier_limits("tiny", 5, 0)
        gw.register_user("alice", "tiny")
        gw.handle_cached_request("alice", "p1", "r1", 100, now=0)  # rate limited
        self.assertEqual(gw.get_cache_size(), 0)


class TestGetCacheHits(unittest.TestCase):
    def test_cache_hits_zero_initially(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        self.assertEqual(gw.get_cache_hits("alice"), 0)

    def test_cache_hits_missing_user_returns_neg1(self):
        gw = LLMGateway()
        self.assertEqual(gw.get_cache_hits("ghost"), -1)

    def test_cache_hits_incremented_on_hit(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.register_user("bob", "free")
        gw.handle_cached_request("alice", "p", "r", 100, now=0)
        gw.handle_cached_request("bob", "p", "r", 100, now=0)  # hit for bob
        gw.handle_cached_request("bob", "p", "r", 100, now=0)  # hit for bob again
        self.assertEqual(gw.get_cache_hits("alice"), 0)
        self.assertEqual(gw.get_cache_hits("bob"), 2)

    def test_cache_misses_do_not_count_as_hits(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.handle_cached_request("alice", "new_prompt", "r", 100, now=0)
        self.assertEqual(gw.get_cache_hits("alice"), 0)


class TestInvalidateCache(unittest.TestCase):
    def test_invalidate_by_prefix_returns_count(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.handle_cached_request("alice", "hello world", "r1", 10, now=0)
        gw.handle_cached_request("alice", "hello there", "r2", 10, now=0)
        gw.handle_cached_request("alice", "goodbye", "r3", 10, now=0)
        count = gw.invalidate_cache("hello")
        self.assertEqual(count, 2)

    def test_invalidate_removes_entries(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.handle_cached_request("alice", "hello", "r", 10, now=0)
        gw.invalidate_cache("hello")
        self.assertEqual(gw.get_cache_size(), 0)

    def test_invalidate_empty_prefix_clears_all(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.handle_cached_request("alice", "p1", "r1", 10, now=0)
        gw.handle_cached_request("alice", "p2", "r2", 10, now=0)
        gw.handle_cached_request("alice", "p3", "r3", 10, now=0)
        count = gw.invalidate_cache("")
        self.assertEqual(count, 3)
        self.assertEqual(gw.get_cache_size(), 0)

    def test_invalidate_no_match_returns_zero(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.handle_cached_request("alice", "hello", "r", 10, now=0)
        count = gw.invalidate_cache("xyz")
        self.assertEqual(count, 0)
        self.assertEqual(gw.get_cache_size(), 1)

    def test_invalidate_allows_repopulation(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.handle_cached_request("alice", "p", "old", 10, now=0)
        gw.invalidate_cache("p")
        gw.handle_cached_request("alice", "p", "new", 10, now=0)
        result = gw.handle_cached_request("alice", "p", "ignored", 10, now=0)
        self.assertEqual(result, "new")


class TestGetCacheHitRate(unittest.TestCase):
    def test_hit_rate_zero_slash_zero_initially(self):
        gw = LLMGateway()
        self.assertEqual(gw.get_cache_hit_rate(), "0/0")

    def test_hit_rate_format_correct(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.handle_cached_request("alice", "p1", "r1", 10, now=0)  # miss
        gw.handle_cached_request("alice", "p1", "r1", 10, now=0)  # hit
        self.assertEqual(gw.get_cache_hit_rate(), "1/2")

    def test_hit_rate_counts_all_attempts_including_missing_user(self):
        gw = LLMGateway()
        gw.handle_cached_request("ghost", "p", "r", 10, now=0)  # missing user
        self.assertEqual(gw.get_cache_hit_rate(), "0/1")

    def test_hit_rate_all_hits(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.handle_cached_request("alice", "p", "r", 10, now=0)  # miss + store
        gw.handle_cached_request("alice", "p", "r", 10, now=0)  # hit
        gw.handle_cached_request("alice", "p", "r", 10, now=0)  # hit
        self.assertEqual(gw.get_cache_hit_rate(), "2/3")

    def test_hit_rate_rate_limited_counts_as_attempt(self):
        gw = LLMGateway()
        gw.set_tier_limits("tiny", 5, 0)
        gw.register_user("alice", "tiny")
        gw.handle_cached_request("alice", "p", "r", 100, now=0)  # miss + rate limited
        self.assertEqual(gw.get_cache_hit_rate(), "0/1")


if __name__ == "__main__":
    unittest.main()
