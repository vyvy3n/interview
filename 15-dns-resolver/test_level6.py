"""Level 6 — cached batch resolution via resolve_all().

Tests cover every spec bullet from Step 6:
  - keys preserve input form (not normalized)
  - cache (name, server) -> response, scoped to this call
  - NXDOMAIN AND REFUSED responses are cached (not just NOERROR)
  - max_queries is per-domain
  - cache hits do not call send_query but still count against per-domain budget
"""
import unittest

from _fixtures import (
    SCENARIO_BASIC,
    scenario_all_ns_fail,
    scenario_batch_overlap,
    scenario_nxdomain,
)
from dns_mock import install_scenario, query_count
from solution import resolve_all


class TestBatchKeyPreservation(unittest.TestCase):
    def setUp(self):
        install_scenario(SCENARIO_BASIC)

    def test_keys_match_input_form(self):
        # Input case + missing trailing dot must be preserved in result keys.
        result = resolve_all(["Anthropic.COM", "anthropic.com."])
        self.assertEqual(result, {
            "Anthropic.COM": "160.79.104.10",
            "anthropic.com.": "160.79.104.10",
        })


class TestBatchDedupesDuplicates(unittest.TestCase):
    def setUp(self):
        install_scenario(SCENARIO_BASIC)

    def test_duplicate_inputs_only_query_once(self):
        # Two identical inputs should not double the network traffic.
        resolve_all(["anthropic.com", "anthropic.com", "anthropic.com"])
        # 3 hops to resolve, cached on the first → still 3 total queries.
        self.assertEqual(query_count(), 3)


class TestBatchSharesOverlappingPaths(unittest.TestCase):
    def setUp(self):
        install_scenario(scenario_batch_overlap())

    def test_overlapping_paths_share_cache(self):
        result = resolve_all([
            "www.example.com",
            "api.example.com",
            "cdn.example.com",
        ])
        self.assertEqual(result, {
            "www.example.com": "93.184.216.1",
            "api.example.com": "93.184.216.2",
            "cdn.example.com": "93.184.216.3",
        })
        # Each domain has 3 unique queries (different name at each tier).
        # No (name, server) pair repeats → 9 total send_query calls.
        self.assertEqual(query_count(), 9)


class TestBatchEmpty(unittest.TestCase):
    def setUp(self):
        install_scenario(SCENARIO_BASIC)

    def test_empty_input_returns_empty_dict(self):
        self.assertEqual(resolve_all([]), {})


class TestBatchCacheIsScopedToCall(unittest.TestCase):
    def setUp(self):
        install_scenario(SCENARIO_BASIC)

    def test_second_call_does_full_work_again(self):
        resolve_all(["anthropic.com"])
        first = query_count()
        resolve_all(["anthropic.com"])
        # Cache must NOT survive across resolve_all() calls.
        self.assertEqual(query_count(), 2 * first)


class TestNxdomainCached(unittest.TestCase):
    """Per Step 6 spec: NXDOMAIN responses should also be cached."""

    def setUp(self):
        install_scenario(scenario_nxdomain())

    def test_nxdomain_only_queried_once_for_duplicate_inputs(self):
        result = resolve_all(["missing.example", "Missing.Example"])
        self.assertIsNone(result["missing.example"])
        self.assertIsNone(result["Missing.Example"])
        # Both inputs normalize to "missing.example.", same cache key.
        # First → 1 send_query (NXDOMAIN). Second → cache hit, 0 send_query.
        self.assertEqual(query_count(), 1)


class TestRefusedCached(unittest.TestCase):
    """Per Step 6 spec: REFUSED responses should also be cached."""

    def setUp(self):
        install_scenario(scenario_all_ns_fail())

    def test_refused_paths_only_walked_once(self):
        # Walking broken.com: root (NS delegation), com_tld (2 NS records),
        # ns1 (REFUSED), ns2 (REFUSED). 4 send_query calls per domain
        # if not cached. With caching, the second copy hits all 4 from cache.
        result = resolve_all(["broken.com", "Broken.COM"])
        self.assertIsNone(result["broken.com"])
        self.assertIsNone(result["Broken.COM"])
        self.assertEqual(query_count(), 4)


class TestMaxQueriesIsPerDomain(unittest.TestCase):
    """Per Step 6 spec: max_queries is the limit per domain."""

    def setUp(self):
        install_scenario(SCENARIO_BASIC)

    def test_per_domain_budget_does_not_share_across_domains(self):
        # 3-hop chain. max_queries=3 is exactly enough.
        # If max_queries were per-batch, the second resolve would have 0 budget
        # and fail. Per-domain: each starts fresh.
        result = resolve_all(
            ["anthropic.com.", "Anthropic.COM"],
            max_queries=3,
        )
        self.assertEqual(result["anthropic.com."], "160.79.104.10")
        self.assertEqual(result["Anthropic.COM"], "160.79.104.10")


class TestCacheHitsCountAgainstMaxQueries(unittest.TestCase):
    """Per Step 6 spec: 'A cache hit does not call send_query, but still
    counts against the limit for that domain.'"""

    def setUp(self):
        install_scenario(SCENARIO_BASIC)

    def test_cache_hits_consume_per_domain_budget(self):
        # max_queries=2 against a 3-hop chain.
        # First resolve: completes 2 send_query (cached), then exhausts budget
        # before the 3rd hop → returns None. Cache now has 2 entries.
        # Second resolve (same name): hits cache twice (consuming budget=2),
        # then needs the 3rd hop. Two outcomes possible:
        #   - Cache hits count (per spec): exhausts budget at hop 3 → None.
        #   - Cache hits don't count: would call send_query, complete chain → IP.
        # Spec says cache hits count, so both must be None.
        result = resolve_all(["anthropic.com", "Anthropic.COM"], max_queries=2)
        self.assertIsNone(result["anthropic.com"])
        self.assertIsNone(result["Anthropic.COM"])


if __name__ == "__main__":
    unittest.main()
