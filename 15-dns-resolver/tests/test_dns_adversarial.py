"""Adversarial edge-case tests for the DNS resolver.

These probe corners that the spec implies but does not walk through:
  - normalize boundary forms
  - max_queries == 0 / 1 hard limits
  - mixed-glue authority lists in different orders
  - concurrency stress (1 worker, many workers, empty list, large list)
  - error propagation (NXDOMAIN / REFUSED / success in one batch)
  - input order preservation in resolve_all's returned dict
  - cache scoping across calls and within a call (case-equivalent inputs)
  - per-domain budget interaction with the cross-domain cache

We import from `solution` to mirror the layout of tests/test_dns.py;
swap to `dns_exercise` if you want to grade a fresh implementation.
"""
import os
import sys
import time
import unittest

# Make the package's root importable when running this file directly.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from solution import normalize, resolve, resolve_all  # noqa: E402
from dns_mock import (  # noqa: E402
    reset_call_counter,
    get_call_count,
    get_call_log,
    get_peak_in_flight,
    set_in_flight_hold,
)


# ─────── known-good IPs from the simulated topology ───────
IP_ANTHROPIC      = "160.79.104.10"
IP_API_ANTHROPIC  = "104.16.1.1"
IP_EXAMPLE        = "93.184.216.34"
IP_CDN_FASTCDN    = "203.0.113.99"
IP_DEADNS         = "192.0.2.99"
IP_MIXED          = "203.0.113.50"
IP_GLUEORDER      = "203.0.113.60"


class TestNormalizeBoundary(unittest.TestCase):
    """Spec says: lowercase + ensure trailing dot. Probe inputs that are
    already partially normalized."""

    def test_already_normalized(self):
        self.assertEqual(normalize("anthropic.com."), "anthropic.com.")

    def test_no_trailing_dot(self):
        self.assertEqual(normalize("anthropic.com"), "anthropic.com.")

    def test_uppercase_with_trailing_dot(self):
        self.assertEqual(normalize("ANTHROPIC.COM."), "anthropic.com.")

    def test_uppercase_no_trailing_dot(self):
        self.assertEqual(normalize("ANTHROPIC.COM"), "anthropic.com.")

    def test_mixed_case_subdomain(self):
        self.assertEqual(normalize("Docs.Anthropic.Com"), "docs.anthropic.com.")

    def test_does_not_double_dot(self):
        # If input already ends with '.', normalize must NOT produce '..'.
        self.assertNotIn("..", normalize("anthropic.com."))


class TestResolveNameForms(unittest.TestCase):
    """resolve() should accept all three input forms for the same domain."""

    def setUp(self):
        reset_call_counter()

    def test_resolve_with_trailing_dot(self):
        self.assertEqual(resolve("anthropic.com."), IP_ANTHROPIC)

    def test_resolve_without_trailing_dot(self):
        reset_call_counter()
        self.assertEqual(resolve("anthropic.com"), IP_ANTHROPIC)

    def test_resolve_uppercase_with_dot(self):
        reset_call_counter()
        self.assertEqual(resolve("ANTHROPIC.COM."), IP_ANTHROPIC)

    def test_resolve_uppercase_no_dot(self):
        reset_call_counter()
        self.assertEqual(resolve("ANTHROPIC.COM"), IP_ANTHROPIC)

    def test_resolve_mixed_case(self):
        reset_call_counter()
        self.assertEqual(resolve("AnThRoPiC.cOm"), IP_ANTHROPIC)


class TestMaxQueriesZero(unittest.TestCase):
    """max_queries == 0: Spec says 'gives up after max_queries calls'.
    A budget of zero means we cannot make any call, so we must return None
    BEFORE calling send_query. (If the solution always makes one query first
    and then checks, this test will catch it: send_query was called.)"""

    def setUp(self):
        reset_call_counter()

    def test_zero_budget_returns_none(self):
        ip = resolve("anthropic.com", max_queries=0)
        self.assertIsNone(ip, "max_queries=0 should resolve to None")

    def test_zero_budget_makes_no_calls(self):
        # Even stronger: ZERO calls to send_query should occur.
        resolve("anthropic.com", max_queries=0)
        self.assertEqual(
            get_call_count(), 0,
            f"max_queries=0 must make 0 send_query calls, "
            f"but made {get_call_count()}",
        )


class TestMaxQueriesOne(unittest.TestCase):
    """max_queries == 1: succeed only if the answer arrives in 1 call."""

    def setUp(self):
        reset_call_counter()

    def test_one_query_against_three_hop_domain(self):
        # anthropic.com. needs 3 hops (root, com, anthropic_ns). With a
        # budget of 1, we cannot finish — must return None.
        ip = resolve("anthropic.com", max_queries=1)
        self.assertIsNone(ip, "1 query is not enough for anthropic.com")

    def test_one_query_against_root_nxdomain(self):
        # missing.example. NXDOMAINs in 1 query at root. The spec says
        # cycle-detection gives up AFTER max_queries calls. NXDOMAIN at
        # root is decided by query #1, so it should resolve to None
        # (the NXDOMAIN-None, not the budget-None — but both are None,
        # so this just checks it doesn't crash or loop).
        ip = resolve("missing.example", max_queries=1)
        self.assertIsNone(ip)
        self.assertEqual(get_call_count(), 1,
                         "Should have made exactly 1 query for NXDOMAIN at root")


class TestNSGlueIPv4Selection(unittest.TestCase):
    """Spec says glue 'A' is IPv4 and 'AAAA' (IPv6) should be ignored.
    Every _delegate() in the mock returns BOTH an AAAA and an A glue
    record — if the resolver picks the AAAA rdata as a server IP,
    send_query will reject it with ValueError. This is implicitly
    tested by every passing resolution, but we make it explicit."""

    def setUp(self):
        reset_call_counter()

    def test_resolver_never_uses_aaaa_glue_as_server_ip(self):
        # If the resolver were picking the AAAA glue (an IPv6 string like
        # '2001:db8::1'), send_query would raise ValueError. So a clean
        # resolution is proof.
        ip = resolve("anthropic.com")
        self.assertEqual(ip, IP_ANTHROPIC)
        # And no IPv6-looking string should appear in the call log as a server.
        for name, server in get_call_log():
            self.assertNotIn(":", server,
                             f"Server IP looks like IPv6: {server!r}")


class TestMixedGlueOrdering(unittest.TestCase):
    """authority lists where glue/no-glue NSes appear in different orders."""

    def setUp(self):
        reset_call_counter()

    def test_unglued_first_must_skip_to_glued_second(self):
        # mixed.com.: NS1 (no glue) cannot be resolved → skip → NS2 (glue) wins
        ip = resolve("mixed.com", max_queries=20)
        self.assertEqual(ip, IP_MIXED)

    def test_glued_first_refused_falls_back_to_unglued_second(self):
        # glueorder.com.: NS1 (glue, REFUSED) → NS2 (no glue, recurses, wins)
        ip = resolve("glueorder.com", max_queries=20)
        self.assertEqual(ip, IP_GLUEORDER)

    def test_glueorder_with_tight_budget_fails_predictably(self):
        # glueorder.com requires 7 queries when fresh. Budget of 6 must fail.
        reset_call_counter()
        ip = resolve("glueorder.com", max_queries=6)
        self.assertIsNone(ip, "budget of 6 should be too small for glueorder.com")


# ─────── Concurrency stress ───────

class TestConcurrencyStress(unittest.TestCase):

    def setUp(self):
        reset_call_counter()
        set_in_flight_hold(0.0)

    def test_max_workers_one_serializes(self):
        # With max_workers=1, peak in-flight should never exceed 1.
        set_in_flight_hold(0.005)
        try:
            domains = ["anthropic.com", "example.com", "api.anthropic.com"]
            result = resolve_all(domains, max_workers=1)
        finally:
            set_in_flight_hold(0.0)
        self.assertEqual(set(result.keys()), set(domains))
        peak = get_peak_in_flight()
        self.assertLessEqual(
            peak, 1,
            f"max_workers=1 should fully serialize, peak was {peak}",
        )

    def test_max_workers_exceeds_domain_count(self):
        # 10 workers against only 3 domains must not crash, and peak ≤ 10.
        domains = ["anthropic.com", "example.com", "api.anthropic.com"]
        result = resolve_all(domains, max_workers=10)
        self.assertEqual(set(result.keys()), set(domains))
        self.assertLessEqual(get_peak_in_flight(), 10)

    def test_empty_input_returns_empty_dict(self):
        result = resolve_all([], max_workers=5)
        self.assertEqual(result, {})
        self.assertEqual(get_call_count(), 0)

    def test_empty_input_max_workers_zero(self):
        # max_workers=0 with empty list — should not crash (no work to do).
        try:
            result = resolve_all([], max_workers=0)
        except Exception as e:
            self.fail(f"resolve_all([], max_workers=0) raised: {e!r}")
        self.assertEqual(result, {})

    def test_large_input_completes(self):
        # 50 domains (mixed across the topology) should resolve.
        names = [
            "anthropic.com", "example.com", "api.anthropic.com",
            "store.example.com", "cdn.fastcdn.net", "shop.fastcdn.net",
            "deadns.com", "missing.example", "broken.com",
            "mixed.com",
        ]
        # Repeat to get 50.
        domains = (names * 5)[:50]
        result = resolve_all(domains, max_workers=5, max_queries=30)
        # All 10 unique inputs must be present as keys.
        self.assertEqual(set(result.keys()), set(names))
        # Spot-check a couple of successes.
        self.assertEqual(result["anthropic.com"], IP_ANTHROPIC)
        self.assertEqual(result["cdn.fastcdn.net"], IP_CDN_FASTCDN)
        # And a couple of failures.
        self.assertIsNone(result["missing.example"])
        self.assertIsNone(result["broken.com"])

    def test_in_flight_cap_under_load(self):
        # Force overlap so the cap matters; many domains, max_workers=3.
        set_in_flight_hold(0.01)
        try:
            domains = [
                "anthropic.com", "api.anthropic.com",
                "example.com", "www.example.com", "store.example.com",
                "shop.fastcdn.net", "cdn.fastcdn.net",
                "deadns.com",
            ]
            result = resolve_all(domains, max_workers=3, max_queries=30)
        finally:
            set_in_flight_hold(0.0)
        self.assertEqual(set(result.keys()), set(domains))
        peak = get_peak_in_flight()
        self.assertLessEqual(
            peak, 3,
            f"max_workers=3 violated: peak in-flight was {peak}",
        )


class TestErrorPropagationConcurrent(unittest.TestCase):
    """Mix successes, NXDOMAIN, and REFUSED in one batch — every input
    string must appear as a key in the result dict (None on failure)."""

    def setUp(self):
        reset_call_counter()

    def test_mixed_outcomes_all_present(self):
        domains = [
            "anthropic.com",      # success
            "missing.example",    # NXDOMAIN at root → None
            "broken.com",         # both NSes REFUSED → None
            "example.com",        # success
        ]
        result = resolve_all(domains, max_workers=4, max_queries=30)
        self.assertEqual(set(result.keys()), set(domains))
        self.assertEqual(result["anthropic.com"], IP_ANTHROPIC)
        self.assertIsNone(result["missing.example"])
        self.assertIsNone(result["broken.com"])
        self.assertEqual(result["example.com"], IP_EXAMPLE)

    def test_serial_mixed_outcomes_all_present(self):
        # Same test but max_workers=1 to isolate ordering vs concurrency.
        domains = ["broken.com", "anthropic.com", "missing.example"]
        result = resolve_all(domains, max_workers=1, max_queries=30)
        self.assertEqual(set(result.keys()), set(domains))


class TestInputOrderPreservation(unittest.TestCase):
    """Spec doesn't mandate it, but the natural reading of 'a mapping from
    each input domain to its resolved IP' is to iterate the result in
    input order. CPython dicts preserve insertion order, so this is a
    legitimate ergonomic expectation. Mark this as 'might be over-reach'
    if it fails — it's an implicit-spec test."""

    def setUp(self):
        reset_call_counter()

    def test_input_order_preserved_serial(self):
        domains = ["example.com", "anthropic.com", "api.anthropic.com"]
        result = resolve_all(domains, max_workers=1, max_queries=30)
        self.assertEqual(list(result.keys()), domains,
                         "Result dict should iterate in input order")

    def test_input_order_preserved_concurrent(self):
        # Concurrency shouldn't reorder the result dict.
        domains = [
            "store.example.com", "anthropic.com", "missing.example",
            "broken.com", "example.com",
        ]
        result = resolve_all(domains, max_workers=5, max_queries=30)
        self.assertEqual(list(result.keys()), domains,
                         "Result dict should iterate in input order")


class TestCacheScoping(unittest.TestCase):
    """The cache must be scoped to each resolve_all() call."""

    def setUp(self):
        reset_call_counter()

    def test_separate_calls_do_not_share_cache(self):
        # First call populates a hypothetical cache.
        result1 = resolve_all(["anthropic.com"], max_workers=1, max_queries=30)
        count_after_first = get_call_count()
        self.assertGreater(count_after_first, 0)
        self.assertEqual(result1["anthropic.com"], IP_ANTHROPIC)

        # Second call MUST start fresh — it should make at least as many
        # send_query calls as the first one (because nothing carries over).
        before_second = get_call_count()
        result2 = resolve_all(["anthropic.com"], max_workers=1, max_queries=30)
        count_added_by_second = get_call_count() - before_second

        self.assertEqual(result2["anthropic.com"], IP_ANTHROPIC)
        self.assertEqual(
            count_added_by_second, count_after_first,
            f"Second resolve_all should make the same number of calls as "
            f"the first ({count_after_first}); made {count_added_by_second}. "
            f"Cache may be leaking across calls.",
        )

    def test_solo_resolve_does_not_share_cache_with_resolve_all(self):
        # A bare resolve() should not see resolve_all()'s cache, and vice versa.
        # First, prime via resolve_all.
        resolve_all(["anthropic.com"], max_workers=1, max_queries=30)
        baseline_count = get_call_count()
        # Now a solo resolve — should make its own queries.
        before = get_call_count()
        ip = resolve("anthropic.com")
        added = get_call_count() - before
        self.assertEqual(ip, IP_ANTHROPIC)
        self.assertGreater(
            added, 0,
            "resolve() must not see cache from a previous resolve_all() call",
        )


class TestCaseEquivalentInputs(unittest.TestCase):
    """Within ONE resolve_all, two inputs that normalize to the same name
    should both appear as distinct keys in the output dict, and both
    should resolve to the same IP. The cache should treat them as one."""

    def setUp(self):
        reset_call_counter()

    def test_two_case_variants_both_present(self):
        domains = ["anthropic.com", "ANTHROPIC.COM"]
        result = resolve_all(domains, max_workers=1, max_queries=30)
        self.assertEqual(set(result.keys()), set(domains))
        self.assertEqual(result["anthropic.com"], IP_ANTHROPIC)
        self.assertEqual(result["ANTHROPIC.COM"], IP_ANTHROPIC)

    def test_dot_variants_both_present(self):
        domains = ["anthropic.com", "anthropic.com."]
        result = resolve_all(domains, max_workers=1, max_queries=30)
        self.assertEqual(set(result.keys()), set(domains))
        self.assertEqual(result["anthropic.com"], IP_ANTHROPIC)
        self.assertEqual(result["anthropic.com."], IP_ANTHROPIC)

    def test_case_variants_share_cache(self):
        # If the cache normalizes properly, two case-variants of the same
        # domain in one batch should NOT each pay the full query cost.
        # Compute solo cost first.
        reset_call_counter()
        resolve_all(["anthropic.com"], max_workers=1, max_queries=30)
        solo_cost = get_call_count()

        # Now batch two case-variants. Total cost should NOT be ~2x solo —
        # the second one should hit cache for everything.
        reset_call_counter()
        resolve_all(["anthropic.com", "ANTHROPIC.COM"],
                    max_workers=1, max_queries=30)
        batch_cost = get_call_count()
        self.assertLess(
            batch_cost, 2 * solo_cost,
            f"Two case-variants paid {batch_cost} queries, but solo costs "
            f"{solo_cost} — cache may not be normalizing names",
        )

    def test_duplicate_inputs_collapse_keys(self):
        # Real edge case: the input list has the SAME string twice.
        # Python dict keys collapse — there's only one key in the result.
        # We just want to verify resolve_all doesn't crash and the
        # value is correct.
        domains = ["anthropic.com", "anthropic.com"]
        result = resolve_all(domains, max_workers=1, max_queries=30)
        self.assertIn("anthropic.com", result)
        self.assertEqual(result["anthropic.com"], IP_ANTHROPIC)


class TestPerDomainBudgetWithCache(unittest.TestCase):
    """The spec says: 'A cache hit does not call send_query, but still
    counts against the limit for that domain.' So a domain whose path
    overlaps a previously-resolved domain can fail purely because cache
    HITS exhausted its budget."""

    def setUp(self):
        reset_call_counter()

    def test_budget_exhausted_by_cache_hits(self):
        # First, find the natural cost of www.example.com.
        reset_call_counter()
        ip = resolve("www.example.com")
        natural_cost = get_call_count()
        self.assertEqual(ip, IP_EXAMPLE)
        self.assertEqual(natural_cost, 6,
                         "Sanity: www.example.com naturally costs 6 queries")

        # Now: in a single resolve_all batch, prime the cache with example.com
        # (cost 3), then ask for www.example.com (which would normally cost 6
        # but with a max_queries=5 budget, it must fail because the cache
        # hits on (example.com, ROOT/COM/EXAMPLE_NS) still count.
        reset_call_counter()
        result = resolve_all(
            ["example.com", "www.example.com"],
            max_workers=1,
            max_queries=5,  # tight enough that cache hits exhaust the budget
        )
        self.assertEqual(result["example.com"], IP_EXAMPLE,
                         "example.com on its own only needs 3 queries")
        self.assertIsNone(
            result["www.example.com"],
            "www.example.com should fail: 6-query budget vs. max_queries=5 "
            "(3 fresh + 3 cache hits both count)",
        )

    def test_budget_just_enough_with_cache_hits(self):
        # Same setup but with max_queries=6 — should succeed.
        reset_call_counter()
        result = resolve_all(
            ["example.com", "www.example.com"],
            max_workers=1,
            max_queries=6,
        )
        self.assertEqual(result["example.com"], IP_EXAMPLE)
        self.assertEqual(result["www.example.com"], IP_EXAMPLE,
                         "max_queries=6 is exactly enough for www.example.com")

    def test_solo_resolve_with_max_queries_one_for_root_nxdomain(self):
        # Spec ambiguity: max_queries=1 on a domain that NXDOMAINs at root.
        # The NXDOMAIN is decided BY query #1 — does cycle detection trigger
        # before or after we look at the response? The reasonable reading
        # is that the answer is whatever query #1 returned, so None
        # (because NXDOMAIN means definitely-doesn't-exist).
        # Either way, the result must be None, and the call count must
        # not exceed 1.
        ip = resolve("missing.example", max_queries=1)
        self.assertIsNone(ip)
        self.assertLessEqual(
            get_call_count(), 1,
            f"max_queries=1 must not exceed 1 send_query call, "
            f"but made {get_call_count()}",
        )


class TestSingleFlightWithinBatch(unittest.TestCase):
    """Step 7 says: 'If a query is already in-flight from another domain's
    resolution, wait for it rather than sending a duplicate.'
    Concurrent resolutions sharing a path must NOT each issue the same
    (name, server) query."""

    def setUp(self):
        reset_call_counter()

    def test_overlapping_paths_share_in_flight_queries(self):
        # Force overlap so all resolutions are concurrent.
        set_in_flight_hold(0.02)
        try:
            # Three DIFFERENT Anthropic-family domains. They share the
            # (anthropic.com., ROOT) and (anthropic.com., COM) prefix
            # only via the common .com TLD delegation lookup. Each unique
            # (name, server) tuple must appear at most once in the call log.
            domains = ["anthropic.com", "api.anthropic.com", "example.com"]
            result = resolve_all(domains, max_workers=5, max_queries=30)
        finally:
            set_in_flight_hold(0.0)
        self.assertEqual(result["anthropic.com"], IP_ANTHROPIC)
        self.assertEqual(result["api.anthropic.com"], IP_API_ANTHROPIC)
        self.assertEqual(result["example.com"], IP_EXAMPLE)
        # Each unique (name, server) tuple should appear at most once.
        # If single-flight is broken, concurrent resolutions for the
        # same (name, server) would each issue their own query.
        unique_calls = set(get_call_log())
        total_calls = len(get_call_log())
        self.assertEqual(
            total_calls, len(unique_calls),
            f"Single-flight violated: {total_calls} calls but only "
            f"{len(unique_calls)} are unique (name, server) pairs",
        )

    def test_same_name_concurrent_dedupes(self):
        # A subtler single-flight test: case-variants of the same domain
        # in one batch. They normalize to the same name, so concurrent
        # resolution should issue each (name, server) at most once.
        set_in_flight_hold(0.02)
        try:
            domains = ["anthropic.com", "ANTHROPIC.COM", "Anthropic.Com"]
            result = resolve_all(domains, max_workers=5, max_queries=30)
        finally:
            set_in_flight_hold(0.0)
        self.assertEqual(set(result.keys()), set(domains))
        for k in domains:
            self.assertEqual(result[k], IP_ANTHROPIC, f"key={k!r}")
        unique_calls = set(get_call_log())
        total_calls = len(get_call_log())
        self.assertEqual(
            total_calls, len(unique_calls),
            f"Single-flight violated for case-variants: {total_calls} "
            f"calls but {len(unique_calls)} unique pairs",
        )


class TestNXDOMAINGivesUpImmediately(unittest.TestCase):
    """Spec (level 4): NXDOMAIN means 'definitely doesn't exist' — no
    point trying another NS. The resolver should return None at the
    very first NXDOMAIN, NOT cycle through the rest of the authority
    list."""

    def setUp(self):
        reset_call_counter()

    def test_nxdomain_at_root_returns_quickly(self):
        ip = resolve("missing.example", max_queries=15)
        self.assertIsNone(ip)
        # missing.example is NXDOMAIN at ROOT — exactly 1 call.
        self.assertEqual(
            get_call_count(), 1,
            f"NXDOMAIN at root should take 1 query, took {get_call_count()}",
        )


class TestCycleDetectionBoundary(unittest.TestCase):
    """The CNAME loop loop-a.test ↔ loop-b.test naturally consumes
    queries forever. With max_queries=N, we should make ≤ N calls and
    return None."""

    def setUp(self):
        reset_call_counter()

    def test_loop_respects_budget_exactly(self):
        # Try several budgets and verify each one stops at-or-before the limit.
        for budget in [3, 5, 10, 15]:
            with self.subTest(budget=budget):
                reset_call_counter()
                ip = resolve("loop-a.test", max_queries=budget)
                self.assertIsNone(ip)
                self.assertLessEqual(
                    get_call_count(), budget,
                    f"budget={budget}, made {get_call_count()} queries",
                )


class TestResolveAllSinglesAreFreshCache(unittest.TestCase):
    """Each call to resolve_all should be hermetic. If the user makes
    N small calls, the total call count should equal N * solo cost
    (no leakage), and within any single call, repeated identical
    domains should pay the cost once."""

    def setUp(self):
        reset_call_counter()

    def test_three_separate_calls_three_full_costs(self):
        # Solo cost.
        reset_call_counter()
        resolve_all(["anthropic.com"], max_workers=1, max_queries=30)
        solo = get_call_count()

        # Three independent calls.
        reset_call_counter()
        for _ in range(3):
            resolve_all(["anthropic.com"], max_workers=1, max_queries=30)
        total = get_call_count()
        self.assertEqual(
            total, 3 * solo,
            f"3 calls × {solo} = {3*solo} expected, got {total}. "
            f"Cache may be leaking across calls.",
        )


# ─────── Runner: print pass/fail counts ───────

if __name__ == "__main__":
    # Use a buffered runner so failures are easy to read at the end.
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 60)
    print(f"Total tests : {result.testsRun}")
    print(f"Failures    : {len(result.failures)}")
    print(f"Errors      : {len(result.errors)}")
    print(f"Skipped     : {len(result.skipped)}")
    print("=" * 60)

    sys.exit(0 if result.wasSuccessful() else 1)
