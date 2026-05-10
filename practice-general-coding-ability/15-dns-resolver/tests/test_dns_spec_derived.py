"""Spec-derived independent test suite for DNS resolver.

Written without reading solution.py or tests/test_dns.py — derived purely
from spec/level1.md..level7.md, dns_types.py, and dns_mock.py topology.

The goal is adversarial: catch implementations that pass the existing
suite but violate the spec. Tests assert both result correctness and
the exact sequence of send_query calls (where the spec dictates a
specific traversal).
"""
import os
import sys
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

# Make the project root importable when running this file directly.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(HERE)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from solution import normalize, resolve, resolve_all  # noqa: E402
from dns_mock import (  # noqa: E402
    ROOT, COM, NET,
    ROOT_SERVER, COM_TLD, NET_TLD,
    ANTHROPIC_NS, API_ANTHROPIC_NS, CLOUDFLARE_NS,
    EXAMPLE_NS, FASTCDN_NS,
    DEAD_NS, DEADNS_BACKUP,
    reset_call_counter, get_call_count, get_call_log, get_peak_in_flight,
    set_in_flight_hold,
)


# ─────────────────────────────────────────────────────────────────────────
# Step 0 — normalize()
# Spec: lowercase + ensure trailing dot.
# ─────────────────────────────────────────────────────────────────────────
class TestStep0(unittest.TestCase):
    def test_already_normalized_passthrough(self):
        self.assertEqual(normalize("anthropic.com."), "anthropic.com.")

    def test_lowercases_uppercase(self):
        self.assertEqual(normalize("ANTHROPIC.COM"), "anthropic.com.")

    def test_lowercases_mixed_case(self):
        self.assertEqual(normalize("Docs.Anthropic.Com"), "docs.anthropic.com.")

    def test_adds_trailing_dot_when_missing(self):
        self.assertEqual(normalize("anthropic.com"), "anthropic.com.")

    def test_does_not_double_trailing_dot(self):
        # If the name already ends in a dot, we must not add a second one.
        result = normalize("anthropic.com.")
        self.assertTrue(result.endswith("."))
        self.assertFalse(result.endswith(".."))

    def test_uppercase_with_trailing_dot(self):
        self.assertEqual(normalize("ANTHROPIC.COM."), "anthropic.com.")

    def test_subdomain(self):
        self.assertEqual(normalize("Api.Anthropic.Com"), "api.anthropic.com.")

    def test_root_label_only_dot(self):
        # The root zone is just "." — should remain a single dot,
        # not become "..".
        self.assertEqual(normalize("."), ".")


# ─────────────────────────────────────────────────────────────────────────
# Step 1 — basic delegation, NOERROR only.
# Walks ROOT → TLD → authoritative, single NS, glue present.
# ─────────────────────────────────────────────────────────────────────────
class TestStep1(unittest.TestCase):
    def setUp(self):
        reset_call_counter()

    def test_resolves_anthropic_com(self):
        ip = resolve("anthropic.com.")
        self.assertEqual(ip, "160.79.104.10")

    def test_anthropic_com_query_sequence(self):
        resolve("anthropic.com.")
        self.assertEqual(get_call_log(), [
            ("anthropic.com.", ROOT),
            ("anthropic.com.", COM),
            ("anthropic.com.", ANTHROPIC_NS),
        ])

    def test_anthropic_com_uses_exactly_three_queries(self):
        resolve("anthropic.com.")
        self.assertEqual(get_call_count(), 3)

    def test_normalizes_input_to_resolve(self):
        # The user might pass a non-normalized name; resolve must normalize
        # before any send_query call (which would reject uppercase / no dot).
        ip = resolve("Anthropic.COM")
        self.assertEqual(ip, "160.79.104.10")

    def test_normalizes_no_trailing_dot(self):
        ip = resolve("anthropic.com")
        self.assertEqual(ip, "160.79.104.10")

    def test_first_query_goes_to_root(self):
        resolve("anthropic.com.")
        log = get_call_log()
        self.assertGreater(len(log), 0)
        self.assertEqual(log[0][1], ROOT,
                         "First send_query must target ROOT_SERVER")

    def test_first_query_uses_normalized_name(self):
        resolve("ANTHROPIC.COM")
        log = get_call_log()
        self.assertEqual(log[0][0], "anthropic.com.",
                         "First query must use the normalized name")


# ─────────────────────────────────────────────────────────────────────────
# Step 2 — CNAME single + multi-hop.
# Spec: on CNAME answer, restart from root with rdata.
# ─────────────────────────────────────────────────────────────────────────
class TestStep2(unittest.TestCase):
    def setUp(self):
        reset_call_counter()

    def test_single_hop_cname(self):
        # www.example.com. → CNAME example.com. → A 93.184.216.34
        ip = resolve("www.example.com.")
        self.assertEqual(ip, "93.184.216.34")

    def test_single_hop_cname_call_sequence(self):
        resolve("www.example.com.")
        self.assertEqual(get_call_log(), [
            ("www.example.com.", ROOT),
            ("www.example.com.", COM),
            ("www.example.com.", EXAMPLE_NS),
            # CNAME → restart from root for example.com.
            ("example.com.", ROOT),
            ("example.com.", COM),
            ("example.com.", EXAMPLE_NS),
        ])

    def test_multi_hop_cname_resolves(self):
        # store.example.com. → CNAME shop.fastcdn.net. → CNAME cdn.fastcdn.net. → A
        ip = resolve("store.example.com.", max_queries=20)
        self.assertEqual(ip, "203.0.113.99")

    def test_multi_hop_cname_call_sequence(self):
        resolve("store.example.com.", max_queries=20)
        self.assertEqual(get_call_log(), [
            ("store.example.com.", ROOT),
            ("store.example.com.", COM),
            ("store.example.com.", EXAMPLE_NS),
            # CNAME → shop.fastcdn.net.
            ("shop.fastcdn.net.", ROOT),
            ("shop.fastcdn.net.", NET),
            ("shop.fastcdn.net.", FASTCDN_NS),
            # CNAME → cdn.fastcdn.net.
            ("cdn.fastcdn.net.", ROOT),
            ("cdn.fastcdn.net.", NET),
            ("cdn.fastcdn.net.", FASTCDN_NS),
        ])

    def test_cname_restarts_from_root_not_continues(self):
        # The spec says on CNAME we restart "from the root server".
        # After the first CNAME hop in www.example.com., the next query
        # must be to ROOT (not to EXAMPLE_NS again).
        resolve("www.example.com.")
        log = get_call_log()
        # Find the CNAME-receiving query and verify the next is ROOT.
        # The 3rd call (index 2) returned the CNAME; next call must be ROOT.
        self.assertEqual(log[3][1], ROOT,
                         "After CNAME, must restart from ROOT_SERVER")


# ─────────────────────────────────────────────────────────────────────────
# Step 3 — Missing glue records: recursively resolve NS name first.
# ─────────────────────────────────────────────────────────────────────────
class TestStep3(unittest.TestCase):
    def setUp(self):
        reset_call_counter()

    def test_api_anthropic_com_resolves(self):
        # api.anthropic.com → NS gemma.ns.cloudflare.com (no glue).
        # Resolve gemma.ns.cloudflare.com → API_ANTHROPIC_NS, then continue.
        ip = resolve("api.anthropic.com.", max_queries=20)
        self.assertEqual(ip, "104.16.1.1")

    def test_api_anthropic_com_call_sequence(self):
        resolve("api.anthropic.com.", max_queries=20)
        self.assertEqual(get_call_log(), [
            ("api.anthropic.com.", ROOT),
            ("api.anthropic.com.", COM),
            # No glue for gemma.ns.cloudflare.com — recursively resolve it.
            ("gemma.ns.cloudflare.com.", ROOT),
            ("gemma.ns.cloudflare.com.", COM),
            ("gemma.ns.cloudflare.com.", CLOUDFLARE_NS),
            # Now continue resolving api.anthropic.com against API_ANTHROPIC_NS.
            ("api.anthropic.com.", API_ANTHROPIC_NS),
        ])

    def test_recursive_ns_resolution_starts_from_root(self):
        # The spec says "starting from the root server, just like any other
        # resolution". So when we go off to resolve gemma.ns.cloudflare.com.,
        # the first query for that name must hit ROOT.
        resolve("api.anthropic.com.", max_queries=20)
        log = get_call_log()
        # Find first occurrence of gemma.ns.cloudflare.com. in log.
        for name, server in log:
            if name == "gemma.ns.cloudflare.com.":
                self.assertEqual(server, ROOT,
                                 "Recursive NS resolution must start at ROOT")
                return
        self.fail("Expected a query for gemma.ns.cloudflare.com.")


# ─────────────────────────────────────────────────────────────────────────
# Step 4 — Multiple NS, REFUSED fallback, NXDOMAIN giveup.
# ─────────────────────────────────────────────────────────────────────────
class TestStep4(unittest.TestCase):
    def setUp(self):
        reset_call_counter()

    def test_refused_falls_back_to_next_ns(self):
        # deadns.com — first NS DEAD_NS returns REFUSED, second succeeds.
        ip = resolve("deadns.com.", max_queries=20)
        self.assertEqual(ip, "192.0.2.99")

    def test_refused_fallback_call_sequence(self):
        resolve("deadns.com.", max_queries=20)
        self.assertEqual(get_call_log(), [
            ("deadns.com.", ROOT),
            ("deadns.com.", COM),
            ("deadns.com.", DEAD_NS),       # REFUSED
            ("deadns.com.", DEADNS_BACKUP), # answers
        ])

    def test_all_ns_refused_returns_none(self):
        # broken.com — both NS return REFUSED → return None.
        result = resolve("broken.com.", max_queries=20)
        self.assertIsNone(result)

    def test_all_ns_refused_call_sequence(self):
        resolve("broken.com.", max_queries=20)
        log = get_call_log()
        self.assertEqual(log, [
            ("broken.com.", ROOT),
            ("broken.com.", COM),
            ("broken.com.", DEAD_NS),
            ("broken.com.", "192.0.2.99"),
        ])

    def test_nxdomain_returns_none_immediately(self):
        # missing.example. → NXDOMAIN at root → return None, no more queries.
        result = resolve("missing.example.", max_queries=20)
        self.assertIsNone(result)

    def test_nxdomain_does_not_try_other_paths(self):
        # Spec: NXDOMAIN means "the name definitely doesn't exist" — give up.
        # Should be exactly one query (ROOT only).
        resolve("missing.example.", max_queries=20)
        self.assertEqual(get_call_count(), 1)
        self.assertEqual(get_call_log(), [("missing.example.", ROOT)])

    def test_nxdomain_doesnotexist_invalid(self):
        result = resolve("doesnotexist.invalid.", max_queries=20)
        self.assertIsNone(result)
        self.assertEqual(get_call_count(), 1)


# ─────────────────────────────────────────────────────────────────────────
# Step 5 — Cycle detection via max_queries.
# ─────────────────────────────────────────────────────────────────────────
class TestStep5(unittest.TestCase):
    def setUp(self):
        reset_call_counter()

    def test_cname_cycle_returns_none(self):
        # loop-a → CNAME loop-b → CNAME loop-a → ...
        result = resolve("loop-a.test.", max_queries=15)
        self.assertIsNone(result)

    def test_cname_cycle_respects_max_queries_upper_bound(self):
        # Should give up by the time we hit max_queries calls.
        resolve("loop-a.test.", max_queries=15)
        self.assertLessEqual(get_call_count(), 15,
            "Resolver must stop at or before max_queries calls")

    def test_max_queries_allows_normal_resolution(self):
        # Default max_queries=15 must be enough for the normal anthropic.com case.
        ip = resolve("anthropic.com.", max_queries=15)
        self.assertEqual(ip, "160.79.104.10")

    def test_low_max_queries_aborts_normal_resolution(self):
        # If we set max_queries to 2 (below the 3 required), the resolution
        # cannot complete and should return None rather than blowing past
        # the limit.
        result = resolve("anthropic.com.", max_queries=2)
        self.assertIsNone(result)
        self.assertLessEqual(get_call_count(), 2)

    def test_max_queries_one_returns_none_for_complex_case(self):
        # max_queries=1 cannot complete a full resolution.
        result = resolve("anthropic.com.", max_queries=1)
        self.assertIsNone(result)
        self.assertLessEqual(get_call_count(), 1)


# ─────────────────────────────────────────────────────────────────────────
# Step 6 — resolve_all() with cache, scoped per call.
# ─────────────────────────────────────────────────────────────────────────
class TestStep6(unittest.TestCase):
    def setUp(self):
        reset_call_counter()

    def test_returns_dict_with_input_as_keys(self):
        # Spec: "return a mapping from each input domain... to its resolved IP".
        # Inputs are not necessarily normalized; the *keys* should be the
        # original inputs, not the normalized form.
        result = resolve_all(["Anthropic.COM"])
        self.assertIn("Anthropic.COM", result,
            "resolve_all must key by the original (un-normalized) input")
        self.assertEqual(result["Anthropic.COM"], "160.79.104.10")

    def test_resolves_each_domain(self):
        result = resolve_all(["anthropic.com.", "www.example.com."], max_queries=20)
        self.assertEqual(result.get("anthropic.com."), "160.79.104.10")
        self.assertEqual(result.get("www.example.com."), "93.184.216.34")

    def test_cache_eliminates_redundant_root_queries(self):
        # Two domains both query ROOT for ".com" delegation; the second
        # delegation lookup should be a cache hit, not a fresh send_query.
        # anthropic.com alone uses 3 calls. A second resolution of
        # anthropic.com (different input string but same normalized name)
        # should add zero new send_query calls because all three (name, server)
        # pairs are cached.
        before = get_call_count()
        resolve_all(["anthropic.com.", "Anthropic.COM"], max_queries=20)
        after = get_call_count()
        self.assertEqual(after - before, 3,
            "Resolving the same domain twice should hit the cache for all "
            "queries on the second pass")

    def test_cache_eliminates_redundant_path_queries(self):
        # anthropic.com and api.anthropic.com share the (name, ROOT) and
        # (name, COM) prefix with different *names*, so those are NOT shared.
        # But www.example.com. and example.com. should share a lot.
        # Let's instead verify with two anthropic queries that the second
        # shares everything.
        resolve_all(["anthropic.com."], max_queries=20)
        first_count = get_call_count()
        reset_call_counter()
        resolve_all(["anthropic.com.", "anthropic.com."], max_queries=20)
        second_count = get_call_count()
        # The second call's two anthropic.com lookups together should still
        # be exactly 3 send_queries (one full traversal, then all-cache-hits).
        self.assertEqual(second_count, first_count,
            "Duplicate domain in the same batch should reuse cache")

    def test_cache_is_scoped_per_call(self):
        # Spec: cache must NOT persist across resolve_all() invocations.
        resolve_all(["anthropic.com."], max_queries=20)
        first = get_call_count()
        # New call → fresh cache → must re-issue every query.
        resolve_all(["anthropic.com."], max_queries=20)
        second_total = get_call_count()
        self.assertEqual(second_total - first, first,
            "Cache must be scoped per resolve_all call")

    def test_nxdomain_is_cached(self):
        # Spec: "NXDOMAIN and REFUSED responses should also be cached."
        # Two NXDOMAIN lookups for the same name should issue only one query.
        resolve_all(["missing.example.", "missing.example."], max_queries=20)
        # Each NXDOMAIN lookup is 1 query against ROOT. With cache, second
        # is a hit → exactly 1 send_query call total.
        self.assertEqual(get_call_count(), 1,
            "NXDOMAIN response must be cached so duplicate lookups don't "
            "re-query")

    def test_refused_is_cached(self):
        # broken.com queries DEAD_NS and "192.0.2.99", both REFUSED.
        # Resolving broken.com twice should not re-issue the REFUSED queries.
        resolve_all(["broken.com.", "broken.com."], max_queries=20)
        # Single resolution of broken.com is 4 calls (ROOT, COM, DEAD_NS, .99).
        # With cache, the second resolution is all hits → still 4 total.
        self.assertEqual(get_call_count(), 4,
            "REFUSED responses must be cached")

    def test_cache_hit_counts_against_per_domain_max_queries(self):
        # Spec: "A cache hit does not call send_query, but still counts
        # against the limit for that domain."
        # Strategy: prime the cache with anthropic.com (3 cache entries),
        # then ask for anthropic.com again with max_queries=2. The second
        # resolution would hit cache 3 times but only 2 are allowed →
        # should return None.
        result = resolve_all(
            ["anthropic.com.", "anthropic.com."],
            max_queries=2,
        )
        # First resolution can't even complete with max_queries=2 (needs 3).
        # So the first one returns None. Both should return None.
        self.assertIsNone(result.get("anthropic.com."),
            "max_queries=2 cannot complete anthropic.com resolution; "
            "and cache hits must count toward the per-domain limit")

    def test_cache_hit_budget_blocks_completion(self):
        # Resolve anthropic.com once successfully (with adequate budget),
        # then in a SECOND batch with low budget, the cache won't help
        # because cache is per-call. So we need a single batch.
        # Better test: resolve www.example.com (6 calls) twice in one batch
        # with max_queries=5. The first one fails (needs 6). The second one
        # also fails because even cache hits count.
        result = resolve_all(
            ["www.example.com.", "www.example.com."],
            max_queries=5,
        )
        self.assertIsNone(result.get("www.example.com."),
            "www.example.com. needs 6 cache lookups; max_queries=5 means "
            "even the cached re-resolution must fail")

    def test_empty_input_returns_empty_dict(self):
        result = resolve_all([])
        self.assertEqual(result, {})
        self.assertEqual(get_call_count(), 0)

    def test_single_input(self):
        result = resolve_all(["anthropic.com."])
        self.assertEqual(result, {"anthropic.com.": "160.79.104.10"})

    def test_returns_none_for_unresolvable(self):
        result = resolve_all(["missing.example."])
        self.assertIn("missing.example.", result)
        self.assertIsNone(result["missing.example."])

    def test_mixed_success_and_failure(self):
        result = resolve_all(
            ["anthropic.com.", "missing.example.", "broken.com."],
            max_queries=20,
        )
        self.assertEqual(result["anthropic.com."], "160.79.104.10")
        self.assertIsNone(result["missing.example."])
        self.assertIsNone(result["broken.com."])

    def test_duplicate_input_returns_one_entry(self):
        # A dict can't have duplicate keys, so the same string twice
        # should appear once. Verify the value is correct.
        result = resolve_all(["anthropic.com.", "anthropic.com."])
        self.assertEqual(len(result), 1)
        self.assertEqual(result["anthropic.com."], "160.79.104.10")


# ─────────────────────────────────────────────────────────────────────────
# Step 7 — Bounded concurrency + in-flight dedup.
# ─────────────────────────────────────────────────────────────────────────
class TestStep7(unittest.TestCase):
    def setUp(self):
        reset_call_counter()
        set_in_flight_hold(0.0)

    def tearDown(self):
        set_in_flight_hold(0.0)

    def test_concurrency_cap_respected(self):
        # Issue many independent resolutions; with hold=50ms and max_workers=3,
        # peak in-flight must be <= 3.
        set_in_flight_hold(0.05)
        domains = [
            "anthropic.com.",
            "api.anthropic.com.",
            "www.example.com.",
            "store.example.com.",
            "deadns.com.",
            "broken.com.",
        ]
        resolve_all(domains, max_workers=3, max_queries=30)
        peak = get_peak_in_flight()
        self.assertLessEqual(peak, 3,
            f"max_workers=3 means at most 3 concurrent send_query calls; "
            f"peak observed: {peak}")

    def test_concurrency_actually_parallelizes(self):
        # With hold=100ms and max_workers=5, resolving 5 independent simple
        # domains should be substantially faster than sequential.
        set_in_flight_hold(0.05)
        domains = ["anthropic.com."] * 1  # warm one
        # Use distinct domains so caching doesn't make this trivially fast.
        domains = [
            "anthropic.com.",
            "api.anthropic.com.",
            "www.example.com.",
            "store.example.com.",
            "deadns.com.",
        ]
        start = time.time()
        resolve_all(domains, max_workers=5, max_queries=30)
        elapsed = time.time() - start
        # Sequential would be sum(query_count)*0.05. With max_workers=5,
        # we expect significantly less than the sequential lower bound.
        # Total queries for all 5: 3 + 6 + 6 + 9 + 4 = 28. Sequential ≈ 1.4s.
        # Parallel with 5 workers should be < 1.0s.
        self.assertLess(elapsed, 1.2,
            f"Expected parallel execution to be substantially faster; "
            f"elapsed={elapsed:.2f}s")

    def test_in_flight_dedup_no_duplicate_query(self):
        # If the same (name, server) is requested by two domains
        # simultaneously, only ONE send_query should be issued.
        # anthropic.com and Anthropic.COM resolve to the same normalized
        # name; both must hit ROOT for "anthropic.com." If we slow each
        # send_query down, the second domain's ROOT lookup should wait on
        # the first rather than sending its own.
        set_in_flight_hold(0.10)
        result = resolve_all(
            ["anthropic.com.", "Anthropic.COM"],
            max_workers=5,
            max_queries=20,
        )
        self.assertEqual(result.get("anthropic.com."), "160.79.104.10")
        self.assertEqual(result.get("Anthropic.COM"), "160.79.104.10")
        # Without dedup, both resolutions would issue 3 queries each = 6.
        # With dedup, only 3 unique (name, server) queries happen.
        self.assertEqual(get_call_count(), 3,
            "In-flight dedup: concurrent requests for the same (name, server)"
            " must share a single send_query call")

    def test_concurrent_results_correct(self):
        # Sanity: parallel execution must still produce correct results.
        domains = [
            "anthropic.com.",
            "api.anthropic.com.",
            "www.example.com.",
            "store.example.com.",
            "deadns.com.",
            "broken.com.",
            "missing.example.",
        ]
        result = resolve_all(domains, max_workers=4, max_queries=30)
        self.assertEqual(result["anthropic.com."], "160.79.104.10")
        self.assertEqual(result["api.anthropic.com."], "104.16.1.1")
        self.assertEqual(result["www.example.com."], "93.184.216.34")
        self.assertEqual(result["store.example.com."], "203.0.113.99")
        self.assertEqual(result["deadns.com."], "192.0.2.99")
        self.assertIsNone(result["broken.com."])
        self.assertIsNone(result["missing.example."])

    def test_default_max_workers_is_5(self):
        # Spec: "max_workers (default 5)"
        set_in_flight_hold(0.03)
        # Build enough work to reliably saturate concurrency.
        domains = [
            "anthropic.com.",
            "api.anthropic.com.",
            "www.example.com.",
            "store.example.com.",
            "deadns.com.",
            "broken.com.",
        ]
        resolve_all(domains, max_queries=30)
        self.assertLessEqual(get_peak_in_flight(), 5,
            "Default max_workers must be 5 (per spec)")

    def test_parallel_does_not_exceed_per_domain_max_queries(self):
        # Each domain's resolution must independently respect max_queries.
        # If we set max_queries=1, every domain must fail.
        result = resolve_all(
            ["anthropic.com.", "www.example.com."],
            max_workers=3,
            max_queries=1,
        )
        self.assertIsNone(result.get("anthropic.com."))
        self.assertIsNone(result.get("www.example.com."))


if __name__ == "__main__":
    unittest.main(verbosity=2)
