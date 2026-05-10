"""
Level 5 tests — Async concurrent request handling
Run: python3 test_level5.py
"""

import unittest
import asyncio
from solution import LLMGateway


class TestAsyncRegisterUser(unittest.IsolatedAsyncioTestCase):
    async def test_aregister_new_user_returns_true(self):
        gw = LLMGateway()
        self.assertTrue(await gw.aregister_user("alice", "free"))

    async def test_aregister_duplicate_returns_false(self):
        gw = LLMGateway()
        await gw.aregister_user("alice", "free")
        self.assertFalse(await gw.aregister_user("alice", "build"))

    async def test_aregister_result_visible_to_sync(self):
        gw = LLMGateway()
        await gw.aregister_user("alice", "free")
        # sync handle_request should see the registration
        result = gw.handle_request("alice", "p", 10)
        self.assertEqual(result, "ok")

    async def test_concurrent_register_same_user_only_one_succeeds(self):
        gw = LLMGateway()
        results = await asyncio.gather(*[
            gw.aregister_user("alice", "free") for _ in range(50)
        ])
        self.assertEqual(sum(results), 1)

    async def test_concurrent_register_different_users_all_succeed(self):
        gw = LLMGateway()
        results = await asyncio.gather(*[
            gw.aregister_user(f"user{i}", "free") for i in range(50)
        ])
        self.assertEqual(sum(results), 50)


class TestAsyncHandleRequestAt(unittest.IsolatedAsyncioTestCase):
    async def test_ahandle_request_at_accepted_returns_ok(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        result = await gw.ahandle_request_at("alice", "p", 100, now=0)
        self.assertEqual(result, "ok")

    async def test_ahandle_request_at_rate_limited(self):
        gw = LLMGateway()
        gw.set_tier_limits("tiny", 50, 0)
        gw.register_user("alice", "tiny")
        result = await gw.ahandle_request_at("alice", "p", 100, now=0)
        self.assertEqual(result, "rate_limited")

    async def test_ahandle_request_at_missing_user_returns_empty(self):
        gw = LLMGateway()
        result = await gw.ahandle_request_at("ghost", "p", 10, now=0)
        self.assertEqual(result, "")

    async def test_concurrent_requests_do_not_over_deduct(self):
        """50 concurrent requests of 100 tokens each, bucket = 500. Exactly 5 should succeed."""
        gw = LLMGateway()
        gw.set_tier_limits("free", 500, 0)
        gw.register_user("alice", "free")
        results = await asyncio.gather(*[
            gw.ahandle_request_at("alice", f"p{i}", 100, now=0)
            for i in range(50)
        ])
        ok_count = sum(1 for r in results if r == "ok")
        self.assertEqual(ok_count, 5)

    async def test_concurrent_requests_exact_token_accounting(self):
        """After concurrent deductions, remaining tokens should be exactly 0."""
        gw = LLMGateway()
        gw.set_tier_limits("free", 500, 0)
        gw.register_user("alice", "free")
        await asyncio.gather(*[
            gw.ahandle_request_at("alice", f"p{i}", 100, now=0)
            for i in range(50)
        ])
        remaining = await gw.aget_remaining_tokens_at("alice", now=0)
        self.assertEqual(remaining, 0)

    async def test_sync_request_count_consistent_after_async_ops(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        await asyncio.gather(*[
            gw.ahandle_request_at("alice", f"p{i}", 10, now=0)
            for i in range(20)
        ])
        self.assertEqual(gw.get_request_count("alice"), 20)


class TestAsyncGetRemainingTokensAt(unittest.IsolatedAsyncioTestCase):
    async def test_aget_remaining_returns_correct_value(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 300, now=0)
        remaining = await gw.aget_remaining_tokens_at("alice", now=0)
        self.assertEqual(remaining, 700)

    async def test_aget_remaining_triggers_refill(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 100)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 1000, now=0)  # drain
        remaining = await gw.aget_remaining_tokens_at("alice", now=5)  # +500
        self.assertEqual(remaining, 500)

    async def test_aget_remaining_missing_user_returns_neg1(self):
        gw = LLMGateway()
        result = await gw.aget_remaining_tokens_at("ghost", now=0)
        self.assertEqual(result, -1)


class TestAsyncHandleCachedRequest(unittest.IsolatedAsyncioTestCase):
    async def test_ahandle_cached_request_miss_returns_ok(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        result = await gw.ahandle_cached_request("alice", "p", "r", 100, now=0)
        self.assertEqual(result, "ok")

    async def test_ahandle_cached_request_hit_returns_cached(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.register_user("bob", "free")
        await gw.ahandle_cached_request("alice", "prompt", "the answer", 100, now=0)
        result = await gw.ahandle_cached_request("bob", "prompt", "ignored", 999, now=0)
        self.assertEqual(result, "the answer")

    async def test_concurrent_cache_misses_same_prompt_cache_written_once(self):
        """100 concurrent requests for the same uncached prompt. Cache should contain it once."""
        gw = LLMGateway()
        gw.set_tier_limits("free", 100_000, 0)
        gw.register_user("alice", "free")
        await asyncio.gather(*[
            gw.ahandle_cached_request("alice", "shared", "resp", 10, now=0)
            for _ in range(100)
        ])
        self.assertEqual(gw.get_cache_size(), 1)

    async def test_concurrent_cache_hits_no_token_deduction(self):
        """Cache hit should never deduct tokens, even under concurrency."""
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.register_user("bob", "free")
        # alice populates cache
        await gw.ahandle_cached_request("alice", "cached", "answer", 100, now=0)
        tokens_before = gw.get_remaining_tokens_at("bob", now=0)
        # 50 concurrent cache hits from bob — no tokens should be deducted
        await asyncio.gather(*[
            gw.ahandle_cached_request("bob", "cached", "ignored", 9999, now=0)
            for _ in range(50)
        ])
        tokens_after = gw.get_remaining_tokens_at("bob", now=0)
        self.assertEqual(tokens_before, tokens_after)

    async def test_ahandle_cached_missing_user_returns_empty(self):
        gw = LLMGateway()
        result = await gw.ahandle_cached_request("ghost", "p", "r", 10, now=0)
        self.assertEqual(result, "")


class TestMixedSyncAsync(unittest.IsolatedAsyncioTestCase):
    async def test_sync_register_async_handle(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        result = await gw.ahandle_request_at("alice", "p", 100, now=0)
        self.assertEqual(result, "ok")

    async def test_async_register_sync_handle(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        await gw.aregister_user("alice", "free")
        result = gw.handle_request("alice", "p", 100)
        self.assertEqual(result, "ok")

    async def test_l2_reports_work_after_async_ops(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        await asyncio.gather(*[gw.aregister_user(f"u{i}", "free") for i in range(5)])
        await asyncio.gather(*[gw.ahandle_request_at(f"u{i}", "p", 10, now=0) for i in range(5)])
        self.assertEqual(gw.get_total_requests(), 5)

    async def test_l3_remaining_tokens_consistent_after_async(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        await asyncio.gather(*[gw.ahandle_request_at("alice", f"p{i}", 100, now=0) for i in range(5)])
        remaining = gw.get_remaining_tokens_at("alice", now=0)
        self.assertEqual(remaining, 500)

    async def test_l4_cache_consistent_after_async(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        await gw.ahandle_cached_request("alice", "p", "resp", 100, now=0)
        # sync call should see the cached entry
        result = gw.handle_cached_request("alice", "p", "different", 100, now=0)
        self.assertEqual(result, "resp")

    async def test_100_concurrent_different_users_no_interference(self):
        """Each user has their own bucket; concurrent requests must not interfere."""
        gw = LLMGateway()
        gw.set_tier_limits("free", 100, 0)
        for i in range(100):
            gw.register_user(f"u{i}", "free")
        results = await asyncio.gather(*[
            gw.ahandle_request_at(f"u{i}", "p", 100, now=0) for i in range(100)
        ])
        # Each user has exactly 100 tokens; each request costs 100 → all succeed
        self.assertEqual(sum(1 for r in results if r == "ok"), 100)


if __name__ == "__main__":
    unittest.main()
