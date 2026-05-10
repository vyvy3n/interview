"""Level 6 — cached batch resolution via resolve_all()."""
import unittest

from _fixtures import SCENARIO_BASIC, scenario_batch_overlap
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


if __name__ == "__main__":
    unittest.main()
