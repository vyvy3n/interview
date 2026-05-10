"""
Level 6 tests — Atomic compound operations
Run: python3 test_level6.py
"""

import unittest
import asyncio
from solution import LLMGateway


class TestAbatchHandle(unittest.IsolatedAsyncioTestCase):
    async def test_batch_all_fit_returns_count(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        result = await gw.abatch_handle("alice", [("p1", 200), ("p2", 300), ("p3", 100)], now=0)
        self.assertEqual(result, 3)

    async def test_batch_does_not_fit_returns_neg1(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 500, 0)
        gw.register_user("alice", "free")
        result = await gw.abatch_handle("alice", [("p1", 300), ("p2", 300)], now=0)
        self.assertEqual(result, -1)

    async def test_batch_rejection_does_not_deduct_tokens(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 500, 0)
        gw.register_user("alice", "free")
        await gw.abatch_handle("alice", [("p1", 300), ("p2", 300)], now=0)  # -1
        remaining = gw.get_remaining_tokens_at("alice", now=0)
        self.assertEqual(remaining, 500)

    async def test_batch_success_deducts_all_tokens(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        await gw.abatch_handle("alice", [("p1", 200), ("p2", 150), ("p3", 250)], now=0)
        remaining = gw.get_remaining_tokens_at("alice", now=0)
        self.assertEqual(remaining, 400)

    async def test_batch_success_increments_request_count(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        await gw.abatch_handle("alice", [("p1", 100), ("p2", 100)], now=0)
        self.assertEqual(gw.get_request_count("alice"), 2)

    async def test_batch_success_increments_total_tokens_used(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        await gw.abatch_handle("alice", [("p1", 100), ("p2", 150)], now=0)
        self.assertEqual(gw.get_total_tokens_used("alice"), 250)

    async def test_batch_rejection_does_not_increment_request_count(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 100, 0)
        gw.register_user("alice", "free")
        await gw.abatch_handle("alice", [("p1", 200)], now=0)  # -1
        self.assertEqual(gw.get_request_count("alice"), 0)

    async def test_batch_missing_user_returns_neg1(self):
        gw = LLMGateway()
        result = await gw.abatch_handle("ghost", [("p1", 100)], now=0)
        self.assertEqual(result, -1)

    async def test_batch_empty_list_returns_zero(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        result = await gw.abatch_handle("alice", [], now=0)
        self.assertEqual(result, 0)

    async def test_batch_triggers_refill_before_check(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 100)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "drain", 1000, now=0)  # drain to 0
        # after 10 seconds: refill +1000 → 1000
        result = await gw.abatch_handle("alice", [("p1", 500), ("p2", 500)], now=10)
        self.assertEqual(result, 2)

    async def test_concurrent_batches_atomicity(self):
        """Two concurrent batches each needing 600 tokens (bucket = 1000). Only one should win."""
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        results = await asyncio.gather(
            gw.abatch_handle("alice", [("a1", 300), ("a2", 300)], now=0),
            gw.abatch_handle("alice", [("b1", 300), ("b2", 300)], now=0),
        )
        winners = [r for r in results if r == 2]
        losers = [r for r in results if r == -1]
        self.assertEqual(len(winners), 1)
        self.assertEqual(len(losers), 1)


class TestAmergeUsers(unittest.IsolatedAsyncioTestCase):
    async def test_merge_returns_true_on_success(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        gw.register_user("bob", "free")
        self.assertTrue(await gw.amerge_users("alice", "bob"))

    async def test_merge_removes_absorbed_user(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        gw.register_user("bob", "free")
        await gw.amerge_users("alice", "bob")
        self.assertEqual(gw.get_request_count("bob"), -1)

    async def test_merge_sums_max_tokens(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        gw.register_user("bob", "free")
        await gw.amerge_users("alice", "bob")
        # new max = 1000 + 1000 = 2000
        # current tokens = 1000 + 1000 = 2000 (capped at 2000)
        remaining = gw.get_remaining_tokens_at("alice", now=0)
        self.assertEqual(remaining, 2000)

    async def test_merge_sums_request_counts(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.register_user("bob", "free")
        gw.handle_request("alice", "p", 10)
        gw.handle_request("alice", "p", 10)
        gw.handle_request("bob", "p", 10)
        await gw.amerge_users("alice", "bob")
        self.assertEqual(gw.get_request_count("alice"), 3)

    async def test_merge_sums_total_tokens_used(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.register_user("bob", "free")
        gw.handle_request("alice", "p", 200)
        gw.handle_request("bob", "p", 300)
        await gw.amerge_users("alice", "bob")
        self.assertEqual(gw.get_total_tokens_used("alice"), 500)

    async def test_merge_sums_cache_hits(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.register_user("bob", "free")
        gw.handle_cached_request("alice", "p", "r", 10, now=0)  # alice stores
        gw.handle_cached_request("alice", "p", "r", 10, now=0)  # hit for alice
        gw.handle_cached_request("bob", "p", "r", 10, now=0)    # hit for bob
        gw.handle_cached_request("bob", "p", "r", 10, now=0)    # hit for bob
        await gw.amerge_users("alice", "bob")
        self.assertEqual(gw.get_cache_hits("alice"), 3)

    async def test_merge_keeps_survivor_tier(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.set_tier_limits("scale", 5000, 200)
        gw.register_user("alice", "free")
        gw.register_user("bob", "scale")
        await gw.amerge_users("alice", "bob")
        users_in_free = gw.get_users_in_tier("free")
        self.assertIn("alice", users_in_free)

    async def test_merge_max_refill_rate(self):
        gw = LLMGateway()
        gw.set_tier_limits("slow", 1000, 10)
        gw.set_tier_limits("fast", 1000, 100)
        gw.register_user("alice", "slow")
        gw.register_user("bob", "fast")
        await gw.amerge_users("alice", "bob")
        # drain to 0, then refill for 5 sec at max(10,100)=100 rate
        gw.handle_request_at("alice", "drain", 2000, now=0)  # drain (no rate limit on handle_request)
        # Actually use handle_request which doesn't enforce rate limit,
        # set_tier_limits was called to set up refill rates
        # Let's just check remaining after refill
        gw._users["alice"].current_tokens = 0  # manually drain
        gw._users["alice"].last_action_ts = 0
        remaining = gw.get_remaining_tokens_at("alice", now=5)
        # should refill at rate 100 (max of 10 and 100)
        self.assertEqual(remaining, min(2000, 500))

    async def test_merge_caps_current_tokens_at_new_max(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        gw.register_user("bob", "free")
        # Both have 1000 current. merged max = 2000. merged current = min(2000, 2000) = 2000
        await gw.amerge_users("alice", "bob")
        remaining = gw.get_remaining_tokens_at("alice", now=0)
        self.assertLessEqual(remaining, 2000)

    async def test_merge_same_user_returns_false(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        self.assertFalse(await gw.amerge_users("alice", "alice"))

    async def test_merge_missing_survivor_returns_false(self):
        gw = LLMGateway()
        gw.register_user("bob", "free")
        self.assertFalse(await gw.amerge_users("ghost", "bob"))

    async def test_merge_missing_absorbed_returns_false(self):
        gw = LLMGateway()
        gw.register_user("alice", "free")
        self.assertFalse(await gw.amerge_users("alice", "ghost"))


class TestAcompareAndHandle(unittest.IsolatedAsyncioTestCase):
    async def test_cas_succeeds_when_expected_matches(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        result = await gw.acompare_and_handle("alice", "p", 1000, 100, now=0)
        self.assertEqual(result, "ok")

    async def test_cas_returns_stale_when_expected_does_not_match(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 100, now=0)  # now at 900
        result = await gw.acompare_and_handle("alice", "p", 1000, 100, now=0)
        self.assertEqual(result, "stale")

    async def test_cas_returns_empty_when_user_missing(self):
        gw = LLMGateway()
        result = await gw.acompare_and_handle("ghost", "p", 1000, 100, now=0)
        self.assertEqual(result, "")

    async def test_cas_returns_rate_limited_when_not_enough_tokens(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 100, 0)
        gw.register_user("alice", "free")
        # expected = 100 (correct), but requesting 200 tokens
        result = await gw.acompare_and_handle("alice", "p", 100, 200, now=0)
        self.assertEqual(result, "rate_limited")

    async def test_cas_deducts_tokens_on_success(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        await gw.acompare_and_handle("alice", "p", 1000, 300, now=0)
        remaining = gw.get_remaining_tokens_at("alice", now=0)
        self.assertEqual(remaining, 700)

    async def test_cas_increments_request_count_on_ok(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        await gw.acompare_and_handle("alice", "p", 1000, 100, now=0)
        self.assertEqual(gw.get_request_count("alice"), 1)

    async def test_cas_triggers_refill_before_compare(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 100)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "drain", 1000, now=0)  # drain to 0
        # after 5 sec, refill +500 → 500. expected = 500 → match
        result = await gw.acompare_and_handle("alice", "p", 500, 100, now=5)
        self.assertEqual(result, "ok")

    async def test_concurrent_cas_only_one_wins(self):
        """100 concurrent CAS calls with same expected_remaining. Only 1 should succeed."""
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        results = await asyncio.gather(*[
            gw.acompare_and_handle("alice", f"p{i}", 1000, 100, now=0)
            for i in range(100)
        ])
        ok_count = sum(1 for r in results if r == "ok")
        stale_count = sum(1 for r in results if r == "stale")
        self.assertEqual(ok_count, 1)
        self.assertEqual(stale_count, 99)

    async def test_concurrent_cas_remaining_correct_after_one_win(self):
        """After the CAS race, the bucket should reflect exactly one deduction."""
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        await asyncio.gather(*[
            gw.acompare_and_handle("alice", f"p{i}", 1000, 100, now=0)
            for i in range(100)
        ])
        remaining = gw.get_remaining_tokens_at("alice", now=0)
        self.assertEqual(remaining, 900)

    async def test_sequential_cas_can_all_succeed(self):
        """Each CAS reads the updated expected value → all succeed sequentially."""
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        current = 1000
        for _ in range(5):
            result = await gw.acompare_and_handle("alice", "p", current, 100, now=0)
            self.assertEqual(result, "ok")
            current -= 100
        self.assertEqual(gw.get_remaining_tokens_at("alice", now=0), 500)

    async def test_cas_stale_does_not_deduct_tokens(self):
        gw = LLMGateway()
        gw.set_tier_limits("free", 1000, 0)
        gw.register_user("alice", "free")
        gw.handle_request_at("alice", "p", 100, now=0)  # now at 900
        await gw.acompare_and_handle("alice", "p", 1000, 50, now=0)  # stale
        remaining = gw.get_remaining_tokens_at("alice", now=0)
        self.assertEqual(remaining, 900)

    async def test_all_three_l6_ops_interleave_safely(self):
        """Mix batch, CAS, and register under concurrency."""
        gw = LLMGateway()
        gw.set_tier_limits("free", 10_000, 0)
        gw.register_user("alice", "free")
        gw.register_user("bob", "free")

        async def do_batch():
            return await gw.abatch_handle("alice", [("b1", 100), ("b2", 100)], now=0)

        async def do_cas():
            remaining = gw.get_remaining_tokens_at("alice", now=0)
            return await gw.acompare_and_handle("alice", "p", remaining, 50, now=0)

        async def do_register():
            return await gw.aregister_user(f"new_user_{id(asyncio.current_task())}", "free")

        tasks = (
            [do_batch() for _ in range(5)]
            + [do_cas() for _ in range(5)]
            + [do_register() for _ in range(5)]
        )
        results = await asyncio.gather(*tasks)
        # No exceptions = good. All results should be valid types.
        for r in results:
            self.assertIn(type(r), (int, str, bool))


if __name__ == "__main__":
    unittest.main()
