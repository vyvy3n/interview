"""Level 5 — cycle detection via max_queries cap."""
import unittest

from _fixtures import (
    SCENARIO_BASIC,
    scenario_cname_loop,
    scenario_glue_cycle,
)
from dns_mock import install_scenario, query_count
from solution import resolve


class TestCnameLoop(unittest.TestCase):
    def setUp(self):
        install_scenario(scenario_cname_loop(), limit=10_000)

    def test_cname_loop_returns_none_via_max_queries(self):
        # A → B → A loop — must give up at max_queries, not infinite-loop.
        self.assertIsNone(resolve("a.example", max_queries=15))


class TestGlueCycle(unittest.TestCase):
    def setUp(self):
        install_scenario(scenario_glue_cycle(), limit=10_000)

    def test_glue_cycle_returns_none(self):
        self.assertIsNone(resolve("x.alpha", max_queries=15))


class TestMaxQueriesRespected(unittest.TestCase):
    def setUp(self):
        install_scenario(SCENARIO_BASIC, limit=10_000)

    def test_clean_resolve_uses_few_queries(self):
        # Sanity: a 3-hop resolve should NOT trip max_queries.
        self.assertEqual(resolve("anthropic.com", max_queries=15), "160.79.104.10")
        self.assertLess(query_count(), 15)

    def test_low_max_queries_kills_resolve(self):
        # With max_queries=2 we can't reach the answer (needs 3 hops).
        self.assertIsNone(resolve("anthropic.com", max_queries=2))


if __name__ == "__main__":
    unittest.main()
